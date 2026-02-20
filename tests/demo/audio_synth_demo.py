"""McRogueFace Audio Synth Demo - SFXR Clone + Animalese Speech

Two-scene interactive demo showcasing the SoundBuffer procedural audio system:
- Scene 1 (SFXR): Full sfxr parameter editor with presets, waveform selection,
  24 synthesis parameters, DSP effect chain, and real-time playback
- Scene 2 (Animalese): Animal Crossing-style speech synthesis with formant
  generation, character personality presets, and text-to-speech playback

Controls:
  SFXR Scene: SPACE=play, R=randomize, M=mutate, 1-4=waveform, TAB=switch
  Animalese Scene: Type text, ENTER=speak, 1-5=personality, TAB=switch
  Both: ESC=quit
"""
import mcrfpy
import sys
import random

# ============================================================
# Constants
# ============================================================
W, H = 1024, 768

# Retro sfxr color palette
C_BG      = mcrfpy.Color(198, 186, 168)
C_PANEL   = mcrfpy.Color(178, 166, 148)
C_BTN     = mcrfpy.Color(158, 148, 135)
C_BTN_ON  = mcrfpy.Color(115, 168, 115)
C_BTN_ACC = mcrfpy.Color(168, 115, 115)
C_TEXT    = mcrfpy.Color(35, 30, 25)
C_LABEL   = mcrfpy.Color(55, 48, 40)
C_HEADER  = mcrfpy.Color(25, 20, 15)
C_SL_BG   = mcrfpy.Color(80, 72, 62)
C_SL_FILL = mcrfpy.Color(192, 152, 58)
C_VALUE   = mcrfpy.Color(68, 60, 50)
C_OUTLINE = mcrfpy.Color(95, 85, 72)
C_ACCENT  = mcrfpy.Color(200, 75, 55)
C_BG2     = mcrfpy.Color(85, 92, 110)
C_BG2_PNL = mcrfpy.Color(100, 108, 128)

# ============================================================
# Shared State
# ============================================================
class S:
    """Global mutable state."""
    wave_type = 0
    params = {
        'env_attack': 0.0, 'env_sustain': 0.3, 'env_punch': 0.0,
        'env_decay': 0.4,
        'base_freq': 0.3, 'freq_limit': 0.0, 'freq_ramp': 0.0,
        'freq_dramp': 0.0,
        'vib_strength': 0.0, 'vib_speed': 0.0,
        'arp_mod': 0.0, 'arp_speed': 0.0,
        'duty': 0.0, 'duty_ramp': 0.0,
        'repeat_speed': 0.0,
        'pha_offset': 0.0, 'pha_ramp': 0.0,
        'lpf_freq': 1.0, 'lpf_ramp': 0.0, 'lpf_resonance': 0.0,
        'hpf_freq': 0.0, 'hpf_ramp': 0.0,
    }
    volume = 80.0
    auto_play = True

    # Post-processing DSP
    fx_on = {
        'low_pass': False, 'high_pass': False, 'echo': False,
        'reverb': False, 'distortion': False, 'bit_crush': False,
    }

    # Animalese
    text = "HELLO WORLD"
    base_pitch = 180.0
    speech_rate = 12.0
    pitch_jitter = 2.0
    breathiness = 0.2

    # UI refs (populated during setup)
    sliders = {}
    wave_btns = []
    fx_btns = {}
    text_cap = None
    letter_cap = None
    speak_idx = 0
    speaking = False

    # Prevent GC of sound/timer objects
    sound = None
    anim_sound = None
    speak_timer = None

    # Scene refs
    sfxr_scene = None
    anim_scene = None

    # Animalese sliders
    anim_sliders = {}


# ============================================================
# UI Helpers
# ============================================================
# Keep all widget objects alive
_widgets = []

def _cap(parent, x, y, text, size=11, color=None):
    """Add a Caption to parent.children."""
    c = mcrfpy.Caption(text=text, pos=(x, y),
                       fill_color=color or C_LABEL)
    c.font_size = size
    parent.children.append(c)
    return c

def _btn(parent, x, y, w, h, label, cb, color=None, fsize=11):
    """Clickable button frame with centered text.

    Caption is a child of the Frame but has NO on_click handler.
    This way, Caption returns nullptr from click_at(), letting the
    click fall through to the parent Frame's handler.
    """
    f = mcrfpy.Frame(pos=(x, y), size=(w, h),
                     fill_color=color or C_BTN,
                     outline_color=C_OUTLINE, outline=1.0)
    parent.children.append(f)
    tx = max(2, (w - len(label) * fsize * 0.58) / 2)
    ty = max(1, (h - fsize) / 2)
    c = mcrfpy.Caption(text=label, pos=(int(tx), int(ty)),
                       fill_color=C_TEXT)
    c.font_size = fsize
    f.children.append(c)
    def click(pos, button, action):
        if button == mcrfpy.MouseButton.LEFT and action == mcrfpy.InputState.PRESSED:
            cb()
    f.on_click = click
    # Do NOT set c.on_click - Caption children consume click events
    # and prevent the parent Frame's handler from firing.
    return f, c


class Slider:
    """Horizontal slider widget with label and value display."""
    def __init__(self, parent, x, y, label, lo, hi, val, cb,
                 sw=140, sh=10, lw=108):
        _widgets.append(self)
        self.lo, self.hi, self.val, self.cb = lo, hi, val, cb
        self.sw = sw
        self.tx = x + lw  # track absolute x

        # label
        _cap(parent, x, y, label)

        # track
        self.track = mcrfpy.Frame(
            pos=(self.tx, y), size=(sw, sh),
            fill_color=C_SL_BG, outline_color=C_OUTLINE, outline=1.0)
        parent.children.append(self.track)

        # fill
        pct = self._pct(val)
        self.fill = mcrfpy.Frame(
            pos=(0, 0), size=(max(1, int(sw * pct)), sh),
            fill_color=C_SL_FILL)
        self.track.children.append(self.fill)

        # value text
        self.vcap = mcrfpy.Caption(
            text=self._fmt(val),
            pos=(self.tx + sw + 4, y), fill_color=C_VALUE)
        self.vcap.font_size = 10
        parent.children.append(self.vcap)

        self.track.on_click = self._click
        self.fill.on_click = self._click

    def _pct(self, v):
        r = self.hi - self.lo
        return (v - self.lo) / r if r else 0.0

    def _fmt(self, v):
        if abs(v) < 0.001 and v != 0:
            return f"{v:.4f}"
        return f"{v:.3f}"

    def _click(self, pos, button, action):
        if button != mcrfpy.MouseButton.LEFT:
            return
        if action != mcrfpy.InputState.PRESSED:
            return
        p = max(0.0, min(1.0, (pos.x - self.tx) / self.sw))
        self.val = self.lo + p * (self.hi - self.lo)
        self.fill.w = max(1, int(self.sw * p))
        self.vcap.text = self._fmt(self.val)
        self.cb(self.val)

    def set(self, v):
        self.val = max(self.lo, min(self.hi, v))
        p = self._pct(self.val)
        self.fill.w = max(1, int(self.sw * p))
        self.vcap.text = self._fmt(self.val)


# ============================================================
# SFXR Audio Logic
# ============================================================
def play_sfxr():
    """Generate sfxr buffer from current params and play it."""
    p = dict(S.params)
    p['wave_type'] = S.wave_type
    try:
        buf = mcrfpy.SoundBuffer.sfxr(**p)
    except Exception as e:
        print(f"sfxr generation error: {e}")
        return

    # Post-processing DSP chain
    if S.fx_on['low_pass']:
        buf = buf.low_pass(2000.0)
    if S.fx_on['high_pass']:
        buf = buf.high_pass(500.0)
    if S.fx_on['echo']:
        buf = buf.echo(200.0, 0.4, 0.5)
    if S.fx_on['reverb']:
        buf = buf.reverb(0.8, 0.5, 0.3)
    if S.fx_on['distortion']:
        buf = buf.distortion(2.0)
    if S.fx_on['bit_crush']:
        buf = buf.bit_crush(8, 4)

    buf = buf.normalize()
    if buf.sample_count == 0:
        # Some param combos produce silence (e.g. freq_limit > base_freq)
        return
    S.sound = mcrfpy.Sound(buf)
    S.sound.volume = S.volume
    S.sound.play()


def load_preset(name):
    """Load sfxr preset, sync UI, optionally auto-play."""
    try:
        buf = mcrfpy.SoundBuffer.sfxr(name)
    except Exception as e:
        print(f"Preset error: {e}")
        return
    mp = buf.sfxr_params
    if not mp:
        return
    S.wave_type = int(mp.get('wave_type', 0))
    for k in S.params:
        if k in mp:
            S.params[k] = mp[k]
    _sync_sfxr_ui()
    if S.auto_play:
        play_sfxr()


def mutate_sfxr():
    """Mutate current params slightly."""
    p = dict(S.params)
    p['wave_type'] = S.wave_type
    try:
        buf = mcrfpy.SoundBuffer.sfxr(**p)
        m = buf.sfxr_mutate(0.05)
    except Exception as e:
        print(f"Mutate error: {e}")
        return
    mp = m.sfxr_params
    if mp:
        S.wave_type = int(mp.get('wave_type', S.wave_type))
        for k in S.params:
            if k in mp:
                S.params[k] = mp[k]
    _sync_sfxr_ui()
    if S.auto_play:
        play_sfxr()


def randomize_sfxr():
    """Load a random preset with random seed."""
    presets = ["coin", "laser", "explosion", "powerup", "hurt", "jump", "blip"]
    buf = mcrfpy.SoundBuffer.sfxr(random.choice(presets),
                                   seed=random.randint(0, 999999))
    mp = buf.sfxr_params
    if mp:
        S.wave_type = int(mp.get('wave_type', 0))
        for k in S.params:
            if k in mp:
                S.params[k] = mp[k]
    _sync_sfxr_ui()
    if S.auto_play:
        play_sfxr()


def _sync_sfxr_ui():
    """Push state to all sfxr UI widgets."""
    for k, sl in S.sliders.items():
        if k in S.params:
            sl.set(S.params[k])
    _update_wave_btns()


def _update_wave_btns():
    for i, (btn, _cap) in enumerate(S.wave_btns):
        btn.fill_color = C_BTN_ON if i == S.wave_type else C_BTN


def set_wave(i):
    S.wave_type = i
    _update_wave_btns()
    if S.auto_play:
        play_sfxr()


def toggle_fx(key):
    S.fx_on[key] = not S.fx_on[key]
    if key in S.fx_btns:
        S.fx_btns[key].fill_color = C_BTN_ON if S.fx_on[key] else C_BTN


# ============================================================
# Animalese Audio Logic
# ============================================================
# Vowel formant frequencies (F1, F2)
FORMANTS = {
    'ah': (660, 1700),
    'eh': (530, 1850),
    'ee': (270, 2300),
    'oh': (570, 870),
    'oo': (300, 870),
}

LETTER_VOWEL = {}
for _c in 'AHLR':
    LETTER_VOWEL[_c] = 'ah'
for _c in 'EDTSNZ':
    LETTER_VOWEL[_c] = 'eh'
for _c in 'ICJY':
    LETTER_VOWEL[_c] = 'ee'
for _c in 'OGKQX':
    LETTER_VOWEL[_c] = 'oh'
for _c in 'UBFMPVW':
    LETTER_VOWEL[_c] = 'oo'

CONSONANTS = set('BCDFGJKPQSTVXZ')

# Cache generated vowel base sounds per pitch
_vowel_cache = {}

def _make_vowel(vowel_key, pitch, breathiness):
    """Generate a single vowel sound (~120ms) at given pitch."""
    f1, f2 = FORMANTS[vowel_key]
    dur = 0.12

    # Glottal source: sawtooth at fundamental
    source = mcrfpy.SoundBuffer.tone(pitch, dur, "saw",
        attack=0.005, decay=0.015, sustain=0.7, release=0.015)

    # Formant approximation: low-pass at F1 frequency
    # (single-pole filter, so we use a higher cutoff for approximation)
    filtered = source.low_pass(float(f1) * 1.5)

    # Add breathiness as noise
    if breathiness > 0.05:
        noise = mcrfpy.SoundBuffer.tone(1000, dur, "noise",
            attack=0.003, decay=0.01, sustain=breathiness * 0.25,
            release=0.01)
        filtered = mcrfpy.SoundBuffer.mix([filtered, noise])

    return filtered.normalize()


def _make_letter_sound(char, pitch, breathiness):
    """Generate audio for a single letter."""
    ch = char.upper()
    if ch not in LETTER_VOWEL:
        return None

    vowel = _make_vowel(LETTER_VOWEL[ch], pitch, breathiness)

    # Add consonant noise burst
    if ch in CONSONANTS:
        burst = mcrfpy.SoundBuffer.tone(2500, 0.012, "noise",
            attack=0.001, decay=0.003, sustain=0.6, release=0.003)
        vowel = mcrfpy.SoundBuffer.concat([burst, vowel], overlap=0.004)

    return vowel


def speak_text():
    """Generate and play animalese speech from current text."""
    text = S.text.upper()
    if not text.strip():
        return

    rate = S.speech_rate
    letter_dur = 1.0 / rate
    overlap = letter_dur * 0.25

    bufs = []
    for ch in text:
        if ch == ' ':
            # Short silence for spaces
            sil = mcrfpy.SoundBuffer.from_samples(
                b'\x00\x00' * int(44100 * 0.04), 1, 44100)
            bufs.append(sil)
        elif ch in '.!?':
            # Longer pause for punctuation
            sil = mcrfpy.SoundBuffer.from_samples(
                b'\x00\x00' * int(44100 * 0.12), 1, 44100)
            bufs.append(sil)
        elif ch.isalpha():
            # Pitch jitter in semitones
            jitter = random.uniform(-S.pitch_jitter, S.pitch_jitter)
            pitch = S.base_pitch * (2.0 ** (jitter / 12.0))
            lsnd = _make_letter_sound(ch, pitch, S.breathiness)
            if lsnd:
                # Trim to letter duration
                if lsnd.duration > letter_dur:
                    lsnd = lsnd.slice(0, letter_dur)
                bufs.append(lsnd)

    if not bufs:
        return

    result = mcrfpy.SoundBuffer.concat(bufs, overlap=overlap)
    result = result.normalize()

    # Optional: add room reverb for warmth
    result = result.reverb(0.3, 0.5, 0.15)

    S.anim_sound = mcrfpy.Sound(result)
    S.anim_sound.volume = S.volume
    S.anim_sound.play()

    # Start letter animation
    S.speak_idx = 0
    S.speaking = True
    if S.letter_cap:
        S.letter_cap.text = ""
    interval = int(1000.0 / S.speech_rate)
    S.speak_timer = mcrfpy.Timer("speak_tick", _tick_letter, interval)


def _tick_letter(timer, runtime):
    """Advance the speaking letter display."""
    text = S.text.upper()
    if S.speak_idx < len(text):
        ch = text[S.speak_idx]
        if S.letter_cap:
            S.letter_cap.text = ch if ch.strip() else "_"
        S.speak_idx += 1
    else:
        if S.letter_cap:
            S.letter_cap.text = ""
        S.speaking = False
        timer.stop()


# Personality presets
PERSONALITIES = {
    'CRANKY':  {'pitch': 90,  'rate': 10, 'jitter': 1.5, 'breath': 0.4},
    'NORMAL':  {'pitch': 180, 'rate': 12, 'jitter': 2.0, 'breath': 0.2},
    'PEPPY':   {'pitch': 280, 'rate': 18, 'jitter': 3.5, 'breath': 0.1},
    'LAZY':    {'pitch': 120, 'rate': 8,  'jitter': 1.0, 'breath': 0.5},
    'JOCK':    {'pitch': 100, 'rate': 15, 'jitter': 2.5, 'breath': 0.3},
}

def load_personality(name):
    p = PERSONALITIES[name]
    S.base_pitch = p['pitch']
    S.speech_rate = p['rate']
    S.pitch_jitter = p['jitter']
    S.breathiness = p['breath']
    _sync_anim_ui()


def _sync_anim_ui():
    for k, sl in S.anim_sliders.items():
        if k == 'pitch':
            sl.set(S.base_pitch)
        elif k == 'rate':
            sl.set(S.speech_rate)
        elif k == 'jitter':
            sl.set(S.pitch_jitter)
        elif k == 'breath':
            sl.set(S.breathiness)


# ============================================================
# Build SFXR Scene
# ============================================================
def build_sfxr():
    scene = mcrfpy.Scene("sfxr")
    bg = mcrfpy.Frame(pos=(0, 0), size=(W, H), fill_color=C_BG)
    scene.children.append(bg)

    # --- Left Panel: Presets ---
    _cap(bg, 12, 8, "GENERATOR", size=13, color=C_HEADER)

    presets = [
        ("PICKUP/COIN", "coin"),
        ("LASER/SHOOT", "laser"),
        ("EXPLOSION", "explosion"),
        ("POWERUP", "powerup"),
        ("HIT/HURT", "hurt"),
        ("JUMP", "jump"),
        ("BLIP/SELECT", "blip"),
    ]
    py = 30
    for label, preset in presets:
        _btn(bg, 10, py, 118, 22, label,
             lambda p=preset: load_preset(p))
        py += 26

    py += 10
    _btn(bg, 10, py, 118, 22, "MUTATE", mutate_sfxr, color=C_BTN_ACC)
    py += 26
    _btn(bg, 10, py, 118, 22, "RANDOMIZE", randomize_sfxr, color=C_BTN_ACC)

    # --- Right Panel ---
    rx = 730

    # Waveform Selection
    _cap(bg, rx, 8, "WAVEFORM", size=12, color=C_HEADER)
    wave_names = ["SQUARE", "SAW", "SINE", "NOISE"]
    S.wave_btns = []
    for i, wn in enumerate(wave_names):
        bx = rx + i * 68
        b, c = _btn(bg, bx, 26, 64, 20, wn,
                     lambda idx=i: set_wave(idx), fsize=10)
        S.wave_btns.append((b, c))
    _update_wave_btns()

    # Volume
    _cap(bg, rx, 54, "VOLUME", size=12, color=C_HEADER)
    Slider(bg, rx, 70, "", 0, 100, S.volume,
           lambda v: setattr(S, 'volume', v),
           sw=220, lw=0)

    # Play button
    _btn(bg, rx, 90, 270, 28, "PLAY SOUND", play_sfxr,
         color=mcrfpy.Color(180, 100, 80), fsize=13)

    # Auto-play toggle
    auto_btn, auto_cap = _btn(bg, rx, 124, 270, 22, "AUTO-PLAY: ON",
                               lambda: None, color=C_BTN_ON)
    def toggle_auto():
        S.auto_play = not S.auto_play
        auto_btn.fill_color = C_BTN_ON if S.auto_play else C_BTN
        auto_cap.text = "AUTO-PLAY: ON" if S.auto_play else "AUTO-PLAY: OFF"
    auto_btn.on_click = lambda p, b, a: (
        toggle_auto() if b == mcrfpy.MouseButton.LEFT
        and a == mcrfpy.InputState.PRESSED else None)
    # Do NOT set auto_cap.on_click - let clicks pass through to Frame

    # DSP Effects
    _cap(bg, rx, 158, "DSP EFFECTS", size=12, color=C_HEADER)

    fx_list = [
        ("LOW PASS",   'low_pass'),
        ("HIGH PASS",  'high_pass'),
        ("ECHO",       'echo'),
        ("REVERB",     'reverb'),
        ("DISTORTION", 'distortion'),
        ("BIT CRUSH",  'bit_crush'),
    ]
    fy = 176
    for label, key in fx_list:
        fb, fc = _btn(bg, rx, fy, 270, 20, label,
                       lambda k=key: toggle_fx(k))
        S.fx_btns[key] = fb
        fy += 24

    # Navigation
    _cap(bg, rx, fy + 10, "NAVIGATION", size=12, color=C_HEADER)
    _btn(bg, rx, fy + 28, 270, 26, "ANIMALESE >>",
         lambda: setattr(mcrfpy, 'current_scene', S.anim_scene))

    # --- Center: SFXR Parameter Sliders (single column) ---
    sx = 140
    cy = 8
    ROW = 18
    SL_W = 220
    LBL_W = 108

    all_params = [
        ("ENVELOPE", None),
        ("ATTACK TIME",    'env_attack',    0.0, 1.0),
        ("SUSTAIN TIME",   'env_sustain',   0.0, 1.0),
        ("SUSTAIN PUNCH",  'env_punch',     0.0, 1.0),
        ("DECAY TIME",     'env_decay',     0.0, 1.0),
        ("FREQUENCY", None),
        ("START FREQ",     'base_freq',     0.0, 1.0),
        ("MIN FREQ",       'freq_limit',    0.0, 1.0),
        ("SLIDE",          'freq_ramp',    -1.0, 1.0),
        ("DELTA SLIDE",    'freq_dramp',   -1.0, 1.0),
        ("VIBRATO", None),
        ("VIB DEPTH",      'vib_strength',  0.0, 1.0),
        ("VIB SPEED",      'vib_speed',     0.0, 1.0),
        ("DUTY", None),
        ("SQUARE DUTY",    'duty',          0.0, 1.0),
        ("DUTY SWEEP",     'duty_ramp',    -1.0, 1.0),
        ("ARPEGGIATION", None),
        ("ARP MOD",        'arp_mod',      -1.0, 1.0),
        ("ARP SPEED",      'arp_speed',     0.0, 1.0),
        ("REPEAT", None),
        ("REPEAT SPEED",   'repeat_speed',  0.0, 1.0),
        ("PHASER", None),
        ("PHA OFFSET",     'pha_offset',   -1.0, 1.0),
        ("PHA SWEEP",      'pha_ramp',     -1.0, 1.0),
        ("FILTER", None),
        ("LP CUTOFF",      'lpf_freq',      0.0, 1.0),
        ("LP SWEEP",       'lpf_ramp',     -1.0, 1.0),
        ("LP RESONANCE",   'lpf_resonance', 0.0, 1.0),
        ("HP CUTOFF",      'hpf_freq',      0.0, 1.0),
        ("HP SWEEP",       'hpf_ramp',     -1.0, 1.0),
    ]

    for entry in all_params:
        if len(entry) == 2:
            # Section header
            header_text, _ = entry
            _cap(bg, sx, cy, header_text, size=10, color=C_HEADER)
            cy += 14
            continue
        label, key, lo, hi = entry
        val = S.params[key]
        sl = Slider(bg, sx, cy, label, lo, hi, val,
                    lambda v, k=key: _sfxr_param_changed(k, v),
                    sw=SL_W, lw=LBL_W)
        S.sliders[key] = sl
        cy += ROW

    # --- Keyboard hints ---
    _cap(bg, 10, H - 44, "Keyboard:", size=11, color=C_HEADER)
    _cap(bg, 10, H - 28, "SPACE=Play  R=Random  M=Mutate  1-4=Wave  TAB=Animalese  ESC=Quit",
         size=10, color=C_VALUE)

    # --- Key handler ---
    def on_key(key, action):
        if action != mcrfpy.InputState.PRESSED:
            return
        if key == mcrfpy.Key.ESCAPE:
            sys.exit(0)
        elif key == mcrfpy.Key.TAB:
            mcrfpy.current_scene = S.anim_scene
        elif key == mcrfpy.Key.SPACE:
            play_sfxr()
        elif key == mcrfpy.Key.R:
            randomize_sfxr()
        elif key == mcrfpy.Key.M:
            mutate_sfxr()
        elif key == mcrfpy.Key.NUM_1:
            set_wave(0)
        elif key == mcrfpy.Key.NUM_2:
            set_wave(1)
        elif key == mcrfpy.Key.NUM_3:
            set_wave(2)
        elif key == mcrfpy.Key.NUM_4:
            set_wave(3)

    scene.on_key = on_key
    return scene


def _sfxr_param_changed(key, val):
    """Called when a slider changes an sfxr param."""
    S.params[key] = val
    if S.auto_play:
        play_sfxr()


# ============================================================
# Build Animalese Scene
# ============================================================
def build_animalese():
    scene = mcrfpy.Scene("animalese")
    bg = mcrfpy.Frame(pos=(0, 0), size=(W, H), fill_color=C_BG2)
    scene.children.append(bg)

    # Title
    _cap(bg, 20, 10, "ANIMALESE SPEECH SYNTH", size=16, color=mcrfpy.Color(240, 235, 220))

    # --- Text Display ---
    _cap(bg, 20, 50, "TEXT (type to edit, ENTER to speak):", size=11,
         color=mcrfpy.Color(220, 215, 200))

    # Text input display
    text_frame = mcrfpy.Frame(pos=(20, 70), size=(700, 36),
                               fill_color=mcrfpy.Color(30, 35, 48),
                               outline_color=mcrfpy.Color(100, 110, 130),
                               outline=1.0)
    bg.children.append(text_frame)
    S.text_cap = mcrfpy.Caption(text=S.text + "_", pos=(6, 8),
                                 fill_color=mcrfpy.Color(220, 220, 180))
    S.text_cap.font_size = 16
    text_frame.children.append(S.text_cap)

    # Current letter display (large)
    _cap(bg, 740, 50, "NOW:", size=11, color=mcrfpy.Color(220, 215, 200))
    S.letter_cap = mcrfpy.Caption(text="", pos=(740, 68),
                                   fill_color=C_ACCENT)
    S.letter_cap.font_size = 42
    bg.children.append(S.letter_cap)

    # --- Personality Presets ---
    _cap(bg, 20, 120, "CHARACTER PRESETS", size=13,
         color=mcrfpy.Color(240, 235, 220))

    px = 20
    for name in ['CRANKY', 'NORMAL', 'PEPPY', 'LAZY', 'JOCK']:
        _btn(bg, px, 142, 95, 24, name,
             lambda n=name: load_personality(n),
             color=C_BG2_PNL)
        px += 102

    # --- Voice Parameters ---
    _cap(bg, 20, 185, "VOICE PARAMETERS", size=13,
         color=mcrfpy.Color(240, 235, 220))

    sy = 208
    S.anim_sliders['pitch'] = Slider(
        bg, 20, sy, "BASE PITCH", 60, 350, S.base_pitch,
        lambda v: setattr(S, 'base_pitch', v),
        sw=200, lw=110)
    sy += 28
    S.anim_sliders['rate'] = Slider(
        bg, 20, sy, "SPEECH RATE", 4, 24, S.speech_rate,
        lambda v: setattr(S, 'speech_rate', v),
        sw=200, lw=110)
    sy += 28
    S.anim_sliders['jitter'] = Slider(
        bg, 20, sy, "PITCH JITTER", 0, 6, S.pitch_jitter,
        lambda v: setattr(S, 'pitch_jitter', v),
        sw=200, lw=110)
    sy += 28
    S.anim_sliders['breath'] = Slider(
        bg, 20, sy, "BREATHINESS", 0, 1.0, S.breathiness,
        lambda v: setattr(S, 'breathiness', v),
        sw=200, lw=110)

    # --- Speak Button ---
    _btn(bg, 20, sy + 38, 200, 32, "SPEAK", speak_text,
         color=mcrfpy.Color(80, 140, 80), fsize=14)

    # --- Formant Reference ---
    ry = 185
    _cap(bg, 550, ry, "LETTER -> VOWEL MAPPING", size=12,
         color=mcrfpy.Color(240, 235, 220))
    ry += 22
    mappings = [
        ("A H L R", "-> 'ah' (F1=660, F2=1700)"),
        ("E D T S N Z", "-> 'eh' (F1=530, F2=1850)"),
        ("I C J Y", "-> 'ee' (F1=270, F2=2300)"),
        ("O G K Q X", "-> 'oh' (F1=570, F2=870)"),
        ("U B F M P V W", "-> 'oo' (F1=300, F2=870)"),
    ]
    for letters, desc in mappings:
        _cap(bg, 555, ry, letters, size=11,
             color=mcrfpy.Color(240, 220, 140))
        _cap(bg, 680, ry, desc, size=10,
             color=mcrfpy.Color(200, 195, 180))
        ry += 18

    _cap(bg, 555, ry + 8, "Consonants (B,C,D,...) add", size=10,
         color=mcrfpy.Color(185, 180, 170))
    _cap(bg, 555, ry + 22, "a noise burst before the vowel", size=10,
         color=mcrfpy.Color(185, 180, 170))

    # --- How it works ---
    hy = 420
    _cap(bg, 20, hy, "HOW IT WORKS", size=13,
         color=mcrfpy.Color(240, 235, 220))
    steps = [
        "1. Each letter maps to a vowel class (ah/eh/ee/oh/oo)",
        "2. Sawtooth tone at base_pitch filtered through low_pass (formant F1)",
        "3. Noise mixed in for breathiness, burst prepended for consonants",
        "4. Pitch jittered per-letter for natural variation",
        "5. Letters concatenated with overlap for babble effect",
        "6. Light reverb applied for warmth",
    ]
    for i, step in enumerate(steps):
        _cap(bg, 25, hy + 22 + i * 17, step, size=10,
             color=mcrfpy.Color(200, 198, 188))

    # --- Navigation ---
    _btn(bg, 20, H - 50, 200, 28, "<< SFXR SYNTH",
         lambda: setattr(mcrfpy, 'current_scene', S.sfxr_scene),
         color=C_BG2_PNL)

    # --- Keyboard hints ---
    _cap(bg, 250, H - 46, "Type letters to edit text | ENTER = Speak | "
         "1-5 = Presets | TAB = SFXR | ESC = Quit",
         size=10, color=mcrfpy.Color(190, 188, 175))

    # Build key-to-char map
    key_chars = {}
    for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        k = getattr(mcrfpy.Key, c, None)
        if k is not None:
            key_chars[k] = c

    # --- Key handler ---
    def on_key(key, action):
        if action != mcrfpy.InputState.PRESSED:
            return
        if key == mcrfpy.Key.ESCAPE:
            sys.exit(0)
        elif key == mcrfpy.Key.TAB:
            mcrfpy.current_scene = S.sfxr_scene
        elif key == mcrfpy.Key.ENTER:
            speak_text()
        elif key == mcrfpy.Key.BACKSPACE:
            if S.text:
                S.text = S.text[:-1]
                S.text_cap.text = S.text + "_"
        elif key == mcrfpy.Key.SPACE:
            S.text += ' '
            S.text_cap.text = S.text + "_"
        elif key == mcrfpy.Key.NUM_1:
            load_personality('CRANKY')
        elif key == mcrfpy.Key.NUM_2:
            load_personality('NORMAL')
        elif key == mcrfpy.Key.NUM_3:
            load_personality('PEPPY')
        elif key == mcrfpy.Key.NUM_4:
            load_personality('LAZY')
        elif key == mcrfpy.Key.NUM_5:
            load_personality('JOCK')
        elif key in key_chars:
            S.text += key_chars[key]
            S.text_cap.text = S.text + "_"

    scene.on_key = on_key
    return scene


# ============================================================
# Main
# ============================================================
S.sfxr_scene = build_sfxr()
S.anim_scene = build_animalese()
mcrfpy.current_scene = S.sfxr_scene
