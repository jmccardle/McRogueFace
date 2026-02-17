"""CharacterAssembler - composite layered sprite sheets with HSL recoloring.

Uses the engine's Texture.composite() and texture.hsl_shift() methods to
build composite character textures from multiple layer PNG files, without
requiring PIL or any external Python packages.
"""
import mcrfpy
from .formats import PUNY_29, SheetFormat


class CharacterAssembler:
    """Build composite character sheets from layer files.

    Layers are added bottom-to-top (skin first, then clothes, hair, etc).
    Each layer can be HSL-shifted for recoloring before compositing.

    Args:
        fmt: SheetFormat describing the sprite dimensions (default: PUNY_29)
    """

    def __init__(self, fmt=None):
        if fmt is None:
            fmt = PUNY_29
        self.fmt = fmt
        self.layers = []

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

        Loads each layer file, applies HSL shifts if any, then composites
        all layers bottom-to-top using alpha blending.

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
            tex = mcrfpy.Texture(path, self.fmt.tile_w, self.fmt.tile_h)
            if h != 0.0 or s != 0.0 or l != 0.0:
                tex = tex.hsl_shift(h, s, l)
            textures.append(tex)

        if len(textures) == 1:
            return textures[0]

        return mcrfpy.Texture.composite(
            textures, self.fmt.tile_w, self.fmt.tile_h, name
        )
