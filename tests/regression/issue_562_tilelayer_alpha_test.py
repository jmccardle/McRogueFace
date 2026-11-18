"""Regression test for #562 - layer chunks applied alpha twice.

A TileLayer/ColorLayer paints each chunk into a RenderTexture, then composites the chunk
sprite onto the target. With plain alpha blending at both steps, a translucent texel was
multiplied by its alpha twice: white@128 over blue (0,0,255) read (64,64,191) instead of
(128,128,255), red@128 read (64,0,127) instead of (128,0,127). The chunk now holds correct
premultiplied RGBA (colour SrcAlpha/OneMinusSrcAlpha, alpha One/OneMinusSrcAlpha) and is
composited with One/OneMinusSrcAlpha.

The same double alpha hit Frame's clip_children / cache_subtree texture (section 4).

Ground truth is a Sprite / Frame (drawn straight to the target, never through a chunk)
over the same background, within +-2, and the closed-form value.
"""
import os
import sys
import tempfile
import warnings

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _png  # noqa: E402
import mcrfpy  # noqa: E402
from mcrfpy import automation  # noqa: E402

TMPDIR = tempfile.mkdtemp(prefix="mcrf562_")
failures = []
warnings.simplefilter("ignore", mcrfpy.TextureWarning)


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


def shot(name):
    path = os.path.join(TMPDIR, name + ".png")
    mcrfpy.step(0)  # the screenshot shows the last complete frame; draw this one (#529)
    automation.screenshot(path)
    return _png.read_png(path)


def px(img, x, y):
    w, h, ch, data = img
    i = (y * w + x) * ch
    return tuple(data[i:i + 3])


def near(a, b, tol=2):
    return all(abs(p - q) <= tol for p, q in zip(a, b))


BLUE = (0, 0, 255)
# 4 sprites of 16x16: 0 white@128, 1 red@128, 2 opaque green, 3 white@255
SPRITES = [(255, 255, 255, 128), (255, 0, 0, 128), (0, 200, 0, 255), (255, 255, 255, 255)]
data = bytearray()
for y in range(16):
    for s in SPRITES:
        data += bytes(s) * 16
tex = mcrfpy.Texture.from_bytes(bytes(data), 64, 16, 16, 16, name="<issue562>")
tex_b = mcrfpy.Texture.from_bytes(bytes(data), 64, 16, 16, 16, name="<issue562b>")

scene = mcrfpy.Scene("s562")
scene.activate()
bg = mcrfpy.Frame(pos=(0, 0), size=(500, 420), fill_color=mcrfpy.Color(*BLUE))
scene.children.append(bg)


def grid_at(y):
    g = mcrfpy.Grid(grid_size=(4, 1), texture=tex, pos=(10, y), size=(64, 16))
    g.cell_size = (16, 16)
    g.center = (32, 8)
    g.fill_color = mcrfpy.Color(*BLUE)
    scene.children.append(g)
    return g


# --- TileLayer: one layer, tiles 0..3 -------------------------------------------------
g1 = grid_at(10)
t = g1.layer("tilesprite")
for i in range(4):
    t.set((i, 0), i)

# --- reference: the same sprites drawn directly --------------------------------------
for i in range(4):
    bg.children.append(mcrfpy.Sprite(pos=(10 + 16 * i, 60), texture=tex, sprite_index=i))

# --- two stacked TileLayers (white@128 twice) vs two stacked Sprites -------------------
g2 = grid_at(110)
t_lo = g2.layer("tilesprite")
t_lo.fill(-1)
t_lo.set((0, 0), 0)
t_lo.set((1, 0), 1)
t_hi = mcrfpy.TileLayer(name="hi", z_index=1, texture=tex_b)
g2.add_layer(t_hi)
t_hi.fill(-1)
t_hi.set((0, 0), 0)
t_hi.set((1, 0), 1)
for i in range(2):
    for _ in range(2):
        bg.children.append(mcrfpy.Sprite(pos=(10 + 16 * i, 160), texture=tex, sprite_index=i))

# --- ColorLayers: translucent white, alone and stacked, vs Frames ----------------------
g3 = grid_at(210)
c1 = mcrfpy.ColorLayer(name="c1", z_index=1)
g3.add_layer(c1)
c1.fill(mcrfpy.Color(255, 255, 255, 128))
g4 = grid_at(250)
ca = mcrfpy.ColorLayer(name="ca", z_index=1)
cb = mcrfpy.ColorLayer(name="cb", z_index=2)
g4.add_layer(ca)
g4.add_layer(cb)
ca.fill(mcrfpy.Color(255, 255, 255, 128))
cb.fill(mcrfpy.Color(255, 255, 255, 128))
for _ in range(2):
    bg.children.append(mcrfpy.Frame(pos=(200, 250), size=(64, 16), fill_color=mcrfpy.Color(255, 255, 255, 128)))
bg.children.append(mcrfpy.Frame(pos=(200, 210), size=(64, 16), fill_color=mcrfpy.Color(255, 255, 255, 128)))

# --- Frame render-texture paths (cache_subtree / clip_children) vs the direct path -----
WHITE128 = mcrfpy.Color(255, 255, 255, 128)
SOLID = mcrfpy.Color(255, 255, 255, 255)
FRAME_X = 300
frame_rows = []   # (label, y, expected)


def frame_row(label, y, fill, expected, **kw):
    f = mcrfpy.Frame(pos=(FRAME_X, y), size=(40, 16), fill_color=fill)
    for k, v in kw.items():
        setattr(f, k, v)
    if kw.get("clip_children"):
        f.children.append(mcrfpy.Frame(pos=(0, 0), size=(4, 4)))
    bg.children.append(f)
    frame_rows.append((label, y, expected))


frame_row("plain translucent frame", 10, WHITE128, (128, 128, 255))
frame_row("cache_subtree translucent frame", 40, WHITE128, (128, 128, 255), cache_subtree=True)
frame_row("clip_children translucent frame", 70, WHITE128, (128, 128, 255), clip_children=True)
frame_row("plain translucent frame, opacity 0.5", 100, WHITE128, (64, 64, 255), opacity=0.5)
frame_row("cached translucent frame, opacity 0.5", 130, WHITE128, (64, 64, 255),
          cache_subtree=True, opacity=0.5)
frame_row("plain solid frame, opacity 0.5", 160, SOLID, (127, 127, 255), opacity=0.5)
frame_row("cached solid frame, opacity 0.5", 190, SOLID, (127, 127, 255),
          cache_subtree=True, opacity=0.5)

# --- Frame shader branch: the pre-#562 straight-alpha contract is unchanged ------------
ALPHA_HALF = mcrfpy.Shader("""
    uniform sampler2D texture;
    void main() {
        vec4 c = texture2D(texture, gl_TexCoord[0].xy);
        c.a *= 0.5;
        gl_FragColor = c;
    }
""")
IGNORE_COLOR = mcrfpy.Shader("""
    uniform sampler2D texture;
    void main() { gl_FragColor = texture2D(texture, gl_TexCoord[0].xy); }
""")
TEX_TIMES_COLOR = mcrfpy.Shader("""
    uniform sampler2D texture;
    void main() { gl_FragColor = texture2D(texture, gl_TexCoord[0].xy) * gl_Color; }
""")
SHADER_X = 360
shader_rows = []


def shader_row(label, y, sh, expected, **kw):
    f = mcrfpy.Frame(pos=(SHADER_X, y), size=(30, 16), fill_color=SOLID)
    for k, v in kw.items():
        setattr(f, k, v)
    f.shader = sh
    bg.children.append(f)
    shader_rows.append((label, y, expected))


# Expected values are what 8288c73 (before #562) produced for these opaque frames, measured on
# that build. The shader branch is intentionally unchanged by #562 (the shader contract is a
# separate question), so these include its existing double application of Frame opacity: the
# box is painted at opacity into the texture and the sprite is blitted at opacity again.
shader_row("opaque frame + alpha-only shader", 10, ALPHA_HALF, (128, 128, 255))
shader_row("opaque frame + shader ignoring gl_Color, opacity 0.5", 40, IGNORE_COLOR, (63, 63, 191), opacity=0.5)
shader_row("opaque frame + tex*gl_Color shader, opacity 0.5", 70, TEX_TIMES_COLOR, (31, 31, 223), opacity=0.5)

# --- GridView texture: translucent / transparent fill, cached frame, camera rotation ----
# white@128 tile over a black@128 fill over blue: fill (0,0,127) then tile -> (128,128,191)
GRID_X = 10
grid_rows = []   # (label, x, y, expected)


def grid_case(label, x, y, fill, tile=True, **kw):
    g = mcrfpy.Grid(grid_size=(2, 1), texture=tex, pos=(x, y), size=(32, 16))
    g.cell_size = (16, 16)
    g.center = (16, 8)
    g.fill_color = fill
    g.layer("tilesprite").fill(0 if tile else -1)
    for k, v in kw.items():
        setattr(g, k, v)
    scene.children.append(g)
    return g


BLACK128 = mcrfpy.Color(0, 0, 0, 128)
CLEAR = mcrfpy.Color(0, 0, 0, 0)
grid_case("translucent fill + white@128 tile", 10, 270, BLACK128)
grid_rows.append(("translucent fill + white@128 tile", 18, 278, (128, 128, 191)))
grid_case("transparent fill + white@128 tile", 60, 270, CLEAR)
grid_rows.append(("transparent fill + white@128 tile", 68, 278, (128, 128, 255)))
cf = mcrfpy.Frame(pos=(110, 270), size=(32, 16), fill_color=CLEAR)
cf.cache_subtree = True
bg.children.append(cf)
g_in = mcrfpy.Grid(grid_size=(2, 1), texture=tex, pos=(0, 0), size=(32, 16))
g_in.cell_size = (16, 16)
g_in.center = (16, 8)
g_in.fill_color = CLEAR
g_in.layer("tilesprite").fill(0)
cf.children.append(g_in)
grid_rows.append(("transparent fill grid in cache_subtree frame", 118, 278, (128, 128, 255)))
cf2 = mcrfpy.Frame(pos=(160, 270), size=(32, 16), fill_color=CLEAR)
cf2.cache_subtree = True
bg.children.append(cf2)
g_in2 = mcrfpy.Grid(grid_size=(2, 1), texture=tex, pos=(0, 0), size=(32, 16))
g_in2.cell_size = (16, 16)
g_in2.center = (16, 8)
g_in2.fill_color = BLACK128
g_in2.layer("tilesprite").fill(0)
cf2.children.append(g_in2)
grid_rows.append(("translucent fill grid in cache_subtree frame", 168, 278, (128, 128, 191)))
grid_case("camera_rotation 90, translucent fill + tile", 210, 270, BLACK128, camera_rotation=90)
grid_rows.append(("camera_rotation 90, translucent fill + tile", 218, 278, (128, 128, 191)))
grid_case("camera_rotation 90, translucent fill, no tiles", 260, 270, BLACK128, tile=False, camera_rotation=90)
grid_rows.append(("camera_rotation 90, translucent fill, no tiles", 268, 278, (0, 0, 127)))
grid_case("translucent fill, no tiles", 310, 270, BLACK128, tile=False)
grid_rows.append(("translucent fill, no tiles", 318, 278, (0, 0, 127)))

ge = grid_case("translucent entity over translucent fill", 360, 270, BLACK128, tile=False)
mcrfpy.Entity((0, 0), grid=ge, sprite_index=0)
grid_rows.append(("translucent entity over translucent fill", 368, 278, (128, 128, 191)))
ger = grid_case("translucent entity, camera_rotation 90", 410, 270, BLACK128, tile=False, camera_rotation=90)
mcrfpy.Entity((0, 0), grid=ger, sprite_index=0)
grid_rows.append(("translucent entity, camera_rotation 90", 418, 278, (128, 128, 191)))

# --- a translucent Caption inside a transparent cache_subtree frame == drawn directly ----
CAP_TEXT = dict(text="HHH", font_size=14, fill_color=mcrfpy.Color(255, 255, 255, 128), outline=0)
bg.children.append(mcrfpy.Caption(pos=(10, 330), **CAP_TEXT))
cap_frame = mcrfpy.Frame(pos=(10, 360), size=(60, 24), fill_color=CLEAR)
cap_frame.cache_subtree = True
cap_frame.children.append(mcrfpy.Caption(pos=(0, 0), **CAP_TEXT))
bg.children.append(cap_frame)
# the cached frame's opacity is changed after its first render (1 -> 0.5)
op_frame = mcrfpy.Frame(pos=(100, 330), size=(30, 16), fill_color=SOLID)
op_frame.cache_subtree = True
bg.children.append(op_frame)

img = shot("all")
op_frame.opacity = 0.5
img_after = shot("opacity")


def cell(x0, y0, i):
    return px(img, x0 + 16 * i + 8, y0 + 8)


print("1. single TileLayer vs Sprite vs closed form")
# 255 * 128/255 = 128 ; 255 * (1 - 128/255) = 127
want = [(128, 128, 255), (128, 0, 127), (0, 200, 0), (255, 255, 255)]
for i in range(4):
    got, ref = cell(10, 10, i), cell(10, 60, i)
    check(near(ref, want[i]), "Sprite tile %d = %s (want %s)" % (i, ref, want[i]))
    check(near(got, ref), "TileLayer tile %d = %s matches Sprite %s" % (i, got, ref))
    check(near(got, want[i]), "TileLayer tile %d = %s (want %s)" % (i, got, want[i]))

print("2. two stacked TileLayers")
# white@128 over (128,128,255) -> 255*a + 128*(1-a) = 191.75 ; red@128 over red-on-blue (128,0,127)
# -> R 255*a + 128*(1-a) = 191.75, B 127*(1-a) = 63.25
for i in range(2):
    got, ref = cell(10, 110, i), cell(10, 160, i)
    check(near(got, ref), "stacked TileLayers tile %d = %s matches stacked Sprites %s" % (i, got, ref))
check(near(cell(10, 110, 0), (192, 192, 255)), "stacked white@128 = (192,192,255), got %s" % (cell(10, 110, 0),))

print("3. ColorLayer")
got = px(img, 10 + 8, 210 + 8)
check(near(got, (128, 128, 255)), "one translucent ColorLayer = %s (want 128,128,255)" % (got,))
got, ref = px(img, 10 + 8, 250 + 8), px(img, 200 + 8, 250 + 8)
check(near(got, ref), "two stacked ColorLayers = %s matches two Frames %s" % (got, ref))

print("4. Frame cache_subtree / clip_children / opacity")
for label, y, want in frame_rows:
    got = px(img, FRAME_X + 30, y + 12)   # clear of clip_children's 4x4 child
    check(near(got, want), "%s = %s (want %s)" % (label, got, want))

print("5. Frame shader branch keeps the straight-alpha contract")
for label, y, want in shader_rows:
    got = px(img, SHADER_X + 24, y + 4)
    check(near(got, want), "%s = %s (want %s)" % (label, got, want))

print("6. GridView texture")
for label, x, y, want in grid_rows:
    got = px(img, x, y)
    check(near(got, want), "%s = %s (want %s)" % (label, got, want))

print("7. Caption in a transparent cache_subtree frame; opacity changed after first render")
worst = 0
for dy in range(24):
    for dx in range(60):
        a, b = px(img, 10 + dx, 330 + dy), px(img, 10 + dx, 360 + dy)
        worst = max(worst, max(abs(p - q) for p, q in zip(a, b)))
check(worst <= 3, "cached translucent Caption matches the direct Caption (worst channel diff %d)" % worst)
ink = max(px(img, 10 + dx, 330 + dy)[0] for dx in range(60) for dy in range(24))
check(ink > 60, "the Caption is visible (red channel peak %d over blue)" % ink)
check(near(px(img, 100 + 24, 330 + 4), (255, 255, 255)), "opacity 1 first render is solid")
got = px(img_after, 100 + 24, 330 + 4)
check(near(got, (127, 127, 255)), "cached frame opacity 1 -> 0.5 = %s (want 127,127,255)" % (got,))

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
