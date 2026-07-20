# WASM playground browser tests (#239)

Host-side smoke tests that boot the built WebAssembly playground in a headless
Chromium (via Playwright) and exercise the JS interop surface exported from
`src/platform/EmscriptenStubs.cpp` (`window.runPython`, `resetGame`,
`getPythonState`, `clearPythonError`, `getPythonGlobalsCount`).

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
make test-wasm         # serves the build + runs the suite headless
```

Or directly:

```bash
.venv-wasmtest/bin/python tests/wasm/run_wasm_tests.py            # serves build-playground/
.venv-wasmtest/bin/python tests/wasm/run_wasm_tests.py --url URL  # test an already-served page
.venv-wasmtest/bin/python tests/wasm/run_wasm_tests.py --headed -v
```

Exit code `0` = all passed, `1` = a test failed, `2` = setup/harness error.

## Notes

- The runner serves the build in-process with the correct `application/wasm`
  MIME type so emscripten's streaming instantiation is used.
- A page-level uncaught JS error (e.g. the IDBFS regression, or the `_colorize`
  traceback bug #392) fails the run even if every Python assertion passes —
  a broken shell is a failure.
- Playwright pins a specific Chromium build; `chromium-headless-shell` is the
  smaller headless-only download and is sufficient here.
