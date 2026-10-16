# McRogueFace 0.3.4 — release notes

> Changes since the `0.3.3` tag.

## Breaking changes and upgrade notes

| Change | What to do |
|---|---|
| **A `.venv` made by an older `mcrf_project deps` has no `pyvenv.cfg`** (#499). The engine now honours an activated virtualenv (`VIRTUAL_ENV`), and fails with an error naming the path if that directory has no `pyvenv.cfg` or no `lib/pythonX.Y/site-packages`. It never guesses `.venv`. | Re-run `mcrf_project deps` once per project. `mcrf_project run` sets `VIRTUAL_ENV` for you. |
| **`automation.keyDown` / `keyUp` / `hotkey` raise `ValueError` for `capslock`, `numlock`, `scrolllock`** (#504). They used to inject a Ctrl press, so `mcrfpy.keyboard.ctrl` read True. The `Key` enum has no lock keys. | Remove those names from automation scripts. |
| **Color strings are accepted everywhere a Color is** (#458). `Color("red")` used to raise `NotImplementedError`; it now resolves a name or hex string, and so does every Color setter, constructor kwarg and `animate` target (`frame.fill_color = "navy"`). An unknown string still raises `ValueError`. | Nothing breaks; see Colors below for the rules. |
| **`mcrfpy.default_fov` is a typed property** (#493). It accepts an `FOV` member or an in-range int; `None` and strings raise. New grids start from it (it used to be a plain attribute nothing read). | Set it before creating grids. |
| **`mcrfpy.keyboard` modifiers come from the key event** (#497), not from polling the hardware. Synthesized (`automation`) events now change `shift`/`ctrl`/`alt`/`system`, and queued events no longer disagree with the one being handled. | None, unless you worked around the old behaviour. |

## Colors (#458)

```python
Color("red")          # CSS: (255, 0, 0)
Color("Dark Green")   # == "dark_green" == "darkgreen"
Color("dust")         # xkcd-only name
Color("#f00"), Color("#f008"), Color("#ff0000"), Color("#ff000080")
Color("red", a=128)   # alpha only by keyword
Color("redd")         # ValueError: unknown color name 'redd' (did you mean 'red'?)
Color.names()         # 1073 names
```

- One list of 1073 names from four sources, normalized once (ASCII lowercase, letters and digits only; spaces, `_`, `-`, `/`, `'` are ignored). Shared names resolve **CSS > xkcd > Crayola > Jenny**, so `"brick red"` is xkcd's.
- **There are no `source:name` forms.** `Color("xkcd:dust")` raises `ValueError`, and `Color.names()` takes no argument. The first draft had prefixes; they were dropped in favour of one list.
- Hex needs the `#` (`#rgb`, `#rgba`, `#rrggbb`, `#rrggbbaa`). `Color.from_hex` keeps its `#`-optional 6/8-digit contract but now validates every digit (`"1g0000"` used to pass).
- `Color("red", 128)` is a `TypeError`; hex alpha plus `a=` is a `TypeError`.
- Provenance and licences are in the headers of `tools/color_names/*.tsv`; `tools/generate_color_table.py --check` keeps the generated `src/ColorNameTable.h` current.
- Not done: `Color == "red"` is still False; reverse lookup (nearest name for an RGB value).

## Input

- **`scene.on_text(text)`** (#495): typed text as an event, one UTF-8 code point per call, separate from `on_key` (a German `z` arrives as `Key.Y`; dead keys and IME can't be expressed as keys). Control characters (Enter, Tab, Backspace, Escape, DEL) stay keys. `automation.typeText(text)` synthesizes text with no key presses; `typewrite()` now delivers `on_text` between each key's press and release. Web: multi-character `SDL_TEXTINPUT` (IME commits) is decoded in full and malformed UTF-8 is dropped.
- **Configurable dev-tool hotkeys** (#496, #503): `Window.console_key` (Grave), `Window.explorer_key` (F4) and `Window.profiler_key` (F3) are a `Key` or `None`, changeable at runtime. An app that needs every key (a terminal, an editor) can set them to `None`. The three can't share a key, and a hotkey's release is swallowed together with its press. This also fixes `set_dev_console(False)` still swallowing Grave and F4. Headless builds have no tools, so every key reaches `on_key`. The web build gets the same filter (it was compiled out for SDL2).
- Automation key names `grave` and a backtick.

## Engine and project tooling

- **`mcrfpy.config`** (#501): a read-only view of the parsed engine flags (`headless`, `audio_enabled`, `exec_scripts`, `script_path`, `script_args`, `run_forever`, `interactive`, `screenshot_path`); `exit_on_exception` is also writable. Under `--exec`, `sys.argv` is the script's, so scripts could not see engine flags before.
- **`VIRTUAL_ENV` on `sys.path`** (#499): after the main script directory and ahead of the sibling `venv/`. The full order is documented in `docs/sys-path-order.md` (#502), which also lists the known gap with a `python` symlink into a venv (#505).
- **`mcrf_project deps`** installs `mcrf.toml` requirements into the project `.venv` with the engine's own interpreter and the pip wheel the package ships; `dist` bundles them into the package's `venv/`. Binary wheels only; a stale install, native code for another platform, or a web build is an error.
- **`mcrf_project` finds an installed engine** (#500): `--engine`, `$MCROGUEFACE`, `mcrf.toml`, then `~/.local/share/mcrogueface/<version>/`. `run`, `info` and `dist` share the lookup; a source that is set but wrong is an error. `mcrf.toml` is validated and rejects unknown keys.
- **Engine packages ship `_sysconfigdata`** (#498), so `pydoc` and `sysconfig` import from a package.

## Known gaps

- Web: #495, #496, #497 and F3 are compile-verified on web only; the wasm suite does not press keys in a browser.
- `automation.hotkey` presses keys before validating the later ones (tracked as its own issue).
- Using `mcrogueface` as a venv's `python` is not supported yet (#505).
