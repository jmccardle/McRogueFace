# Web key-input tester sheet (0.3.4)

Covers #495 (`on_text`), #496/#503 (configurable dev hotkeys) and #497 (modifiers from the event) in a **real browser**. `tests/wasm/run_wasm_key_tests.py` (Chromium, `make test-wasm`) now automates checks 1-5 and 7-13. What stays manual here: **6** (dead keys / IME / non-ASCII text, which synthetic input cannot reach), **14** (browser shortcuts), Firefox, and other layouts. Do it in Chrome and Firefox, on a US layout, then once on another layout or an IME if you have one.

## Setup

```bash
source ~/emsdk/emsdk_env.sh
make playground && make serve-playground      # http://localhost:8080
```

In the page's Python REPL, paste this once. It prints every key and text event, with modifiers, and shows the profiler state:

```python
import mcrfpy
s = mcrfpy.Scene("keytest"); s.activate()
log = mcrfpy.Caption(text="press keys", pos=(10, 10)); s.children.append(log)
lines = []
def show(m):
    lines.append(m); del lines[:-12]; log.text = "\n".join(lines)
def on_key(k, a):
    kb = mcrfpy.keyboard
    show(f"key  {k} {a}  s={kb.shift} c={kb.ctrl} a={kb.alt} m={kb.system}")
def on_text(t):
    show(f"text {t!r}")
s.on_key = on_key
s.on_text = on_text
```

Click the canvas once so it has focus.

## Checks

Record PASS / FAIL and what you saw. "Expected" is what the desktop build does.

| # | Do | Expected | Issue |
|---|---|---|---|
| 1 | Type `a` | `key A PRESSED`, `text 'a'`, `key A RELEASED` (text between press and release, or right after the press) | #495 |
| 2 | Type `A` (Shift+a) | text `'A'`; key lines show `s=True` while Shift is down | #495 #497 |
| 3 | Type `!` (Shift+1) | text `'!'` | #495 |
| 4 | Press Enter, Tab, Backspace, Escape, Delete | `key` lines only, **no** `text` line | #495 |
| 5 | Hold `a` for a second | repeated text events, one per code point (key repeat may or may not repeat `key` lines; note which) | #495 |
| 6 | Non-US layout / dead key (`´` then `e`) / IME commit of a multi-character string | one `text` line per code point, in order; no `U+FFFD` | #495 |
| 7 | Hold Ctrl, tap `a`; hold Alt, tap `a`; hold Shift, tap `a` | `c=True`, `a=True`, `s=True` on the `a` event only while held; all False after release | #497 |
| 8 | Hold Ctrl, switch to another tab/window, release Ctrl there, come back, press `a` | `c=False` (focus loss clears modifiers) | #497 |
| 9 | Press Grave (`` ` ``) and F4 | both reach `on_key` (web has no console or explorer) | #496 |
| 10 | Press F3 | *(Chromium result: the profiler overlay swallows F3 and F6 on web, press and release both.)* **Report which:** (a) a profiler overlay toggles and no `key F3` line appears, or (b) `key F3` appears and nothing toggles. Both press and release must go the same way. | #503 |
| 11 | Run `mcrfpy.window.profiler_key = None`, press F3 | `key F3 PRESSED` / `RELEASED` appear | #503 |
| 12 | Run `mcrfpy.window.profiler_key = mcrfpy.Key.F6`, press F6, then F3 | F6 behaves as in #10; F3 now reaches `on_key` | #503 |
| 13 | Run `mcrfpy.window.console_key = mcrfpy.window.profiler_key` | raises (the three tools cannot share a key) | #496 |
| 14 | Browser shortcuts: press F5, Ctrl+R, F11, Ctrl+W | the page must not be left in a stuck state; note any key the page swallows that the browser should keep (and the reverse) | #495 |

## Report

For each failure give browser + version, OS, keyboard layout, the exact keys, and the lines the log showed. Failures go on #495, #496, #497 or #503 as appropriate.
