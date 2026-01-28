#!/usr/bin/env python3
"""Rotation Demo - Transform rotation and origin points

Interactive controls:
    Left/Right: Rotate selected element
    Up/Down: Adjust rotation speed
    1-4: Select element to rotate
    O: Cycle origin point
    R: Reset all rotations
    A: Toggle auto-rotation
    ESC: Exit demo

Rotation properties:
    - rotation: Angle in degrees
    - origin: (x, y) rotation center point
    - rotate_with_camera: For Grid entities
"""
import mcrfpy
import sys


class RotationDemo:
    def __init__(self):
        self.scene = mcrfpy.Scene("rotation_demo")
        self.ui = self.scene.children
        self.elements = []
        self.selected = 0
        self.auto_rotate = False
        self.rotation_speed = 45  # degrees per second
        self.origin_index = 0
        self.setup()

    def setup(self):
        """Build the demo scene."""
        # Background
        bg = mcrfpy.Frame(
            pos=(0, 0),
            size=(1024, 768),
            fill_color=mcrfpy.Color(15, 15, 20)
        )
        self.ui.append(bg)

        # Title
        title = mcrfpy.Caption(
            text="Rotation Demo",
            pos=(512, 30),
            font_size=28,
            fill_color=mcrfpy.Color(255, 255, 255)
        )
        title.outline = 2
        title.outline_color = mcrfpy.Color(0, 0, 0)
        self.ui.append(title)

        # Create rotatable elements
        self._create_frame_demo(100, 120)
        self._create_sprite_demo(400, 120)
        self._create_caption_demo(700, 120)
        self._create_origin_demo(250, 450)

        # Control panel
        self._create_control_panel()

        # Instructions
        instr = mcrfpy.Caption(
            text="Left/Right: Rotate | 1-4: Select | O: Cycle origin | A: Auto-rotate | R: Reset | ESC: Exit",
            pos=(50, 730),
            font_size=14,
            fill_color=mcrfpy.Color(120, 120, 120)
        )
        self.ui.append(instr)

        # Start update timer for auto-rotation
        mcrfpy.Timer("rotation_update", self._update, 16)  # ~60fps

    def _create_frame_demo(self, x, y):
        """Create rotating frame demo."""
        # Label
        label = mcrfpy.Caption(
            text="1. Frame Rotation",
            pos=(x + 100, y - 20),
            font_size=16,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(label)

        # Rotatable frame
        frame = mcrfpy.Frame(
            pos=(x, y),
            size=(200, 200),
            fill_color=mcrfpy.Color(80, 100, 140),
            outline_color=mcrfpy.Color(120, 150, 200),
            outline=3
        )

        # Add child content
        inner = mcrfpy.Frame(
            pos=(50, 50),
            size=(100, 100),
            fill_color=mcrfpy.Color(100, 120, 160),
            outline=1
        )
        frame.children.append(inner)

        content = mcrfpy.Caption(
            text="Rotates!",
            pos=(100, 85),
            font_size=14,
            fill_color=mcrfpy.Color(255, 255, 255)
        )
        frame.children.append(content)

        self.ui.append(frame)
        self.elements.append(('Frame', frame))

        # Rotation indicator
        angle_label = mcrfpy.Caption(
            text="0.0°",
            pos=(x + 100, y + 220),
            font_size=14,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(angle_label)
        self.frame_angle_label = angle_label

    def _create_sprite_demo(self, x, y):
        """Create rotating sprite demo (using Frame as placeholder)."""
        # Label
        label = mcrfpy.Caption(
            text="2. Sprite Rotation",
            pos=(x + 100, y - 20),
            font_size=16,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(label)

        # Use a frame to simulate sprite (actual sprite would need texture)
        sprite_frame = mcrfpy.Frame(
            pos=(x, y),
            size=(200, 200),
            fill_color=mcrfpy.Color(100, 140, 80),
            outline_color=mcrfpy.Color(150, 200, 120),
            outline=3
        )

        # Arrow pattern to show rotation direction
        arrow_v = mcrfpy.Caption(
            text="^",
            pos=(100, 40),
            font_size=48,
            fill_color=mcrfpy.Color(255, 255, 255)
        )
        sprite_frame.children.append(arrow_v)

        sprite_label = mcrfpy.Caption(
            text="UP",
            pos=(100, 100),
            font_size=24,
            fill_color=mcrfpy.Color(255, 255, 255)
        )
        sprite_frame.children.append(sprite_label)

        self.ui.append(sprite_frame)
        self.elements.append(('Sprite', sprite_frame))

        angle_label = mcrfpy.Caption(
            text="0.0°",
            pos=(x + 100, y + 220),
            font_size=14,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(angle_label)
        self.sprite_angle_label = angle_label

    def _create_caption_demo(self, x, y):
        """Create rotating caption demo."""
        # Label
        label = mcrfpy.Caption(
            text="3. Caption Rotation",
            pos=(x + 100, y - 20),
            font_size=16,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(label)

        # Background for visibility
        caption_bg = mcrfpy.Frame(
            pos=(x, y),
            size=(200, 200),
            fill_color=mcrfpy.Color(40, 40, 50),
            outline_color=mcrfpy.Color(80, 80, 100),
            outline=1
        )
        self.ui.append(caption_bg)

        # Rotatable caption
        caption = mcrfpy.Caption(
            text="Rotating Text!",
            pos=(x + 100, y + 100),
            font_size=24,
            fill_color=mcrfpy.Color(255, 200, 100)
        )
        caption.outline = 2
        caption.outline_color = mcrfpy.Color(0, 0, 0)

        self.ui.append(caption)
        self.elements.append(('Caption', caption))

        angle_label = mcrfpy.Caption(
            text="0.0°",
            pos=(x + 100, y + 220),
            font_size=14,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(angle_label)
        self.caption_angle_label = angle_label

    def _create_origin_demo(self, x, y):
        """Create demo showing different origin points."""
        # Label
        label = mcrfpy.Caption(
            text="4. Origin Point Demo (press O to cycle)",
            pos=(x + 200, y - 20),
            font_size=16,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(label)

        # Large frame to show origin effects
        origin_frame = mcrfpy.Frame(
            pos=(x, y),
            size=(400, 200),
            fill_color=mcrfpy.Color(140, 80, 100),
            outline_color=mcrfpy.Color(200, 120, 150),
            outline=3
        )

        # Origin marker
        origin_marker = mcrfpy.Frame(
            pos=(0, 0),
            size=(10, 10),
            fill_color=mcrfpy.Color(255, 255, 0),
            outline=0
        )
        origin_frame.children.append(origin_marker)
        self.origin_marker = origin_marker

        # Origin name
        origin_label = mcrfpy.Caption(
            text="Origin: Top-Left",
            pos=(200, 85),
            font_size=16,
            fill_color=mcrfpy.Color(255, 255, 255)
        )
        origin_frame.children.append(origin_label)
        self.origin_name_label = origin_label

        self.ui.append(origin_frame)
        self.elements.append(('Origin Demo', origin_frame))
        self.origin_frame = origin_frame

        # Origin positions to cycle through
        self.origins = [
            ("Top-Left", (0, 0)),
            ("Top-Center", (200, 0)),
            ("Top-Right", (400, 0)),
            ("Center-Left", (0, 100)),
            ("Center", (200, 100)),
            ("Center-Right", (400, 100)),
            ("Bottom-Left", (0, 200)),
            ("Bottom-Center", (200, 200)),
            ("Bottom-Right", (400, 200)),
        ]

        angle_label = mcrfpy.Caption(
            text="0.0°",
            pos=(x + 200, y + 220),
            font_size=14,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(angle_label)
        self.origin_angle_label = angle_label

    def _create_control_panel(self):
        """Create control panel showing current state."""
        panel = mcrfpy.Frame(
            pos=(750, 450),
            size=(220, 180),
            fill_color=mcrfpy.Color(30, 30, 40),
            outline_color=mcrfpy.Color(60, 60, 80),
            outline=1
        )
        self.ui.append(panel)

        panel_title = mcrfpy.Caption(
            text="Status",
            pos=(110, 10),
            font_size=16,
            fill_color=mcrfpy.Color(200, 200, 200)
        )
        panel.children.append(panel_title)

        self.selected_label = mcrfpy.Caption(
            text="Selected: Frame",
            pos=(15, 40),
            font_size=14,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        panel.children.append(self.selected_label)

        self.speed_label = mcrfpy.Caption(
            text="Speed: 45°/sec",
            pos=(15, 65),
            font_size=14,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        panel.children.append(self.speed_label)

        self.auto_label = mcrfpy.Caption(
            text="Auto-rotate: Off",
            pos=(15, 90),
            font_size=14,
            fill_color=mcrfpy.Color(200, 100, 100)
        )
        panel.children.append(self.auto_label)

    def _update(self, runtime):
        """Update loop for auto-rotation."""
        if self.auto_rotate:
            dt = 0.016  # Approximately 16ms per frame
            for name, element in self.elements:
                try:
                    element.rotation = (element.rotation + self.rotation_speed * dt) % 360
                except AttributeError:
                    pass

        # Update angle labels
        self._update_angle_labels()

    def _update_angle_labels(self):
        """Update the angle display labels."""
        labels = [self.frame_angle_label, self.sprite_angle_label,
                  self.caption_angle_label, self.origin_angle_label]

        for i, (name, element) in enumerate(self.elements):
            if i < len(labels):
                try:
                    labels[i].text = f"{element.rotation:.1f}°"
                except AttributeError:
                    labels[i].text = "N/A"

    def _cycle_origin(self):
        """Cycle to the next origin point."""
        self.origin_index = (self.origin_index + 1) % len(self.origins)
        name, pos = self.origins[self.origin_index]

        # Update origin
        try:
            self.origin_frame.origin = pos
            self.origin_name_label.text = f"Origin: {name}"
            # Move marker to show origin position
            self.origin_marker.x = pos[0] - 5
            self.origin_marker.y = pos[1] - 5
        except AttributeError:
            pass

    def on_key(self, key, state):
        """Handle keyboard input."""
        if state != "start":
            return

        if key == "Escape":
            sys.exit(0)
        elif key == "Left":
            # Rotate left (counter-clockwise)
            name, element = self.elements[self.selected]
            try:
                element.rotation = (element.rotation - 15) % 360
            except AttributeError:
                pass
        elif key == "Right":
            # Rotate right (clockwise)
            name, element = self.elements[self.selected]
            try:
                element.rotation = (element.rotation + 15) % 360
            except AttributeError:
                pass
        elif key == "Up":
            self.rotation_speed = min(180, self.rotation_speed + 15)
            self.speed_label.text = f"Speed: {self.rotation_speed}°/sec"
        elif key == "Down":
            self.rotation_speed = max(15, self.rotation_speed - 15)
            self.speed_label.text = f"Speed: {self.rotation_speed}°/sec"
        elif key in ("Num1", "Num2", "Num3", "Num4"):
            self.selected = int(key[-1]) - 1
            if self.selected < len(self.elements):
                self.selected_label.text = f"Selected: {self.elements[self.selected][0]}"
        elif key == "O":
            self._cycle_origin()
        elif key == "A":
            self.auto_rotate = not self.auto_rotate
            if self.auto_rotate:
                self.auto_label.text = "Auto-rotate: On"
                self.auto_label.fill_color = mcrfpy.Color(100, 200, 100)
            else:
                self.auto_label.text = "Auto-rotate: Off"
                self.auto_label.fill_color = mcrfpy.Color(200, 100, 100)
        elif key == "R":
            # Reset all rotations
            for name, element in self.elements:
                try:
                    element.rotation = 0
                except AttributeError:
                    pass
            self.origin_index = 0
            name, pos = self.origins[0]
            try:
                self.origin_frame.origin = pos
                self.origin_name_label.text = f"Origin: {name}"
                self.origin_marker.x = pos[0] - 5
                self.origin_marker.y = pos[1] - 5
            except AttributeError:
                pass

    def activate(self):
        """Activate the demo scene."""
        self.scene.on_key = self.on_key
        mcrfpy.current_scene = self.scene


def main():
    """Run the rotation demo."""
    demo = RotationDemo()
    demo.activate()

    # Headless mode: capture screenshot and exit
    try:
        if mcrfpy.headless_mode():
            from mcrfpy import automation
            # Rotate elements for visual interest
            for name, element in demo.elements:
                try:
                    element.rotation = 15
                except AttributeError:
                    pass
            mcrfpy.Timer("screenshot", lambda rt: (
                automation.screenshot("screenshots/features/rotation_demo.png"),
                sys.exit(0)
            ), 200)
    except AttributeError:
        pass


if __name__ == "__main__":
    main()
