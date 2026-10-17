#!/usr/bin/env python3
"""Real-browser key-input tests for the web build (#495, #496, #497, #503).

Automates docs/web-key-test-sheet.md: Playwright presses real keys in headless
Chromium, SDL2's emscripten backend turns them into events, and a scene's
``on_key`` / ``on_text`` log is read back through ``run_python_string_with_output``.
Reuses the server and ccall helpers of run_wasm_tests.py.

Usage (same setup as run_wasm_tests.py, see tests/wasm/README.md):
    python run_wasm_key_tests.py [--build-dir DIR] [--url URL] [--headed] [-v]

Not automated (needs a real IME / OS keyboard; stays on the sheet): non-ASCII text, dead
keys and IME commits (sheet #6) -- CDP insertText never reaches SDL's keypress path --
browser shortcuts (#14), other layouts.

Exit code 0 = all passed, 1 = a test failed, 2 = harness/setup error.
"""
import argparse
import json
import sys
from pathlib import Path

from run_wasm_tests import DEFAULT_BUILD_DIR, _Server, _free_port, rp

SETUP = r'''
import json, mcrfpy
_s = mcrfpy.Scene("keytest"); _s.activate()
_log = []
def _on_key(k, a):
    kb = mcrfpy.keyboard
    _log.append(["key", k.name, a.name, kb.shift, kb.ctrl, kb.alt, kb.system])
def _on_text(t):
    _log.append(["text", t])
_s.on_key = _on_key
_s.on_text = _on_text
'''


def log(page):
    """Let the frame loop deliver queued events, then return and clear the log."""
    page.wait_for_timeout(150)
    out = rp(page, "print(json.dumps(_log)); _log.clear()").strip()
    return json.loads(out.splitlines()[-1])


def keys(entries):
    return [(e[1], e[2]) for e in entries if e[0] == "key"]


def texts(entries):
    return [e[1] for e in entries if e[0] == "text"]


def t_text_between_press_and_release(page):
    page.keyboard.press("a")
    ev = log(page)
    kinds = [e[0] for e in ev]
    ok = (texts(ev) == ["a"] and keys(ev) == [("A", "PRESSED"), ("A", "RELEASED")]
          and kinds.index("text") > kinds.index("key"))
    return ok, f"{ev}"


def t_shift_text_and_modifier(page):
    page.keyboard.press("Shift+A")
    ev = log(page)
    a_events = [e for e in ev if e[0] == "key" and e[1] == "A"]
    ok = (texts(ev) == ["A"] and a_events and all(e[3] for e in a_events))
    return ok, f"{ev}"


def t_shift_digit(page):
    page.keyboard.press("Shift+Digit1")
    ev = log(page)
    return texts(ev) == ["!"], f"{ev}"


def t_control_keys_make_no_text(page):
    for k in ("Enter", "Tab", "Backspace", "Escape", "Delete"):
        page.keyboard.press(k)
    ev = log(page)
    return (not texts(ev) and len(keys(ev)) == 10), f"{ev}"


def t_modifiers_follow_event(page):
    result = []
    for mod, idx in (("Control", 4), ("Alt", 5), ("Shift", 3)):
        page.keyboard.down(mod)
        page.keyboard.press("b")
        page.keyboard.up(mod)
        ev = log(page)
        b = [e for e in ev if e[0] == "key" and e[1] == "B"]
        result.append(bool(b) and all(e[idx] for e in b))
    page.keyboard.press("b")
    ev = log(page)
    after = [e for e in ev if e[0] == "key" and e[1] == "B"]
    result.append(bool(after) and not any(e[3] or e[4] or e[5] for e in after))
    return all(result), f"ctrl/alt/shift held then clear -> {result}"


def t_focus_loss_clears_modifiers(page):
    page.keyboard.down("Control")
    log(page)
    page.evaluate("window.dispatchEvent(new Event('blur'))")
    page.wait_for_timeout(100)
    state = rp(page, "print(mcrfpy.keyboard.ctrl)").strip()
    page.keyboard.up("Control")
    log(page)
    return state == "False", f"keyboard.ctrl after blur with Ctrl down -> {state}"


def t_grave_and_f4_reach_on_key(page):
    page.keyboard.press("Backquote")
    page.keyboard.press("F4")
    ev = log(page)
    names = [k for k, _ in keys(ev)]
    return ("GRAVE" in names and "F4" in names), f"{names}"


def t_f3_press_release_consistent(page):
    """F3 may be swallowed by the profiler overlay or reach on_key; press and
    release must go the same way (#503). Reports which."""
    page.keyboard.press("F3")
    ev = log(page)
    got = keys(ev)
    return got in ([], [("F3", "PRESSED"), ("F3", "RELEASED")]), \
        f"F3 {'reached on_key' if got else 'swallowed (overlay)'}: {got}"


def t_profiler_key_none_releases_f3(page):
    rp(page, "mcrfpy.window.profiler_key = None")
    page.keyboard.press("F3")
    ev = log(page)
    return keys(ev) == [("F3", "PRESSED"), ("F3", "RELEASED")], f"{ev}"


def t_profiler_key_rebind(page):
    rp(page, "mcrfpy.window.profiler_key = mcrfpy.Key.F6")
    page.keyboard.press("F3")
    f3 = keys(log(page))
    page.keyboard.press("F6")
    f6 = keys(log(page))
    rp(page, "mcrfpy.window.profiler_key = mcrfpy.Key.F3")
    return (f3 == [("F3", "PRESSED"), ("F3", "RELEASED")] and f6 in
            ([], [("F6", "PRESSED"), ("F6", "RELEASED")])), f"F3 -> {f3}; F6 -> {f6}"


def t_printable_hotkey_swallows_text(page):
    # #508: a printable hotkey's keystroke is press, text, release; all three belong to the
    # tool. The F-key tests above can't see this: F-keys type no text.
    rp(page, "mcrfpy.window.profiler_key = mcrfpy.Key.P")
    page.keyboard.press("p")
    on = log(page)
    page.keyboard.press("p")
    off = log(page)
    rp(page, "mcrfpy.window.profiler_key = mcrfpy.Key.F3")
    page.keyboard.press("p")
    plain = log(page)
    return (on == [] and off == [] and texts(plain) == ["p"]), \
        f"profiler_key=P: p -> {on}, again -> {off}; profiler_key=F3: p -> {plain}"

def t_shared_key_rejected(page):
    out = rp(page, (
        "try:\n"
        "    mcrfpy.window.console_key = mcrfpy.window.profiler_key\n"
        "    print('no error')\n"
        "except Exception as e:\n"
        "    print(type(e).__name__)\n"
    )).strip()
    return out == "ValueError", f"console_key = profiler_key -> {out!r}"


TESTS = [
    ("text_between_press_and_release", t_text_between_press_and_release),
    ("shift_text_and_modifier", t_shift_text_and_modifier),
    ("shift_digit", t_shift_digit),
    ("control_keys_make_no_text", t_control_keys_make_no_text),
    ("modifiers_follow_event", t_modifiers_follow_event),
    ("focus_loss_clears_modifiers", t_focus_loss_clears_modifiers),
    ("grave_and_f4_reach_on_key", t_grave_and_f4_reach_on_key),
    ("f3_press_release_consistent", t_f3_press_release_consistent),
    ("profiler_key_none_releases_f3", t_profiler_key_none_releases_f3),
    ("profiler_key_rebind", t_profiler_key_rebind),
    ("printable_hotkey_swallows_text", t_printable_hotkey_swallows_text),
    ("shared_key_rejected", t_shared_key_rejected),
]


def run(url, headed, timeout_ms, verbose):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: playwright not installed. See tests/wasm/README.md.", file=sys.stderr)
        return 2
    page_errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not headed)
        page = browser.new_page()
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.goto(url, timeout=timeout_ms, wait_until="load")
        try:
            page.wait_for_function(
                "() => typeof Module !== 'undefined' && Module.calledRun"
                " && Module.ccall('get_python_state', 'string', [], []) === 'OK'",
                timeout=timeout_ms)
        except Exception as e:
            print(f"[key-test] FATAL: runtime never became ready: {e}", file=sys.stderr)
            browser.close()
            return 2
        # The playground's start overlay covers the canvas and, on Start, runs the editor's
        # demo code; dismiss it first so that code cannot replace our scene afterwards.
        if page.locator("#clickOverlay").is_visible():
            page.wait_for_selector("#startBtn:not([disabled])", timeout=timeout_ms)
            page.click("#startBtn")
            page.wait_for_timeout(500)
        out = rp(page, SETUP)
        if "Error" in out or "Traceback" in out:
            print(f"[key-test] FATAL: setup failed: {out}", file=sys.stderr)
            browser.close()
            return 2
        page.click("canvas")  # SDL listens for keys once the page has focus
        log(page)
        passed = failed = 0
        for name, fn in TESTS:
            try:
                ok, detail = fn(page)
            except Exception as e:
                ok, detail = False, f"raised {type(e).__name__}: {e}"
            passed, failed = passed + bool(ok), failed + (not ok)
            if not ok or verbose:
                print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
            else:
                print(f"  [PASS] {name}")
        browser.close()
    if page_errors:
        print(f"\n[key-test] {len(page_errors)} uncaught page error(s): {page_errors}",
              file=sys.stderr)
        failed += 1
    print(f"\n[key-test] {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


def main():
    ap = argparse.ArgumentParser(description="Real-browser key tests for the web build")
    ap.add_argument("--build-dir", type=Path, default=DEFAULT_BUILD_DIR)
    ap.add_argument("--url", default=None)
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--timeout", type=int, default=60000)
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    if args.url:
        return run(args.url, args.headed, args.timeout, args.verbose)
    entry = next((args.build_dir / n for n in ("index.html", "mcrogueface.html")
                  if (args.build_dir / n).is_file()), None)
    if entry is None:
        print(f"ERROR: no web build in {args.build_dir}; run 'make playground'.", file=sys.stderr)
        return 2
    with _Server(args.build_dir, _free_port()) as srv:
        return run(f"http://127.0.0.1:{srv.port}/{entry.name}", args.headed,
                   args.timeout, args.verbose)


if __name__ == "__main__":
    sys.exit(main())
