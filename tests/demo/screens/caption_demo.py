"""Caption widget demonstration."""
import mcrfpy
from .base import DemoScreen

class CaptionDemo(DemoScreen):
    name = "Caption"
    description = "Text rendering with fonts, colors, and outlines"

    def setup(self):
        self.add_title("Caption Widget")
        self.add_description("Text rendering with customizable fonts, colors, and outlines")

        # Basic caption
        c1 = mcrfpy.Caption(text="Basic Caption", pos=(50, 120))
        c1.fill_color = mcrfpy.Color(255, 255, 255)
        self.ui.append(c1)

        # Colored caption
        c2 = mcrfpy.Caption(text="Colored Text", pos=(50, 160))
        c2.fill_color = mcrfpy.Color(255, 100, 100)
        self.ui.append(c2)

        # Outlined caption
        c3 = mcrfpy.Caption(text="Outlined Text", pos=(50, 200))
        c3.fill_color = mcrfpy.Color(255, 255, 0)
        c3.outline = 2
        c3.outline_color = mcrfpy.Color(0, 0, 0)
        self.ui.append(c3)

        # Large text with background
        c4 = mcrfpy.Caption(text="Large Title", pos=(50, 260))
        c4.fill_color = mcrfpy.Color(100, 200, 255)
        c4.outline = 3
        c4.outline_color = mcrfpy.Color(0, 50, 100)
        self.ui.append(c4)

        # Code example
        code = """# Caption Examples
caption = mcrfpy.Caption("Hello!", pos=(100, 100))
caption.fill_color = mcrfpy.Color(255, 255, 255)
caption.outline = 2
caption.outline_color = mcrfpy.Color(0, 0, 0)"""
        self.add_code_example(code, y=350)
