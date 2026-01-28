#!/usr/bin/env python3
"""Animation Chain/Group Demo - Complex animation orchestration

Interactive controls:
    1: Run sequential chain demo
    2: Run parallel group demo
    3: Run callback demo
    4: Run looping demo
    5: Run combined demo
    R: Reset all animations
    ESC: Exit demo
"""
import mcrfpy
import sys

# Add parent to path for imports
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from lib.anim_utils import (
    AnimationChain, AnimationGroup, delay, callback,
    fade_in, fade_out, slide_in_from_left, shake
)


class AnimationDemo:
    def __init__(self):
        self.scene = mcrfpy.Scene("animation_demo")
        self.ui = self.scene.children
        self.demo_frames = []
        self.active_animations = []
        self.setup()

    def setup(self):
        """Build the demo scene."""
        # Background
        bg = mcrfpy.Frame(
            pos=(0, 0),
            size=(1024, 768),
            fill_color=mcrfpy.Color(20, 20, 25)
        )
        self.ui.append(bg)

        # Title
        title = mcrfpy.Caption(
            text="Animation Chain/Group Demo",
            pos=(512, 30),
            font_size=28,
            fill_color=mcrfpy.Color(255, 255, 255)
        )
        title.outline = 2
        title.outline_color = mcrfpy.Color(0, 0, 0)
        self.ui.append(title)

        # Create demo areas
        self._create_chain_demo()
        self._create_group_demo()
        self._create_callback_demo()
        self._create_loop_demo()
        self._create_combined_demo()

        # Status display
        self.status = mcrfpy.Caption(
            text="Press 1-5 to run demos, R to reset",
            pos=(50, 700),
            font_size=16,
            fill_color=mcrfpy.Color(100, 200, 100)
        )
        self.ui.append(self.status)

        # Instructions
        instr = mcrfpy.Caption(
            text="1: Chain | 2: Group | 3: Callback | 4: Loop | 5: Combined | R: Reset | ESC: Exit",
            pos=(50, 730),
            font_size=14,
            fill_color=mcrfpy.Color(120, 120, 120)
        )
        self.ui.append(instr)

    def _create_chain_demo(self):
        """Create the sequential chain demo area."""
        # Label
        label = mcrfpy.Caption(
            text="1. Sequential Chain",
            pos=(50, 80),
            font_size=16,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(label)

        # Description
        desc = mcrfpy.Caption(
            text="Move right -> wait -> move down -> wait -> move left",
            pos=(50, 100),
            font_size=12,
            fill_color=mcrfpy.Color(100, 100, 100)
        )
        self.ui.append(desc)

        # Animated frame
        self.chain_frame = mcrfpy.Frame(
            pos=(50, 130),
            size=(60, 60),
            fill_color=mcrfpy.Color(100, 150, 200),
            outline_color=mcrfpy.Color(150, 200, 255),
            outline=2
        )
        self.demo_frames.append(('chain', self.chain_frame, (50, 130)))
        self.ui.append(self.chain_frame)

    def _create_group_demo(self):
        """Create the parallel group demo area."""
        # Label
        label = mcrfpy.Caption(
            text="2. Parallel Group",
            pos=(350, 80),
            font_size=16,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(label)

        # Description
        desc = mcrfpy.Caption(
            text="Move + resize + change color simultaneously",
            pos=(350, 100),
            font_size=12,
            fill_color=mcrfpy.Color(100, 100, 100)
        )
        self.ui.append(desc)

        # Animated frame
        self.group_frame = mcrfpy.Frame(
            pos=(350, 130),
            size=(60, 60),
            fill_color=mcrfpy.Color(200, 100, 100),
            outline_color=mcrfpy.Color(255, 150, 150),
            outline=2
        )
        self.demo_frames.append(('group', self.group_frame, (350, 130)))
        self.ui.append(self.group_frame)

    def _create_callback_demo(self):
        """Create the callback demo area."""
        # Label
        label = mcrfpy.Caption(
            text="3. Callbacks",
            pos=(650, 80),
            font_size=16,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(label)

        # Description
        desc = mcrfpy.Caption(
            text="Each step triggers a callback",
            pos=(650, 100),
            font_size=12,
            fill_color=mcrfpy.Color(100, 100, 100)
        )
        self.ui.append(desc)

        # Animated frame
        self.callback_frame = mcrfpy.Frame(
            pos=(650, 130),
            size=(60, 60),
            fill_color=mcrfpy.Color(100, 200, 100),
            outline_color=mcrfpy.Color(150, 255, 150),
            outline=2
        )
        self.demo_frames.append(('callback', self.callback_frame, (650, 130)))
        self.ui.append(self.callback_frame)

        # Callback counter display
        self.callback_counter = mcrfpy.Caption(
            text="Callbacks: 0",
            pos=(720, 160),
            font_size=12,
            fill_color=mcrfpy.Color(100, 200, 100)
        )
        self.ui.append(self.callback_counter)

    def _create_loop_demo(self):
        """Create the looping demo area."""
        # Label
        label = mcrfpy.Caption(
            text="4. Looping",
            pos=(50, 280),
            font_size=16,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(label)

        # Description
        desc = mcrfpy.Caption(
            text="Continuous back-and-forth animation",
            pos=(50, 300),
            font_size=12,
            fill_color=mcrfpy.Color(100, 100, 100)
        )
        self.ui.append(desc)

        # Animated frame
        self.loop_frame = mcrfpy.Frame(
            pos=(50, 330),
            size=(40, 40),
            fill_color=mcrfpy.Color(200, 200, 100),
            outline_color=mcrfpy.Color(255, 255, 150),
            outline=2
        )
        self.demo_frames.append(('loop', self.loop_frame, (50, 330)))
        self.ui.append(self.loop_frame)

        self.loop_chain = None

    def _create_combined_demo(self):
        """Create the combined demo area."""
        # Label
        label = mcrfpy.Caption(
            text="5. Combined (Chain of Groups)",
            pos=(350, 280),
            font_size=16,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(label)

        # Description
        desc = mcrfpy.Caption(
            text="Multiple frames animating in complex patterns",
            pos=(350, 300),
            font_size=12,
            fill_color=mcrfpy.Color(100, 100, 100)
        )
        self.ui.append(desc)

        # Multiple animated frames
        self.combined_frames = []
        colors = [
            mcrfpy.Color(200, 100, 150),
            mcrfpy.Color(150, 100, 200),
            mcrfpy.Color(100, 150, 200),
        ]
        for i, color in enumerate(colors):
            frame = mcrfpy.Frame(
                pos=(350 + i * 70, 330),
                size=(50, 50),
                fill_color=color,
                outline=1
            )
            self.combined_frames.append(frame)
            self.demo_frames.append(('combined', frame, (350 + i * 70, 330)))
            self.ui.append(frame)

    def run_chain_demo(self):
        """Run the sequential chain demo."""
        self.status.text = "Running: Sequential Chain"

        chain = AnimationChain(
            (self.chain_frame, "x", 200, 0.5),
            delay(0.3),
            (self.chain_frame, "y", 200, 0.5),
            delay(0.3),
            (self.chain_frame, "x", 50, 0.5),
            callback=lambda: setattr(self.status, 'text', 'Chain complete!')
        )
        chain.start()
        self.active_animations.append(chain)

    def run_group_demo(self):
        """Run the parallel group demo."""
        self.status.text = "Running: Parallel Group"

        group = AnimationGroup(
            (self.group_frame, "x", 500, 1.0),
            (self.group_frame, "w", 100, 1.0),
            (self.group_frame, "h", 100, 1.0),
            callback=lambda: setattr(self.status, 'text', 'Group complete!')
        )
        group.start()
        self.active_animations.append(group)

    def run_callback_demo(self):
        """Run the callback demo."""
        self.status.text = "Running: Callbacks"
        self.callback_count = 0

        def increment_counter():
            self.callback_count += 1
            self.callback_counter.text = f"Callbacks: {self.callback_count}"

        chain = AnimationChain(
            callback(increment_counter),
            (self.callback_frame, "x", 750, 0.3),
            callback(increment_counter),
            delay(0.2),
            callback(increment_counter),
            (self.callback_frame, "y", 200, 0.3),
            callback(increment_counter),
            (self.callback_frame, "x", 650, 0.3),
            callback(increment_counter),
            callback=lambda: setattr(self.status, 'text', f'Callback demo complete! ({self.callback_count} callbacks)')
        )
        chain.start()
        self.active_animations.append(chain)

    def run_loop_demo(self):
        """Run the looping demo."""
        self.status.text = "Running: Looping (press R to stop)"

        # Stop any existing loop
        if self.loop_chain:
            self.loop_chain.stop()

        self.loop_chain = AnimationChain(
            (self.loop_frame, "x", 250, 1.0),
            (self.loop_frame, "x", 50, 1.0),
            loop=True
        )
        self.loop_chain.start()
        self.active_animations.append(self.loop_chain)

    def run_combined_demo(self):
        """Run the combined demo with chain of groups."""
        self.status.text = "Running: Combined"

        # First, all frames slide down together
        # Then, each one bounces back up sequentially
        frame1, frame2, frame3 = self.combined_frames

        chain = AnimationChain(
            # Phase 1: All move down together (as a group effect via separate chains)
            (frame1, "y", 450, 0.5),
            delay(0.1),
            (frame2, "y", 450, 0.5),
            delay(0.1),
            (frame3, "y", 450, 0.5),
            delay(0.5),
            # Phase 2: Spread out horizontally
            (frame1, "x", 320, 0.3),
            (frame3, "x", 520, 0.3),
            delay(0.5),
            # Phase 3: All return home
            (frame1, "x", 350, 0.3),
            (frame1, "y", 330, 0.3),
            delay(0.1),
            (frame2, "y", 330, 0.3),
            delay(0.1),
            (frame3, "x", 490, 0.3),
            (frame3, "y", 330, 0.3),
            callback=lambda: setattr(self.status, 'text', 'Combined demo complete!')
        )
        chain.start()
        self.active_animations.append(chain)

    def reset_all(self):
        """Reset all animations to initial state."""
        # Stop all active animations
        for anim in self.active_animations:
            if hasattr(anim, 'stop'):
                anim.stop()
        self.active_animations.clear()

        if self.loop_chain:
            self.loop_chain.stop()
            self.loop_chain = None

        # Reset positions
        for name, frame, (orig_x, orig_y) in self.demo_frames:
            frame.x = orig_x
            frame.y = orig_y
            if name == 'group':
                frame.w = 60
                frame.h = 60

        # Reset callback counter
        self.callback_count = 0
        self.callback_counter.text = "Callbacks: 0"

        self.status.text = "All animations reset"

    def on_key(self, key, state):
        """Handle keyboard input."""
        if state != "start":
            return

        if key == "Escape":
            sys.exit(0)
        elif key == "Num1":
            self.run_chain_demo()
        elif key == "Num2":
            self.run_group_demo()
        elif key == "Num3":
            self.run_callback_demo()
        elif key == "Num4":
            self.run_loop_demo()
        elif key == "Num5":
            self.run_combined_demo()
        elif key == "R":
            self.reset_all()

    def activate(self):
        """Activate the demo scene."""
        self.scene.on_key = self.on_key
        mcrfpy.current_scene = self.scene


def main():
    """Run the animation demo."""
    demo = AnimationDemo()
    demo.activate()

    # Headless mode: capture screenshot and exit
    try:
        if mcrfpy.headless_mode():
            from mcrfpy import automation
            # Run a quick demo then screenshot
            demo.run_chain_demo()
            mcrfpy.Timer("screenshot", lambda rt: (
                automation.screenshot("screenshots/features/animation_chain_demo.png"),
                sys.exit(0)
            ), 500)
    except AttributeError:
        pass


if __name__ == "__main__":
    main()
