#!/usr/bin/env python3
"""Test for Sound, Music, Keyboard classes and __version__ (#66, #160, #164)."""

import mcrfpy
import sys

def test_version():
    """Test that __version__ exists and is a valid semver string."""
    assert hasattr(mcrfpy, '__version__'), "mcrfpy.__version__ not found"
    version = mcrfpy.__version__
    assert isinstance(version, str), f"__version__ should be str, got {type(version)}"
    parts = version.split('.')
    assert len(parts) == 3, f"Version should be MAJOR.MINOR.PATCH, got {version}"
    print(f"  Version: {version}")

def test_keyboard():
    """Test Keyboard singleton exists and has expected properties."""
    assert hasattr(mcrfpy, 'keyboard'), "mcrfpy.keyboard not found"
    kb = mcrfpy.keyboard

    # Check all modifier properties exist and are bool
    for prop in ['shift', 'ctrl', 'alt', 'system']:
        assert hasattr(kb, prop), f"keyboard.{prop} not found"
        val = getattr(kb, prop)
        assert isinstance(val, bool), f"keyboard.{prop} should be bool, got {type(val)}"

    print(f"  Keyboard state: {kb}")

def test_sound_class():
    """Test Sound class creation and properties."""
    # Test with a known good file
    sound = mcrfpy.Sound("assets/sfx/splat1.ogg")

    # Check repr works
    repr_str = repr(sound)
    assert 'Sound' in repr_str
    assert 'splat1.ogg' in repr_str
    print(f"  Sound: {repr_str}")

    # Check default values
    assert sound.volume == 100.0, f"Default volume should be 100, got {sound.volume}"
    assert sound.loop == False, f"Default loop should be False, got {sound.loop}"
    assert sound.playing == False, f"Should not be playing initially"
    assert sound.duration > 0, f"Duration should be positive, got {sound.duration}"
    assert sound.source == "assets/sfx/splat1.ogg"

    # Test setting properties (use tolerance for floating point)
    sound.volume = 50.0
    assert abs(sound.volume - 50.0) < 0.01, f"Volume should be ~50, got {sound.volume}"

    sound.loop = True
    assert sound.loop == True

    # Test methods exist (don't actually play in headless)
    assert callable(sound.play)
    assert callable(sound.pause)
    assert callable(sound.stop)

    print(f"  Duration: {sound.duration:.3f}s")

def test_sound_error_handling():
    """Test Sound raises on invalid file."""
    try:
        sound = mcrfpy.Sound("nonexistent_file.ogg")
        print("  ERROR: Should have raised RuntimeError")
        return False
    except RuntimeError as e:
        print(f"  Correctly raised: {e}")
        return True

def test_music_class():
    """Test Music class creation and properties."""
    music = mcrfpy.Music("assets/sfx/splat1.ogg")

    # Check repr works
    repr_str = repr(music)
    assert 'Music' in repr_str
    print(f"  Music: {repr_str}")

    # Check default values
    assert music.volume == 100.0, f"Default volume should be 100, got {music.volume}"
    assert music.loop == False, f"Default loop should be False, got {music.loop}"
    assert music.playing == False, f"Should not be playing initially, got {music.playing}"
    assert music.duration > 0, f"Duration should be positive, got {music.duration}"
    # Position comparison needs tolerance for floating point
    assert abs(music.position) < 0.001, f"Position should be ~0, got {music.position}"
    assert music.source == "assets/sfx/splat1.ogg", f"Source mismatch: {music.source}"

    # Test setting properties (use tolerance for floating point)
    music.volume = 30.0
    assert abs(music.volume - 30.0) < 0.01, f"Volume should be ~30, got {music.volume}"

    music.loop = True
    assert music.loop == True, f"Loop should be True, got {music.loop}"

    # Test position can be set (seek)
    # Can't really test this without playing, but check it's writable
    music.position = 0.1

    print(f"  Duration: {music.duration:.3f}s")

def test_music_error_handling():
    """Test Music raises on invalid file."""
    try:
        music = mcrfpy.Music("nonexistent_file.ogg")
        print("  ERROR: Should have raised RuntimeError")
        return False
    except RuntimeError as e:
        print(f"  Correctly raised: {e}")
        return True

def main():
    print("Testing mcrfpy audio and keyboard features (#66, #160, #164)")
    print()

    tests = [
        ("__version__", test_version),
        ("keyboard singleton", test_keyboard),
        ("Sound class", test_sound_class),
        ("Sound error handling", test_sound_error_handling),
        ("Music class", test_music_class),
        ("Music error handling", test_music_error_handling),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        print(f"Testing {name}...")
        try:
            result = test_fn()
            if result is False:
                failed += 1
                print(f"  FAILED")
            else:
                passed += 1
                print(f"  PASSED")
        except Exception as e:
            failed += 1
            print(f"  FAILED: {e}")

    print()
    print(f"Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("PASS")
        sys.exit(0)
    else:
        print("FAIL")
        sys.exit(1)

if __name__ == "__main__":
    main()
