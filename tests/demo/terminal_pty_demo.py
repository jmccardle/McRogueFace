#!/usr/bin/env python3
"""Run a shell (or any program) in a TerminalLayer -- the Python-side PTY pattern (#550).

LINUX ONLY. A demo, not a test. The engine has no PTY type, by design: a TerminalLayer only
turns bytes into cells (write) and input into bytes (on_output). This script supplies the
PTY with Python's standard library:

    child output  --os.read(pty)-->  term.write()          (polled by a 16 ms Timer)
    term.on_output  --os.write(pty)-->  child input        (query replies and encoded keys)
    scene.on_key  -->  term.key(key, state)                 (arrows, Enter, Ctrl/Alt combos, ...)
    scene.on_text -->  term.text(text)                      (typed characters)

    cd build && ./mcrogueface ../tests/demo/terminal_pty_demo.py            # $SHELL
    cd build && ./mcrogueface ../tests/demo/terminal_pty_demo.py -- htop    # any program

The window closes when the program exits. MCRF_DEMO_SHOT=path.png saves a screenshot after 1.5 s. The developer-tool hotkeys are switched off so every
key reaches the program.
"""
import fcntl
import os
import pty
import struct
import sys
import termios

import mcrfpy

if not sys.platform.startswith("linux"):
    print("terminal_pty_demo.py needs Linux (pty.fork)")
    sys.exit(1)

COLS, ROWS = 100, 30
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [os.environ.get("SHELL", "/bin/sh")]

font = mcrfpy.Font("assets/JetbrainsMono.ttf")
tex = mcrfpy.Texture.from_font(font, 16, codepoints=[(0x20, 0x7E), (0xA0, 0x17F), (0x2190, 0x21FF),
                                                     (0x2500, 0x259F), (0x25A0, 0x25FF)])

# --- the PTY (Python side) -------------------------------------------------------------------
pid, fd = pty.fork()
if pid == 0:  # child: become the program, attached to the PTY's slave side
    os.environ["TERM"] = "xterm-256color"
    os.environ["COLUMNS"], os.environ["LINES"] = str(COLS), str(ROWS)
    try:
        os.execvp(argv[0], argv)
    finally:
        os._exit(127)
fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", ROWS, COLS, COLS * tex.sprite_width, ROWS * tex.sprite_height))
os.set_blocking(fd, False)


def to_child(data):
    os.write(fd, data)


# --- the terminal (engine side) ----------------------------------------------------------------
term = mcrfpy.TerminalLayer(texture=tex, grid_size=(COLS, ROWS), on_output=to_child)
term.background = mcrfpy.Color(16, 16, 24)
scene = mcrfpy.Scene("terminal")
grid = mcrfpy.Grid(grid_size=(COLS, ROWS), texture=tex, pos=(0, 0),
                   size=(COLS * tex.sprite_width, ROWS * tex.sprite_height), layers=[term])
grid.center = (COLS * tex.sprite_width / 2, ROWS * tex.sprite_height / 2)
scene.children.append(grid)

window = mcrfpy.Window.get()
window.resolution = (COLS * tex.sprite_width, ROWS * tex.sprite_height)
window.console_key = None
window.explorer_key = None
window.profiler_key = None


# The minimal wiring, all of it:
#     term.on_output = lambda data: os.write(fd, data)      # replies and input -> program
#     term.write(os.read(fd, 65536))                        # program -> screen (polled)
#     scene.on_key  = lambda key, state: term.key(key, state)
#     scene.on_text = lambda text: term.text(text)          # minus the Ctrl/Alt filter below


# Keys that type a character (key() sends them only as Ctrl/Alt combinations).
TEXT_KEYS = {k for k in mcrfpy.Key if len(k.name) == 1 or k.name.startswith("NUM_") or k.name in (
    "SPACE", "COMMA", "PERIOD", "SLASH", "BACKSLASH", "SEMICOLON", "APOSTROPHE", "GRAVE", "EQUAL",
    "HYPHEN", "LEFT_BRACKET", "RIGHT_BRACKET")}


def on_key(key, state):
    kb = mcrfpy.keyboard
    if kb.ctrl and kb.alt and key in TEXT_KEYS:
        return   # AltGr: the character arrives through on_text
    term.key(key, state)


def on_text(text):
    # key() already sent a Ctrl or Alt combination (Ctrl+C, Alt+x); text the platform also
    # reports for it would be a second copy. Ctrl and Alt TOGETHER is AltGr on many layouts
    # (e.g. AltGr+q = @ on a German keyboard): that text is the character the user typed.
    kb = mcrfpy.keyboard
    if (kb.ctrl or kb.alt) and not (kb.ctrl and kb.alt):
        return
    term.text(text)


scene.on_key = on_key
scene.on_text = on_text


def pump(timer, runtime):
    while True:
        try:
            data = os.read(fd, 65536)
        except BlockingIOError:
            break
        except OSError:  # EIO: the program exited and the PTY closed
            data = b""
        if not data:
            try:
                os.waitpid(pid, 0)
            except ChildProcessError:  # already reaped
                pass
            mcrfpy.exit()
            return
        term.write(data)
    if term.title:
        window.title = term.title
    if os.environ.get("MCRF_DEMO_SHOT") and runtime > 1500:
        from mcrfpy import automation
        automation.screenshot(os.environ["MCRF_DEMO_SHOT"])
        os.environ.pop("MCRF_DEMO_SHOT")


mcrfpy.Timer("pty", pump, 16)
scene.activate()
