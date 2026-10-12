# WASM browser tests (#239, #473)

Host-side smoke tests that boot a built WebAssembly build in a headless
Chromium (via Playwright) and exercise the JS interop surface exported from
`src/platform/EmscriptenStubs.cpp` (`run_python_string_with_output`,
`reset_python_environment`, `get_python_state`, `clear_python_error`,
`get_python_globals_count`), called through `Module.ccall`. That works with
either HTML shell, so the same suite covers the playground (`build-playground`)
and the shipped game build (`build-wasm-game`, which the release WASM zip
contains). `make test-wasm` runs both.

This validates that the web build boots, that Python runs, that UI objects
construct, and that the interpreter reports **and recovers from** errors — the
substrate the #388 cross-backend screenshot-diff harness builds on.

This is a **host** tool (system Python + Playwright), separate from mcrfpy's
embedded interpreter. It does not touch the desktop test suite in `tests/`.

## One-time setup

The host Python is PEP-668 externally-managed, so use a dedicated venv
(`.venv-wasmtest/` is gitignored). Either run the Makefile target:

```bash
make test-wasm-setup
```

or do it by hand:

```bash
python3 -m venv .venv-wasmtest
.venv-wasmtest/bin/pip install playwright
.venv-wasmtest/bin/python -m playwright install chromium-headless-shell
```

## Running

```bash
source ~/emsdk/emsdk_env.sh
make playground        # build build-playground/ if needed
make wasm-game         # build build-wasm-game/ if needed
make test-wasm         # serves each build + runs the suite headless
```

Or directly:

```bash
.venv-wasmtest/bin/python tests/wasm/run_wasm_tests.py            # serves build-playground/
.venv-wasmtest/bin/python tests/wasm/run_wasm_tests.py --build-dir build-wasm-game
.venv-wasmtest/bin/python tests/wasm/run_wasm_tests.py --url URL  # test an already-served page
.venv-wasmtest/bin/python tests/wasm/run_wasm_tests.py --headed -v
```

Exit code `0` = all passed, `1` = a test failed, `2` = setup/harness error.

## Cross-backend screenshot diff (#388)

`snippet_diff.py` renders the `tests/snippets/` corpus on the **web** (SDL2/WebGL)
backend in headless Chromium, captures the canvas, and diffs each frame against
the **desktop-headless oracle** PNG from `tools/generate_snippet_shots.py` (#381).
A diff above threshold is a desktop↔web divergence to triage (feeds #347/#390).

```bash
source ~/emsdk/emsdk_env.sh
make snippet-shots     # generate desktop oracle PNGs (needs a native build)
make playground        # build build-playground/
make test-wasm-diff              # diff the whole corpus
make test-wasm-diff SNIPPETS="1 6 8"   # or a subset
```

Direct invocation exposes the thresholds:

```bash
.venv-wasmtest/bin/python tests/wasm/snippet_diff.py 1 6 8 -v \
    --channel-tol 40 --frac-gate 0.03
```

Outputs: web captures in `snippet-shots/web/`, divergence masks (white = differing
pixel) in `snippet-shots/web-diff/`. Exit `0` = no divergences, `1` = ≥1 DIVERGE,
`2` = harness/setup error.

**Capture:** the WebGL context has no `preserveDrawingBuffer`, so an out-of-frame
readback reads a cleared (black) buffer. The harness forces `preserveDrawingBuffer:
true` with an `add_init_script` `getContext` shim that runs before SDL creates the
context — a host-side capture concern, **no engine/build change**. It waits for two
identical consecutive frames before reading, so it never grabs a mid-render frame.

**Determinism boundary (Fail-Early, no silent skips):** the desktop oracle is
captured on a *virtual* clock; the web build advances on the browser's rAF *wall
clock*, so a frame mid-animation is not reproducible cross-backend. The harness
diffs **static** snippets only and explicitly reports every skip — a snippet with
no oracle (`noshot`), still-active `mcrfpy.animations`, or that raised on web.
Deterministic animated capture (pause the main loop, step a virtual clock via
`Module.pauseMainLoop` + `mcrfpy.step`) is a documented follow-up.

## Notes

- The runner serves the build in-process with the correct `application/wasm`
  MIME type so emscripten's streaming instantiation is used.
- A page-level uncaught JS error (e.g. the IDBFS regression, or the `_colorize`
  traceback bug #392) fails the run even if every Python assertion passes —
  a broken shell is a failure.
- Playwright pins a specific Chromium build; `chromium-headless-shell` is the
  smaller headless-only download and is sufficient here.
- `test-wasm-diff` additionally needs `pillow` + `numpy` (installed by
  `make test-wasm-setup`).
