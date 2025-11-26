"""Frame container demonstration."""
import mcrfpy
from .base import DemoScreen

class FrameDemo(DemoScreen):
    name = "Frame"
    description = "Container widget with children, clipping, and styling"

    def setup(self):
        self.add_title("Frame Widget")
        self.add_description("Container for organizing UI elements with clipping support")

        # Basic frame
        f1 = mcrfpy.Frame(pos=(50, 120), size=(150, 100))
        f1.fill_color = mcrfpy.Color(60, 60, 80)
        f1.outline = 2
        f1.outline_color = mcrfpy.Color(100, 100, 150)
        self.ui.append(f1)

        label1 = mcrfpy.Caption(text="Basic Frame", pos=(10, 10))
        label1.fill_color = mcrfpy.Color(255, 255, 255)
        f1.children.append(label1)

        # Frame with children
        f2 = mcrfpy.Frame(pos=(220, 120), size=(200, 150))
        f2.fill_color = mcrfpy.Color(40, 60, 40)
        f2.outline = 2
        f2.outline_color = mcrfpy.Color(80, 150, 80)
        self.ui.append(f2)

        for i in range(3):
            child = mcrfpy.Caption(text=f"Child {i+1}", pos=(10, 10 + i*30))
            child.fill_color = mcrfpy.Color(200, 255, 200)
            f2.children.append(child)

        # Nested frames
        f3 = mcrfpy.Frame(pos=(450, 120), size=(200, 150))
        f3.fill_color = mcrfpy.Color(60, 40, 60)
        f3.outline = 2
        f3.outline_color = mcrfpy.Color(150, 80, 150)
        self.ui.append(f3)

        inner = mcrfpy.Frame(pos=(20, 40), size=(100, 60))
        inner.fill_color = mcrfpy.Color(100, 60, 100)
        f3.children.append(inner)

        inner_label = mcrfpy.Caption(text="Nested", pos=(10, 10))
        inner_label.fill_color = mcrfpy.Color(255, 200, 255)
        inner.children.append(inner_label)

        # Code example
        code = """# Frame with children
frame = mcrfpy.Frame(pos=(50, 50), size=(200, 150))
frame.fill_color = mcrfpy.Color(60, 60, 80)
label = mcrfpy.Caption("Inside frame", pos=(10, 10))
frame.children.append(label)"""
        self.add_code_example(code, y=350)
