#!/usr/bin/env python3
"""Drag and Drop (Frame) Demo - Sort colored frames into target bins

Interactive controls:
    Mouse drag: Move frames
    ESC: Return to menu

This demonstrates:
    - Frame drag and drop using on_click + on_move (Pythonic method override pattern)
    - Hit testing for drop targets
    - State tracking and validation
"""
import mcrfpy
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class DraggableFrame(mcrfpy.Frame):
    """A frame that can be dragged around the screen.

    Uses Pythonic method override pattern - just define on_click and on_move
    methods directly, no need for self.on_click = self._on_click assignment.
    """

    def __init__(self, pos, size, color, color_type):
        """
        Args:
            pos: Initial position tuple (x, y)
            size: Size tuple (w, h)
            color: Fill color tuple (r, g, b)
            color_type: 'red' or 'blue' for sorting validation
        """
        super().__init__(pos, size, fill_color=color, outline=2, outline_color=(255, 255, 255))
        self.color_type = color_type
        self.dragging = False
        self.drag_offset = (0, 0)
        self.original_pos = pos
        # No need for self.on_click = self._on_click - just define on_click method below!

    def on_click(self, pos, button, action):
        """Handle click events for drag start/end.

        Args:
            pos: mcrfpy.Vector with x, y coordinates
            button: mcrfpy.MouseButton enum (LEFT, RIGHT, etc.)
            action: mcrfpy.InputState enum (PRESSED, RELEASED)
        """
        if button != mcrfpy.MouseButton.LEFT:
            return

        if action == mcrfpy.InputState.PRESSED:
            # Begin dragging - calculate offset from frame origin
            self.dragging = True
            self.drag_offset = (pos.x - self.x, pos.y - self.y)
        elif action == mcrfpy.InputState.RELEASED:
            if self.dragging:
                self.dragging = False
                # Notify demo of drop
                if hasattr(self, 'on_drop_callback'):
                    self.on_drop_callback(self)

    def on_move(self, pos):
        """Handle mouse movement for dragging.

        Args:
            pos: mcrfpy.Vector with x, y coordinates
        Note: #230 - on_move now only receives position, not button/action
        """
        if self.dragging:
            self.x = pos.x - self.drag_offset[0]
            self.y = pos.y - self.drag_offset[1]


class DragDropFrameDemo:
    """Demo showing frame drag and drop with sorting bins."""

    def __init__(self):
        self.scene = mcrfpy.Scene("demo_drag_drop_frame")
        self.ui = self.scene.children
        self.draggables = []
        self.setup()

    def setup(self):
        """Build the demo UI."""
        # Background
        bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=(30, 30, 35))
        self.ui.append(bg)

        # Title
        title = mcrfpy.Caption(
            text="Drag & Drop: Sort by Color",
            pos=(512, 30),
            font_size=28,
            fill_color=(255, 255, 255)
        )
        title.outline = 2
        title.outline_color = (0, 0, 0)
        self.ui.append(title)

        # Score caption
        self.score_caption = mcrfpy.Caption(
            text="Sorted: 0 / 8",
            pos=(512, 70),
            font_size=20,
            fill_color=(200, 200, 200)
        )
        self.ui.append(self.score_caption)

        # Target bins (bottom half)
        # Red bin on the left
        self.red_bin = mcrfpy.Frame(
            pos=(20, 500),
            size=(482, 248),
            fill_color=(96, 0, 0),
            outline=3,
            outline_color=(200, 50, 50)
        )
        self.ui.append(self.red_bin)

        red_label = mcrfpy.Caption(
            text="RED BIN",
            pos=(261, 600),
            font_size=32,
            fill_color=(200, 100, 100)
        )
        self.ui.append(red_label)

        # Blue bin on the right
        self.blue_bin = mcrfpy.Frame(
            pos=(522, 500),
            size=(482, 248),
            fill_color=(0, 0, 96),
            outline=3,
            outline_color=(50, 50, 200)
        )
        self.ui.append(self.blue_bin)

        blue_label = mcrfpy.Caption(
            text="BLUE BIN",
            pos=(763, 600),
            font_size=32,
            fill_color=(100, 100, 200)
        )
        self.ui.append(blue_label)

        # Create draggable frames (top half)
        # 4 red frames, 4 blue frames, arranged in 2 rows
        frame_size = (100, 80)
        spacing = 20
        start_x = 100
        start_y = 120

        positions = []
        for row in range(2):
            for col in range(4):
                x = start_x + col * (frame_size[0] + spacing + 80)
                y = start_y + row * (frame_size[1] + spacing + 40)
                positions.append((x, y))

        # Interleave red and blue
        colors = [
            ((255, 64, 64), 'red'),
            ((64, 64, 255), 'blue'),
            ((255, 64, 64), 'red'),
            ((64, 64, 255), 'blue'),
            ((64, 64, 255), 'blue'),
            ((255, 64, 64), 'red'),
            ((64, 64, 255), 'blue'),
            ((255, 64, 64), 'red'),
        ]

        for i, (pos, (color, color_type)) in enumerate(zip(positions, colors)):
            frame = DraggableFrame(pos, frame_size, color, color_type)
            frame.on_drop_callback = self._on_frame_drop
            self.draggables.append(frame)
            self.ui.append(frame)

            # Add label inside frame
            label = mcrfpy.Caption(
                text=f"{i+1}",
                pos=(40, 25),
                font_size=24,
                fill_color=(255, 255, 255)
            )
            frame.children.append(label)

        # Instructions
        instr = mcrfpy.Caption(
            text="Drag red frames to red bin, blue frames to blue bin | ESC to exit",
            pos=(512, 470),
            font_size=14,
            fill_color=(150, 150, 150)
        )
        self.ui.append(instr)

        # Initial score update
        self._update_score()

    def _point_in_frame(self, x, y, frame):
        """Check if point (x, y) is inside frame."""
        return (frame.x <= x <= frame.x + frame.w and
                frame.y <= y <= frame.y + frame.h)

    def _frame_in_bin(self, draggable, bin_frame):
        """Check if draggable frame's center is in bin."""
        center_x = draggable.x + draggable.w / 2
        center_y = draggable.y + draggable.h / 2
        return self._point_in_frame(center_x, center_y, bin_frame)

    def _on_frame_drop(self, frame):
        """Called when a frame is dropped."""
        self._update_score()

    def _update_score(self):
        """Count and display correctly sorted frames."""
        correct = 0
        for frame in self.draggables:
            if frame.color_type == 'red' and self._frame_in_bin(frame, self.red_bin):
                correct += 1
                frame.outline_color = (0, 255, 0)  # Green outline for correct
            elif frame.color_type == 'blue' and self._frame_in_bin(frame, self.blue_bin):
                correct += 1
                frame.outline_color = (0, 255, 0)
            else:
                frame.outline_color = (255, 255, 255)  # White outline otherwise

        self.score_caption.text = f"Sorted: {correct} / 8"

        if correct == 8:
            self.score_caption.text = "All Sorted! Well done!"
            self.score_caption.fill_color = (100, 255, 100)

    def on_key(self, key, state):
        """Handle keyboard input."""
        if state != "start":
            return
        if key == "Escape":
            # Return to cookbook menu or exit
            try:
                from cookbook_main import main
                main()
            except:
                sys.exit(0)

    def activate(self):
        """Activate the demo scene."""
        self.scene.on_key = self.on_key
        mcrfpy.current_scene = self.scene


def main():
    """Run the demo."""
    demo = DragDropFrameDemo()
    demo.activate()

    # Headless screenshot
    try:
        if mcrfpy.headless_mode():
            from mcrfpy import automation
            # Move some frames to bins for screenshot
            demo.draggables[0].x = 100
            demo.draggables[0].y = 550
            demo.draggables[1].x = 600
            demo.draggables[1].y = 550
            demo._update_score()

            mcrfpy.Timer("screenshot", lambda rt: (
                automation.screenshot("screenshots/primitives/drag_drop_frame.png"),
                sys.exit(0)
            ), 100)
    except AttributeError:
        pass


if __name__ == "__main__":
    main()
