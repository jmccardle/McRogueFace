# McRogueFace Cookbook - Standard Widget Library
"""
Reusable UI widget patterns for game development.

Widgets:
    Button - Clickable button with hover/press states
    StatBar - Horizontal bar showing current/max value (HP, mana, XP)
    ChoiceList - Vertical list of selectable text options
    ScrollableList - Scrolling list with arbitrary item rendering
    TextBox - Word-wrapped text with typewriter effect
    DialogueBox - TextBox with speaker name display
    Modal - Overlay popup that blocks background input
    ConfirmModal - Pre-configured yes/no modal
    AlertModal - Pre-configured OK modal
    ToastManager - Auto-dismissing notification popups
    GridContainer - NxM clickable cells for inventory/slot systems

Utilities:
    AnimationChain - Sequential animation execution
    AnimationGroup - Parallel animation execution
    delay - Create a delay step for animation chains
    callback - Create a callback step for animation chains
    fade_in, fade_out - Opacity animations
    slide_in_from_* - Slide-in animations
    shake - Shake effect animation
"""

from .button import Button, create_button_row, create_button_column
from .stat_bar import StatBar, create_stat_bar_group
from .choice_list import ChoiceList, create_menu
from .text_box import TextBox, DialogueBox
from .scrollable_list import ScrollableList
from .modal import Modal, ConfirmModal, AlertModal
from .toast import Toast, ToastManager
from .grid_container import GridContainer
from .anim_utils import (
    AnimationChain, AnimationGroup, AnimationSequence,
    PropertyAnimation, DelayStep, CallbackStep,
    delay, callback,
    fade_in, fade_out,
    slide_in_from_left, slide_in_from_right,
    slide_in_from_top, slide_in_from_bottom,
    pulse, shake
)

__all__ = [
    # Widgets
    'Button',
    'create_button_row',
    'create_button_column',
    'StatBar',
    'create_stat_bar_group',
    'ChoiceList',
    'create_menu',
    'TextBox',
    'DialogueBox',
    'ScrollableList',
    'Modal',
    'ConfirmModal',
    'AlertModal',
    'Toast',
    'ToastManager',
    'GridContainer',
    # Animation utilities
    'AnimationChain',
    'AnimationGroup',
    'AnimationSequence',
    'PropertyAnimation',
    'DelayStep',
    'CallbackStep',
    'delay',
    'callback',
    'fade_in',
    'fade_out',
    'slide_in_from_left',
    'slide_in_from_right',
    'slide_in_from_top',
    'slide_in_from_bottom',
    'pulse',
    'shake',
]
