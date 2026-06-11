# Unit test for entity.texture (#313): happy-path get/set semantics.
import mcrfpy
import sys

failures = []

def check(cond, label):
    status = "ok" if cond else "FAIL"
    print("  %s: %s" % (status, label))
    if not cond:
        failures.append(label)

def main():
    # Entity constructed WITHOUT a texture falls back to mcrfpy.default_texture
    e_default = mcrfpy.Entity(grid_pos=(0, 0))
    dt = mcrfpy.default_texture
    check(e_default.texture is not None, "no-texture entity exposes a texture")
    check(isinstance(e_default.texture, mcrfpy.Texture),
          "no-texture entity texture is a Texture")
    check(e_default.texture.source == dt.source and
          e_default.texture.sprite_width == dt.sprite_width,
          "no-texture entity uses mcrfpy.default_texture")

    # Entity constructed WITH a texture exposes that texture
    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    e = mcrfpy.Entity(grid_pos=(1, 1), texture=tex, sprite_index=3)
    check(e.texture.source == tex.source, "constructor texture is exposed")
    check(e.texture.sprite_count == tex.sprite_count,
          "exposed texture matches constructor texture's sprite_count")

    # Setting a texture is reflected on read-back; sprite_index preserved
    tex2 = mcrfpy.Texture.from_bytes(bytes([0, 255, 0, 255] * 256), 16, 16, 16, 16,
                                     name="<entity-texture-test>")
    e.texture = tex2
    check(e.texture.source == tex2.source, "assigned texture is exposed")
    check(e.sprite_index == 3, "sprite_index preserved across texture assignment")

    # Works without a grid attachment (no crash, no grid needed)
    check(e_default.texture is not None, "texture access works without grid attachment")

    if failures:
        print("FAIL: %d check(s) failed" % len(failures))
        sys.exit(1)
    print("PASS")
    sys.exit(0)

if __name__ == "__main__":
    main()
