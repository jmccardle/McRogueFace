#!/usr/bin/env python3
"""
Object identity for TileSetFile and SoundBuffer (#430, Phase 2: tilesets_audio).

TileMapFile.tileset() and LdtkProject.tileset() used to tp_alloc a fresh TileSetFile on
every call, and every SoundBuffer handed back to Python (Sound.buffer, every factory and
effect) was a fresh wrapper. Both types now carry their PythonObjectCache key on the C++
object (TileSetData / SoundBufferData::serial_number), so one underlying tileset or
buffer always comes back as one Python object -- including the one the user built.
"""
import gc
import os
import sys
import weakref

import mcrfpy

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = os.path.dirname(HERE)
ROOT = os.path.dirname(TESTS)
TMX = os.path.join(TESTS, "assets", "tiled", "test_map.tmx")
TSX = os.path.join(TESTS, "assets", "tiled", "test_tileset.tsx")
LDTK = os.path.join(TESTS, "fixtures", "test_project.ldtk")
OGG = os.path.join(ROOT, "assets", "sfx", "splat1.ogg")

failures = []


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


def tilesets():
    print("tilesets")
    tm = mcrfpy.TileMapFile(TMX)
    same("TileMapFile.tileset(0)[1]", lambda: tm.tileset(0)[1])
    firstgid, ts = tm.tileset(0)
    check(isinstance(ts, mcrfpy.TileSetFile), "TileMapFile.tileset(0) yields a TileSetFile")
    check(weakref.ref(ts)() is ts, "TileSetFile is weak-referenceable")
    name = ts.name
    del ts
    gc.collect()
    _, again = tm.tileset(0)
    check(again.name == name, "tileset re-fetched after its wrapper died is the same data")

    user = mcrfpy.TileSetFile(TSX)
    check(weakref.ref(user)() is user, "user-built TileSetFile is weak-referenceable")
    check(user.tile_count > 0, "user-built TileSetFile loaded")

    proj = mcrfpy.LdtkProject(LDTK)
    same("LdtkProject.tileset(name)", lambda: proj.tileset("Test_Tileset"))
    check(proj.tileset("Test_Tileset") is not tm.tileset(0)[1],
          "different parsed tilesets are different objects")


def soundbuffers():
    print("soundbuffers")
    buf = mcrfpy.SoundBuffer.tone(440, 0.25, "sine")
    check(weakref.ref(buf)() is buf, "SoundBuffer is weak-referenceable")
    snd = mcrfpy.Sound(buf)
    check(snd.buffer is buf, "Sound(buf).buffer is the factory-made buffer")
    same("Sound.buffer", lambda: snd.buffer)

    effected = buf.gain(0.5)
    check(effected is not buf, "an effect returns a new SoundBuffer")
    check(mcrfpy.Sound(effected).buffer is effected, "an effect's buffer comes back as itself")

    loaded = mcrfpy.SoundBuffer(OGG)
    check(mcrfpy.Sound(loaded).buffer is loaded, "user-loaded SoundBuffer comes back as itself")

    # The wrapper may die while a Sound still holds the data: a new wrapper is made.
    snd2 = mcrfpy.Sound(mcrfpy.SoundBuffer.tone(220, 0.1, "square"))
    gc.collect()
    b1 = snd2.buffer
    check(b1 is not None and snd2.buffer is b1, "Sound.buffer re-wrapped after its wrapper died")


def main():
    for t in (tilesets, soundbuffers):
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
