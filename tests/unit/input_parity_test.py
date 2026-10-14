#!/usr/bin/env python3
"""Input parity: mcrfpy.Key / MouseButton / InputState inventory + SDL2 web-backend audit (#389).

Desktop input is SFML; the web build uses the SDL2 stubs in src/platform/SDL2Types.h
plus an SDL-event -> sf::Event pump in src/platform/SDL2Renderer.cpp. CLAUDE.md's
"Web Build Constraints" table claims Input is "Full -- SDL events translated to SFML
enums" but nothing tested the translation. This test locks the Python-facing enum
inventory (checkable from the running desktop/headless build) and records the static
C++-side audit findings so they cannot silently rot.

=============================================================================
STATIC AUDIT (source-verified 2026-07-19, branch feat/387-web-parity-sprint)
=============================================================================

Enum-value parity between backends -- PASS.
  PyKey.cpp / PyMouseButton.cpp reference `sf::Keyboard::*` / `sf::Mouse::*` symbols
  that resolve to REAL SFML headers on desktop and to the stub enums in
  src/platform/SDL2Types.h on web. The stub `enum Key` (SDL2Types.h:1269-1289) and
  `enum Button` (SDL2Types.h:1296) enumerate members in the exact SFML 2.6 order
  (A=0..Z=25, Num0..Num9, Escape=36, ... Pause=100, KeyCount=101; Left/Right/Middle/
  XButton1/XButton2 = 0..4). Therefore the integer values baked into mcrfpy.Key /
  mcrfpy.MouseButton are identical on both backends.

Keyboard translation coverage -- FULL.
  sdlScancodeToSfKey()  SDL2Renderer.cpp:825-936 maps SDL scancodes -> sf::Keyboard::Key.
  sfKeyToSdlScancode()  SDL2Renderer.cpp:937-1042 is the inverse (used by isKeyPressed).
  Every one of the 101 real sf::Keyboard::Key members that mcrfpy.Key exposes has a
  case in both directions (letters, Num0-9, Numpad0-9, F1-F15, all modifiers,
  navigation, editing, symbols, Add/Subtract/Multiply/Divide, Pause). No exposed Key
  is unmapped on web. Unmapped/exotic scancodes fall through to Keyboard::Unknown
  (-1), i.e. mcrfpy.Key.UNKNOWN -- a valid delivered member, not a silent zero.

Mouse-button translation coverage -- FULL.
  sdlButtonToSfButton()  SDL2Renderer.cpp:1044-1052 maps SDL_BUTTON_LEFT/RIGHT/MIDDLE/
  X1/X2 -> Mouse::Left/Right/Middle/XButton1/XButton2. All 5 physical buttons the
  API exposes are covered. (SCROLL_UP=10 / SCROLL_DOWN=11 are synthetic API values
  produced from the shared MouseWheelScrolled path, SDL2Renderer.cpp:809-815 -- not
  from the button table -- so they are backend-agnostic.)

Modifiers -- FULL.
  SDL2Renderer.cpp:783-786 populates sf::Event.key.{alt,control,shift,system} from
  KMOD_ALT / KMOD_CTRL / KMOD_SHIFT / KMOD_GUI. All four modifier flags are carried.

Non-blocking issues noted for follow-up (NOT enum gaps, do not fail this test):
  * SDL2Renderer.cpp:742-745  `SDL_SCANCODE_TO_SF_KEY[]` is a dead placeholder array
    ("Placeholder" / Keyboard::Unknown). Real work is the switch in sdlScancodeToSfKey();
    the array is unused and misleading -- candidate for deletion.
  * SDL2Renderer.cpp:1049  sdlButtonToSfButton default returns Mouse::Left, so an
    unknown SDL button id would silently become a LEFT click (Fail-Early violation).
    Unreachable today because all 5 SDL button ids are mapped, but it should raise/
    return an Unknown sentinel rather than fabricate a Left click.
  * (resolved in #495) SDL_TEXTINPUT used to copy only `text.text[0]` as one unsigned
    char, mangling every non-ASCII character and dropping all but the first character
    of an IME commit. translateSDLEvent now decodes every code point (the first is
    returned, the rest wait in g_pendingText and are drained by pollEvent/waitEvent),
    and drops malformed UTF-8 instead of inventing U+FFFD. test_text_entry_audit below
    keeps that from regressing.

Text entry (#495) -- scene.on_text(text: str), one printable code point per call.
  SFML delivers sf::Event::TextEntered, SDL2 delivers SDL_TEXTINPUT translated to the
  same event. SFML also reports control characters (Backspace 8, Tab 9, Enter 13,
  Escape 27, DEL 127) as text and SDL never does, so GameEngine::dispatchText drops
  C0/DEL/C1 and both backends deliver the same thing; those are keys, on on_key.

Modifiers (#497) -- mcrfpy.keyboard.{shift,ctrl,alt,system} report the modifiers of the key
  event being handled, never a hardware poll. SDL2Renderer.cpp copies KMOD_* into
  key.{alt,control,shift,system} (above), SFML sets the same fields, so both backends
  feed GameEngine::noteKeyModifiers the same way.

Developer-tool hotkeys (#496) -- Window.console_key / explorer_key. The ImGui console and
  scene explorer exist only in windowed SFML builds. On web (SDL2) and headless there is no
  tool to toggle, so every key, Grave and F4 included, always reaches on_key there.

Conclusion: for the enum-based input path (Key / MouseButton / modifiers) the web
SDL2 backend is at full parity with desktop SFML -- no unmapped keys, buttons, or
modifiers. This test asserts the Python-side inventory that both backends share.
=============================================================================
"""

import mcrfpy
import sys


# Expected complete mcrfpy.Key inventory: name -> integer value.
# Values match SFML 2.6 sf::Keyboard::Key ordering (see PyKey.cpp key_table).
EXPECTED_KEYS = {
    # Letters A-Z = 0..25
    **{c: i for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")},
    # Number row = 26..35
    **{f"NUM_{n}": 26 + n for n in range(10)},
    # Control keys
    "ESCAPE": 36, "LEFT_CONTROL": 37, "LEFT_SHIFT": 38, "LEFT_ALT": 39,
    "LEFT_SYSTEM": 40, "RIGHT_CONTROL": 41, "RIGHT_SHIFT": 42, "RIGHT_ALT": 43,
    "RIGHT_SYSTEM": 44, "MENU": 45,
    # Punctuation / symbols
    "LEFT_BRACKET": 46, "RIGHT_BRACKET": 47, "SEMICOLON": 48, "COMMA": 49,
    "PERIOD": 50, "APOSTROPHE": 51, "SLASH": 52, "BACKSLASH": 53, "GRAVE": 54,
    "EQUAL": 55, "HYPHEN": 56,
    # Whitespace / editing
    "SPACE": 57, "ENTER": 58, "BACKSPACE": 59, "TAB": 60,
    # Navigation
    "PAGE_UP": 61, "PAGE_DOWN": 62, "END": 63, "HOME": 64, "INSERT": 65, "DELETE": 66,
    # Numpad operators
    "ADD": 67, "SUBTRACT": 68, "MULTIPLY": 69, "DIVIDE": 70,
    # Arrows
    "LEFT": 71, "RIGHT": 72, "UP": 73, "DOWN": 74,
    # Numpad numbers = 75..84
    **{f"NUMPAD_{n}": 75 + n for n in range(10)},
    # Function keys F1..F15 = 85..99
    **{f"F{n}": 84 + n for n in range(1, 16)},
    # Misc
    "PAUSE": 100,
    # Unknown sentinel
    "UNKNOWN": -1,
}

EXPECTED_MOUSE_BUTTONS = {
    "LEFT": 0, "RIGHT": 1, "MIDDLE": 2, "X1": 3, "X2": 4,
    "SCROLL_UP": 10, "SCROLL_DOWN": 11,
}

EXPECTED_INPUT_STATES = {
    "PRESSED": 0, "RELEASED": 1,
}


def _members(enum_cls):
    """Return {name: int_value} for every member of an IntEnum-style mcrfpy enum."""
    out = {}
    for name in dir(enum_cls):
        if name.startswith("_"):
            continue
        member = getattr(enum_cls, name)
        # Enum members are instances of the enum class; skip helper methods/attrs.
        if isinstance(member, enum_cls):
            out[name] = int(member)
    return out


def test_key_inventory():
    print("Testing mcrfpy.Key inventory...")
    assert hasattr(mcrfpy, "Key"), "mcrfpy.Key must exist"
    actual = _members(mcrfpy.Key)

    missing = set(EXPECTED_KEYS) - set(actual)
    extra = set(actual) - set(EXPECTED_KEYS)
    assert not missing, f"Key missing members: {sorted(missing)}"
    assert not extra, f"Key has unexpected members: {sorted(extra)}"

    for name, val in EXPECTED_KEYS.items():
        assert actual[name] == val, f"Key.{name} expected {val}, got {actual[name]}"

    print(f"  {len(actual)} Key members present with correct values")


def test_key_values_consistent():
    """Values must be unique and the real keys must be contiguous 0..KeyCount-1."""
    print("Testing mcrfpy.Key value consistency...")
    actual = _members(mcrfpy.Key)
    values = list(actual.values())
    assert len(values) == len(set(values)), "Key has duplicate integer values"

    real = sorted(v for v in values if v >= 0)
    assert real[0] == 0, f"Real Key values should start at 0, got {real[0]}"
    assert real == list(range(len(real))), "Real Key values must be contiguous 0..N-1"
    assert min(values) == -1, "UNKNOWN must be the only negative value (-1)"
    # This contiguous 0..100 range is exactly what sdlScancodeToSfKey() /
    # SDL2Types.h enum Key enumerate, i.e. every value has an SDL source mapping.
    print(f"  {len(real)} real keys contiguous 0..{real[-1]}, UNKNOWN=-1")


def test_mouse_button_inventory():
    print("Testing mcrfpy.MouseButton inventory...")
    assert hasattr(mcrfpy, "MouseButton"), "mcrfpy.MouseButton must exist"
    actual = _members(mcrfpy.MouseButton)

    missing = set(EXPECTED_MOUSE_BUTTONS) - set(actual)
    extra = set(actual) - set(EXPECTED_MOUSE_BUTTONS)
    assert not missing, f"MouseButton missing members: {sorted(missing)}"
    assert not extra, f"MouseButton has unexpected members: {sorted(extra)}"

    for name, val in EXPECTED_MOUSE_BUTTONS.items():
        assert actual[name] == val, f"MouseButton.{name} expected {val}, got {actual[name]}"

    values = list(actual.values())
    assert len(values) == len(set(values)), "MouseButton has duplicate integer values"
    # Physical buttons 0..4 are exactly what sdlButtonToSfButton() maps.
    print(f"  {len(actual)} MouseButton members present with correct values")


def test_input_state_inventory():
    print("Testing mcrfpy.InputState inventory...")
    assert hasattr(mcrfpy, "InputState"), "mcrfpy.InputState must exist"
    actual = _members(mcrfpy.InputState)

    missing = set(EXPECTED_INPUT_STATES) - set(actual)
    extra = set(actual) - set(EXPECTED_INPUT_STATES)
    assert not missing, f"InputState missing members: {sorted(missing)}"
    assert not extra, f"InputState has unexpected members: {sorted(extra)}"

    for name, val in EXPECTED_INPUT_STATES.items():
        assert actual[name] == val, f"InputState.{name} expected {val}, got {actual[name]}"
    print(f"  {len(actual)} InputState members present with correct values")


def test_ne_operator_gotcha():
    """IntEnum needs explicit __ne__ (known gotcha): int's inherited __ne__ broke
    string-name compares. Verify != behaves for same-enum and cross-type compares."""
    print("Testing __ne__ behavior (IntEnum gotcha)...")
    # Same enum
    assert mcrfpy.Key.A != mcrfpy.Key.ESCAPE
    assert not (mcrfpy.Key.A != mcrfpy.Key.A)
    assert mcrfpy.MouseButton.LEFT != mcrfpy.MouseButton.RIGHT
    assert not (mcrfpy.MouseButton.LEFT != mcrfpy.MouseButton.LEFT)
    assert mcrfpy.InputState.PRESSED != mcrfpy.InputState.RELEASED
    # Legacy string comparison removed (#306): != a string must be True, == False.
    assert mcrfpy.Key.ESCAPE != "Escape"
    assert mcrfpy.Key.ESCAPE != "ESCAPE"
    assert mcrfpy.MouseButton.LEFT != "left"
    assert mcrfpy.InputState.PRESSED != "start"
    assert not (mcrfpy.Key.ESCAPE == "ESCAPE")
    print("  __ne__ correct for same-enum and cross-type compares")


def test_text_and_modifier_surface():
    """The Python-visible #495/#496/#497 API exists on every backend (it is backend-agnostic)."""
    print("Testing text-entry / modifier / dev-hotkey surface...")
    from mcrfpy import automation
    assert hasattr(mcrfpy.Scene, "on_text"), "Scene.on_text must exist"
    assert hasattr(automation, "typeText"), "automation.typeText must exist"
    for name in ("console_key", "explorer_key"):
        assert hasattr(mcrfpy.Window, name), f"Window.{name} must exist"
    for name in ("shift", "ctrl", "alt", "system"):
        assert isinstance(getattr(mcrfpy.keyboard, name), bool), f"keyboard.{name} must be a bool"
    print("  on_text, typeText, console_key/explorer_key and keyboard modifiers present")


def test_text_entry_audit():
    """Static audit of the SDL2 TEXTINPUT translation (web cannot be run from here)."""
    print("Auditing SDL_TEXTINPUT translation (source)...")
    import os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
                        "src", "platform", "SDL2Renderer.cpp")
    with open(path, encoding="utf-8") as f:
        src = f.read()
    a = src.index("case SDL_TEXTINPUT")
    block = src[a:src.index("case SDL_MOUSEMOTION", a)]
    assert "next_codepoint" in block, "TEXTINPUT must decode every code point"
    assert "g_pendingText" in block, "extra code points must be queued, not dropped"
    assert "text.text[0]" not in block, "TEXTINPUT must not read only the first byte"
    poll = src[src.index("bool RenderWindow::pollEvent"):src.index("bool RenderWindow::waitEvent")]
    assert "g_pendingText" in poll, "pollEvent must drain the queued code points"
    kb = src[src.index("case SDL_KEYDOWN"):src.index("case SDL_TEXTINPUT")]
    for field in ("key.alt", "key.control", "key.shift", "key.system"):
        assert field in kb, f"SDL key events must carry {field} (#497)"
    print("  TEXTINPUT decodes all code points; key events carry all four modifiers")


def main():
    print("=" * 60)
    print("Input Parity Test (#389) -- Key / MouseButton / InputState")
    print("=" * 60)
    try:
        test_key_inventory()
        test_key_values_consistent()
        test_mouse_button_inventory()
        test_input_state_inventory()
        test_ne_operator_gotcha()
        test_text_and_modifier_surface()
        test_text_entry_audit()
        print()
        print("=" * 60)
        print("All tests PASSED")
        print("=" * 60)
        sys.exit(0)
    except AssertionError as e:
        print(f"\nTest FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
