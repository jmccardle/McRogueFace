"""Drawing primitives demonstration (Line, Circle, Arc)."""
import mcrfpy
from .base import DemoScreen

class PrimitivesDemo(DemoScreen):
    name = "Drawing Primitives"
    description = "Line, Circle, and Arc drawing primitives"

    def setup(self):
        self.add_title("Drawing Primitives")
        self.add_description("Line, Circle, and Arc shapes for visual effects")

        # Lines
        line1 = mcrfpy.Line(start=(50, 150), end=(200, 150),
                           color=mcrfpy.Color(255, 100, 100), thickness=3)
        self.ui.append(line1)

        line2 = mcrfpy.Line(start=(50, 180), end=(200, 220),
                           color=mcrfpy.Color(100, 255, 100), thickness=5)
        self.ui.append(line2)

        line3 = mcrfpy.Line(start=(50, 250), end=(200, 200),
                           color=mcrfpy.Color(100, 100, 255), thickness=2)
        self.ui.append(line3)

        # Circles
        circle1 = mcrfpy.Circle(center=(320, 180), radius=40,
                               fill_color=mcrfpy.Color(255, 200, 100, 150),
                               outline_color=mcrfpy.Color(255, 150, 50),
                               outline=3)
        self.ui.append(circle1)

        circle2 = mcrfpy.Circle(center=(420, 200), radius=30,
                               fill_color=mcrfpy.Color(100, 200, 255, 100),
                               outline_color=mcrfpy.Color(50, 150, 255),
                               outline=2)
        self.ui.append(circle2)

        # Arcs
        arc1 = mcrfpy.Arc(center=(550, 180), radius=50,
                         start_angle=0, end_angle=270,
                         color=mcrfpy.Color(255, 100, 255), thickness=5)
        self.ui.append(arc1)

        arc2 = mcrfpy.Arc(center=(680, 180), radius=40,
                         start_angle=45, end_angle=315,
                         color=mcrfpy.Color(255, 255, 100), thickness=3)
        self.ui.append(arc2)

        # Labels
        l1 = mcrfpy.Caption(text="Lines", pos=(100, 120))
        l1.fill_color = mcrfpy.Color(200, 200, 200)
        self.ui.append(l1)

        l2 = mcrfpy.Caption(text="Circles", pos=(350, 120))
        l2.fill_color = mcrfpy.Color(200, 200, 200)
        self.ui.append(l2)

        l3 = mcrfpy.Caption(text="Arcs", pos=(600, 120))
        l3.fill_color = mcrfpy.Color(200, 200, 200)
        self.ui.append(l3)

        # Code example
        code = """# Drawing primitives
line = mcrfpy.Line(start=(0, 0), end=(100, 100), color=Color(255,0,0), thickness=3)
circle = mcrfpy.Circle(center=(200, 200), radius=50, fill_color=Color(0,255,0,128))
arc = mcrfpy.Arc(center=(300, 200), radius=40, start_angle=0, end_angle=270)"""
        self.add_code_example(code, y=350)
