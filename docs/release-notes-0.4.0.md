# McRogueFace 0.4.0 — release notes (in progress)

> Changes since the `0.3.6` tag.

## Breaking changes and upgrade notes

| Change | What to do |
|---|---|
| **Key auto-repeat is `InputState.REPEATED`, not another `PRESSED`** (#549). `on_key` receives `(key, PRESSED)` once when a key goes down, `(key, REPEATED)` for each auto-repeat while it is held, and `(key, RELEASED)` when it comes up. `InputState` gains `REPEATED = 2`. The engine tracks held keys from the event stream on every backend (SFML, SDL2/web, headless/automation) and forgets them on focus loss, so a key released while the window was unfocused is not reported as a repeat. The dev-tool hotkeys (console, scene explorer, profiler overlay) fire on the press only. In headless tests a second `automation.keyDown(k)` with no `keyUp(k)` in between is a repeat. | A handler that tests `action == InputState.PRESSED` (or `!= PRESSED: return`) no longer sees repeats: right for hotkeys and menus. Movement or text-editing handlers that relied on a held key repeating must also act on `REPEATED`, e.g. `if action == InputState.RELEASED: return`. The bundled tutorials, templates and the demo game were updated this way. Scene `on_click` and the other mouse callbacks never receive `REPEATED`. |
