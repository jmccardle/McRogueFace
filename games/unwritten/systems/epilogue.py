"""UNWRITTEN - the epilogue: the Book read aloud. Owner: Agent C.

HOOKS["epilogue"]() renders data.epilogue.PAGES as full-screen INK pages with
centered PARCH text and a small GOLD ornament, one keypress per page, a soft
fade between them. The final card shows UNWRITTEN, then strikes it with a gold
line and stamps WRITTEN beneath. A last keypress returns to the title scene.

Page conditions use the dialogue req schema (None / ("flag",x) / ("flag_not",x)
/ ("points",n)); {light_name} is substituted from the moth_light_name_* flag
per data/epilogue.py's module docstring.
"""
import mcrfpy

from core import palette
from core import ui
from core import tween
from core.inputstack import InputStack
from systems import dialogue
from systems.state import GS

_LIGHT_NAME = {
    "moth_light_name_dark": "for the ones walking in the dark",
    "moth_light_name_lost": "for everything the vale lost waiting",
    "moth_light_name_small": "for suppers, and mending, and company",
}


def _light_name():
    for flag, phrase in _LIGHT_NAME.items():
        if GS.has(flag):
            return phrase
    return None


def _resolve(text):
    if "{light_name}" in text:
        name = _light_name()
        if name is None:
            raise KeyError("epilogue page needs {light_name} but no "
                           "moth_light_name_* flag is set")
        text = text.replace("{light_name}", name)
    return text


def _collect_pages():
    from data import epilogue as ep
    out = []
    for cond, text in ep.PAGES:
        if dialogue.req_met(cond):
            out.append(_resolve(text))
    return out


class _Epilogue:
    def __init__(self):
        self.scene = mcrfpy.Scene("epilogue")
        mcrfpy.current_scene = self.scene
        self.ch = self.scene.children
        self.ch.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768),
                                    fill_color=palette.INK))
        self.pages = _collect_pages()
        self.index = -1
        self.page_nodes = []
        self.final = False
        self.done = False
        self.stack = InputStack(self.scene)
        self.stack.push(self._on_key, "epilogue")

    # ----------------------------------------------------------------- flow
    def start(self):
        self._advance()

    def _on_key(self, key, state):
        if state != mcrfpy.InputState.PRESSED:
            return True
        if self.done:
            self._return_to_title()
            return True
        self._advance()
        return True

    def _advance(self):
        # fade current page out, then show next
        old = self.page_nodes
        self.page_nodes = []
        for n in old:
            n.animate("opacity", 0.0, 0.22, mcrfpy.Easing.EASE_IN,
                      callback=self._remove_cb(n))
        self.index += 1
        if self.index >= len(self.pages):
            self._final_card()
            return
        mcrfpy.Timer("epi_next", self._show_page, 240)

    def _remove_cb(self, node):
        def cb(*_a):
            try:
                self.ch.remove(node)
            except Exception:
                pass
        return cb

    def _show_page(self, timer=None, runtime=None):
        if timer is not None:
            timer.stop()
        text = self.pages[self.index]
        nodes = []

        # centered multi-line body
        body = mcrfpy.Caption(pos=(0, 0), text=text, font_size=palette.BODY_SIZE + 4,
                              fill_color=palette.PARCH)
        body.x = 512 - body.size.x / 2
        body.y = 384 - body.size.y / 2
        body.opacity = 0.0
        self.ch.append(body)
        nodes.append(body)

        # gold ornament: a thin rule with a diamond, above the text
        rule = mcrfpy.Frame(pos=(512 - 90, body.y - 34), size=(180, 2),
                            fill_color=palette.GOLD)
        rule.opacity = 0.0
        self.ch.append(rule)
        nodes.append(rule)
        diamond = mcrfpy.Caption(pos=(0, 0), text="*", font_size=palette.NAME_SIZE,
                                 fill_color=palette.GOLD)
        diamond.x = 512 - diamond.size.x / 2
        diamond.y = body.y - 44
        diamond.opacity = 0.0
        self.ch.append(diamond)
        nodes.append(diamond)

        # page count hint (DIM, small)
        hint = mcrfpy.Caption(pos=(0, 712), text="press any key",
                              font_size=palette.SMALL_SIZE, fill_color=palette.DIM)
        hint.x = 512 - hint.size.x / 2
        hint.opacity = 0.0
        self.ch.append(hint)
        nodes.append(hint)

        for n in nodes:
            n.animate("opacity", 1.0, 0.4, mcrfpy.Easing.EASE_OUT)
        self.page_nodes = nodes

    # ----------------------------------------------------------------- final
    def _final_card(self):
        self.final = True
        self.title = mcrfpy.Caption(pos=(0, 0), text="UNWRITTEN",
                                    font_size=palette.TITLE_SIZE,
                                    fill_color=palette.PARCH)
        self.title.x = 512 - self.title.size.x / 2
        self.title.y = 300
        self.title.opacity = 0.0
        self.title.outline = 2
        self.title.outline_color = palette.INK
        self.ch.append(self.title)
        self.title.animate("opacity", 1.0, 0.6, mcrfpy.Easing.EASE_OUT)
        mcrfpy.Timer("epi_stamp", self._stamp, 950)

    def _stamp(self, timer=None, runtime=None):
        if timer is not None:
            timer.stop()
        # gold strike across UNWRITTEN
        y = int(self.title.y + self.title.size.y / 2)
        strike = mcrfpy.Frame(pos=(int(self.title.x), y), size=(0, 5),
                              fill_color=palette.GOLD)
        strike.z_index = 10
        self.ch.append(strike)
        strike.animate("w", self.title.size.x, 0.28, mcrfpy.Easing.EASE_OUT,
                       callback=self._stamp_word)

    def _stamp_word(self, *_a):
        written = mcrfpy.Caption(pos=(0, 0), text="WRITTEN",
                                 font_size=palette.TITLE_SIZE,
                                 fill_color=palette.GOLD)
        written.x = 512 - written.size.x / 2
        written.y = 410
        written.opacity = 0.0
        written.outline = 2
        written.outline_color = palette.INK
        written.z_index = 20
        self.ch.append(written)
        # thunk: fast opacity pop + a single shake
        written.animate("opacity", 1.0, 0.12, mcrfpy.Easing.EASE_OUT)
        tween.shake(written, mag=8, dur=0.25)
        mcrfpy.Timer("epi_ready", self._ready, 700)

    def _ready(self, timer=None, runtime=None):
        if timer is not None:
            timer.stop()
        self.done = True

    def _return_to_title(self):
        self.stack.pop("epilogue")
        import main
        main.build_title()


# The live epilogue, if one is running (test seam: a scripted playthrough drives
# it by pressing keys on its scene and inspects .final/.done). None otherwise.
CURRENT = None


def start_epilogue():
    global CURRENT
    if not GS.has("nyx_joined"):
        GS.add_flag("nyx_missed")
    ep = _Epilogue()
    CURRENT = ep
    ep.start()
    return ep


def register_hooks():
    dialogue.HOOKS["epilogue"] = start_epilogue


register_hooks()
