"""Regression test: UniformCollection must check owner validity.

Issue #272: PyUniformCollectionObject stored a raw pointer to UniformCollection
but only checked non-NULL. If the owning UIDrawable was destroyed, the raw
pointer dangled, causing use-after-free.

Fix: Added weak_ptr<void> owner field. All accessors now check owner.lock()
before accessing the collection, raising RuntimeError if the owner is gone.
"""
import mcrfpy
import gc
import sys

def test_uniforms_basic_access():
    """Uniform collection should work when owner is alive."""
    frame = mcrfpy.Frame(pos=(0, 0), size=(100, 100))
    u = frame.uniforms
    assert len(u) == 0, f"Expected empty uniforms, got {len(u)}"

    u['brightness'] = 1.0
    assert len(u) == 1, f"Expected 1 uniform, got {len(u)}"
    assert 'brightness' in u, "brightness should be in uniforms"

    del u['brightness']
    assert len(u) == 0, f"Expected 0 after delete, got {len(u)}"

    print("  PASS: basic uniform access")

def test_uniforms_owner_destroyed():
    """Accessing uniforms after owner destruction must fail gracefully."""
    frame = mcrfpy.Frame(pos=(0, 0), size=(100, 100))
    u = frame.uniforms
    u['test'] = 1.0

    del frame
    gc.collect()

    # len() and __contains__ return 0/False gracefully
    assert len(u) == 0, f"len should be 0 after owner destroyed, got {len(u)}"
    assert 'test' not in u, "'test' should not be found after owner destroyed"

    # Subscript access and assignment raise RuntimeError
    errors = 0
    try:
        _ = u['test']
    except RuntimeError:
        errors += 1

    try:
        u['new'] = 2.0
    except RuntimeError:
        errors += 1

    assert errors == 2, f"Expected 2 RuntimeErrors from subscript ops, got {errors}"
    print("  PASS: uniforms after owner destroyed")

def test_uniforms_owner_in_scene():
    """Uniforms should work while owner is in a scene's children."""
    scene = mcrfpy.Scene("uniform_test")
    frame = mcrfpy.Frame(pos=(0, 0), size=(100, 100))
    scene.children.append(frame)
    u = frame.uniforms
    u['value'] = 0.5
    assert len(u) == 1, "Uniform should be accessible while in scene"
    print("  PASS: uniforms with scene-owned frame")

def test_uniforms_multiple_values():
    """Multiple uniform types should work correctly."""
    frame = mcrfpy.Frame(pos=(0, 0), size=(100, 100))
    u = frame.uniforms

    u['f'] = 1.0
    u['v2'] = (1.0, 2.0)
    u['v3'] = (1.0, 2.0, 3.0)
    u['v4'] = (1.0, 2.0, 3.0, 4.0)

    assert len(u) == 4, f"Expected 4 uniforms, got {len(u)}"

    keys = list(u.keys())
    assert len(keys) == 4, f"Expected 4 keys, got {len(keys)}"

    print("  PASS: multiple uniform types")

print("Testing issue #272: UniformCollection owner validity...")
test_uniforms_basic_access()
test_uniforms_owner_destroyed()
test_uniforms_owner_in_scene()
test_uniforms_multiple_values()
print("All #272 tests passed.")
sys.exit(0)
