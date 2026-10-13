"""Write a minimal TrueType font whose metrics and ink are known exactly (#478).

Real fonts antialias, hint and carry metrics a test would have to re-derive from the
font itself. This one is built from numbers the test chooses: a filled rectangle
mapped to "X" and U+2588 and, optionally, a second rectangle that reaches below the
baseline mapped to the descender letters "gjpqy". At a pixel size where every
coordinate is a whole number of pixels, the ink is solid blocks with exact edges on
every backend. Space is an empty glyph; every other character is the empty .notdef.

Used by tests/regression/issue_478_*_test.py. The leading underscore keeps
run_tests.py from running it as a test.
"""
import struct


def _table_checksum(data):
    data = data + b"\0" * (-len(data) % 4)
    return sum(struct.unpack(">%dI" % (len(data) // 4), data)) & 0xFFFFFFFF


def _cmap(mapping):
    """Format-4 cmap: one segment per code point in `mapping` {code point: glyph}."""
    cps = sorted(mapping)
    segs = [(c, c) for c in cps] + [(0xFFFF, 0xFFFF)]
    n = len(segs)
    ends = b"".join(struct.pack(">H", e) for _, e in segs)
    starts = b"".join(struct.pack(">H", s) for s, _ in segs)
    # idDelta maps start -> glyph; the 0xFFFF sentinel maps to glyph 0.
    deltas = b"".join(struct.pack(">h", ((mapping[s] - s + 0x8000) & 0xFFFF) - 0x8000)
                      for s, _ in segs[:-1])
    deltas += struct.pack(">h", 1)
    offsets = b"\0\0" * n
    search = 2 ** (n.bit_length() - 1)
    body = struct.pack(">HHHH", n * 2, search * 2, (search.bit_length() - 1), n * 2 - search * 2)
    body += ends + b"\0\0" + starts + deltas + offsets
    sub = struct.pack(">HHH", 4, 6 + len(body), 0) + body
    # One encoding record: Windows (3), Unicode BMP (1).
    return struct.pack(">HHHHI", 0, 1, 3, 1, 12) + sub


def _box_glyph(box):
    x0, y0, x1, y1 = box
    pts = [(x0, y0), (x0, y1), (x1, y1), (x1, y0)]   # clockwise = filled in TrueType
    flags = bytes([0x01] * 4)                          # on-curve, 16-bit signed deltas
    xs = b"".join(struct.pack(">h", pts[i][0] - (pts[i - 1][0] if i else 0)) for i in range(4))
    ys = b"".join(struct.pack(">h", pts[i][1] - (pts[i - 1][1] if i else 0)) for i in range(4))
    g = struct.pack(">hhhhh", 1, x0, y0, x1, y1) + struct.pack(">H", 3) + struct.pack(">H", 0)
    g += flags + xs + ys
    return g + b"\0" * (-len(g) % 4)


def build(units_per_em, ascender, descender, box, advance, descender_box=None,
          family="McrfSynthetic"):
    """Return TTF bytes.

    box = (x_min, y_min, x_max, y_max) of the rectangle glyph, in font units, y up
    from the baseline. descender_box, if given, is a second rectangle for "gjpqy".
    ascender/descender go into both hhea and OS/2 (typo and win), so every metrics
    path in FreeType reads the same values.
    """
    x0, y0, x1, y1 = box
    # glyf: glyph 0 (.notdef) and 1 (space) are empty; glyph 2 is the box, 3 the descender.
    boxes = [box] + ([descender_box] if descender_box else [])
    glyphs = [_box_glyph(b) for b in boxes]
    glyf = b"".join(glyphs)
    offsets = [0, 0, 0]
    for g in glyphs:
        offsets.append(offsets[-1] + len(g))
    loca = b"".join(struct.pack(">I", o) for o in offsets)  # long offsets
    num_glyphs = 2 + len(glyphs)
    mapping = {0x20: 1, 0x58: 2, 0x2588: 2}
    if descender_box:
        mapping.update({ord(c): 3 for c in "gjpqy"})
    all_y0 = min(b[1] for b in boxes)

    head = struct.pack(">IIIIHH", 0x00010000, 0x00010000, 0, 0x5F0F3CF5,
                       0x000B,  # baseline at y=0, lsb at x=0, integer ppem (bit 3)
                       units_per_em)
    head += struct.pack(">qq", 0, 0)
    head += struct.pack(">hhhh", x0, min(descender, all_y0), max(x1, advance), max(y1, ascender))
    head += struct.pack(">HHhhh", 0, 8, 2, 1, 0)       # macStyle, lowestRecPPEM, dir, long loca, glyf fmt

    hhea = struct.pack(">Ihhh", 0x00010000, ascender, descender, 0)
    hhea += struct.pack(">Hhhhhhh", advance, 0, 0, x1, 1, 0, 0)
    hhea += struct.pack(">hhhhhH", 0, 0, 0, 0, 0, num_glyphs)

    maxp = struct.pack(">IHHHHHHHHHHHHHH", 0x00010000, num_glyphs, 4, 1, 0, 0,
                       2, 0, 0, 0, 0, 0, 0, 0, 0)
    hmtx = struct.pack(">HhHh", advance, 0, advance, 0)
    hmtx += b"".join(struct.pack(">Hh", advance, b[0]) for b in boxes)

    os2 = struct.pack(">HhHHH", 4, advance, 400, 5, 0)
    os2 += struct.pack(">hhhhhhhhhh", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)  # sub/superscript, strikeout
    os2 += struct.pack(">h", 0)                          # family class
    os2 += b"\0" * 10                                    # panose
    os2 += struct.pack(">IIII", 1, 0, 0, 0)              # unicode ranges (Basic Latin)
    os2 += b"MCRF"
    os2 += struct.pack(">HHH", 0x0040, 0x0020, 0x2588)  # fsSelection REGULAR, first/last char
    os2 += struct.pack(">hhh", ascender, descender, 0)   # typo
    os2 += struct.pack(">HH", ascender, -descender)      # win
    os2 += struct.pack(">II", 1, 0)                      # code page ranges
    os2 += struct.pack(">hhHHH", 0, y1, 0, 0x20, 0)

    post = struct.pack(">IIhhIIIII", 0x00030000, 0, 0, 0, 1, 0, 0, 0, 0)

    fam = family.encode("utf-16-be")
    sub = "Regular".encode("utf-16-be")
    recs = [(1, fam), (2, sub), (4, fam)]
    strings = b"".join(s for _, s in recs)
    name = struct.pack(">HHH", 0, len(recs), 6 + 12 * len(recs))
    off = 0
    for nid, s in recs:
        name += struct.pack(">HHHHHH", 3, 1, 0x0409, nid, len(s), off)
        off += len(s)
    name += strings

    tables = {
        b"OS/2": os2, b"cmap": _cmap(mapping), b"glyf": glyf, b"head": head,
        b"hhea": hhea, b"hmtx": hmtx, b"loca": loca, b"maxp": maxp, b"name": name,
        b"post": post,
    }
    tags = sorted(tables)
    n = len(tags)
    search = 2 ** (n.bit_length() - 1)
    out = struct.pack(">IHHHH", 0x00010000, n, search * 16, search.bit_length() - 1, n * 16 - search * 16)
    offset = 12 + 16 * n
    directory = b""
    blobs = b""
    for tag in tags:
        data = tables[tag]
        directory += struct.pack(">4sIII", tag, _table_checksum(data), offset + len(blobs), len(data))
        blobs += data + b"\0" * (-len(data) % 4)
    font = bytearray(out + directory + blobs)
    # head.checkSumAdjustment
    head_off = 12 + 16 * n + sum(len(tables[t]) + (-len(tables[t]) % 4) for t in tags[:tags.index(b"head")])
    adjust = (0xB1B0AFBA - _table_checksum(bytes(font))) & 0xFFFFFFFF
    font[head_off + 8:head_off + 12] = struct.pack(">I", adjust)
    return bytes(font)


def write(path, **kw):
    with open(path, "wb") as f:
        f.write(build(**kw))
    return path
