"""Regression test for #342 - Animation scalar-float fast path.

The animation hot path was optimized to bypass two per-frame std::variant
std::visit dispatches (interpolate() + applyValue()) for scalar-float
animations (x, y, w, h, opacity, rotation, color channels, ...). This test
verifies that the fast path produces the SAME interpolated values as the
general path -- i.e. the optimization is behavior-preserving.

Direct-execution style with headless mcrfpy.step() to advance animations.
"""
import mcrfpy
import sys


def approx(a, b, tol=0.5):
    return abs(a - b) < tol


def main():
    scene = mcrfpy.Scene("t342")
    mcrfpy.current_scene = scene
    f = mcrfpy.Frame(pos=(0, 0), size=(50, 50))
    f.fill_color = mcrfpy.Color(10, 20, 30, 0)
    scene.children.append(f)

    # Scalar-float property animations (these hit the #342 fast path)
    f.animate("x", 100.0, 10.0, mcrfpy.Easing.LINEAR)       # 0 -> 100
    f.animate("opacity", 0.0, 10.0, mcrfpy.Easing.LINEAR)   # 1.0 -> 0.0
    f.animate("fill_color.a", 200.0, 10.0, mcrfpy.Easing.LINEAR)  # 0 -> 200, deep name

    # Halfway (linear): each property at 50%
    mcrfpy.step(5.0)
    assert approx(f.x, 50.0), f"x halfway: {f.x}"
    assert approx(f.opacity, 0.5, 0.02), f"opacity halfway: {f.opacity}"
    assert approx(f.fill_color.a, 100.0, 1.5), f"fill_color.a halfway: {f.fill_color.a}"

    # Complete
    mcrfpy.step(5.0)
    assert approx(f.x, 100.0), f"x end: {f.x}"
    assert approx(f.opacity, 0.0, 0.02), f"opacity end: {f.opacity}"
    assert approx(f.fill_color.a, 200.0, 1.5), f"fill_color.a end: {f.fill_color.a}"

    # A non-linear easing still lands exactly on the target (fast path end value)
    f2 = mcrfpy.Frame(pos=(0, 0), size=(10, 10))
    scene.children.append(f2)
    f2.animate("y", 42.0, 4.0, mcrfpy.Easing.EASE_IN_OUT)
    mcrfpy.step(4.0)
    assert approx(f2.y, 42.0), f"eased y end: {f2.y}"

    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
