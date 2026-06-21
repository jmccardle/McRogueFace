"""fuzz_import_parsers - Tiled/LDtk external file parser fuzzing (#312, Tier A).

External file parsers are historically the highest-yield fuzz target. This
drives the three loaders that ingest untrusted XML/JSON from disk:

    mcrfpy.TileSetFile(path)   -- .tsx (XML) / .tsj / .json
    mcrfpy.TileMapFile(path)   -- .tmx (XML) / .tmj / .json
    mcrfpy.LdtkProject(path)   -- .ldtk (JSON)

All three take a filesystem PATH (verified: src/tiled/PyTileSetFile.cpp:20,
src/tiled/PyTileMapFile.cpp:22, src/ldtk/PyLdtkProject.cpp:24 -- each parses
"s"). So each iteration writes the fuzzer bytes to a temp file with a
format-appropriate extension, then loads it.

Input layout: byte[0] selects the loader/extension (see LOADERS); the rest is
the file body. Seeds are built as bytes([selector]) + <fixture file bytes> so
libFuzzer mutates real .tsx/.tmx/.tmj/.ldtk content (see tests/fuzz/seeds/).

After a successful load the parsed object's properties, lookups, and dynamic
IntEnum builders (terrain_enum) are exercised -- the underlying parse code has
unguarded std::stoi on wangid tokens (src/tiled/TiledParse.cpp:200-202) and
divisions that depend on parsed grid_size/tile_size (src/ldtk/LdtkParse.cpp).

Contract: fuzz_one_input(data: bytes) -> None.
"""

import os

import mcrfpy

from fuzz_common import ByteStream, EXPECTED_EXCEPTIONS, safe_reset

# The loaders wrap std::exceptions (malformed file, unresolvable external
# tileset reference, etc.) in PyExc_IOError == OSError, which the shared
# EXPECTED_EXCEPTIONS tuple does not include. Swallow it here: a parse failure
# on garbage input is the expected outcome, not a bug.
PARSER_EXPECTED = EXPECTED_EXCEPTIONS + (OSError,)

# (extension, loader-callable). byte[0] % len(LOADERS) selects one.
LOADERS = (
    ("tsx", lambda p: mcrfpy.TileSetFile(p)),
    ("tmx", lambda p: mcrfpy.TileMapFile(p)),
    ("tmj", lambda p: mcrfpy.TileMapFile(p)),
    ("ldtk", lambda p: mcrfpy.LdtkProject(p)),
    ("tsj", lambda p: mcrfpy.TileSetFile(p)),
    ("json", lambda p: mcrfpy.TileMapFile(p)),
)

_TMP_DIR = os.environ.get("TMPDIR", "/tmp")
_TMP_BASE = os.path.join(_TMP_DIR, "mcrf_fuzz_parser_%d" % os.getpid())


def _read_seq(obj, names):
    """Read a list of property names, swallowing expected errors."""
    for name in names:
        try:
            _ = getattr(obj, name)
        except EXPECTED_EXCEPTIONS:
            pass


def exercise_tileset(stream, ts):
    _read_seq(ts, ("name", "tile_width", "tile_height", "tile_count", "columns",
                   "margin", "spacing", "image_source", "properties", "wang_sets"))
    # tile_info over a few ids including out-of-range
    for _ in range(stream.int_in_range(0, 4)):
        try:
            ts.tile_info(stream.int_in_range(-5, 4096))
        except EXPECTED_EXCEPTIONS:
            pass
    # Walk wang sets; terrain_enum builds a Python IntEnum from parsed colors.
    try:
        for ws in ts.wang_sets:
            _read_seq(ws, ("name", "type", "color_count", "colors"))
            try:
                ws.terrain_enum()
            except EXPECTED_EXCEPTIONS:
                pass
    except EXPECTED_EXCEPTIONS:
        pass


def exercise_tilemap(stream, tm):
    _read_seq(tm, ("width", "height", "tile_width", "tile_height", "orientation",
                   "properties", "tileset_count", "tile_layer_names",
                   "object_layer_names"))
    try:
        for i in range(min(tm.tileset_count, 4)):
            try:
                tm.tileset(i)
            except EXPECTED_EXCEPTIONS:
                pass
    except EXPECTED_EXCEPTIONS:
        pass
    try:
        for name in list(tm.tile_layer_names)[:3]:
            try:
                tm.tile_layer_data(name)
            except EXPECTED_EXCEPTIONS:
                pass
    except EXPECTED_EXCEPTIONS:
        pass
    for _ in range(stream.int_in_range(0, 4)):
        try:
            tm.resolve_gid(stream.int_in_range(-5, 1 << 20))
        except EXPECTED_EXCEPTIONS:
            pass
    try:
        for name in list(tm.object_layer_names)[:3]:
            try:
                tm.object_layer(name)
            except EXPECTED_EXCEPTIONS:
                pass
    except EXPECTED_EXCEPTIONS:
        pass


def exercise_ldtk(stream, proj):
    _read_seq(proj, ("version", "tileset_names", "ruleset_names", "level_names",
                     "enums"))
    try:
        for name in list(proj.tileset_names)[:3]:
            try:
                proj.tileset(name)
            except EXPECTED_EXCEPTIONS:
                pass
    except EXPECTED_EXCEPTIONS:
        pass
    try:
        for name in list(proj.ruleset_names)[:3]:
            try:
                rs = proj.ruleset(name)
                _read_seq(rs, ("name", "grid_size", "value_count", "values",
                               "rule_count", "group_count"))
                try:
                    rs.terrain_enum()
                except EXPECTED_EXCEPTIONS:
                    pass
            except EXPECTED_EXCEPTIONS:
                pass
    except EXPECTED_EXCEPTIONS:
        pass
    try:
        for name in list(proj.level_names)[:3]:
            try:
                proj.level(name)
            except EXPECTED_EXCEPTIONS:
                pass
    except EXPECTED_EXCEPTIONS:
        pass


EXERCISE = {
    "tsx": exercise_tileset,
    "tsj": exercise_tileset,
    "tmx": exercise_tilemap,
    "tmj": exercise_tilemap,
    "json": exercise_tilemap,
    "ldtk": exercise_ldtk,
}


def fuzz_one_input(data):
    stream = ByteStream(data)
    if stream.remaining < 1:
        return
    ext, loader = LOADERS[stream.u8() % len(LOADERS)]
    body = stream.take(stream.remaining)
    path = "%s.%s" % (_TMP_BASE, ext)
    try:
        with open(path, "wb") as fh:
            fh.write(body)
    except OSError:
        return
    try:
        obj = loader(path)
        EXERCISE[ext](stream, obj)
    except PARSER_EXPECTED:
        pass
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
