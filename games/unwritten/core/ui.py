"""UNWRITTEN - the widget kit. Owner: Agent A.

Panel, Label, MenuList, Bar, DialogueBox, Toast, TitleBanner. Every widget
takes a parent UICollection (scene.children or frame.children) and absolute
pixel positions, and follows the palette exactly. See ARCHITECTURE section 3.
"""
import mcrfpy
from core import palette
from core import assets
from core import tween


# ---------------------------------------------------------------- text wrapping
def wrap_lines(meas, text, max_px, font_size):
    """Word-wrap `text` to fit within max_px, measuring with the hidden Caption
    `meas`. Honors any explicit newlines already in the text. Returns a list of
    line strings."""
    meas.font_size = font_size
    out = []
    for para in text.split("\n"):
        words = para.split(" ")
        cur = ""
        for w in words:
            trial = w if not cur else cur + " " + w
            meas.text = trial
            if meas.size.x <= max_px or not cur:
                cur = trial
            else:
                out.append(cur)
                cur = w
        out.append(cur)
    return out


# ------------------------------------------------------------------------ Panel
class Panel:
    """A Frame with PANEL fill and a 2px outline. .frame is the Frame,
    .children is its child collection."""

    def __init__(self, parent, pos, size, fill=None, outline_color=None,
                 outline=2, z_index=None):
        self._parent = parent
        self.frame = mcrfpy.Frame(
            pos=(pos[0], pos[1]), size=(size[0], size[1]),
            fill_color=palette.to_color(fill) if fill is not None else palette.PANEL,
            outline=outline,
            outline_color=palette.to_color(outline_color) if outline_color is not None
            else palette.OUTLINE)
        if z_index is not None:
            self.frame.z_index = z_index
        parent.append(self.frame)
        self.children = self.frame.children

    def destroy(self):
        try:
            self._parent.remove(self.frame)
        except Exception:
            pass


# ------------------------------------------------------------------------ Label
def Label(parent, text, pos, color=None, size=palette.BODY_SIZE, center=False,
          outline=0, z_index=None):
    """Caption factory with palette defaults. If center=True, pos is treated as
    the center point."""
    cap = mcrfpy.Caption(pos=(pos[0], pos[1]), text=str(text), font_size=size,
                         fill_color=palette.to_color(color) if color is not None
                         else palette.PARCH)
    if outline:
        cap.outline = outline
        cap.outline_color = palette.INK
    if z_index is not None:
        cap.z_index = z_index
    parent.append(cap)
    if center:
        cap.x = pos[0] - cap.size.x / 2
        cap.y = pos[1] - cap.size.y / 2
    return cap


# --------------------------------------------------------------------- MenuList
class MenuList:
    """Vertical keyboard menu. items = list of (label, value, enabled) or
    (label, value, enabled, lock_reason). Gold '>' cursor; W/S or Up/Down move;
    Enter/Space pick an ENABLED row; Esc cancels. Disabled rows render DIM with
    their lock reason. Push .handle onto an InputStack (or wire it yourself)."""

    ROW_H = 30

    def __init__(self, parent, pos, width, items, on_pick=None, on_cancel=None,
                 title=None, size=palette.CHOICE_SIZE):
        self._parent = parent
        self.items = [self._norm(i) for i in items]
        self.on_pick = on_pick
        self.on_cancel = on_cancel
        self.index = self._first_enabled()

        title_h = 30 if title else 8
        h = title_h + self.ROW_H * len(self.items) + 8
        self.panel = Panel(parent, pos, (width, h),
                           outline_color=palette.GOLD)
        self._x = pos[0]
        self._y = pos[1]
        self._top = title_h
        self._size = size

        if title:
            Label(self.panel.children, title, (14, 7),
                  color=palette.GOLD, size=palette.NAME_SIZE)

        self.cursor = Label(self.panel.children, ">", (10, self._top),
                            color=palette.GOLD, size=size)
        self.rows = []
        for i, (label, value, enabled, reason) in enumerate(self.items):
            txt = label
            if not enabled and reason:
                txt = "%s  (%s)" % (label, reason)
            row = Label(self.panel.children, txt, (30, self._top + i * self.ROW_H),
                        color=palette.PARCH if enabled else palette.DIM, size=size)
            self.rows.append(row)
        self._place_cursor()

    def _norm(self, item):
        label = item[0]
        value = item[1] if len(item) > 1 else item[0]
        enabled = item[2] if len(item) > 2 else True
        reason = item[3] if len(item) > 3 else ""
        return (label, value, bool(enabled), reason)

    def _first_enabled(self):
        for i, it in enumerate(self.items):
            if it[2]:
                return i
        return 0

    def _place_cursor(self):
        self.cursor.y = self._top + self.index * self.ROW_H

    def move(self, delta):
        n = len(self.items)
        self.index = (self.index + delta) % n
        self._place_cursor()

    def handle(self, key, state):
        if state != mcrfpy.InputState.PRESSED:
            return False
        K = mcrfpy.Key
        if key in (K.W, K.UP):
            self.move(-1)
            return True
        if key in (K.S, K.DOWN):
            self.move(1)
            return True
        if key in (K.ENTER, K.SPACE):
            label, value, enabled, reason = self.items[self.index]
            if enabled:
                if self.on_pick:
                    self.on_pick(value)
            else:
                tween.shake(self.cursor, mag=5, dur=0.2)
            return True
        if key == K.ESCAPE:
            if self.on_cancel:
                self.on_cancel()
            return True
        return False

    def destroy(self):
        self.panel.destroy()


# -------------------------------------------------------------------------- Bar
class Bar:
    """Stat bar: PANEL background + colored fill + optional "cur/max" caption.
    .set(cur, max) updates fill width and text."""

    def __init__(self, parent, pos, size, color, cur=1, maxv=1,
                 show_text=True):
        self._parent = parent
        self.w = size[0]
        self.h = size[1]
        self.bg = mcrfpy.Frame(pos=(pos[0], pos[1]), size=(self.w, self.h),
                               fill_color=palette.INSET, outline=2,
                               outline_color=palette.OUTLINE)
        parent.append(self.bg)
        self._fill_w = self.w - 4
        self.fill = mcrfpy.Frame(pos=(2, 2), size=(self._fill_w, self.h - 4),
                                 fill_color=palette.to_color(color))
        self.bg.children.append(self.fill)
        self.cap = None
        if show_text:
            self.cap = mcrfpy.Caption(pos=(0, 0), text="", font_size=palette.SMALL_SIZE,
                                      fill_color=palette.PARCH)
            self.cap.outline = 1
            self.cap.outline_color = palette.INK
            self.bg.children.append(self.cap)
        self.set(cur, maxv)

    def set(self, cur, maxv):
        frac = 0.0 if maxv <= 0 else max(0.0, min(1.0, float(cur) / float(maxv)))
        self.fill.w = max(0, self._fill_w * frac)
        if self.cap is not None:
            self.cap.text = "%d/%d" % (int(cur), int(maxv))
            self.cap.x = (self.w - self.cap.size.x) / 2
            self.cap.y = (self.h - self.cap.size.y) / 2

    def destroy(self):
        try:
            self._parent.remove(self.bg)
        except Exception:
            pass


# ------------------------------------------------------------------------ Toast
class Toast:
    """Top-right slide-in note that auto-dismisses after 2.2s. Stacks
    downward as multiple toasts appear."""

    _live = []       # currently visible toasts, for stacking
    _seq = [0]

    W = 268
    H = 44
    MARGIN = 16

    def __init__(self, parent, text, color=None):
        self._parent = parent
        Toast._seq[0] += 1
        self._id = Toast._seq[0]
        slot = len(Toast._live)
        y = self.MARGIN + slot * (self.H + 8)
        final_x = 1024 - self.W - self.MARGIN
        self.frame = mcrfpy.Frame(pos=(final_x + 26, y), size=(self.W, self.H),
                                  fill_color=palette.PANEL, outline=2,
                                  outline_color=palette.GOLD)
        self.frame.z_index = 6000
        parent.append(self.frame)
        Label(self.frame.children, text, (self.W / 2, self.H / 2),
              color=palette.to_color(color) if color is not None else palette.PARCH,
              size=palette.SMALL_SIZE, center=True)
        Toast._live.append(self)
        self.frame.animate("x", final_x, 0.28, mcrfpy.Easing.EASE_OUT)

        self._timer = mcrfpy.Timer("toast_%d" % self._id, self._dismiss, 2200)

    def _dismiss(self, timer, runtime):
        timer.stop()
        self.frame.animate("x", 1024 + 10, 0.28, mcrfpy.Easing.EASE_IN,
                           callback=self._remove)

    def _remove(self, *_a):
        try:
            self._parent.remove(self.frame)
        except Exception:
            pass
        if self in Toast._live:
            Toast._live.remove(self)

    def destroy(self):
        try:
            self._timer.stop()
        except Exception:
            pass
        self._remove()


# ------------------------------------------------------------------ TitleBanner
class TitleBanner:
    """Area-entry banner: big centered caption that fades in, holds, fades out
    (1.8s total) then removes itself."""

    def __init__(self, parent, text, cx=512, cy=120, size=palette.BANNER_SIZE,
                 color=None, total=1.8):
        self._parent = parent
        self.cap = Label(parent, text, (cx, cy),
                         color=palette.to_color(color) if color is not None
                         else palette.GOLD,
                         size=size, center=True, outline=2, z_index=6500)
        self.cap.opacity = 0.0
        fade = total * 0.25
        hold = total - 2 * fade
        self.cap.animate("opacity", 1.0, fade, mcrfpy.Easing.EASE_OUT)
        self._timer = mcrfpy.Timer("banner_%d" % id(self), self._out,
                                   int((fade + hold) * 1000))

    def _out(self, timer, runtime):
        timer.stop()
        self.cap.animate("opacity", 0.0, 0.45, mcrfpy.Easing.EASE_IN,
                         callback=self._remove)

    def _remove(self, *_a):
        try:
            self._parent.remove(self.cap)
        except Exception:
            pass

    def destroy(self):
        try:
            self._timer.stop()
        except Exception:
            pass
        self._remove()


# ------------------------------------------------------------------ DialogueBox
class DialogueBox:
    """The flagship. Bottom box 940x190 at (42, 556): portrait chip (sprite
    scale 5.0 inside a 96px inner frame), gold name plate on the rim, typewriter
    body at 45 chars/sec, blinking down-indicator when waiting, choice mode with
    gold '>' cursor and DIM-but-visible disabled choices.

    Content-agnostic: show_node(speaker, text, choices=None, on_advance=,
    on_choice=). `choices` is a list of (label, enabled) tuples. This lets the
    dialogue runner AND battle Talk menus reuse the same widget.
    """

    BOX_X, BOX_Y = 42, 556
    BOX_W, BOX_H = 940, 190
    CPS = 45.0            # typewriter characters per second

    # portrait chip
    CHIP_X, CHIP_Y, CHIP = 16, 47, 96
    # text columns (box-relative)
    BODY_X_PORTRAIT = 130
    BODY_X_NARRATOR = 64
    BODY_Y = 20
    WRAP_PORTRAIT = 772
    WRAP_NARRATOR = 800

    def __init__(self, parent):
        self._parent = parent

        # book-hum ring lives behind the box, on the top rim
        self._hum_center = (self.BOX_X + self.BOX_W / 2, self.BOX_Y)

        self.frame = mcrfpy.Frame(
            pos=(self.BOX_X, self.BOX_Y), size=(self.BOX_W, self.BOX_H),
            fill_color=palette.PANEL, outline=2, outline_color=palette.GOLD)
        self.frame.z_index = 3000
        parent.append(self.frame)
        kids = self.frame.children

        # portrait chip
        self.chip = mcrfpy.Frame(pos=(self.CHIP_X, self.CHIP_Y),
                                 size=(self.CHIP, self.CHIP),
                                 fill_color=palette.INSET, outline=2,
                                 outline_color=palette.GOLD)
        kids.append(self.chip)
        self.portrait = mcrfpy.Sprite(pos=(8, 8), texture=assets.TEX,
                                      sprite_index=0)
        self.portrait.scale = 5.0
        self.chip.children.append(self.portrait)

        # name plate (sits on the top rim of the box)
        self.plate = mcrfpy.Frame(pos=(self.BODY_X_PORTRAIT - 2, -16),
                                  size=(120, 30), fill_color=palette.GOLD,
                                  outline=2, outline_color=palette.INK)
        kids.append(self.plate)
        self.name_cap = mcrfpy.Caption(pos=(10, 5), text="", font_size=palette.NAME_SIZE,
                                       fill_color=palette.INK)
        self.plate.children.append(self.name_cap)

        # body caption (typewriter target)
        self.body = mcrfpy.Caption(pos=(self.BODY_X_PORTRAIT, self.BODY_Y),
                                   text="", font_size=palette.BODY_SIZE,
                                   fill_color=palette.PARCH)
        kids.append(self.body)

        # hidden measuring caption (never shown)
        self._meas = mcrfpy.Caption(pos=(0, 0), text="", font_size=palette.BODY_SIZE,
                                    fill_color=palette.PARCH)
        self._meas.visible = False
        kids.append(self._meas)

        # down indicator
        self.indicator = mcrfpy.Caption(pos=(self.BOX_W - 40, self.BOX_H - 34),
                                        text="v", font_size=22,
                                        fill_color=palette.GOLD)
        self.indicator.visible = False
        kids.append(self.indicator)

        # choice captions (rebuilt each choice node)
        self.choice_caps = []
        self.choice_cursor = mcrfpy.Caption(pos=(0, 0), text=">",
                                            font_size=palette.CHOICE_SIZE,
                                            fill_color=palette.GOLD)
        self.choice_cursor.visible = False
        kids.append(self.choice_cursor)

        # state
        self._full = ""
        self._typing = False
        self._t0 = None
        self._on_advance = None
        self._on_choice = None
        self._choices = None          # list of (enabled, first_line_y)
        self._sel = 0

        # entrance: slide up + fade in
        self.frame.opacity = 0.0
        self.frame.y = self.BOX_Y + 12
        self.frame.animate("y", self.BOX_Y, 0.22, mcrfpy.Easing.EASE_OUT)
        self.frame.animate("opacity", 1.0, 0.22, mcrfpy.Easing.EASE_OUT)

        self._timer = mcrfpy.Timer("dlg_type", self._tick, 16)

    # ------------------------------------------------------------------ display
    def show_node(self, speaker, text, choices=None, on_advance=None,
                  on_choice=None):
        self._on_advance = on_advance
        self._on_choice = on_choice
        self._clear_choices()
        self.indicator.visible = False

        is_narrator = (speaker == "NARRATOR" or speaker is None or
                       assets.PORTRAITS.get(speaker) is None)

        if is_narrator:
            self.chip.visible = False
            self.portrait.visible = False
            self.plate.visible = False
            self.name_cap.visible = False
            self.body.x = self.BODY_X_NARRATOR
            self.body.fill_color = palette.DIM
            wrap = self.WRAP_NARRATOR
        else:
            self.chip.visible = True
            self.portrait.visible = True
            self.portrait.sprite_index = assets.portrait_index(speaker)
            self.plate.visible = True
            self.name_cap.visible = True
            self.name_cap.text = speaker
            self.plate.w = self.name_cap.size.x + 22
            self.body.x = self.BODY_X_PORTRAIT
            self.body.fill_color = palette.PARCH
            wrap = self.WRAP_PORTRAIT

        self.body.y = self.BODY_Y
        lines = wrap_lines(self._meas, text, wrap, palette.BODY_SIZE) if text else [""]
        self._full = "\n".join(lines)
        self._raw_choices = choices

        if self._full.strip() == "":
            # empty text node: reveal instantly, go straight to choices/advance
            self.body.text = ""
            self._typing = False
            self._on_reveal_done()
        else:
            self.body.text = ""
            self._typing = True
            self._t0 = None

    def _tick(self, timer, runtime):
        if not self._typing:
            return
        if self._t0 is None:
            self._t0 = runtime
        elapsed = runtime - self._t0
        n = int(elapsed / 1000.0 * self.CPS)
        if n >= len(self._full):
            self.body.text = self._full
            self._typing = False
            self._on_reveal_done()
        else:
            self.body.text = self._full[:n]

    def _skip(self):
        self.body.text = self._full
        self._typing = False
        self._on_reveal_done()

    def _on_reveal_done(self):
        if self._raw_choices:
            self._build_choices(self._raw_choices)
        else:
            self.indicator.visible = True
            self._blink_indicator()

    def _blink_indicator(self):
        self.indicator.opacity = 1.0
        self.indicator.animate("opacity", 0.15, 0.55, mcrfpy.Easing.EASE_IN_OUT,
                               loop=True)

    # ------------------------------------------------------------------ choices
    def _clear_choices(self):
        for c in self.choice_caps:
            try:
                self.frame.children.remove(c)
            except Exception:
                pass
        self.choice_caps = []
        self._choices = None
        self.choice_cursor.visible = False

    def _build_choices(self, choices):
        # choices: list of (label, enabled)
        body_bottom = self.body.y + self.body.size.y
        y = body_bottom + 12
        wrap = (self.WRAP_PORTRAIT if self.body.x == self.BODY_X_PORTRAIT
                else self.WRAP_NARRATOR) - 24
        x = self.body.x
        self._choices = []
        for label, enabled in choices:
            lines = wrap_lines(self._meas, label, wrap, palette.CHOICE_SIZE)
            cap = mcrfpy.Caption(pos=(x + 22, y), text="\n".join(lines),
                                 font_size=palette.CHOICE_SIZE,
                                 fill_color=palette.PARCH if enabled else palette.DIM)
            self.frame.children.append(cap)
            self.choice_caps.append(cap)
            self._choices.append([bool(enabled), y])
            y += cap.size.y + 8
        # select first enabled
        self._sel = 0
        for i, (en, _yy) in enumerate(self._choices):
            if en:
                self._sel = i
                break
        self._place_choice_cursor()
        self.choice_cursor.visible = True

    def _place_choice_cursor(self):
        if not self._choices:
            return
        _en, yy = self._choices[self._sel]
        self.choice_cursor.x = self.body.x
        self.choice_cursor.y = yy
        self.choice_cursor.fill_color = palette.GOLD

    def _move_choice(self, delta):
        n = len(self._choices)
        self._sel = (self._sel + delta) % n
        self._place_choice_cursor()

    # -------------------------------------------------------------------- input
    def handle(self, key, state):
        if state != mcrfpy.InputState.PRESSED:
            return False
        K = mcrfpy.Key
        # typing: any advance key skips to full
        if self._typing:
            if key in (K.SPACE, K.ENTER):
                self._skip()
            return True
        # choice mode
        if self._choices:
            if key in (K.W, K.UP):
                self._move_choice(-1)
                return True
            if key in (K.S, K.DOWN):
                self._move_choice(1)
                return True
            if key in (K.ENTER, K.SPACE):
                enabled, _yy = self._choices[self._sel]
                if enabled:
                    idx = self._sel
                    if self._on_choice:
                        self._on_choice(idx)
                else:
                    tween.shake(self.choice_cursor, mag=5, dur=0.2)
                return True
            return True
        # text node waiting to advance
        if key in (K.SPACE, K.ENTER):
            if self._on_advance:
                self._on_advance()
            return True
        return True

    # ---------------------------------------------------------------- book hum
    def hum(self):
        tween.gold_ring(self._parent, self._hum_center, max_r=64, dur=0.5)

    # ----------------------------------------------------------------- teardown
    def destroy(self):
        try:
            self._timer.stop()
        except Exception:
            pass
        try:
            self._parent.remove(self.frame)
        except Exception:
            pass
