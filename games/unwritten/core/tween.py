"""UNWRITTEN - motion helpers. Owner: Agent A.

Thin wrappers over obj.animate(...) so call sites read as intentions, not
easing bookkeeping. Nothing here teleports; every transition is a tween
(BIBLE section 6: Motion).
"""
import mcrfpy
from core import palette

_uid = [0]


def _next_id():
    _uid[0] += 1
    return _uid[0]


def fade_scene(scene, on_done=None, dur=0.25):
    """Cover the scene with an INK frame fading 0 -> 1 over dur, then call
    on_done (which typically activates/builds the next scene). Returns the
    cover frame so the caller can fade it back out on the new scene."""
    cover = mcrfpy.Frame(pos=(0, 0), size=(1024, 768),
                         fill_color=palette.C(palette.INK_T, 0))
    cover.z_index = 100000
    scene.children.append(cover)

    def done(*_a):
        if on_done:
            on_done()
    cover.animate("opacity", 1.0, dur, mcrfpy.Easing.EASE_IN_OUT, callback=done)
    return cover


def uncover(scene, cover, dur=0.25):
    """Fade an INK cover frame back out and remove it from the scene."""
    def done(*_a):
        try:
            scene.children.remove(cover)
        except Exception:
            pass
    cover.animate("opacity", 0.0, dur, mcrfpy.Easing.EASE_IN_OUT, callback=done)


def float_text(parent, text, pos, color, rise=42, dur=0.85, size=20):
    """Rising, fading caption. `parent` is a UICollection (scene.children or
    frame.children). Used for damage numbers, +1 Story Point, loot notes."""
    cap = mcrfpy.Caption(pos=(pos[0], pos[1]), text=str(text), font_size=size,
                         fill_color=palette.to_color(color))
    cap.outline = 1
    cap.outline_color = palette.INK
    cap.z_index = 5000
    parent.append(cap)
    cap.animate("y", pos[1] - rise, dur, mcrfpy.Easing.EASE_OUT)

    def done(*_a):
        try:
            parent.remove(cap)
        except Exception:
            pass
    cap.animate("opacity", 0.0, dur, mcrfpy.Easing.EASE_OUT, callback=done)
    return cap


def shake(drawable, mag=6, dur=0.3):
    """Small horizontal shake that returns to the original x."""
    ox = drawable.x
    seq = [ox + mag, ox - mag, ox + mag * 0.5, ox]
    step_dur = max(0.02, dur / len(seq))

    def go(i):
        if i >= len(seq):
            return
        drawable.animate("x", seq[i], step_dur,
                         callback=lambda *_a: go(i + 1))
    go(0)


def pulse(drawable, prop, hi, dur=1.0, loop=True, easing=None):
    """Animate a property toward hi (looping by default) for idle throbs."""
    drawable.animate(prop, hi, dur,
                     easing if easing is not None else mcrfpy.Easing.EASE_IN_OUT,
                     loop=loop)


def gold_ring(parent, center, max_r=70, dur=0.5):
    """A single gold circle that rings outward and fades. The Book hum."""
    circ = mcrfpy.Circle(radius=2, center=(center[0], center[1]),
                         fill_color=palette.C(palette.GOLD_T, 0),
                         outline=2, outline_color=palette.C(palette.GOLD_T, 200))
    circ.z_index = 4000
    parent.append(circ)
    circ.animate("radius", max_r, dur, mcrfpy.Easing.EASE_OUT)

    def done(*_a):
        try:
            parent.remove(circ)
        except Exception:
            pass
    circ.animate("opacity", 0.0, dur, mcrfpy.Easing.EASE_OUT, callback=done)
    return circ
