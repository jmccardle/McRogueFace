#!/usr/bin/env python3
"""
Texture identity (#430, Phase 2, texture group).

A PyTexture now carries a PythonObjectCache serial, PyTexture::pyobject_for() is the one
conversion path, and Texture(...) / its factories register themselves. So every accessor
that hands a texture back returns THE wrapper: the very Texture the user passed in, and
the same object across two reads.
"""
import gc
import sys

import mcrfpy

failures = []
TEX_PATH = "assets/kenney_tinydungeon.png"


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


def same(label, get):
    try:
        a, b = get(), get()
    except Exception as exc:  # an accessor that raises is a failure, not a skip
        check(False, f"{label}: raised {type(exc).__name__}: {exc}")
        return
    check(a is not None and a is b, f"{label} is stable")


def user_texture_comes_back():
    print("user-constructed Texture comes back as itself")
    tex = mcrfpy.Texture(TEX_PATH, 16, 16)
    g = mcrfpy.Grid(grid_size=(4, 4), texture=tex)
    check(g.texture is tex, "GridView.texture is the texture passed in")
    check(g.grid_data.texture is tex, "GridData.texture is the texture passed in")
    same("GridView.texture", lambda: g.texture)
    same("GridData.texture", lambda: g.grid_data.texture)

    t = mcrfpy.TileLayer(name="t", texture=tex)
    check(t.texture is tex, "TileLayer.texture is the texture passed in")
    same("TileLayer.texture", lambda: t.texture)

    gd = mcrfpy.GridData(grid_size=(3, 3), texture=tex)
    check(gd.texture is tex, "standalone GridData.texture is the texture passed in")


def engine_held_texture_is_stable():
    print("a texture only the engine holds keeps one wrapper while it is alive")
    tex = mcrfpy.Texture(TEX_PATH, 16, 16)
    g = mcrfpy.Grid(grid_size=(4, 4), texture=tex)
    del tex
    gc.collect()
    a = g.texture
    b = g.grid_data.texture
    check(a is b, "GridView.texture is GridData.texture after the user's ref is gone")
    check(a.sprite_width == 16 and a.sprite_height == 16, "re-wrapped texture keeps its data")
    del a, b
    gc.collect()
    same("GridView.texture (re-wrapped)", lambda: g.texture)


def factory_textures():
    print("factory-made textures register and round-trip")
    data = bytes([255, 0, 0, 255]) * (16 * 16)
    fb = mcrfpy.Texture.from_bytes(data, 16, 16, 16, 16)
    layer = mcrfpy.TileLayer(name="fb", texture=fb)
    check(layer.texture is fb, "TileLayer.texture is a Texture.from_bytes result")

    comp = mcrfpy.Texture.composite([fb, fb], 16, 16)
    g = mcrfpy.Grid(grid_size=(2, 2), texture=comp)
    check(g.texture is comp, "GridView.texture is a Texture.composite result")

    shifted = fb.hsl_shift(90.0)
    check(shifted is not fb, "hsl_shift returns a NEW texture")
    layer2 = mcrfpy.TileLayer(name="hs", texture=shifted)
    check(layer2.texture is shifted, "TileLayer.texture is an hsl_shift result")


def shared_texture_across_owners():
    print("one texture shared by several owners is one wrapper")
    tex = mcrfpy.Texture(TEX_PATH, 16, 16)
    g = mcrfpy.Grid(grid_size=(4, 4), texture=tex)
    t = mcrfpy.TileLayer(name="shared", texture=tex)
    spr = mcrfpy.Sprite(pos=(0, 0), texture=tex, sprite_index=0)
    check(g.texture is t.texture, "GridView.texture is TileLayer.texture")
    check(spr.texture is tex, "Sprite.texture (pyObject() path) is the texture passed in")
    same("Sprite.texture", lambda: spr.texture)


def default_texture():
    print("mcrfpy.default_texture")
    dt = mcrfpy.default_texture
    if dt is None:
        print("  (no default_texture in this build; skipped)")
        return
    g = mcrfpy.Grid(grid_size=(4, 4))
    gt = g.texture
    if gt is not None:
        check(gt is dt, "default Grid's texture is mcrfpy.default_texture")


def main():
    for t in (user_texture_comes_back, engine_held_texture_is_stable,
              factory_textures, shared_texture_across_owners, default_texture):
        try:
            t()
        except Exception as exc:
            check(False, f"{t.__name__}: raised {type(exc).__name__}: {exc}")
        gc.collect()
    if failures:
        print(f"FAIL: {len(failures)} check(s) failed")
        sys.exit(1)
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
