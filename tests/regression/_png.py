"""Stdlib-only PNG decoding for screenshot tests (#478): 8-bit RGB/RGBA, non-interlaced,
which is what the engine's screenshot encoder emits. The leading underscore keeps
run_tests.py from running it as a test."""
import struct
import zlib


def read_png(path, crop_w=None, crop_h=None):
    """Return (width, height, channels, pixel bytes).

    With crop_w / crop_h, decode only the top-left crop_w x crop_h pixels and return that crop
    (width and height are then the crop's, so (x, y) indexing is unchanged inside it). This is exact:
    un-filtering a row needs only the row above and the bytes to its left. The pure-Python filter loop
    over a whole 1024x768 screenshot costs ~0.7 s (several times that under the debug CPython build),
    so a test that inspects a small corner should crop."""
    with open(path, "rb") as f:
        data = f.read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    pos = 8
    idat = b""
    width = height = color = None
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        ctype = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if ctype == b"IHDR":
            width, height, depth, color, _, _, interlace = struct.unpack(">IIBBBBB", chunk)
            assert depth == 8 and color in (2, 6) and interlace == 0
        elif ctype == b"IDAT":
            idat += chunk
        elif ctype == b"IEND":
            break
    raw = zlib.decompress(idat)
    channels = 3 if color == 2 else 4
    full_stride = width * channels
    out_w = min(width, crop_w) if crop_w else width
    out_h = min(height, crop_h) if crop_h else height
    stride = out_w * channels
    height, width = out_h, out_w
    out = bytearray(height * stride)
    prev = bytearray(stride)
    p = 0
    for y in range(height):
        filt = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += full_stride
        if filt == 1:
            for i in range(channels, stride):
                line[i] = (line[i] + line[i - channels]) & 0xFF
        elif filt == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif filt == 3:
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif filt == 4:
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                b = prev[i]
                c = prev[i - channels] if i >= channels else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        elif filt != 0:
            raise AssertionError("bad PNG filter %d" % filt)
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return width, height, channels, bytes(out)


def mask(img, rgb, region=None):
    """Set of (x, y) whose pixel is exactly `rgb`, inside region (x0, y0, x1, y1)."""
    w, h, ch, px = img
    x0, y0, x1, y1 = region or (0, 0, w, h)
    out = set()
    for y in range(max(0, y0), min(h, y1)):
        for x in range(max(0, x0), min(w, x1)):
            i = (y * w + x) * ch
            if tuple(px[i:i + 3]) == rgb:
                out.add((x, y))
    return out


def bbox(points):
    """(x0, y0, x1, y1) half-open bounding box of a point set, or None."""
    if not points:
        return None
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(xs), min(ys), max(xs) + 1, max(ys) + 1)


def rows(img, region):
    """Raw bytes of `region`, row-major: for exact image comparison."""
    w, h, ch, px = img
    x0, y0, x1, y1 = region
    return b"".join(px[(y * w + x0) * ch:(y * w + x1) * ch] for y in range(y0, y1))
