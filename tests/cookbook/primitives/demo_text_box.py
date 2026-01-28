#!/usr/bin/env python3
"""Text Box Widget Demo - Word-wrapped text with typewriter effect

Interactive controls:
    1: Show typewriter text
    2: Show instant text
    3: Skip animation
    4: Clear text
    D: Toggle dialogue mode
    ESC: Exit demo
"""
import mcrfpy
import sys

# Add parent to path for imports
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from lib.text_box import TextBox, DialogueBox


class TextBoxDemo:
    def __init__(self):
        self.scene = mcrfpy.Scene("text_box_demo")
        self.ui = self.scene.children
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
            text="Text Box Widget Demo",
            pos=(512, 30),
            font_size=28,
            fill_color=mcrfpy.Color(255, 255, 255)
        )
        title.outline = 2
        title.outline_color = mcrfpy.Color(0, 0, 0)
        self.ui.append(title)

        # Section 1: Basic text box with typewriter
        section1_label = mcrfpy.Caption(
            text="Typewriter Effect (press 1 to play)",
            pos=(50, 80),
            font_size=16,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(section1_label)

        self.typewriter_box = TextBox(
            pos=(50, 110),
            size=(400, 120),
            text="",
            chars_per_second=40
        )
        self.ui.append(self.typewriter_box.frame)

        self.sample_text = (
            "Welcome to McRogueFace! This is a demonstration of the "
            "typewriter effect. Each character appears one at a time, "
            "creating a classic RPG dialogue feel. You can adjust the "
            "speed by changing the chars_per_second parameter."
        )

        # Completion indicator
        self.completion_label = mcrfpy.Caption(
            text="Status: Ready",
            pos=(50, 240),
            font_size=12,
            fill_color=mcrfpy.Color(100, 100, 100)
        )
        self.ui.append(self.completion_label)

        # Section 2: Instant text
        section2_label = mcrfpy.Caption(
            text="Instant Text (press 2 to change)",
            pos=(500, 80),
            font_size=16,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(section2_label)

        self.instant_box = TextBox(
            pos=(500, 110),
            size=(450, 120),
            text="This text appeared instantly. Press 2 to change it to different content.",
            chars_per_second=0  # Instant display
        )
        self.ui.append(self.instant_box.frame)

        # Section 3: Dialogue box with speaker
        section3_label = mcrfpy.Caption(
            text="Dialogue Box (press D to cycle speakers)",
            pos=(50, 290),
            font_size=16,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(section3_label)

        self.dialogue_box = DialogueBox(
            pos=(50, 320),
            size=(600, 150),
            speaker="Elder Sage",
            text="Greetings, adventurer. I have been expecting you. The ancient prophecy speaks of one who would come to restore balance to our world.",
            chars_per_second=35
        )
        self.ui.append(self.dialogue_box.frame)

        self.dialogue_index = 0
        self.dialogues = [
            ("Elder Sage", "Greetings, adventurer. I have been expecting you. The ancient prophecy speaks of one who would come to restore balance to our world."),
            ("Hero", "I'm not sure I'm the right person for this task. What exactly must I do?"),
            ("Elder Sage", "You must journey to the Forgotten Temple and retrieve the Crystal of Dawn. Only its light can dispel the darkness that threatens our land."),
            ("Mysterious Voice", "Beware... the path is fraught with danger. Many have tried and failed before you..."),
            ("Hero", "I accept this quest. Point me to the temple, and I shall not rest until the crystal is recovered!"),
        ]

        # Section 4: Different styles
        section4_label = mcrfpy.Caption(
            text="Custom Styles",
            pos=(50, 500),
            font_size=16,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(section4_label)

        # Dark theme
        dark_box = TextBox(
            pos=(50, 530),
            size=(280, 100),
            text="Dark theme with light text. Good for mysterious or ominous messages.",
            chars_per_second=0,
            bg_color=mcrfpy.Color(10, 10, 15),
            text_color=mcrfpy.Color(180, 180, 200),
            outline_color=mcrfpy.Color(60, 60, 80)
        )
        self.ui.append(dark_box.frame)

        # Warning theme
        warning_box = TextBox(
            pos=(350, 530),
            size=(280, 100),
            text="Warning theme! Use for important alerts or danger notifications.",
            chars_per_second=0,
            bg_color=mcrfpy.Color(80, 40, 20),
            text_color=mcrfpy.Color(255, 200, 100),
            outline_color=mcrfpy.Color(200, 100, 50)
        )
        self.ui.append(warning_box.frame)

        # System theme
        system_box = TextBox(
            pos=(650, 530),
            size=(280, 100),
            text="[SYSTEM] Connection established. Loading game data...",
            chars_per_second=0,
            bg_color=mcrfpy.Color(20, 40, 30),
            text_color=mcrfpy.Color(100, 255, 150),
            outline_color=mcrfpy.Color(50, 150, 80)
        )
        self.ui.append(system_box.frame)

        # Instructions
        instr = mcrfpy.Caption(
            text="1: Play typewriter | 2: Change instant text | 3: Skip | 4: Clear | D: Next dialogue | ESC: Exit",
            pos=(50, 730),
            font_size=14,
            fill_color=mcrfpy.Color(120, 120, 120)
        )
        self.ui.append(instr)

    def on_typewriter_complete(self):
        """Called when typewriter animation finishes."""
        self.completion_label.text = "Status: Animation complete!"
        self.completion_label.fill_color = mcrfpy.Color(100, 200, 100)

    def on_key(self, key, state):
        """Handle keyboard input."""
        if state != "start":
            return

        if key == "Escape":
            sys.exit(0)
        elif key == "Num1":
            # Start typewriter animation
            self.typewriter_box.on_complete = self.on_typewriter_complete
            self.typewriter_box.set_text(self.sample_text, animate=True)
            self.completion_label.text = "Status: Playing..."
            self.completion_label.fill_color = mcrfpy.Color(200, 200, 100)
        elif key == "Num2":
            # Change instant text
            texts = [
                "This text appeared instantly. Press 2 to change it to different content.",
                "Here's some different content! Text boxes can hold any message you want.",
                "The quick brown fox jumps over the lazy dog. Perfect for testing fonts!",
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Classic placeholder text.",
            ]
            import random
            self.instant_box.set_text(random.choice(texts), animate=False)
        elif key == "Num3":
            # Skip animation
            self.typewriter_box.skip_animation()
            self.completion_label.text = "Status: Skipped"
            self.completion_label.fill_color = mcrfpy.Color(150, 150, 150)
        elif key == "Num4":
            # Clear text
            self.typewriter_box.clear()
            self.completion_label.text = "Status: Cleared"
            self.completion_label.fill_color = mcrfpy.Color(150, 150, 150)
        elif key == "D":
            # Cycle dialogue
            self.dialogue_index = (self.dialogue_index + 1) % len(self.dialogues)
            speaker, text = self.dialogues[self.dialogue_index]
            self.dialogue_box.set_dialogue(speaker, text, animate=True)

    def activate(self):
        """Activate the demo scene."""
        self.scene.on_key = self.on_key
        mcrfpy.current_scene = self.scene


def main():
    """Run the text box demo."""
    demo = TextBoxDemo()
    demo.activate()

    # Headless mode: capture screenshot and exit
    try:
        if mcrfpy.headless_mode():
            from mcrfpy import automation
            # Trigger typewriter then screenshot
            demo.typewriter_box.set_text(demo.sample_text[:50], animate=False)
            mcrfpy.Timer("screenshot", lambda rt: (
                automation.screenshot("screenshots/primitives/text_box_demo.png"),
                sys.exit(0)
            ), 100)
    except AttributeError:
        pass


if __name__ == "__main__":
    main()
