"""Fuzz target for grid Field-of-View computation (#283).

Exercises ``UIGrid.compute_fov`` / ``UIGrid.is_in_fov`` and the underlying
TCOD FOV state. The mutation surface intentionally hammers:

- transparency / walkability toggles between consecutive computes
  (catches stale FOV state bugs)
- in-bounds and out-of-bounds origins (must raise, not crash)
- radius edge cases: 0, normal, far larger than the grid
- ``light_walls`` flag flipping
- every value of the ``mcrfpy.FOV`` enum (BASIC, DIAMOND, SHADOW,
  PERMISSIVE_0..8, RESTRICTIVE, SYMMETRIC_SHADOWCAST) and raw int values
  including out-of-range integers (must raise ValueError, not crash)
- alternating compute/query loops where the origin walks across the grid

Grid sizes are kept small (2x2 .. 32x32) because compute_fov is the
per-iteration hot path here.
"""

import mcrfpy

from fuzz_common import ByteStream, EXPECTED_EXCEPTIONS, safe_reset


def _get_fov_enum_members():
    """Snapshot mcrfpy.FOV enum members once at import time.

    Returns a list of FOV enum instances. Falls back to integers if the
    enum module is unavailable for any reason — the C++ binding accepts
    raw ints too, so the fuzz target stays functional either way.
    """
    fov = getattr(mcrfpy, "FOV", None)
    if fov is None:
        return list(range(15))  # FOV_BASIC..NB_FOV_ALGORITHMS-1
    members = []
    for name in (
        "BASIC", "DIAMOND", "SHADOW",
        "PERMISSIVE_0", "PERMISSIVE_1", "PERMISSIVE_2", "PERMISSIVE_3",
        "PERMISSIVE_4", "PERMISSIVE_5", "PERMISSIVE_6", "PERMISSIVE_7",
        "PERMISSIVE_8",
        "RESTRICTIVE", "SYMMETRIC_SHADOWCAST",
    ):
        m = getattr(fov, name, None)
        if m is not None:
            members.append(m)
    if not members:
        return list(range(15))
    return members


_FOV_MEMBERS = _get_fov_enum_members()


def _make_grid(stream):
    """Create a fresh small grid and return (grid, w, h)."""
    w = stream.int_in_range(2, 32)
    h = stream.int_in_range(2, 32)
    grid = mcrfpy.Grid(grid_size=(w, h))
    return grid, w, h


def fuzz_one_input(data):
    stream = ByteStream(data)
    try:
        grid, w, h = _make_grid(stream)

        n_ops = stream.int_in_range(1, 30)
        for _ in range(n_ops):
            if stream.remaining < 1:
                break
            op = stream.u8() % 16
            try:
                if op == 0:
                    # Replace the active grid (drop the old one).
                    grid, w, h = _make_grid(stream)

                elif op == 1:
                    # Set transparent on a possibly-OOB cell.
                    x = stream.int_in_range(-5, w + 5)
                    y = stream.int_in_range(-5, h + 5)
                    grid.at(x, y).transparent = stream.bool()

                elif op == 2:
                    # Set walkable on a possibly-OOB cell.
                    x = stream.int_in_range(-5, w + 5)
                    y = stream.int_in_range(-5, h + 5)
                    grid.at(x, y).walkable = stream.bool()

                elif op == 3:
                    # In-bounds compute_fov with reasonable radius.
                    x = stream.int_in_range(0, max(0, w - 1))
                    y = stream.int_in_range(0, max(0, h - 1))
                    radius = stream.int_in_range(0, 20)
                    grid.compute_fov((x, y), radius=radius)

                elif op == 4:
                    # Out-of-bounds origin: must raise, not crash.
                    sign_x = -1 if stream.bool() else 1
                    sign_y = -1 if stream.bool() else 1
                    x = sign_x * stream.int_in_range(0, w + 5)
                    y = sign_y * stream.int_in_range(0, h + 5)
                    if 0 <= x < w and 0 <= y < h:
                        # Force OOB even if randomness lined up in-bounds.
                        x = w + 1
                    radius = stream.int_in_range(0, 10)
                    grid.compute_fov((x, y), radius=radius)

                elif op == 5:
                    # Radius 0 — degenerate case.
                    x = stream.int_in_range(0, max(0, w - 1))
                    y = stream.int_in_range(0, max(0, h - 1))
                    grid.compute_fov((x, y), radius=0)

                elif op == 6:
                    # Extreme radius (far larger than grid).
                    x = stream.int_in_range(0, max(0, w - 1))
                    y = stream.int_in_range(0, max(0, h - 1))
                    radius = stream.int_in_range(50, 1000)
                    grid.compute_fov((x, y), radius=radius)

                elif op == 7:
                    # light_walls toggle.
                    x = stream.int_in_range(0, max(0, w - 1))
                    y = stream.int_in_range(0, max(0, h - 1))
                    radius = stream.int_in_range(0, 15)
                    grid.compute_fov(
                        (x, y),
                        radius=radius,
                        light_walls=stream.bool(),
                    )

                elif op == 8:
                    # Random algorithm selection (valid enum or int).
                    x = stream.int_in_range(0, max(0, w - 1))
                    y = stream.int_in_range(0, max(0, h - 1))
                    radius = stream.int_in_range(0, 15)
                    algo = stream.pick_one(_FOV_MEMBERS)
                    grid.compute_fov(
                        (x, y),
                        radius=radius,
                        light_walls=stream.bool(),
                        algorithm=algo,
                    )

                elif op == 9:
                    # Out-of-range raw int algorithm — must raise ValueError.
                    x = stream.int_in_range(0, max(0, w - 1))
                    y = stream.int_in_range(0, max(0, h - 1))
                    bad_algo = stream.int_in_range(-50, 200)
                    grid.compute_fov(
                        (x, y), radius=5, algorithm=bad_algo
                    )

                elif op == 10:
                    # is_in_fov with possibly-OOB coords.
                    x = stream.int_in_range(-5, w + 5)
                    y = stream.int_in_range(-5, h + 5)
                    _ = grid.is_in_fov(x, y)

                elif op == 11:
                    # Tight loop: 20x compute + query against a moving origin.
                    base_x = stream.int_in_range(0, max(0, w - 1))
                    base_y = stream.int_in_range(0, max(0, h - 1))
                    radius = stream.int_in_range(1, 8)
                    for i in range(20):
                        ox = (base_x + i) % w
                        oy = (base_y + i) % h
                        try:
                            grid.compute_fov((ox, oy), radius=radius)
                            _ = grid.is_in_fov(ox, oy)
                            if w > 1:
                                _ = grid.is_in_fov((ox + 1) % w, oy)
                        except EXPECTED_EXCEPTIONS:
                            pass

                elif op == 12:
                    # Toggle ~20 cells' transparency, recompute, query.
                    n_toggles = stream.int_in_range(1, 20)
                    for _ in range(n_toggles):
                        tx = stream.int_in_range(0, max(0, w - 1))
                        ty = stream.int_in_range(0, max(0, h - 1))
                        try:
                            grid.at(tx, ty).transparent = stream.bool()
                        except EXPECTED_EXCEPTIONS:
                            pass
                    ox = stream.int_in_range(0, max(0, w - 1))
                    oy = stream.int_in_range(0, max(0, h - 1))
                    grid.compute_fov((ox, oy), radius=stream.int_in_range(1, 15))
                    # Query a handful of cells, including OOB.
                    for _ in range(5):
                        qx = stream.int_in_range(-2, w + 2)
                        qy = stream.int_in_range(-2, h + 2)
                        try:
                            _ = grid.is_in_fov(qx, qy)
                        except EXPECTED_EXCEPTIONS:
                            pass
                    # More toggles, recompute, requery.
                    for _ in range(stream.int_in_range(1, 10)):
                        tx = stream.int_in_range(0, max(0, w - 1))
                        ty = stream.int_in_range(0, max(0, h - 1))
                        try:
                            grid.at(tx, ty).transparent = stream.bool()
                        except EXPECTED_EXCEPTIONS:
                            pass
                    ox = stream.int_in_range(0, max(0, w - 1))
                    oy = stream.int_in_range(0, max(0, h - 1))
                    grid.compute_fov((ox, oy), radius=stream.int_in_range(0, 25))
                    for _ in range(5):
                        qx = stream.int_in_range(-2, w + 2)
                        qy = stream.int_in_range(-2, h + 2)
                        try:
                            _ = grid.is_in_fov(qx, qy)
                        except EXPECTED_EXCEPTIONS:
                            pass

                elif op == 13:
                    # Read-only properties: fov_radius, perspective.
                    try:
                        _ = grid.fov_radius
                    except EXPECTED_EXCEPTIONS:
                        pass
                    try:
                        grid.fov_radius = stream.int_in_range(-5, 50)
                    except EXPECTED_EXCEPTIONS:
                        pass
                    try:
                        _ = grid.perspective
                    except EXPECTED_EXCEPTIONS:
                        pass

                elif op == 14:
                    # Type-confusion: pass garbage as pos / radius / algorithm.
                    bad_choice = stream.u8() % 5
                    if bad_choice == 0:
                        grid.compute_fov(None, radius=5)
                    elif bad_choice == 1:
                        grid.compute_fov("not a tuple", radius=5)
                    elif bad_choice == 2:
                        grid.compute_fov((1, 2, 3), radius=5)
                    elif bad_choice == 3:
                        x = stream.int_in_range(0, max(0, w - 1))
                        y = stream.int_in_range(0, max(0, h - 1))
                        grid.compute_fov((x, y), radius="five")
                    else:
                        x = stream.int_in_range(0, max(0, w - 1))
                        y = stream.int_in_range(0, max(0, h - 1))
                        grid.compute_fov((x, y), radius=5, algorithm="basic")

                else:  # op == 15
                    # is_in_fov garbage args.
                    bad_choice = stream.u8() % 3
                    if bad_choice == 0:
                        _ = grid.is_in_fov(None, None)
                    elif bad_choice == 1:
                        _ = grid.is_in_fov("a", "b")
                    else:
                        _ = grid.is_in_fov((1, 2, 3))

            except EXPECTED_EXCEPTIONS:
                pass
    except EXPECTED_EXCEPTIONS:
        pass


# When invoked directly via --exec (smoke test path), run a single iteration
# against a tiny canned input so the script is self-contained.
if __name__ == "__main__":
    import sys

    safe_reset()
    fuzz_one_input(b"\x05\x05\x10\x03\x02\x02\x05\x07\x01\x01\x01\x0c\x03\x03\x05")
    print("PASS")
    sys.exit(0)
