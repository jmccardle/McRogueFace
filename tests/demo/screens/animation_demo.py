"""Animation system demonstration."""
import mcrfpy
from .base import DemoScreen

class AnimationDemo(DemoScreen):
    name = "Animation System"
    description = "Property animation with easing functions"

    def setup(self):
        self.add_title("Animation System")
        self.add_description("Smooth property animation with multiple easing functions")

        # Create frames to animate.
        # #372: easings are the mcrfpy.Easing enum now, not magic strings.
        easing_types = [
            ("linear", mcrfpy.Easing.LINEAR, mcrfpy.Color(255, 100, 100)),
            ("easeIn", mcrfpy.Easing.EASE_IN, mcrfpy.Color(100, 255, 100)),
            ("easeOut", mcrfpy.Easing.EASE_OUT, mcrfpy.Color(100, 100, 255)),
            ("easeInOut", mcrfpy.Easing.EASE_IN_OUT, mcrfpy.Color(255, 255, 100)),
        ]

        self.frames = []
        for i, (easing_name, easing, color) in enumerate(easing_types):
            y = 140 + i * 60

            # Label
            label = mcrfpy.Caption(text=easing_name, pos=(50, y + 5))
            label.fill_color = mcrfpy.Color(200, 200, 200)
            self.ui.append(label)

            # Animated frame
            frame = mcrfpy.Frame(pos=(150, y), size=(40, 40))
            frame.fill_color = color
            frame.outline = 1
            frame.outline_color = mcrfpy.Color(255, 255, 255)
            self.ui.append(frame)
            self.frames.append((frame, easing))

            # Track line
            track = mcrfpy.Line(start=(150, y + 45), end=(600, y + 45),
                               color=mcrfpy.Color(60, 60, 80), thickness=1)
            self.ui.append(track)

        # Start animations for each frame (they'll animate when viewed interactively)
        for frame, easing in self.frames:
            # #372: mcrfpy.Animation is no longer exported -- animations are constructed
            # by the target itself. Animate x to 560 over 2s (starts from current x=150).
            frame.animate("x", 560.0, 2.0, easing)

        # Property animations section
        prop_frame = mcrfpy.Frame(pos=(50, 400), size=(300, 100))
        prop_frame.fill_color = mcrfpy.Color(80, 40, 40)
        prop_frame.outline = 2
        prop_frame.outline_color = mcrfpy.Color(150, 80, 80)
        self.ui.append(prop_frame)

        prop_label = mcrfpy.Caption(text="Animatable Properties:", pos=(10, 10))
        prop_label.fill_color = mcrfpy.Color(255, 200, 200)
        prop_frame.children.append(prop_label)

        props_line1 = mcrfpy.Caption(text="x, y, w, h, r, g, b, a", pos=(10, 40))
        props_line1.fill_color = mcrfpy.Color(200, 200, 200)
        prop_frame.children.append(props_line1)

        props_line2 = mcrfpy.Caption(text="scale_x, scale_y, opacity", pos=(10, 65))
        props_line2.fill_color = mcrfpy.Color(200, 200, 200)
        prop_frame.children.append(props_line2)

        # Code example - positioned below other elements
        code = """# Animate via the target: (property, target, duration, easing)
frame.animate("x", 500.0, 2.0, mcrfpy.Easing.EASE_IN_OUT)
# -> frame.x eases to 500 over 2 seconds"""
        self.add_code_example(code, x=50, y=520)
