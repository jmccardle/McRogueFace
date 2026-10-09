# Native Profiling Workflow (Callgrind + perf)

External C++ profiling for engine hot-path work (issue #345). This is separate from
the in-engine `ProfilerOverlay` / `ProfilingMetrics` live HUD (`src/Profiler.*`,
`GameEngine.h`) — those show frame time / draw calls at runtime; this is for
diagnosing and A/B-validating C++ optimizations (e.g. #331, #342, #343, #344).

## The profiling build

The default `make` (Release, `-O3 -DNDEBUG`) keeps frame pointers (see
[Frame pointers](#frame-pointers-pep-831) below), so `perf --call-graph fp` can unwind
it, but it ships no DWARF and so can't be line-annotated. `make build-debug` (`-O0`)
profiles the wrong (unoptimized) code. For line-level work use the profiling build:

```bash
make profile
```

Produces `build-profile/mcrogueface`, configured `RelWithDebInfo` (`-O2 -g`) with
frame pointers forced on (CMake `-DMCRF_PROFILE=ON`). Not stripped. The build is
self-contained — `lib/`, `assets/`, and `scripts/` are copied next to the binary just
like the normal build, so `--headless --exec` works out of the box.

## Frame pointers (PEP 831)

[PEP 831](https://peps.python.org/pep-0831/) builds CPython 3.15 with
`-fno-omit-frame-pointer -mno-omit-leaf-frame-pointer` and asks embedders to do the
same. A frame-pointer unwinder (perf `--call-graph fp`, eBPF profilers, gdb on a stripped
core, the `perf` trampoline) follows saved-`%rbp` links up the stack and **stops at the
first function that omits one**. McRogueFace's stacks are interleaved, for example:

```
main → executeScript → mcrfpy.step → GameEngine::runSimFrame → Timer::test   (C++)
     → py::on_tick → py::update_world                                     (Python)
     → UIDrawable::set_float_member                                       (C++ binding)
```

Without frame pointers in the engine, a sample inside the binding unwinds through
libpython (which has them) and dies at `Timer::test`. The entire engine side of the
stack is lost, and that's the part that tells you *which* loop phase called into Python.

**CMake knob:** `MCRF_FRAME_POINTERS` (default `ON`; no-op for wasm and MSVC). Opt out
with `-DMCRF_FRAME_POINTERS=OFF`. `MCRF_PROFILE=ON` forces it on.

**Verify a build:**

```bash
# structural: every engine function that makes a call sets up %rbp
./mcrogueface --headless --exec ../tests/regression/issue_421_frame_pointer_test.py

# end to end, no perf permissions needed: stop in a binding, walk %rbp by hand
cd build && MCRF_PERF_TRAMPOLINE=1 gdb -q -batch -x ../tools/fp_walk_gdb.py \
    --args ./mcrogueface --headless --exec ../tests/benchmarks/fp_loop_workload.py
```

`fp_walk_gdb.py` prints the chain the way perf would see it and exits 0 if it reaches
`main`. It normally ends one frame past `main`, in glibc's `__libc_start_call_main`
(Debian's libc has no frame pointers), which is expected.

**What the chain does and doesn't cover:**

- **GCC leaves:** GCC 12 omits the frame in *leaf* functions that need no stack frame,
  even with `-mno-omit-leaf-frame-pointer`. A sample in such a leaf hides that leaf's
  immediate caller, but the chain is never broken. The regression test allows these and
  rejects any frameless function that makes a call.
- **libtcod and SFML** are prebuilt in `__lib/` without frame pointers. That only
  matters for code they call *back* into (for example a Python A* heuristic called from
  libtcod). Samples inside them still show their callers via the engine's frames.
- **libpython** keeps its `.symtab` (`build_python.sh` uses `--strip-debug`, ~+1 MB
  across the lib and extension modules), so static interpreter functions are named
  instead of `??`.

### Cost

Measured on #421: Release `-O3`, GCC 12.2, x86-64, CPython 3.15.0. FP off vs on,
builds run alternately, pinned to one core.

| Measure | Workload | FP cost |
|---|---|---|
| Callgrind Ir, engine code only | Crucible CPU paths (grid_fill, step_swarm, entity_churn, grid_alloc) | +1.4% |
| | `fp_loop_workload.py` (Python ↔ C++ sandwich) | +3.7% |
| | `issue_331_property_read_bench.py` (tight getter loop: worst case) | +12.1% |
| Callgrind Ir, whole process | same three | +0.24%, +0.23%, +0.44% |
| Wall clock | Crucible, 7 of 8 benches (12 rounds) | −2.4% … +0.9%: noise |
| | `fp_loop_workload.py`, median of 12 | −0.9%: noise |
| | property-read microbench, median of 15 | 0 … +1.5% (~1 ns/read) |
| Size | `.text` | +1.4 KB (+0.05%) |

The engine-only Ir increase is real but cheap. Each small binding function gains a
2–3 instruction prologue, so the percentage is largest for tiny getters
(`PyVector::pyObject` +36%) and around zero for loop-heavy code (`fillRect`,
`initStorage`: ±0.01%). The engine is a small share of a typical process's
instructions (Python dominates), and on wall clock the cost stays inside run-to-run
noise. Crucible's `layer_fill` showed a bimodal *off* distribution (1.7 ms or 2.5 ms)
inside full-suite runs only. Run alone 40× per build, both builds sit at a 2.3–2.4 ms
median, and Ir differs by 0.01%. That's heap and layout state left by earlier
benchmarks, not frame pointers.

## Callgrind — primary, deterministic, no special permissions

Best fit for validating optimizations. `--headless --exec <script>` is deterministic,
so Callgrind yields exact, reproducible instruction counts (`Ir`) with source file:line
attribution and call counts. ~30-50x slowdown, so point it at a bounded benchmark.

One-shot via the Makefile (defaults to the #331 benchmark; override with `SCRIPT=`):

```bash
make callgrind SCRIPT=tests/benchmarks/issue_331_property_read_bench.py
callgrind_annotate build-profile/callgrind.out | head -60
```

Or manually:

```bash
valgrind --tool=callgrind --callgrind-out-file=build-profile/callgrind.out \
  build-profile/mcrogueface --headless --exec tests/benchmarks/<bench>.py

# Function-level, engine code only:
callgrind_annotate --threshold=95 build-profile/callgrind.out \
  | grep -E "src/" | grep -Ev "python3\.1[0-9]|/usr/|libpython"
```

**A/B a change:** run Callgrind before and after, compare the total `Ir` for the target
function (Callgrind reports per-function self + inclusive counts and per-call-site
counts). Because it's deterministic, any delta is the change, not noise. `kcachegrind`
(GUI) isn't installed on the dev box; `callgrind_annotate` (CLI) is sufficient.

Caveat: Callgrind models an idealized cache and counts instructions, not wall-clock —
great for "did this do less work," not for real-time behavior.

## Profiling the render path — and the screenshot/PNG trap

In headless mode `mcrfpy.step()` does **not** render (the render path is stubbed); the
only way to force a real render is `automation.screenshot()`, which flushes the
off-screen target to a PNG. That has a sharp consequence for profiling: **PNG encoding
dominates the profile**. On a representative full-loop workload, ~96% of instructions
landed in libsfml's `stbi_zlib_compress` / `stbiw__encode_png_line` — the actual engine
render/update/animation work was buried under 3%.

Implications:

- To profile **update / animation** logic, use a `step()`-only workload with **no**
  screenshots — the render cost (and the PNG artifact) is absent, so engine work is the
  whole profile.
- To profile the **render path** itself, expect to subtract the PNG cost (filter out
  `stbi_*` / libsfml-graphics symbols) or drive rendering by another means.
- The per-frame PNG cost is an artifact of the screenshot *serialization format*, not of
  rendering. A faster capture path (e.g. QOI encoding, plus a McRogueFace-specific UI-tree
  serialization) is explored in the wiki proposal
  [Hybrid Scene Serialization](https://dev.ffwf.net/forgejo/john/McRogueFace/wiki/Proposal%3A-Hybrid-Scene-Serialization);
  if adopted it would also make screenshot-driven profiling far less noisy.

A ready full-loop workload (textured grid + moving entities + animated nested UI, with
forced renders) lives at `tests/benchmarks/profile_workload.py`.

## perf — real wall-clock sampling

For the interactive game where you need actual time spent (draw calls, SFML/Python cost
Callgrind's model hides):

```bash
perf record --call-graph fp -- build-profile/mcrogueface [args]
perf report
```

`--call-graph fp` relies on the frame pointers the build retains (any default build
does; see above).

### Naming Python frames: the perf trampoline

perf sees every Python call as just `_PyEval_EvalFrameDefault`. With CPython's perf
trampoline active, each Python function gets its own tiny stub, named
`py::<function>:<file>` in `/tmp/perf-<pid>.map`, which perf reads automatically.
Activate it from the script; this works under every engine launch mode:

```python
import sys
sys.activate_stack_trampoline("perf")   # before the code you want named
```

`tests/benchmarks/fp_loop_workload.py` does this when `MCRF_PERF_TRAMPOLINE=1`:

```bash
cd build
MCRF_PERF_TRAMPOLINE=1 perf record -F 999 --call-graph fp -o perf.data -- \
    ./mcrogueface --headless --exec ../tests/benchmarks/fp_loop_workload.py
perf report -i perf.data --children          # inclusive: which loop phase costs what
perf script -i perf.data > loop.perf         # load in https://profiler.firefox.com or speedscope
```

`MCRF_FP_WINDOWED=1` (with a display) runs the same workload under the real
`GameEngine::run → doFrame` loop instead of headless `step()`. The trampolines
need the frame pointers: the stubs carry no DWARF, so frame pointers are the only
way to unwind through them.

**Known wart:** `--exec` scripts run via `PyRun_SimpleString`, so their frames (and
tracebacks) report the file as `<string>`, not the script path (#422).

**Prerequisite (one-time, needs root):** the dev box ships
`kernel.perf_event_paranoid = 3`, which blocks `perf_event_open` for non-root entirely.
Lower it for the session:

```bash
sudo sysctl kernel.perf_event_paranoid=1
```

(Or run perf under `sudo`. To persist, add `kernel.perf_event_paranoid = 1` to
`/etc/sysctl.conf`.)

## Notes

- gprof is intentionally not used: it requires a `-pg` instrumentation recompile and
  handles the Python/SFML shared libraries poorly.
- Clean up with `make clean-profile` (also covered by `make clean-all`).
