"""#527: every bundled assets/*.tsx loads, references its image(s) inside assets/, and
declares geometry that matches the tile grid and the real image on disk.

TileSetFile.to_texture() ignores spacing/margin/columns/tilecount, so loading alone
would pass a .tsx with the right path but wrong geometry. Checked here instead:
  image width  == 2*margin + columns*tilewidth  + (columns-1)*spacing
  image height == 2*margin + rows*tileheight    + (rows-1)*spacing   (rows = tilecount/columns)
  declared image width/height == the PNG's real pixel size (IHDR; no engine API exposes it)
"""
import glob, os, re, struct, sys
import xml.etree.ElementTree as ET
import mcrfpy

fails = []
files = sorted(glob.glob("assets/*.tsx"))
if not files:
    print("FAIL no assets/*.tsx found (cwd must be the engine dir)")
    sys.exit(1)

def png_size(path):
    with open(path, "rb") as fh:
        head = fh.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        raise ValueError("not a PNG")
    return struct.unpack(">II", head[16:24])

checked = 0
for f in files:
    root = ET.parse(f).getroot()
    images = list(root.iter("image"))
    if not images:
        fails.append(f"{f}: tileset has no <image> element")
        continue
    ok_sources = True
    for img in images:
        src = img.get("source")
        if not src:
            fails.append(f"{f}: <image> without a source")
            ok_sources = False
        elif os.path.isabs(src) or re.match(r"^[A-Za-z]:", src) or ".." in src.replace("\\", "/").split("/"):
            fails.append(f"{f}: image source {src!r} is absolute or escapes assets/")
            ok_sources = False
        elif not os.path.isfile(os.path.join(os.path.dirname(f), src)):
            fails.append(f"{f}: image source {src!r} does not exist next to the .tsx")
            ok_sources = False
    try:
        tex = mcrfpy.TileSetFile(f).to_texture()
        if tex is None:
            fails.append(f"{f}: to_texture() returned None")
    except Exception as e:
        fails.append(f"{f}: {type(e).__name__}: {e}")

    # geometry: only a single top-level <image> (not image-collection tilesets)
    top = root.findall("image")
    if len(top) != 1 or not ok_sources:
        continue
    checked += 1
    tw, th = int(root.get("tilewidth")), int(root.get("tileheight"))
    count, cols = int(root.get("tilecount")), int(root.get("columns"))
    spacing, margin = int(root.get("spacing", 0)), int(root.get("margin", 0))
    iw, ih = int(top[0].get("width")), int(top[0].get("height"))
    if cols <= 0 or count % cols:
        fails.append(f"{f}: tilecount {count} not divisible by columns {cols}")
        continue
    rows = count // cols
    exp_w = 2 * margin + cols * tw + (cols - 1) * spacing
    exp_h = 2 * margin + rows * th + (rows - 1) * spacing
    if (iw, ih) != (exp_w, exp_h):
        fails.append(f"{f}: declared image {iw}x{ih} != tile grid {exp_w}x{exp_h} "
                     f"({cols}x{rows} tiles {tw}x{th}, spacing {spacing}, margin {margin})")
    path = os.path.join(os.path.dirname(f), top[0].get("source"))
    try:
        real = png_size(path)
    except Exception as e:
        fails.append(f"{f}: cannot read {path}: {e}")
        continue
    if real != (iw, ih):
        fails.append(f"{f}: declared image {iw}x{ih} != real {path} {real[0]}x{real[1]}")

if not checked:
    fails.append("no tileset had a single top-level <image> to geometry-check")

if fails:
    for m in fails:
        print("FAIL", m)
    sys.exit(1)
print(f"PASS ({len(files)} tilesets, {checked} geometry-checked)")
sys.exit(0)
