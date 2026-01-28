#!/usr/bin/env python3
"""Dialogue System - NPC dialogue with choices and mood

Interactive controls:
    1-4: Select dialogue choice
    Enter: Confirm selection
    Space: Advance dialogue (skip typewriter)
    R: Restart conversation
    ESC: Exit demo

This demonstrates:
    - Portrait + text + choices pattern
    - State machine for NPC mood
    - Choice consequences
    - Dynamic UI updates
"""
import mcrfpy
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.text_box import DialogueBox
from lib.choice_list import ChoiceList


class NPC:
    """NPC with mood and dialogue state."""

    MOODS = {
        "neutral": mcrfpy.Color(150, 150, 150),
        "happy": mcrfpy.Color(100, 200, 100),
        "angry": mcrfpy.Color(200, 80, 80),
        "sad": mcrfpy.Color(80, 80, 200),
        "suspicious": mcrfpy.Color(200, 180, 80),
    }

    def __init__(self, name, initial_mood="neutral"):
        self.name = name
        self.mood = initial_mood
        self.trust = 50  # 0-100 scale
        self.dialogue_state = "greeting"

    @property
    def mood_color(self):
        return self.MOODS.get(self.mood, self.MOODS["neutral"])


class DialogueSystem:
    """Complete dialogue system with NPC interaction."""

    def __init__(self):
        self.scene = mcrfpy.Scene("dialogue_system")
        self.ui = self.scene.children

        # Create NPC
        self.npc = NPC("Elder Sage")

        # Dialogue tree
        self.dialogue_tree = self._create_dialogue_tree()

        self.setup()

    def _create_dialogue_tree(self):
        """Create the dialogue tree structure."""
        return {
            "greeting": {
                "text": "Greetings, traveler. I am the Elder Sage of this village. What brings you to these remote lands?",
                "choices": [
                    ("I seek wisdom and knowledge.", "wise_response"),
                    ("I'm looking for treasure!", "treasure_response"),
                    ("None of your business.", "rude_response"),
                    ("I'm lost. Can you help me?", "help_response"),
                ]
            },
            "wise_response": {
                "text": "Ah, a seeker of truth! That is admirable. Knowledge is the greatest treasure one can possess. Tell me, what specific wisdom do you seek?",
                "mood": "happy",
                "trust_change": 10,
                "choices": [
                    ("I want to learn about the ancient prophecy.", "prophecy"),
                    ("Teach me about magic.", "magic"),
                    ("I wish to know the history of this land.", "history"),
                ]
            },
            "treasure_response": {
                "text": "Treasure? Bah! Material wealth corrupts the soul. But... perhaps you could prove yourself worthy of learning where such things might be found.",
                "mood": "suspicious",
                "trust_change": -5,
                "choices": [
                    ("I apologize. I spoke hastily.", "apologize"),
                    ("I don't need your approval!", "defiant"),
                    ("What must I do to prove myself?", "prove_worthy"),
                ]
            },
            "rude_response": {
                "text": "How dare you speak to me with such disrespect! Leave my presence at once!",
                "mood": "angry",
                "trust_change": -30,
                "choices": [
                    ("I'm sorry, I didn't mean that.", "apologize_angry"),
                    ("Make me!", "defiant"),
                    ("*Leave quietly*", "leave"),
                ]
            },
            "help_response": {
                "text": "Lost? Poor soul. These mountains can be treacherous. I will help you find your way, but first, tell me where you wish to go.",
                "mood": "neutral",
                "trust_change": 5,
                "choices": [
                    ("To the nearest town.", "directions"),
                    ("Anywhere but here.", "sad_path"),
                    ("Actually, maybe I'll stay a while.", "stay"),
                ]
            },
            "prophecy": {
                "text": "The ancient prophecy speaks of a chosen one who will restore balance when darkness falls. Many believe that time is now approaching...",
                "mood": "neutral",
                "choices": [
                    ("Am I the chosen one?", "chosen"),
                    ("How can I help prevent this darkness?", "help_prevent"),
                    ("That sounds like nonsense.", "skeptic"),
                ]
            },
            "magic": {
                "text": "Magic is not learned from books alone. It flows from within, from understanding the natural world. Your journey has only begun.",
                "mood": "happy",
                "choices": [
                    ("Will you teach me?", "teach"),
                    ("I understand. Thank you.", "thanks"),
                ]
            },
            "history": {
                "text": "This land was once a great kingdom, until the Shadow Wars tore it asunder. Now only ruins remain of its former glory.",
                "mood": "sad",
                "choices": [
                    ("What caused the Shadow Wars?", "shadow_wars"),
                    ("Can the kingdom be restored?", "restore"),
                    ("Thank you for sharing.", "thanks"),
                ]
            },
            "apologize": {
                "text": "Hmm... perhaps I misjudged you. True wisdom includes recognizing one's mistakes. Let us start again.",
                "mood": "neutral",
                "trust_change": 5,
                "choices": [
                    ("Thank you for understanding.", "wise_response"),
                ]
            },
            "apologize_angry": {
                "text": "*sighs* Very well. I accept your apology. But mind your tongue in the future.",
                "mood": "neutral",
                "trust_change": -10,
                "choices": [
                    ("I will. Now, I seek wisdom.", "wise_response"),
                    ("Thank you, Elder.", "thanks"),
                ]
            },
            "defiant": {
                "text": "GUARDS! Remove this insolent fool from my sight!",
                "mood": "angry",
                "trust_change": -50,
                "choices": [
                    ("*Run away!*", "escape"),
                    ("*Fight the guards*", "fight"),
                ]
            },
            "prove_worthy": {
                "text": "There is a sacred trial in the mountains. Complete it, and I may reconsider my opinion of you.",
                "mood": "neutral",
                "trust_change": 5,
                "choices": [
                    ("I accept the challenge!", "accept_trial"),
                    ("What kind of trial?", "trial_info"),
                    ("Perhaps another time.", "decline"),
                ]
            },
            "thanks": {
                "text": "You are welcome, traveler. May your journey be blessed with wisdom and good fortune. Return if you need guidance.",
                "mood": "happy",
                "choices": [
                    ("Farewell, Elder.", "end_good"),
                    ("I have more questions.", "greeting"),
                ]
            },
            "end_good": {
                "text": "Farewell. May the ancient spirits watch over you.",
                "mood": "happy",
                "choices": [
                    ("*Restart conversation*", "greeting"),
                ]
            },
            "leave": {
                "text": "Perhaps it is for the best. Safe travels... if you can find your way.",
                "mood": "neutral",
                "choices": [
                    ("*Restart conversation*", "greeting"),
                ]
            },
            "escape": {
                "text": "*You flee into the wilderness, the guards' shouts fading behind you...*",
                "mood": "neutral",
                "choices": [
                    ("*Restart conversation*", "greeting"),
                ]
            },
            "fight": {
                "text": "*The guards overwhelm you. You wake up in a cell...*",
                "mood": "angry",
                "choices": [
                    ("*Restart conversation*", "greeting"),
                ]
            },
            # Default responses for missing states
            "chosen": {"text": "That remains to be seen. Only time will tell.", "mood": "neutral", "choices": [("I understand.", "thanks")]},
            "help_prevent": {"text": "Prepare yourself. Train hard. The darkness comes for us all.", "mood": "neutral", "choices": [("I will.", "thanks")]},
            "skeptic": {"text": "Believe what you will. But when darkness comes, remember my words.", "mood": "sad", "choices": [("Perhaps you're right.", "apologize")]},
            "teach": {"text": "In time, perhaps. First, prove your dedication.", "mood": "neutral", "choices": [("How?", "prove_worthy")]},
            "shadow_wars": {"text": "Ancient evils that should have remained buried. Let us speak no more of it.", "mood": "sad", "choices": [("I understand.", "thanks")]},
            "restore": {"text": "Perhaps... if the chosen one rises. Perhaps.", "mood": "neutral", "choices": [("I hope so.", "thanks")]},
            "directions": {"text": "Head east through the mountain pass. The town of Millbrook lies two days' journey.", "mood": "neutral", "choices": [("Thank you!", "thanks")]},
            "sad_path": {"text": "I sense great pain in you. Perhaps you should stay and heal.", "mood": "sad", "choices": [("You're right.", "stay")]},
            "stay": {"text": "You are welcome here. Rest, and we shall talk more.", "mood": "happy", "choices": [("Thank you, Elder.", "thanks")]},
            "accept_trial": {"text": "Brave soul! Seek the Cave of Trials to the north. Return victorious!", "mood": "happy", "choices": [("I will return!", "thanks")]},
            "trial_info": {"text": "It tests courage, wisdom, and heart. Few have succeeded.", "mood": "neutral", "choices": [("I'll try anyway!", "accept_trial"), ("Maybe not...", "decline")]},
            "decline": {"text": "Perhaps another time then. The offer stands.", "mood": "neutral", "choices": [("Thank you.", "thanks")]},
        }

    def setup(self):
        """Build the dialogue UI."""
        # Background
        bg = mcrfpy.Frame(
            pos=(0, 0),
            size=(1024, 768),
            fill_color=mcrfpy.Color(25, 25, 30)
        )
        self.ui.append(bg)

        # Scene background (simple village scene)
        scene_bg = mcrfpy.Frame(
            pos=(0, 0),
            size=(1024, 400),
            fill_color=mcrfpy.Color(40, 60, 40)
        )
        self.ui.append(scene_bg)

        # Ground
        ground = mcrfpy.Frame(
            pos=(0, 350),
            size=(1024, 50),
            fill_color=mcrfpy.Color(60, 45, 30)
        )
        self.ui.append(ground)

        # Simple building shapes
        for i in range(3):
            building = mcrfpy.Frame(
                pos=(100 + i * 300, 200 - i * 20),
                size=(200, 150 + i * 20),
                fill_color=mcrfpy.Color(70 + i * 10, 60 + i * 5, 50),
                outline_color=mcrfpy.Color(40, 35, 30),
                outline=2
            )
            self.ui.append(building)

        # Portrait frame
        self.portrait_frame = mcrfpy.Frame(
            pos=(50, 420),
            size=(150, 180),
            fill_color=mcrfpy.Color(50, 50, 60),
            outline_color=mcrfpy.Color(100, 100, 120),
            outline=3
        )
        self.ui.append(self.portrait_frame)

        # NPC "face" (simple representation)
        face_bg = mcrfpy.Frame(
            pos=(15, 15),
            size=(120, 120),
            fill_color=mcrfpy.Color(200, 180, 160),
            outline=0
        )
        self.portrait_frame.children.append(face_bg)

        # Mood indicator (eyes/expression)
        self.mood_indicator = mcrfpy.Frame(
            pos=(35, 50),
            size=(80, 30),
            fill_color=self.npc.mood_color,
            outline=0
        )
        self.portrait_frame.children.append(self.mood_indicator)

        # Name label
        name_label = mcrfpy.Caption(
            text=self.npc.name,
            pos=(75, 150),
            font_size=14,
            fill_color=mcrfpy.Color(255, 255, 255)
        )
        self.portrait_frame.children.append(name_label)

        # Dialogue box
        self.dialogue_box = DialogueBox(
            pos=(220, 420),
            size=(550, 180),
            speaker=self.npc.name,
            text="",
            chars_per_second=40
        )
        self.ui.append(self.dialogue_box.frame)

        # Choice list
        self.choice_list = ChoiceList(
            pos=(220, 610),
            size=(550, 120),
            choices=["Loading..."],
            on_select=self.on_choice,
            item_height=28
        )
        self.ui.append(self.choice_list.frame)

        # Trust meter
        trust_label = mcrfpy.Caption(
            text="Trust:",
            pos=(820, 430),
            font_size=14,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(trust_label)

        self.trust_bar_bg = mcrfpy.Frame(
            pos=(820, 450),
            size=(150, 20),
            fill_color=mcrfpy.Color(40, 40, 50),
            outline_color=mcrfpy.Color(80, 80, 100),
            outline=1
        )
        self.ui.append(self.trust_bar_bg)

        self.trust_bar = mcrfpy.Frame(
            pos=(0, 0),
            size=(75, 20),  # 50% initial
            fill_color=mcrfpy.Color(100, 150, 100),
            outline=0
        )
        self.trust_bar_bg.children.append(self.trust_bar)

        self.trust_value = mcrfpy.Caption(
            text="50",
            pos=(895, 473),
            font_size=12,
            fill_color=mcrfpy.Color(200, 200, 200)
        )
        self.ui.append(self.trust_value)

        # Mood display
        mood_label = mcrfpy.Caption(
            text="Mood:",
            pos=(820, 500),
            font_size=14,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(mood_label)

        self.mood_display = mcrfpy.Caption(
            text="Neutral",
            pos=(870, 500),
            font_size=14,
            fill_color=self.npc.mood_color
        )
        self.ui.append(self.mood_display)

        # Instructions
        instr = mcrfpy.Caption(
            text="1-4: Select choice | Enter: Confirm | Space: Skip | R: Restart | ESC: Exit",
            pos=(50, 740),
            font_size=14,
            fill_color=mcrfpy.Color(100, 100, 100)
        )
        self.ui.append(instr)

        # Start dialogue
        self._load_dialogue_state("greeting")

    def _load_dialogue_state(self, state_name):
        """Load a dialogue state."""
        self.npc.dialogue_state = state_name

        if state_name not in self.dialogue_tree:
            state_name = "greeting"
            self.npc.dialogue_state = state_name

        state = self.dialogue_tree[state_name]

        # Apply mood change
        if "mood" in state:
            self.npc.mood = state["mood"]
            self._update_mood_display()

        # Apply trust change
        if "trust_change" in state:
            self.npc.trust = max(0, min(100, self.npc.trust + state["trust_change"]))
            self._update_trust_display()

        # Update dialogue
        self.dialogue_box.set_dialogue(self.npc.name, state["text"], animate=True)

        # Update choices
        choices = [choice[0] for choice in state.get("choices", [])]
        self._choice_targets = [choice[1] for choice in state.get("choices", [])]

        if choices:
            self.choice_list.choices = choices
        else:
            self.choice_list.choices = ["*Continue*"]
            self._choice_targets = ["greeting"]

    def _update_mood_display(self):
        """Update the mood indicators."""
        self.mood_indicator.fill_color = self.npc.mood_color
        self.mood_display.text = self.npc.mood.capitalize()
        self.mood_display.fill_color = self.npc.mood_color

    def _update_trust_display(self):
        """Update the trust bar."""
        bar_width = int((self.npc.trust / 100) * 150)
        self.trust_bar.w = bar_width
        self.trust_value.text = str(self.npc.trust)

        # Color based on trust level
        if self.npc.trust >= 70:
            self.trust_bar.fill_color = mcrfpy.Color(100, 200, 100)
        elif self.npc.trust >= 30:
            self.trust_bar.fill_color = mcrfpy.Color(200, 200, 100)
        else:
            self.trust_bar.fill_color = mcrfpy.Color(200, 100, 100)

    def on_choice(self, index, value):
        """Handle choice selection."""
        if index < len(self._choice_targets):
            next_state = self._choice_targets[index]
            self._load_dialogue_state(next_state)

    def on_key(self, key, state):
        """Handle keyboard input."""
        if state != "start":
            return

        if key == "Escape":
            sys.exit(0)
        elif key in ("Num1", "Num2", "Num3", "Num4"):
            idx = int(key[-1]) - 1
            if idx < len(self.choice_list.choices):
                self.choice_list.set_selected(idx)
                self.choice_list.confirm()
        elif key == "Up":
            self.choice_list.navigate(-1)
        elif key == "Down":
            self.choice_list.navigate(1)
        elif key == "Enter":
            self.choice_list.confirm()
        elif key == "Space":
            self.dialogue_box.skip_animation()
        elif key == "R":
            # Restart
            self.npc.mood = "neutral"
            self.npc.trust = 50
            self._update_mood_display()
            self._update_trust_display()
            self._load_dialogue_state("greeting")

    def activate(self):
        """Activate the dialogue scene."""
        self.scene.on_key = self.on_key
        mcrfpy.current_scene = self.scene


def main():
    """Run the dialogue system demo."""
    dialogue = DialogueSystem()
    dialogue.activate()

    # Headless mode: capture screenshot and exit
    try:
        if mcrfpy.headless_mode():
            from mcrfpy import automation
            mcrfpy.Timer("screenshot", lambda rt: (
                automation.screenshot("screenshots/apps/dialogue_system.png"),
                sys.exit(0)
            ), 200)
    except AttributeError:
        pass


if __name__ == "__main__":
    main()
