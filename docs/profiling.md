# Native Profiling Workflow (Callgrind + perf)

External C++ profiling for engine hot-path work (issue #345). This is separate from
the in-engine `ProfilerOverlay` / `ProfilingMetrics` live HUD (`src/Profiler.*`,
`GameEngine.h`) — those show frame time / draw calls at runtime; this is for
diagnosing and A/B-validating C++ optimizations (e.g. #331, #342, #343, #344).

## The profiling build

The default `make` (Release, `-O3 -DNDEBUG`) omits frame pointers and ships no DWARF,
so it can't be line-annotated or unwound. `make build-debug` (`-O0`) profiles the wrong
(unoptimized) code. Use the dedicated profiling build instead:

```bash
make profile
```

Produces `build-profile/mcrogueface`, configured `RelWithDebInfo` (`-O2 -g`) plus
`-fno-omit-frame-pointer` (CMake `-DMCRF_PROFILE=ON`). Not stripped. The build is
self-contained — `lib/`, `assets/`, and `scripts/` are copied next to the binary just
like the normal build, so `--headless --exec` works out of the box.

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
  | grep -E "src/" | grep -Ev "python3\.14|/usr/|libpython"
```

**A/B a change:** run Callgrind before and after, compare the total `Ir` for the target
function (Callgrind reports per-function self + inclusive counts and per-call-site
counts). Because it's deterministic, any delta is the change, not noise. `kcachegrind`
(GUI) isn't installed on the dev box; `callgrind_annotate` (CLI) is sufficient.

Caveat: Callgrind models an idealized cache and counts instructions, not wall-clock —
great for "did this do less work," not for real-time behavior.

## perf — real wall-clock sampling

For the interactive game where you need actual time spent (draw calls, SFML/Python cost
Callgrind's model hides):

```bash
perf record --call-graph fp -- build-profile/mcrogueface [args]
perf report
```

`--call-graph fp` relies on the frame pointers the profiling build retains.

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
