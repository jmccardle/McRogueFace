"""Reusable UI widgets for Crypt of Sokoban.

SweetButton is a composite UI element: a frame with drop shadow,
icon, and caption that responds to click events.
"""

import mcrfpy
from cos import Resources


class SweetButton:
    """A styled button with icon, caption, and press animation.

    The button is a Frame containing a shadow layer and a main
    content layer with an icon sprite and text caption. Clicking
    animates the content layer to simulate a press effect.

    Args:
        pos: (x, y) screen position
        caption: button text
        click: callback(sweet_btn, event_args)
        icon: sprite index in button texture
        box_width, box_height: button dimensions
        shadow: whether to render drop shadow
    """

    def __init__(self, pos, caption, *, click=None,
                 font_size=24, font_color=(255, 255, 255),
                 font_outline_color=(0, 0, 0), font_outline_width=2,
                 shadow_offset=8, box_width=200, box_height=80,
                 shadow_color=(64, 64, 86), box_color=(96, 96, 160),
                 icon=4, icon_scale=1.75, shadow=True):
        res = Resources()
        x, y = pos
        self._click = click or (lambda btn, args: None)
        self.shadow_offset = shadow_offset

        # Outer frame (contains shadow + main button)
        self.base_frame = mcrfpy.Frame(
            pos=(x, y), size=(box_width + shadow_offset, box_height),
            fill_color=(0, 0, 0, 255),
        )
        self.base_frame.on_click = self._do_click

        # Drop shadow
        if shadow:
            self.base_frame.children.append(mcrfpy.Frame(
                pos=(0, 0), size=(box_width, box_height),
                fill_color=shadow_color,
            ))

        # Main button content
        self.main_button = mcrfpy.Frame(
            pos=(shadow_offset, shadow_offset),
            size=(box_width, box_height),
            fill_color=box_color,
        )
        self.base_frame.children.append(self.main_button)

        # Icon
        self.icon = mcrfpy.Sprite(
            x=0, y=3, texture=res.button_texture,
            sprite_index=icon, scale=icon_scale,
        )
        self.main_button.children.append(self.icon)

        # Caption
        self.caption = mcrfpy.Caption(
            text=caption, pos=(40, 3), font=res.font,
            fill_color=font_color,
        )
        self.caption.font_size = font_size
        self.caption.outline_color = font_outline_color
        self.caption.outline = font_outline_width
        self.main_button.children.append(self.caption)

    def _do_click(self, pos, button, action):
        """Handle click: animate press/release and invoke callback."""
        if action == mcrfpy.InputState.PRESSED:
            self.main_button.x = 0
            self.main_button.y = 0
        elif action == mcrfpy.InputState.RELEASED:
            self.main_button.x = self.shadow_offset
            self.main_button.y = self.shadow_offset

        result = self._click(self, (pos.x, pos.y, button, action))
        if result:  # callback returns True to instantly unpress
            self.main_button.x = self.shadow_offset
            self.main_button.y = self.shadow_offset

    def unpress(self):
        """Reset button to unpressed visual state."""
        self.main_button.x = self.shadow_offset
        self.main_button.y = self.shadow_offset

    @property
    def text(self):
        return self.caption.text

    @text.setter
    def text(self, value):
        self.caption.text = value

    @property
    def sprite_number(self):
        return self.icon.sprite_number

    @sprite_number.setter
    def sprite_number(self, value):
        self.icon.sprite_number = value
