# Renderer Parity Investigation (Desktop SFML ↔ Web SDL2/WebGL)

**Issue:** #347 · **Branch:** `feat/387-web-parity-sprint` · **Type:** investigation (read-only)

## Intro

McRogueFace renders through two swappable backends selected at compile time in
`src/Common.h`: desktop uses real **SFML 2.6** (OpenGL, desktop GLSL); web uses a
hand-written **SDL2 + OpenGL ES 2 / WebGL** backend that mimics the SFML API via
`src/platform/SDL2Types.h` (type stubs) and `src/platform/SDL2Renderer.cpp`
(implementation). A third headless backend (`src/platform/HeadlessTypes.h`) provides
no-op stubs for CI.

Because game/UI/binding code is written once against the SFML-shaped API, any place
where the SDL2 backend *silently diverges* from real SFML behaviour is a parity bug
that will not surface until something is rendered and eye-balled in a browser. This
document catalogs those divergences. Findings are tagged **[CONFIRMED]** (provable from
source) or **[VERIFY]** (strongly suspected, needs a runtime cross-backend screenshot to
confirm magnitude). Every finding cites `file:line`.

This directly motivates the **#388** cross-backend screenshot-diff harness (the only way
to catch these) and feeds **#390** SDL hardening (the fixes / fail-early guards).

---

## 1. Shader GLSL dialect portability

### 1a. Custom `mcrfpy.Shader` fragment shaders are SILENTLY IGNORED on the web backend — [CONFIRMED] — **headline gap**

The Python-facing shader system (`src/PyShader.cpp`) lets a user attach a fragment
shader to any drawable. On desktop this works: `UIFrame`, `UISprite`, and `UIGridView`
render their content to a `RenderTexture`, then blit it with the custom program via
`target.draw(sprite, shader->shader.get())`:
- `src/UIFrame.cpp:214-225`
- `src/UISprite.cpp:127-156`
- `src/UIGridView.cpp:236-240`, `src/UIGridView.cpp:461-465`

On the web backend this blit reaches `Sprite::draw(RenderTarget&, RenderStates states)`
at `src/platform/SDL2Renderer.cpp:1859`. **That function never reads `states.shader`.**
It unconditionally calls `drawTriangles(..., ShaderType::Sprite)`
(`SDL2Renderer.cpp:1917`), which hard-selects one of the three built-in programs
(`SDL2Renderer.cpp:441-453`). The same is true of `Shape::draw`
(`SDL2Renderer.cpp:1559`) and `VertexArray::draw` (`SDL2Renderer.cpp:1681`) — none of
them honour `states.shader`. The `drawTriangles` signature itself only accepts a
`ShaderType` enum, so there is *no code path* by which a custom program reaches a draw
call.

Consequence: a shader-decorated drawable renders **identically to an un-shadered one**
on web. No error, no warning — the effect just vanishes. This is a textbook "Fail Early"
violation (silent degradation) and is the single largest confirmed parity gap.

Note the machinery is half-wired: `sf::Shader::loadFromMemory` *does* compile a real GL
program (`SDL2Renderer.cpp:2133-2154`) and `setUniform` *does* upload
(`SDL2Renderer.cpp:2156-2202`), so `shader.is_valid` is `True` and `set_uniform`
succeeds — the program is compiled, uniforms are set, and then it is thrown away at draw
time. This makes the failure especially deceptive.

### 1b. No `precision` qualifier is injected into user fragment shaders — [CONFIRMED]

WebGL / GLSL ES 1.00 **requires** every fragment shader to declare a default float
precision (`precision mediump float;`) or explicitly qualify every float; desktop GLSL
1.20 does **not** accept `precision` at all. The engine's own built-in shaders handle
this with an `#ifdef GL_ES` guard (`SDL2Renderer.cpp:48-122`). But the wrapper vertex
shader that `Shader::loadFromMemory` prepends to user fragment source
(`SDL2Renderer.cpp:2136-2148`) has **no `#ifdef GL_ES` guard and no `precision` line**,
and the user's fragment source is passed through verbatim with nothing prepended.

So even if 1a were fixed, a shader authored/tested on desktop (legacy SFML style:
`varying`, `gl_FragColor`, `texture2D`, no `precision`) would **fail to compile** under
WebGL. The compile error is logged to `std::cerr` (`SDL2Renderer.cpp:222-223`) and
`compileShader` returns 0 → `loaded_ = false`. Whether that surfaces as a Python
exception depends on 1a being fixed; today it is moot because the program is discarded
anyway.

### 1c. Dialect drift direction — [CONFIRMED, informational]

Desktop SFML shaders are conventionally written in legacy GLSL (`attribute`/`varying`/
`gl_FragColor`/`texture2D`), which is *mostly* source-compatible with GLSL ES 1.00 — the
`precision` qualifier (1b) is the main incompatibility, plus ES's stricter type rules
(no implicit int→float, mandatory precision on samplers is `lowp` by default). There is
**no translation layer** (no glslang / SPIRV-Cross / ANGLE-side rewrite) in either
backend: the string handed to `glShaderSource` is exactly the user's bytes
(`SDL2Renderer.cpp:215`). A modern `#version 330` / `in`/`out`/`out vec4 fragColor`
shader written for desktop would fail on both backends here, so the realistic authoring
target is "legacy GLSL that also happens to be ES-clean," which users have no way to
know.

---

## 2. Shader feature availability

### 2a. `Geometry` shaders are structurally impossible on web — [CONFIRMED]

`Shader::Type` enumerates `{ Vertex, Geometry, Fragment }` on all three backends
(`SDL2Types.h:1380`, `HeadlessTypes.h:925`, mirroring SFML). Geometry shaders **do not
exist in OpenGL ES 2 / WebGL 1**. The SDL2 `loadFromMemory` only handles `Fragment` and
returns `false` for anything else (`SDL2Renderer.cpp:2135-2153`), including `Vertex` and
`Geometry`. So the enum advertises capability the web backend cannot deliver.

### 2b. Custom vertex shaders unsupported on web — [CONFIRMED]

`loadFromMemory(src, Vertex)` returns `false` (`SDL2Renderer.cpp:2153` fall-through);
the two-file `loadFromFile(vertex, fragment)` overload is a `// TODO` returning `false`
(`SDL2Renderer.cpp:2128-2131`). The Python binding only ever constructs fragment shaders
(`PyShader.cpp:101`), so this is not currently reachable from Python, but the C++ API
surface claims support it lacks.

### 2c. Uniform type coverage is narrower than SFML — [VERIFY/CONFIRMED]

The web `Shader::setUniform` overloads cover `float`, `Vec2`, `Vec3`, `Vec4`, `Color`
(`SDL2Renderer.cpp:2156-2202`). `setUniform(name, Texture)` and
`setUniform(name, CurrentTexture)` are **no-ops** ("handled during draw" —
`SDL2Renderer.cpp:2180-2182`, `2200-2202`), but the draw path that would honour them
(1a) does not run for custom shaders, so **sampler uniforms other than the implicit
`u_texture` cannot be bound at all on web**. No `int`, `mat4`, or array-uniform overloads
exist on either backend's wrapper. The Python `set_uniform` only exposes float/vec2-4
(`PyShader.cpp:183-225`), so the Python surface is consistent — but any engine-side
sampler effect (e.g. a mask texture) is desktop-only.

Engine auto-uniforms (`time`, `delta_time`, `resolution`, `mouse`, `texture`) are set in
`PyShader::applyEngineUniforms` (`PyShader.cpp:231-250`); `mouse` is forced to `(0,0)`
in headless (`PyShader.cpp:242-245`) and, on web, all of them are uploaded to a program
that is then not used (1a).

---

## 3. Pixel-perfect output

### 3a. FBO Y-flip round-tripping — [VERIFY] — highest off-by-one risk

Web `RenderTexture` wraps an OpenGL FBO whose texture is stored bottom-up, so it sets
`flippedY_ = true` (`SDL2Renderer.cpp:1217`) and `Sprite::draw` compensates by inverting
V coordinates when sampling a flipped texture (`SDL2Renderer.cpp:1887-1890`:
`v0 = 1-v0; v1 = 1-v1`). Desktop SFML hides this entirely. This is correct in the common
case, but it is exactly the kind of transform that produces a **1-px vertical shift or a
fully mirrored image** when a render-texture is itself sampled by another render-texture
(nested caching: grid chunk-cache → `cache_subtree` frame → shader intermediate). The
grid render-texture chunk caching and `UIFrame` `cache_subtree` both create nested FBOs,
so multi-level compositing is the scenario to screenshot-diff. **[VERIFY]** whether
double-flip cases (FBO sampled into another FBO) net out correctly.

### 3b. Texture filtering defaults match (NEAREST) — [CONFIRMED, low risk]

Plain textures default to `GL_NEAREST` min/mag (`SDL2Renderer.cpp:299-300`), matching
the desktop intent of pixel-perfect sprites; `setSmooth(true)` switches to `GL_LINEAR`
(`SDL2Renderer.cpp:322-326`). This is consistent with SFML defaults, so no AA drift is
expected for sprites. `GL_CLAMP_TO_EDGE` wrap (`:301-302`) is the only ES-legal option
and matches SFML's default non-repeated behaviour.

### 3c. Grid camera uses integer truncation for the sprite-pixel origin — [VERIFY]

`UIGridView` computes the render-texture blit origin with `int` truncation:
`int left_spritepixels = center_x - (render_w / 2.0 / zoom);`
(`src/UIGridView.cpp:288-289`, and the mirror at `:151-152`). Entity positions are then
offset by that truncated origin and multiplied by `zoom`
(`UIGridView.cpp:330-331`, `363-364`). This rounding math lives in **shared** grid code
(not backend-specific), so it *should* produce identical results — but it interacts with
3a's FBO sampling and with fractional `zoom`, where a half-pixel sampled through a
NEAREST filter can land on either side of a texel boundary differently depending on the
flip. **[VERIFY]** grid output at non-integer `zoom` and fractional `center_camera`.

### 3d. Text rendering: no kerning, byte-wise (non-UTF-8) glyph iteration, no subpixel — [CONFIRMED]

Both backends use FreeType, but the SDL2 text path is a from-scratch atlas renderer
(`Text::draw`, `SDL2Renderer.cpp:1924+`) that diverges from SFML's `sf::Text`:
- **No kerning.** Advance is `x += glyph.xadvance` per glyph
  (`SDL2Renderer.cpp:2020`); there is no `getKerning` call anywhere in the file (grep:
  zero hits). SFML applies pair kerning, so multi-character strings will have subtly
  different letter spacing → widths differ → center/right alignment drifts.
- **Byte-wise iteration.** `char c = string_[i]` then `static_cast<uint32_t>(c)`
  (`SDL2Renderer.cpp:1960-1974`) walks *bytes*, not codepoints. Any non-ASCII UTF-8
  glyph renders as garbage/mojibake on web while rendering correctly on desktop.
- **Integer/hint-free positioning.** Glyph quads are placed at raw `x + glyph.xoff`
  float positions (`SDL2Renderer.cpp:1995-1998`) with no baseline rounding or hinting
  parity guarantee vs SFML. Combined with NEAREST atlas sampling, glyph edges can shift
  a pixel between backends.

These make text the second-most-likely area (after shaders) to fail a screenshot diff.

---

## 4. Headless testing gap

### 4a. Headless `Shader::loadFromMemory` returns `false` unconditionally — [CONFIRMED]

`HeadlessTypes.h:931`: `bool loadFromMemory(const std::string&, Type) { return false; }`
and `isAvailable()` returns `false` (`HeadlessTypes.h:941`). Because `PyShader::init`
guards on `sf::Shader::isAvailable()` and raises `RuntimeError` when it is false
(`PyShader.cpp:83-87`), **constructing any `mcrfpy.Shader` under `--headless` raises**.
Even if it didn't, compilation would fail. Therefore:

- Shader correctness **cannot** be validated on headless CI at all — not the built-in
  programs, not user shaders, not uniform binding.
- The existing `tests/` suite (headless) can prove a shader *object* raises as expected,
  but can never prove a shader *renders* correctly, nor catch the 1a silent-drop bug
  (which only manifests as wrong pixels, and only on the SDL2 backend).

**Implication:** shader and pixel-parity correctness are only observable by rendering on
a real GL/WebGL context and comparing images. This is precisely the mandate of the
**#388** cross-backend screenshot-diff harness — it is the *only* mechanism that can
regression-guard sections 1–3. Any shader test must run on desktop-SFML and web-SDL2
real contexts and diff, not on headless.

---

## Recommended granular follow-up issues

All tagged `system:rendering`. Priorities suggested relative to the web-parity sprint.

1. **Web backend silently drops custom shaders** (`Bugfix`, `priority:tier1-active`) —
   `Sprite::draw`/`Shape::draw` ignore `states.shader`; either implement a custom-program
   draw path in `drawTriangles`, or **fail loudly** (raise at `Shader` construction on
   the SDL2 backend) rather than degrade silently. Feeds **#390**. This is the headline
   gap (§1a).
2. **Inject `#ifdef GL_ES` / `precision` guard into user fragment shaders** (`Minor
   Feature`, `priority:tier2-foundation`) — prepend the ES precision preamble in
   `Shader::loadFromMemory` so desktop-authored legacy-GLSL shaders compile under WebGL;
   document the authoring dialect contract. Feeds **#390**. (§1b/§1c)
3. **Reject unsupported shader types up front** (`Bugfix`, `priority:tier2-foundation`)
   — `Geometry`/`Vertex` and two-file `loadFromFile` return `false` today; surface a
   clear "not supported on this backend" error instead of a silent false. Feeds **#390**.
   (§2a/§2b)
4. **Cross-backend shader/pixel screenshot-diff coverage** (`Demo Target` /
   `workflow:needs-benchmark`, `priority:tier1-active`) — concrete test scenes for the
   #388 harness: a shadered frame, a nested-FBO grid at fractional zoom, and a
   kerning/UTF-8 text block, diffed desktop-vs-web. Feeds **#388**. (§4, §1a, §3a, §3d)
5. **SDL2 text: add kerning + UTF-8 codepoint iteration** (`Minor Feature`,
   `priority:tier2-foundation`) — bring `Text::draw` glyph advance and string decoding
   to parity with `sf::Text`. Feeds **#390**, verified by #4. (§3d)
6. **Verify nested RenderTexture Y-flip compositing** (`Bugfix`,
   `priority:tier2-foundation`) — audit double-FBO sampling (chunk cache → cache_subtree
   → shader intermediate) for the flip inversion; add a diff scene. Feeds **#388**/§390.
   (§3a)

### Feeds-into summary

- **#390 (SDL hardening):** issues 1, 2, 3, 5, 6 — the actual code fixes / fail-early
  guards.
- **#388 (screenshot-diff harness):** issues 4 and 6, plus the whole of §4 — the harness
  is the only validator for §1–§3, since §4a proves headless CI cannot see any of it.
