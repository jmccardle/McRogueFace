"""Color system demonstration."""
import mcrfpy
from .base import DemoScreen

class ColorDemo(DemoScreen):
    name = "Color System"
    description = "RGBA colors with transparency and blending"

    def setup(self):
        self.add_title("Color System")
        self.add_description("RGBA color support with transparency")

        # Color swatches
        colors = [
            ("Red", mcrfpy.Color(255, 0, 0)),
            ("Green", mcrfpy.Color(0, 255, 0)),
            ("Blue", mcrfpy.Color(0, 0, 255)),
            ("Yellow", mcrfpy.Color(255, 255, 0)),
            ("Cyan", mcrfpy.Color(0, 255, 255)),
            ("Magenta", mcrfpy.Color(255, 0, 255)),
            ("White", mcrfpy.Color(255, 255, 255)),
            ("Gray", mcrfpy.Color(128, 128, 128)),
        ]

        for i, (name, color) in enumerate(colors):
            x = 50 + (i % 4) * 180
            y = 130 + (i // 4) * 80

            swatch = mcrfpy.Frame(pos=(x, y), size=(60, 50))
            swatch.fill_color = color
            swatch.outline = 1
            swatch.outline_color = mcrfpy.Color(100, 100, 100)
            self.ui.append(swatch)

            label = mcrfpy.Caption(text=name, pos=(x + 70, y + 15))
            label.fill_color = mcrfpy.Color(200, 200, 200)
            self.ui.append(label)

        # Transparency demo
        trans_label = mcrfpy.Caption(text="Transparency (Alpha)", pos=(50, 310))
        trans_label.fill_color = mcrfpy.Color(255, 255, 255)
        self.ui.append(trans_label)

        # Background for transparency demo (sized to include labels)
        bg = mcrfpy.Frame(pos=(50, 340), size=(400, 95))
        bg.fill_color = mcrfpy.Color(100, 100, 100)
        self.ui.append(bg)

        # Alpha swatches - centered with symmetric padding
        alphas = [255, 200, 150, 100, 50]
        for i, alpha in enumerate(alphas):
            swatch = mcrfpy.Frame(pos=(70 + i*75, 350), size=(60, 40))
            swatch.fill_color = mcrfpy.Color(255, 100, 100, alpha)
            self.ui.append(swatch)

            label = mcrfpy.Caption(text=f"a={alpha}", pos=(75 + i*75, 400))
            label.fill_color = mcrfpy.Color(180, 180, 180)
            self.ui.append(label)

        # Code example - positioned below other elements
        code = """# Color creation
red = mcrfpy.Color(255, 0, 0)        # Opaque red
trans = mcrfpy.Color(255, 0, 0, 128) # Semi-transparent red
frame.fill_color = mcrfpy.Color(60, 60, 80)"""
        self.add_code_example(code, x=50, y=460)
