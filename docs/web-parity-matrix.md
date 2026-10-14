# Desktop ↔ Web Parity Matrix

**Issue:** #391 · **Branch:** `feat/387-web-parity-sprint` · **Type:** living documentation

McRogueFace renders and runs through two swappable backends selected at compile time in
`src/Common.h`:

- **Desktop** — real **SFML 2.6** (desktop OpenGL, GLSL 1.20), plus the full C Python
  runtime, filesystem, and ImGui debug console.
- **Web** — a hand-written **SDL2 + OpenGL ES 2 / WebGL** backend
  (`src/platform/SDL2Renderer.cpp`) that mimics the SFML API through type stubs in
  `src/platform/SDL2Types.h`, compiled with Emscripten to WebAssembly.

A third **headless** backend (`src/platform/HeadlessTypes.h`) provides no-op graphics
stubs for CI. Game, UI, and binding code is written **once** against the SFML-shaped API,
so any place the web backend silently diverges from real SFML is a parity bug that only
surfaces when something is rendered and eye-balled in a browser.

This matrix is the honest index into **what is actually tested** versus what is merely
claimed. The core rule (from #391): *a row marked ✅ with no test is a claim, not a fact.*
The **Test coverage** column cites a real test file, or says `unverified`, `manual only`,
or `planned: #388`. It never marks a row covered without a test to point at.

---

## Matrix

| Feature | Desktop (SFML) | Web (SDL2/WebGL) | Test coverage | Notes / boundary rationale |
|---|---|---|---|---|
| **Audio** | ✅ Full | ✅ Full | manual only (browser) | SDL2_mixer via `-sUSE_SDL_MIXER=2`; `SoundBuffer`/`Sound`/`Music` work. MP3 + procedural audio confirmed in-browser (Feb 2026), correcting the old "Stubbed on web" claim. No automated audio assertion on either backend yet. |
| **Input** (Key / MouseButton / modifiers) | ✅ Full | ✅ Full | ✅ `tests/unit/input_parity_test.py` (#389) + source audit | Enum inventory, integer values, contiguity, and IntEnum `__ne__` are asserted; SDL→SFML translation coverage is source-audited in the same file (every exposed key/button/modifier is mapped). See [Input parity detail](#input-parity-the-one-fully-covered-row). |
| **Text entry** (`scene.on_text`, `automation.typeText`) (#495) | ✅ Full (`sf::Event::TextEntered`) | ✅ Full (`SDL_TEXTINPUT`) | ✅ `tests/unit/scene_on_text_test.py` (delivery, UTF-8/astral code points, ordering, validation) + `input_parity_test.py` source audit of the SDL translation | One printable code point per call, as a UTF-8-decoded `str`. SDL's `SDL_TEXTINPUT` carries a whole string (IME commit, compose result); the pump now decodes **every** code point and queues the rest (it used to take the first byte only). SFML reports control characters (Backspace, Tab, Enter, Escape, DEL) as text and SDL never does, so the engine drops them on both: they are keys, delivered to `on_key`. The web path itself is not run by CI; the translation is source-audited and the engine side is shared code the desktop test runs. |
| **Modifier state** (`mcrfpy.keyboard.shift/ctrl/alt/system`) (#497) | ✅ From the key event | ✅ From the key event (`KMOD_*`) | ✅ `tests/regression/issue_497_keyboard_modifiers_from_events_test.py` (injected events) + `input_parity_test.py` audit that SDL key events carry all four flags | Reports the modifiers of the key event being handled, not a hardware poll, so it agrees with `on_key` under event lag and in headless tests. The value persists until the next key event and is cleared on focus loss. A modifier key's *own* press/release carries whatever the backend reports for it (injected events: pressed counts, released does not). |
| **Dev-tool hotkeys** (`Window.console_key` / `explorer_key`) (#496) | ✅ Configurable, default Grave / F4 | n/a (no console to toggle; every key reaches `on_key`) | ✅ `tests/regression/issue_496_dev_hotkeys_test.py` (property contract headless; hotkey behaviour in a windowed child process) | `None` frees the key for the game. `mcrfpy.set_dev_console(False)` now also releases Grave/F4 (it used to disable the console but still swallow the keys). The properties exist on web but have no effect. |
| **Dynamic assets** (filesystem) | ✅ Filesystem | ⚠️ Preloaded only | `unverified` (build-time invariant) | All assets are bundled into the Emscripten virtual FS at build time via `--preload-file`; no runtime disk loading. Use absolute VFS paths (`/assets/…`, `/scripts/…`). Not a bug — a platform constraint. |
| **ImGui console** | ✅ Full | ❌ Disabled | n/a (absent by design) | Debug overlay is compiled out on web. Nothing to test — the surface does not exist. Web debugging goes through the JS interop surface exercised by the WASM smoke suite. |
| **Threading** | ✅ Full | ⚠️ Single-threaded | `unverified` | Browser JS execution is single-threaded; no pthreads in this build config. Game logic is single-threaded on both backends, so no divergence is *expected*, but nothing asserts it. |
| **Web build boots / Python runs / UI constructs / error recovery** | n/a (native) | ✅ Works | ✅ `tests/wasm/run_wasm_tests.py` (#239) | Headless-Chromium (Playwright) smoke suite drives the real JS interop surface (`runPython`, `resetGame`, `getPythonState`, `clearPythonError`, `getPythonGlobalsCount`). Asserts eval, stdout capture, `import mcrfpy`, `Frame` construction, syntax/runtime-error recovery, global persistence, reset. A page-level JS error fails the run even if every Python assertion passes. |
| **Shaders** (custom `mcrfpy.Shader`) | ✅ Full | ⚠️ Wired (#390), pixel-unverified | planned: #388 (screenshot diff) | **Was the headline gap (silent drop); #390 wired it.** `Sprite::draw`/`Shape::draw`/`VertexArray::draw` now read `states.shader` and pass the user program to `drawTriangles` as a `programOverride`. A correctly-authored fragment shader (targets the built-in contract: samples `u_texture`, reads `v_texcoord`/`v_color`) is now applied at draw. SFML-dialect constructs (`gl_TexCoord`, a `texture` sampler) are **not** translated — that's a documented contract, not a silent drop. Headless CI still **cannot** see shader output (`HeadlessTypes.h` `loadFromMemory` returns `false`); only a real-GL screenshot diff proves pixel correctness. See #347 §1a, done in #390, verified by #388. |
| **Shader GLSL dialect** (ES precision / version) | ✅ GLSL 1.20 | ⚠️ ES preamble injected (#390) | planned: #388 | `Shader::loadFromMemory` now prepends `#ifdef GL_ES\nprecision mediump float;\n#endif` when the fragment source declares no `precision`, so ES-valid shaders that omit it compile (validated in-browser: a `precision`-less fragment compiles green). Full desktop→ES translation (legacy `varying`/`attribute` rewriting) is still out of scope. See #347 §1b/§1c, done in #390. |
| **Shader types** (Vertex / Geometry) | ⚠️ Vertex only in theory | ❌ Fragment only (rejected loudly) | `manual` (#390) | Geometry shaders don't exist in GL ES 2 / WebGL 1. As of #390, web `loadFromMemory` **rejects** non-`Fragment` types with a clear `err()` message (surfaced to Python) instead of a silent `false`; a broken fragment now raises `ValueError` with the real GL InfoLog (validated in-browser). Python only ever constructs fragment shaders. See #347 §2a/§2b, done in #390. |
| **RenderTexture / FBO round-trip** | ✅ Hidden by SFML | ⚠️ Manual Y-flip | planned: #388 (nested-FBO diff) | Web `RenderTexture` wraps a bottom-up GL FBO (`flippedY_=true`, `SDL2Renderer.cpp:1217`); `Sprite::draw` inverts V to compensate (`:1887-1890`). Correct in the common case, but nested FBOs (grid chunk-cache → `cache_subtree` frame → shader intermediate) risk a 1-px vertical shift or full mirror. Needs a cross-backend diff of multi-level compositing. See #347 §3a, feeds #388/#390. |
| **Pixel-perfect scaling & text AA** | ✅ Reference | ⚠️ Likely-parity | planned: #388 | Texture filtering defaults match (`GL_NEAREST`, `setSmooth`→`GL_LINEAR`, `CLAMP_TO_EDGE`) so sprite AA should not drift (#347 §3b, low risk). Grid camera uses `int`-truncated blit origins in **shared** code (`UIGridView.cpp:288-289`), but fractional `zoom` × the FBO flip (above) can land a NEAREST-sampled half-pixel on either side of a texel edge. Verify grid output at non-integer zoom / fractional `center_camera`. See #347 §3c. |
| **Text rendering** (kerning + UTF-8) | ✅ `sf::Text` (kerning); UTF-8 via `mcrf::from_utf8` (#477) | ⚠️ UTF-8 ✅ (#477), no kerning | ✅ UTF-8: `tests/regression/issue_477_utf8_text_test.py` (desktop), `tests/wasm/run_wasm_tests.py::utf8_text` (web); kerning planned: #388 (text diff) | **UTF-8 (#477):** text is UTF-8 on every backend, regardless of locale. Before #477 *both* backends were wrong: SFML widened each byte to a code point through the C++ locale (`"╔"` drew as `â•”`), and the SDL2 loops iterated bytes. Now `src/Utf8.h` is the one conversion point (`from_utf8`/`to_utf8` at the SFML boundary, `utf8::next_codepoint` in the SDL2 glyph loops), SDL2 loads non-ASCII glyphs on demand, and a character the font lacks draws as its .notdef box on both backends. **Kerning** still diverges: the SDL2 text path is a from-scratch atlas renderer with no `getKerning` (advance is raw `xadvance`), so widths differ and center/right alignment drifts. Second-most-likely area (after shaders) to fail a screenshot diff. See #347 §3d, feeds #390. |
| **Caption baseline** (`Caption.baseline`, #478) | ✅ `sf::Text` baseline at `font_size`, corrected by a text-local shift; ascent from FreeType on the font file | ✅ SDL2 Text baseline at the atlas ascent, corrected by the same shift; ascent from the same FreeType face | ✅ desktop pixels: `tests/regression/issue_478_caption_baseline_test.py`, `issue_478_em_top_reference_test.py`; web layout: `tests/wasm/run_wasm_tests.py::text_baseline` (bounds, not pixels: #388) | Both backends read the ascent as FreeType's `face->size->metrics.ascender` after `FT_Set_Pixel_Sizes(face, 0, font_size)`. Before #478 they *disagreed*: desktop put the baseline at `pos.y + font_size`, web at `pos.y + ascent`. Bounds still differ in kind: desktop reports ink bounds, web the line box. |
| **Multi-window** | ⚠️ Planned (#62) | ❌ Impossible | n/a (desktop-only) | A browser tab hosts a single canvas/GL context; multiple OS windows are not a web concept. Desktop-only by design. |
| **Free-threading** (no-GIL Python) | ⚠️ Planned (#336) | ❌ Impossible | n/a (desktop-only) | Requires a free-threaded CPython build and OS threads; the web build is single-threaded JS. Desktop-only by design. |
| **numpy** (zero-copy buffers) | ⚠️ Planned (#337) | ❌ Out of scope | n/a (desktop-only) | numpy interop targets the native CPython extension ABI; not part of the web build. Desktop-only / out of scope. |

Legend: ✅ full/covered · ⚠️ partial/constrained/planned · ❌ absent or broken ·
`planned: #388` = a screenshot diff is what would prove it, and #388 is not landed yet ·
`unverified` = no test exists · `manual only` = validated by hand in a browser, not
automated · `n/a` = the surface does not exist on that backend.

---

## Input parity — the one fully-covered row

`tests/unit/input_parity_test.py` (#389) is the only row backed by an executable
cross-backend assertion. It proves, from the running desktop/headless build:

- **Enum inventory parity** — `mcrfpy.Key` has exactly the 101 SFML-ordered members
  (A=0…Z=25, Num0-9, Escape=36 … Pause=100, plus `UNKNOWN=-1`); `mcrfpy.MouseButton`
  has the 5 physical buttons (Left=0…XButton2=4) plus synthetic `SCROLL_UP=10`/
  `SCROLL_DOWN=11`; `mcrfpy.InputState` is `PRESSED=0`/`RELEASED=1`.
- **Value uniqueness & contiguity** — real key values are unique and contiguous
  `0..KeyCount-1`, `UNKNOWN` is the only negative. This contiguous range is exactly what
  the SDL stub `enum Key` and `sdlScancodeToSfKey()` enumerate, so every value has an SDL
  source mapping.
- **IntEnum `__ne__` gotcha** — `!=` behaves for same-enum and cross-type (string)
  compares; int's inherited `__ne__` previously broke string-name comparisons (#306).

The same file records the **source audit** (verified 2026-07-19) proving the SDL→SFML
translation is complete: `sdlScancodeToSfKey()` / `sfKeyToSdlScancode()`
(`SDL2Renderer.cpp:825-1042`) map every exposed key in both directions;
`sdlButtonToSfButton()` (`:1044-1052`) maps all 5 buttons; modifiers (`:783-786`) carry
all four flags. It also flags two non-blocking follow-ups for #390: a dead
`SDL_SCANCODE_TO_SF_KEY[]` placeholder array and a `sdlButtonToSfButton` default that
fabricates a `LEFT` click for unknown ids (Fail-Early violation). The third,
the `SDL_TEXTINPUT` single-byte UTF-8 truncation, was fixed in #495 and is now guarded by
`test_text_entry_audit`.

---

## Desktop-only by design

Three rows are not web gaps to be closed — they are platform boundaries:

- **Multi-window (#62)** — the web build renders into a single browser canvas backed by
  one WebGL context. Multiple OS-level windows have no browser analogue. This stays a
  desktop-only feature.
- **Free-threading (#336)** — no-GIL Python needs a free-threaded CPython build and real
  OS threads. The Emscripten build runs single-threaded on the browser's JS event loop.
- **numpy (#337)** — numpy binds against the native CPython C-extension ABI and is out of
  scope for the web build; it is a desktop-only (native-interpreter) capability.

Marking these ❌ on web is correct and permanent; they carry `n/a` for test coverage
because there is no cross-backend behaviour to compare.

---

## Known web divergences (open work)

The rendering rows above are the substance of the parity risk. They trace to two issues:

- **#347 — Renderer parity investigation** (`docs/renderer-parity-investigation.md`): the
  authoritative, source-cited catalog of every divergence. Headline findings: custom
  shaders silently dropped (§1a), no ES `precision` guard (§1b), FBO Y-flip round-trip
  risk (§3a), grid integer-truncation × fractional zoom (§3c), and text with no kerning /
  byte-wise UTF-8 (§3d). §4 establishes that **headless CI cannot observe any of §1–§3** —
  shader construction raises under `--headless` — so these can only be regression-guarded
  by rendering on real GL/WebGL contexts and diffing images.
- **#390 — SDL hardening**: the code fixes / fail-early guards that follow from #347.
  **Landed:** custom-program draw path (`states.shader` → `drawTriangles` programOverride,
  replacing the silent drop); `#ifdef GL_ES` precision-preamble injection; loud rejection of
  unsupported shader types with the real GL InfoLog surfaced to Python; built-in shader
  compile failure is now fatal (no blank-canvas limp-on); `SDL_TEXTINPUT` full-UTF-8
  codepoint decode + `sdlButtonToSfButton` Fail-Early sentinel (no fabricated LEFT clicks).
  **Still open:** SDL2 text kerning + codepoint-wise glyph iteration; nested-FBO Y-flip
  audit; full desktop→ES GLSL translation. Pixel correctness of the now-wired shader path is
  verified only once #388 lands.

The validator for all of these is **#388 — the cross-backend screenshot-diff harness**,
which is **planned, not landed**. Until it lands, every rendering row's coverage is
`planned: #388` (or `unverified`), never ✅. For rendering *performance* specifically, the
native profiling rig is a proxy (`docs/wasm-profiling.md`): the C++ source is identical on
both backends, so algorithmic cost transfers — but pixel *correctness* does not, and only
#388 can prove it.

---

## How coverage is verified

The three real (or planned) entry points behind this matrix:

**Input parity (landed):**

```bash
./build/mcrogueface --headless --exec tests/unit/input_parity_test.py
```

Runs in the normal desktop test suite (`cd tests && python3 run_tests.py`).

**WASM boot / interop smoke suite (landed):**

```bash
source ~/emsdk/emsdk_env.sh
make test-wasm-setup   # one-time: Playwright venv in .venv-wasmtest/
make playground        # build build-playground/ if needed
make test-wasm         # serves the build + runs the headless-Chromium suite
```

Exit `0` = all passed, `1` = a test failed, `2` = harness/setup error. See
`tests/wasm/README.md`.

**Cross-backend screenshot diff (planned — #388):**

The only mechanism that can prove the shader, RenderTexture, pixel-scaling, and text rows.
It renders the same scene on desktop-SFML and web-SDL2 real contexts and diffs the images.
Not yet implemented — do not mark any rendering row ✅ until it lands and the specific
scene (shadered frame, nested-FBO grid at fractional zoom, kerning/UTF-8 text block) is
diffed green.
