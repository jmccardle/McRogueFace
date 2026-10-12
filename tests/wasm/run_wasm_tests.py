#!/usr/bin/env python3
"""Headless-browser smoke tests for McRogueFace WASM builds (issues #239, #473).

Serves a built web directory, drives it with a headless Chromium via Playwright,
and exercises the real JS interop surface exported from
``src/platform/EmscriptenStubs.cpp``, called through ``Module.ccall``:

    run_python_string_with_output(code) -> stdout+stderr+repr/traceback
    reset_python_environment()          -> int
    get_python_state()                  -> "OK" | "NOT_INITIALIZED" | "ERROR_SET: <msg>"
    clear_python_error()
    get_python_globals_count()          -> int

Calling the exports directly, rather than the ``window.runPython`` wrappers that
only the dev/playground shell (src/shell.html) defines, is what lets the same
suite test the shipped game build (build-wasm-game, src/shell_game.html), which
is what the release WASM zip contains (#473).

This is a HOST-side tool (system Python + Playwright), separate from mcrfpy's
embedded interpreter. It validates that the web build boots, that Python runs,
and that the interpreter recovers from errors -- the substrate the #388
cross-backend screenshot-diff harness will build on.

Usage:
    python run_wasm_tests.py [--build-dir DIR] [--url URL] [--port N]   # DIR: build-playground
                             [--headed] [--timeout MS] [-v]

Setup (see tests/wasm/README.md):
    python3 -m venv .venv-wasmtest
    .venv-wasmtest/bin/pip install playwright
    .venv-wasmtest/bin/python -m playwright install chromium-headless-shell

Exit code 0 = all tests passed, 1 = a test failed, 2 = harness/setup error.
"""
import argparse
import functools
import http.server
import socket
import socketserver
import sys
import threading
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BUILD_DIR = REPO_ROOT / "build-playground"


# --------------------------------------------------------------------------- #
# Local static server (correct .wasm MIME; emscripten streaming instantiation
# needs application/wasm or it falls back to a slower arraybuffer path).
# --------------------------------------------------------------------------- #
class _Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".wasm": "application/wasm",
        ".js": "text/javascript",
        ".data": "application/octet-stream",
    }

    def log_message(self, *args):  # silence per-request logging
        pass


class _Server:
    def __init__(self, directory: Path, port: int):
        handler = functools.partial(_Handler, directory=str(directory))
        # ThreadingHTTPServer so the WASM page can fetch .data/.wasm concurrently.
        self._httpd = socketserver.ThreadingTCPServer(("127.0.0.1", port), handler)
        self._httpd.daemon_threads = True
        self.port = self._httpd.server_address[1]
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._httpd.shutdown()
        self._httpd.server_close()


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


# --------------------------------------------------------------------------- #
# Test cases. Each takes the Playwright `page` and returns (passed, detail).
# `rp` runs Python in the page and returns the combined output string.
# --------------------------------------------------------------------------- #
def ccall(page, name: str, ret, argtypes=(), args=()):
    """Call an EMSCRIPTEN_KEEPALIVE export. Works with either shell (#473)."""
    return page.evaluate(
        "([n, r, t, a]) => Module.ccall(n, r, t, a)", [name, ret, list(argtypes), list(args)])


def rp(page, code: str) -> str:
    # json-encode the code so arbitrary source (quotes, newlines) survives the
    # JS string boundary; evaluate arg-passing form, never string interpolation.
    return ccall(page, "run_python_string_with_output", "string", ["string"], [code])


def _expect(condition, detail):
    return (bool(condition), detail)


def t_basic_eval(page):
    out = rp(page, "1 + 1").strip()
    return _expect(out == "2", f"runPython('1 + 1') -> {out!r}")


def t_print_stdout(page):
    out = rp(page, "print('hello-wasm')")
    return _expect("hello-wasm" in out, f"stdout capture -> {out!r}")


def t_import_mcrfpy(page):
    out = rp(page, "import mcrfpy; print(mcrfpy.__name__)")
    return _expect("mcrfpy" in out, f"import mcrfpy -> {out!r}")


def t_ui_object(page):
    out = rp(page, "import mcrfpy; f = mcrfpy.Frame(pos=(0, 0), size=(10, 20)); print(f.w, f.h)")
    return _expect("10" in out and "20" in out, f"Frame(10x20).w/.h -> {out!r}")


def t_syntax_error_recovery(page):
    err = rp(page, "def bad(")
    ok = rp(page, "2 + 2").strip()
    return _expect("SyntaxError" in err and ok == "4",
                   f"syntax err -> {err!r}; recovery '2+2' -> {ok!r}")


def t_runtime_error_recovery(page):
    err = rp(page, "1 / 0")
    ok = rp(page, "3 + 3").strip()
    return _expect("ZeroDivisionError" in err and ok == "6",
                   f"runtime err -> {err!r}; recovery '3+3' -> {ok!r}")


def t_state_persistence(page):
    rp(page, "_wasm_persist = 42")
    out = rp(page, "_wasm_persist").strip()
    return _expect(out == "42", f"persisted global -> {out!r}")


def t_python_state_ok(page):
    # After forcing an error then clearing, the interpreter must report healthy.
    rp(page, "1 / 0")
    ccall(page, "clear_python_error", None)
    state = ccall(page, "get_python_state", "string")
    return _expect(state == "OK", f"getPythonState() -> {state!r}")


def t_globals_count(page):
    n = ccall(page, "get_python_globals_count", "number")
    return _expect(isinstance(n, (int, float)) and n > 0, f"globals count -> {n!r}")


def t_reset_environment(page):
    # reset_python_environment re-execs the build's /scripts/game.py; expect int 0.
    rc = ccall(page, "reset_python_environment", "number")
    # After reset the interpreter must still be usable.
    ok = rp(page, "7 + 7").strip()
    return _expect(rc == 0 and ok == "14", f"resetGame() -> {rc!r}; post-reset '7+7' -> {ok!r}")


def t_utf8_text(page):
    # #477: text is UTF-8 on every backend. The SDL2 glyph loops used to walk bytes,
    # so each non-ASCII character drew (and measured) as 2-4 garbage glyphs. The
    # default font is monospace, so a character between two 'e's is one cell wide.
    out = rp(page, (
        "import mcrfpy\n"
        "def w(t): return mcrfpy.Caption(text=t, pos=(0, 0), font_size=16).w\n"
        "c = mcrfpy.Caption(text='\u2554\u2550\u2557 caf\u00e9', pos=(0, 0))\n"
        "ref = w('eee')\n"
        "bad = [ch for ch in '\u00e9\u2554\u2591\u2588\u2192' if abs(w('e' + ch + 'e') - ref) > 0.5]\n"
        "print(c.text == '\u2554\u2550\u2557 caf\u00e9', ref > 0, bad)\n"
    )).strip()
    return _expect(out == "True True []", f"round-trip, width>0, wrong-width chars -> {out!r}")


TESTS = [
    ("basic_eval", t_basic_eval),
    ("print_stdout", t_print_stdout),
    ("import_mcrfpy", t_import_mcrfpy),
    ("ui_object", t_ui_object),
    ("syntax_error_recovery", t_syntax_error_recovery),
    ("runtime_error_recovery", t_runtime_error_recovery),
    ("state_persistence", t_state_persistence),
    ("python_state_ok", t_python_state_ok),
    ("globals_count", t_globals_count),
    ("reset_environment", t_reset_environment),
    ("utf8_text", t_utf8_text),
]


def run(url: str, headed: bool, timeout_ms: int, verbose: bool) -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: playwright not installed. See tests/wasm/README.md for setup.",
              file=sys.stderr)
        return 2

    console_errors = []
    page_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not headed)
        page = browser.new_page()
        page.on("console", lambda m: console_errors.append(m.text)
                if m.type == "error" else None)
        page.on("pageerror", lambda e: page_errors.append(str(e)))

        print(f"[wasm-test] loading {url}")
        page.goto(url, timeout=timeout_ms, wait_until="load")

        # Wait for the emscripten runtime to boot AND Python to initialize.
        # ccall is only safe once main() has run (Module.calledRun);
        # get_python_state() returns "OK" once Py_Initialize has completed.
        try:
            page.wait_for_function(
                "() => typeof Module !== 'undefined' && Module.calledRun"
                " && Module.ccall('get_python_state', 'string', [], []) === 'OK'",
                timeout=timeout_ms,
            )
        except Exception as e:
            print(f"[wasm-test] FATAL: runtime never became ready: {e}", file=sys.stderr)
            if console_errors:
                print("  console errors:", file=sys.stderr)
                for c in console_errors:
                    print(f"    {c}", file=sys.stderr)
            if page_errors:
                print("  page errors:", file=sys.stderr)
                for c in page_errors:
                    print(f"    {c}", file=sys.stderr)
            browser.close()
            return 2

        print("[wasm-test] runtime ready; running tests\n")
        passed = failed = 0
        for name, fn in TESTS:
            try:
                ok, detail = fn(page)
            except Exception as e:  # a thrown test is a failure, not a crash
                ok, detail = False, f"raised {type(e).__name__}: {e}"
            mark = "PASS" if ok else "FAIL"
            if ok:
                passed += 1
            else:
                failed += 1
            if not ok or verbose:
                print(f"  [{mark}] {name}: {detail}")
            else:
                print(f"  [{mark}] {name}")

        browser.close()

    # A page-level JS error (e.g. the IDBFS regression) is a failure even if
    # every Python test passed -- it means the shell itself is broken.
    if page_errors:
        print(f"\n[wasm-test] {len(page_errors)} uncaught page error(s):", file=sys.stderr)
        for c in page_errors:
            print(f"    {c}", file=sys.stderr)
        failed += 1

    print(f"\n[wasm-test] {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Headless-browser WASM build tests (#239, #473)")
    ap.add_argument("--build-dir", type=Path, default=DEFAULT_BUILD_DIR,
                    help="web build dir to serve: build-playground, build-wasm-game, an "
                         f"unpacked release zip... (default: {DEFAULT_BUILD_DIR})")
    ap.add_argument("--url", default=None,
                    help="test an already-served URL instead of serving --build-dir")
    ap.add_argument("--port", type=int, default=0, help="serve port (default: ephemeral)")
    ap.add_argument("--headed", action="store_true", help="show the browser window")
    ap.add_argument("--timeout", type=int, default=60000, help="runtime-ready timeout in ms")
    ap.add_argument("-v", "--verbose", action="store_true", help="print detail for passing tests")
    args = ap.parse_args()

    if args.url:
        return run(args.url, args.headed, args.timeout, args.verbose)

    build_dir = args.build_dir
    # A packaged web build's entry point is index.html (#474); a build tree's is
    # mcrogueface.html.
    entry = next((build_dir / n for n in ("index.html", "mcrogueface.html")
                  if (build_dir / n).is_file()), None)
    if entry is None:
        print(f"ERROR: no index.html or mcrogueface.html in {build_dir}. Run "
              f"'make playground' / 'make wasm-game' first (or pass --build-dir / --url).",
              file=sys.stderr)
        return 2

    port = args.port or _free_port()
    with _Server(build_dir, port):
        url = f"http://127.0.0.1:{port}/{entry.name}"
        return run(url, args.headed, args.timeout, args.verbose)


if __name__ == "__main__":
    sys.exit(main())
