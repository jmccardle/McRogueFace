"""CharacterAssembler - composite layered sprite sheets with HSL recoloring.

Uses the engine's Texture.composite() and texture.hsl_shift() methods to
build composite character textures from multiple layer PNG files, without
requiring PIL or any external Python packages.

HSL notes (from C++ investigation):
    - tex.hsl_shift(h, s, l) always creates a NEW texture by copying all
      pixels, converting RGB->HSL, applying shifts, converting back.
    - Works on any texture: file-loaded, from_bytes, composite, or
      previously shifted. Alpha is preserved; transparent pixels skipped.
    - No engine-level caching exists -- repeated identical calls produce
      separate texture objects. The TextureCache below avoids redundant
      loads and shifts at the Python level.
"""
import mcrfpy
from .formats import PUNY_29, SheetFormat


class TextureCache:
    """Cache for loaded and HSL-shifted textures to avoid redundant disk I/O.

    Keys are (path, hue_shift, sat_shift, lit_shift) tuples.
    Call clear() to free all cached textures.
    """

    def __init__(self):
        self._cache = {}

    def get(self, path, tile_w, tile_h, hue=0.0, sat=0.0, lit=0.0):
        """Load a texture, using cached version if available.

        Args:
            path: File path to the PNG
            tile_w: Sprite tile width
            tile_h: Sprite tile height
            hue: Hue rotation in degrees
            sat: Saturation adjustment
            lit: Lightness adjustment

        Returns:
            mcrfpy.Texture
        """
        key = (path, hue, sat, lit)
        if key not in self._cache:
            tex = mcrfpy.Texture(path, tile_w, tile_h)
            if hue != 0.0 or sat != 0.0 or lit != 0.0:
                tex = tex.hsl_shift(hue, sat, lit)
            self._cache[key] = tex
        return self._cache[key]

    def clear(self):
        """Drop all cached textures."""
        self._cache.clear()

    def __len__(self):
        return len(self._cache)

    def __contains__(self, key):
        return key in self._cache


class CharacterAssembler:
    """Build composite character sheets from layer files.

    Layers are added bottom-to-top (skin first, then clothes, hair, etc).
    Each layer can be HSL-shifted for recoloring before compositing.

    Args:
        fmt: SheetFormat describing the sprite dimensions (default: PUNY_29)
        cache: Optional TextureCache for reusing loaded textures across
               multiple build() calls. If None, a private cache is created.
    """

    def __init__(self, fmt=None, cache=None):
        if fmt is None:
            fmt = PUNY_29
        self.fmt = fmt
        self.layers = []
        self.cache = cache if cache is not None else TextureCache()

    def add_layer(self, path, hue_shift=0.0, sat_shift=0.0, lit_shift=0.0):
        """Queue a layer PNG with optional HSL recoloring.

        Args:
            path: File path to the layer PNG
            hue_shift: Hue rotation in degrees [0, 360)
            sat_shift: Saturation adjustment [-1.0, 1.0]
            lit_shift: Lightness adjustment [-1.0, 1.0]
        """
        self.layers.append((path, hue_shift, sat_shift, lit_shift))
        return self  # allow chaining

    def clear(self):
        """Remove all queued layers."""
        self.layers.clear()
        return self

    def build(self, name="<composed>"):
        """Composite all queued layers into a single Texture.

        Loads each layer file (using the cache to avoid redundant disk reads
        and HSL computations), then composites all layers bottom-to-top.

        Args:
            name: Optional name for the resulting texture

        Returns:
            mcrfpy.Texture: The composited texture

        Raises:
            ValueError: If no layers have been added
            IOError: If a layer file cannot be loaded
        """
        if not self.layers:
            raise ValueError("No layers added. Call add_layer() first.")

        textures = []
        for path, h, s, l in self.layers:
            tex = self.cache.get(path, self.fmt.tile_w, self.fmt.tile_h, h, s, l)
            textures.append(tex)

        if len(textures) == 1:
            return textures[0]

        return mcrfpy.Texture.composite(
            textures, self.fmt.tile_w, self.fmt.tile_h, name
        )
