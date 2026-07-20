# Web (WASM) Profiling Workflow

Profiling McRogueFace in the browser (issue #346). This is the web sibling of the
native rig in [docs/profiling.md](profiling.md) (Callgrind + perf) — read that first if
you are chasing C++ hot-path cost. This doc covers only the parts native profiling
*can't* reach.

## Key principle — minimize the web-specific surface

**The C++ source is identical on desktop and web.** Only the codegen differs: native is
LLVM → x86-64, web is LLVM → WASM. Algorithmic cost, allocation counts, and
comparison-cascade depth transfer directly between the two. So for anything algorithmic —
a slow update pass, allocation churn (e.g. #348), a quadratic loop, a property-read hot
path (#331) — **profile the native build as a proxy** and use the deterministic tools
that don't exist in a browser:

```bash
make profile
make callgrind SCRIPT=tests/benchmarks/<bench>.py
callgrind_annotate build-profile/callgrind.out | head -60
```

Callgrind gives exact instruction counts with source line attribution; a browser sampler
gives noisy wall-clock buckets. If native says a function does less work, WASM does less
work too. Fix it once, natively, and both backends benefit.

**Reserve browser profiling for genuinely web-specific costs** native cannot predict:

- **WASM↔JS boundary crossings** — `Module.ccall`/`cwrap`, `emscripten_pre.js`,
  `SDL2Renderer.cpp` GL calls that trap out to WebGL. Each crossing has overhead with no
  native analogue.
- **The WebGL / GL ES 2 render backend** — `src/platform/SDL2Renderer.cpp` is a *different
  codebase* from the desktop SFML path. Its shader uploads, draw-call batching, and
  texture binds are not exercised by the native build at all, so native profiling says
  nothing about them.
- **Single-threaded execution** — no worker threads; everything (Python, render, GL)
  shares one JS thread. Contention that desktop hides behind cores is serialized here.
- **`ALLOW_MEMORY_GROWTH` realloc stalls** — the heap is growable
  (`-sALLOW_MEMORY_GROWTH=1`, CMakeLists.txt:436). Each growth event copies the whole WASM
  heap and can cause a visible hitch that never appears natively.
- **Browser frame pacing (rAF)** — the main loop runs under
  `emscripten_set_main_loop_timing(EM_TIMING_RAF, 1)` (GameEngine.cpp:385), i.e.
  `requestAnimationFrame`. Jank, dropped frames, and vsync alignment are browser-scheduler
  behavior, observable only in the browser.

## Chrome DevTools Performance panel

The primary browser instrument. Profile against a debug build so the flame chart is
legible.

```bash
source ~/emsdk/emsdk_env.sh
make wasm-debug          # full game, debug info
# or
make playground-debug    # REPL/playground, debug info
make serve-wasm-debug    # http://localhost:8080  (or serve-playground-debug)
```

Both targets configure with `-DCMAKE_BUILD_TYPE=Debug -DMCRF_SDL2=ON -DMCRF_WASM_DEBUG=ON`
(Makefile:518-521 and 542-546). `MCRF_WASM_DEBUG=ON` adds these emcc flags
(CMakeLists.txt:479-488):

- `-g4` — full DWARF debug info (compile **and** link)
- `-gsource-map` — emits a `.wasm.map` source map
- `--emit-symbol-map` — emits a `.symbols` file mapping `wasm-function[N]` → mangled name

Workflow:

1. Open the served page in Chrome, F12 → **Performance** tab.
2. Click record, exercise the workload (open a scene, run a benchmark script in the
   playground REPL, drive input), stop.
3. Read the **Main** track flame chart. WASM frames appear inline with the JS call
   stack — you'll see `requestAnimationFrame` → the Emscripten main-loop trampoline →
   your C++ frame.
4. Use the **Bottom-Up** / **Call Tree** views to find self-time hot spots, and the
   **Summary** donut to split scripting vs. rendering vs. GPU.

For heap-growth stalls, add the **Memory** checkbox to the recording (or use the Memory
tab) and watch for sawtooth jumps that line up with frame hitches.

## Named WASM functions in the flame chart — `--profiling-funcs`

By default an optimized WASM build strips function names, so the flame chart shows
`wasm-function[2317]` instead of `UIGrid::render`. The `-g4` debug builds above carry
full DWARF, which already gives readable names (and source lines with the DWARF
extension below), so **for debug-build profiling you're covered**.

If you want readable names on an **optimized** build — closer to shipped performance,
without the size and slowdown of full DWARF — emcc's `--profiling-funcs` emits just the
named function symbols and keeps optimization on. This is the right middle ground for
"profile something that behaves like the release build."

**Current state:** `--profiling-funcs` is **not present** anywhere in `CMakeLists.txt`
(verified — only `-g4`/`-gsource-map`/`--emit-symbol-map` under `MCRF_WASM_DEBUG`, and the
native-only `MCRF_PROFILE` frame-pointer option exist). To add it, introduce a new opt-in
CMake option (e.g. `MCRF_WASM_PROFILE`) that appends `--profiling-funcs` to
`EMSCRIPTEN_LINK_OPTIONS` on an otherwise `Release`/`RelWithDebInfo` Emscripten build —
mirroring how `MCRF_WASM_DEBUG` appends its flags at CMakeLists.txt:480-488. Do **not**
combine it with `-g4`; the point is to stay optimized.

*(This doc only recommends the flag; wiring it into CMake is a separate change.)*

## DWARF source-line mapping — the browser extension

Chrome can map optimized/`-g4` WASM back to C++ source lines with the official
**C/C++ DevTools Support (DWARF)** extension:

<https://chromewebstore.google.com/detail/cc++-devtools-support-dwar/pdcpmjffcomdhjbmfaaenmpjbaehbcgd>

With it installed and a `-g4` build (which emits `.wasm.map`), DevTools → Sources shows
your actual `.cpp`/`.h` files, lets you set breakpoints in C++, and attributes flame-chart
samples to source lines. Without it you get mangled symbols only — demangle manually with
`c++filt` (see [WASM_TROUBLESHOOTING.md](WASM_TROUBLESHOOTING.md#reading-wasm-stack-traces)).

## Caveat: browser timer coarsening

Browser time is deliberately imprecise. `performance.now()` is clamped to roughly **100 µs**
resolution (and jittered) as a Spectre side-channel mitigation. High-resolution timers are
gated behind cross-origin isolation — you only get finer granularity when the page is
served with the COOP/COEP headers
(`Cross-Origin-Opener-Policy: same-origin` + `Cross-Origin-Embedder-Policy: require-corp`),
which `make serve*` (plain `python3 -m http.server`) does **not** set.

Consequences for McRogueFace:

- **Don't microbenchmark in the browser.** A single `emscripten_get_now()` /
  `performance.now()` delta around a sub-100-µs operation is pure noise. For precise
  per-function numbers, use the DevTools sampler (which aggregates thousands of samples)
  or — better — profile the operation natively with Callgrind.
- The engine's own frame clock is affected too: the SDL2 backend's `Clock`
  (`src/platform/SDL2Types.h:196-218`) uses `std::chrono::high_resolution_clock`, which
  under Emscripten resolves to `performance.now()`. So `frameTime` and everything derived
  from it inherit the coarsening.

## Portable through-line: the ProfilerOverlay / ProfilingMetrics HUD

The one instrument that is **identical on desktop and web** is the in-engine HUD
(`src/Profiler.h`, `src/ProfilerOverlay.cpp`, `struct ProfilingMetrics` in
`src/GameEngine.h`). It compiles into every backend — SFML, SDL2/WASM, and headless — and
draws through whatever render path is active, so the same numbers and layout appear in the
browser as on the desktop. Toggle it with **F3**.

`ProfilingMetrics` (GameEngine.h:31) breaks the frame down into `frameTime`, `avgFrameTime`,
`fps`, `drawCalls`, and per-phase timers (`gridRenderTime`, `entityRenderTime`,
`fovOverlayTime`, `pythonScriptTime`, `animationTime`, `workTime`). These are captured with
the RAII `ScopedTimer`/`ScopedAccumTimer` helpers in `Profiler.h`, backed by the same
`std::chrono` clock as the frame loop.

**Use it for the right thing.** The HUD is excellent for *"is this frame janky, and which
phase is eating the budget"* — coarse, real-time, cross-target triage. It is **not** a
microbenchmark: on web its timers ride the same coarsened `performance.now()` clock, so a
2-µs difference between two phases is meaningless there. When you need precise numbers,
drop to the DevTools sampler (web) or Callgrind (native) as described above.

## Quick reference

| Goal | Tool | Where |
|------|------|-------|
| Algorithmic cost, allocation counts, A/B a C++ change | Callgrind (`make callgrind`) | native ([profiling.md](profiling.md)) |
| Wall-clock hot spots, GL/JS boundary, rAF jank | DevTools Performance panel | `make wasm-debug` + `serve-wasm-debug` |
| Readable names on an optimized WASM build | emcc `--profiling-funcs` | *not yet in CMake — see above* |
| C++ source lines in DevTools | DWARF browser extension + `-g4` | `make wasm-debug` |
| "Is this frame janky" triage (any backend) | ProfilerOverlay HUD (F3) | built into every build |
| Heap-growth stalls | DevTools Memory / Performance memory track | `make wasm-debug` |

See also: [docs/profiling.md](profiling.md) (native rig),
[docs/WASM_TROUBLESHOOTING.md](WASM_TROUBLESHOOTING.md) (build/debug issues).
