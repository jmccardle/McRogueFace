"""
Unit tests for the geometry module (Pinships orbital mechanics).

Tests cover:
- Basic utility functions (distance, angle, etc.)
- Bresenham circle/line algorithms
- OrbitalBody recursive positioning
- Pathfinding helpers
"""

import sys
import math

# Import the geometry module
sys.path.insert(0, '/home/john/Development/McRogueFace/src/scripts')
from geometry import (
    # Utilities
    distance, distance_squared, angle_between, normalize_angle,
    angle_difference, lerp, clamp, point_on_circle, rotate_point,
    # Grid algorithms
    bresenham_circle, bresenham_line, filled_circle, sort_circle_cells,
    # Orbital system
    OrbitalBody, OrbitingShip,
    # Pathfinding
    nearest_orbit_entry, optimal_exit_heading, is_viable_waypoint,
    project_body_positions, line_of_sight_blocked,
    # Convenience
    create_solar_system, create_planet, create_moon
)

EPSILON = 0.0001  # Float comparison tolerance

def approx_equal(a, b, eps=EPSILON):
    """Check if two floats are approximately equal."""
    return abs(a - b) < eps

def test_distance():
    """Test distance calculations."""
    assert approx_equal(distance((0, 0), (3, 4)), 5.0)
    assert approx_equal(distance((0, 0), (0, 0)), 0.0)
    assert approx_equal(distance((1, 1), (4, 5)), 5.0)
    assert approx_equal(distance((-3, -4), (0, 0)), 5.0)
    print("  distance: PASS")

def test_distance_squared():
    """Test squared distance (no sqrt)."""
    assert distance_squared((0, 0), (3, 4)) == 25
    assert distance_squared((0, 0), (0, 0)) == 0
    print("  distance_squared: PASS")

def test_angle_between():
    """Test angle calculations."""
    # East = 0 degrees
    assert approx_equal(angle_between((0, 0), (1, 0)), 0.0)
    # North = 90 degrees (in screen coordinates, +y is down, but atan2 treats +y as up)
    assert approx_equal(angle_between((0, 0), (0, 1)), 90.0)
    # West = 180 degrees
    assert approx_equal(angle_between((0, 0), (-1, 0)), 180.0)
    # South = 270 degrees
    assert approx_equal(angle_between((0, 0), (0, -1)), 270.0)
    # Diagonal
    assert approx_equal(angle_between((0, 0), (1, 1)), 45.0)
    print("  angle_between: PASS")

def test_normalize_angle():
    """Test angle normalization to 0-360."""
    assert approx_equal(normalize_angle(0), 0.0)
    assert approx_equal(normalize_angle(360), 0.0)
    assert approx_equal(normalize_angle(720), 0.0)
    assert approx_equal(normalize_angle(-90), 270.0)
    assert approx_equal(normalize_angle(-360), 0.0)
    assert approx_equal(normalize_angle(450), 90.0)
    print("  normalize_angle: PASS")

def test_angle_difference():
    """Test shortest angular distance."""
    assert approx_equal(angle_difference(0, 90), 90.0)
    assert approx_equal(angle_difference(90, 0), -90.0)
    assert approx_equal(angle_difference(350, 10), 20.0)  # Wrap around
    assert approx_equal(angle_difference(10, 350), -20.0)
    assert approx_equal(angle_difference(0, 180), 180.0)
    print("  angle_difference: PASS")

def test_lerp():
    """Test linear interpolation."""
    assert approx_equal(lerp(0, 10, 0.0), 0.0)
    assert approx_equal(lerp(0, 10, 1.0), 10.0)
    assert approx_equal(lerp(0, 10, 0.5), 5.0)
    assert approx_equal(lerp(-5, 5, 0.5), 0.0)
    print("  lerp: PASS")

def test_clamp():
    """Test value clamping."""
    assert clamp(5, 0, 10) == 5
    assert clamp(-5, 0, 10) == 0
    assert clamp(15, 0, 10) == 10
    assert clamp(0, 0, 10) == 0
    assert clamp(10, 0, 10) == 10
    print("  clamp: PASS")

def test_point_on_circle():
    """Test point calculation on circle."""
    center = (100, 100)
    radius = 50

    # East (0 degrees)
    p = point_on_circle(center, radius, 0)
    assert approx_equal(p[0], 150.0)
    assert approx_equal(p[1], 100.0)

    # North (90 degrees)
    p = point_on_circle(center, radius, 90)
    assert approx_equal(p[0], 100.0)
    assert approx_equal(p[1], 150.0)

    # West (180 degrees)
    p = point_on_circle(center, radius, 180)
    assert approx_equal(p[0], 50.0)
    assert approx_equal(p[1], 100.0)

    print("  point_on_circle: PASS")

def test_rotate_point():
    """Test point rotation around center."""
    center = (0, 0)
    point = (1, 0)

    # Rotate 90 degrees
    p = rotate_point(point, center, 90)
    assert approx_equal(p[0], 0.0)
    assert approx_equal(p[1], 1.0)

    # Rotate 180 degrees
    p = rotate_point(point, center, 180)
    assert approx_equal(p[0], -1.0)
    assert approx_equal(p[1], 0.0)

    print("  rotate_point: PASS")

def test_bresenham_circle():
    """Test Bresenham circle generation."""
    # Radius 0 = just the center
    cells = bresenham_circle((5, 5), 0)
    assert cells == [(5, 5)]

    # Radius 3 should give a circle-ish shape
    cells = bresenham_circle((10, 10), 3)
    assert len(cells) > 0

    # All cells should be roughly radius distance from center
    for x, y in cells:
        dist = math.sqrt((x - 10) ** 2 + (y - 10) ** 2)
        assert 2.5 <= dist <= 3.5, f"Cell ({x},{y}) has distance {dist}"

    # Should be symmetric
    cells_set = set(cells)
    for x, y in cells:
        # Check all 4 quadrant reflections exist
        dx, dy = x - 10, y - 10
        assert (10 + dx, 10 + dy) in cells_set
        assert (10 - dx, 10 + dy) in cells_set
        assert (10 + dx, 10 - dy) in cells_set
        assert (10 - dx, 10 - dy) in cells_set

    print("  bresenham_circle: PASS")

def test_bresenham_line():
    """Test Bresenham line generation."""
    # Horizontal line
    cells = bresenham_line((0, 0), (5, 0))
    assert cells == [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0)]

    # Vertical line
    cells = bresenham_line((0, 0), (0, 3))
    assert cells == [(0, 0), (0, 1), (0, 2), (0, 3)]

    # Diagonal line
    cells = bresenham_line((0, 0), (3, 3))
    assert (0, 0) in cells
    assert (3, 3) in cells
    assert len(cells) == 4  # Should hit 4 cells for 45-degree line

    # Start and end should be included
    cells = bresenham_line((10, 20), (15, 22))
    assert (10, 20) in cells
    assert (15, 22) in cells

    print("  bresenham_line: PASS")

def test_filled_circle():
    """Test filled circle generation."""
    cells = filled_circle((5, 5), 2)

    # Center should be included
    assert (5, 5) in cells

    # Edges should be included
    assert (5, 3) in cells  # top
    assert (5, 7) in cells  # bottom
    assert (3, 5) in cells  # left
    assert (7, 5) in cells  # right

    # Corners (at distance sqrt(8) ≈ 2.83) should NOT be included for radius 2
    assert (3, 3) not in cells

    print("  filled_circle: PASS")

def test_orbital_body_stationary():
    """Test stationary body (star) positioning."""
    star = OrbitalBody(
        name="Star",
        surface_radius=10,
        orbit_ring_radius=15,
        parent=None,
        base_position=(500, 500)
    )

    # Position should never change
    assert star.grid_position_at_time(0) == (500, 500)
    assert star.grid_position_at_time(100) == (500, 500)
    assert star.grid_position_at_time(9999) == (500, 500)

    # Continuous position should match
    assert star.center_at_time(0) == (500.0, 500.0)

    print("  orbital_body_stationary: PASS")

def test_orbital_body_simple_orbit():
    """Test planet orbiting a star."""
    star = OrbitalBody(
        name="Star",
        surface_radius=10,
        orbit_ring_radius=15,
        parent=None,
        base_position=(500, 500)
    )

    planet = OrbitalBody(
        name="Planet",
        surface_radius=5,
        orbit_ring_radius=10,
        parent=star,
        orbital_radius=100,  # 100 units from star
        angular_velocity=90,  # 90 degrees per turn (quarter orbit)
        initial_angle=0  # Start to the east
    )

    # t=0: Planet should be east of star
    pos0 = planet.center_at_time(0)
    assert approx_equal(pos0[0], 600.0)  # 500 + 100
    assert approx_equal(pos0[1], 500.0)

    # t=1: Planet should be north of star (rotated 90 degrees)
    pos1 = planet.center_at_time(1)
    assert approx_equal(pos1[0], 500.0)
    assert approx_equal(pos1[1], 600.0)  # 500 + 100

    # t=2: Planet should be west of star
    pos2 = planet.center_at_time(2)
    assert approx_equal(pos2[0], 400.0)  # 500 - 100
    assert approx_equal(pos2[1], 500.0)

    # t=4: Back to start (full orbit)
    pos4 = planet.center_at_time(4)
    assert approx_equal(pos4[0], 600.0)
    assert approx_equal(pos4[1], 500.0)

    print("  orbital_body_simple_orbit: PASS")

def test_orbital_body_nested_orbit():
    """Test moon orbiting a planet orbiting a star."""
    star = OrbitalBody(
        name="Star",
        surface_radius=10,
        orbit_ring_radius=15,
        parent=None,
        base_position=(500, 500)
    )

    planet = OrbitalBody(
        name="Planet",
        surface_radius=5,
        orbit_ring_radius=10,
        parent=star,
        orbital_radius=100,
        angular_velocity=90,  # Quarter orbit per turn
        initial_angle=0
    )

    moon = OrbitalBody(
        name="Moon",
        surface_radius=2,
        orbit_ring_radius=5,
        parent=planet,
        orbital_radius=20,  # 20 units from planet
        angular_velocity=180,  # Half orbit per turn (faster than planet)
        initial_angle=0
    )

    # t=0: Moon should be east of planet, which is east of star
    moon_pos0 = moon.center_at_time(0)
    # Planet at (600, 500), moon 20 units east = (620, 500)
    assert approx_equal(moon_pos0[0], 620.0)
    assert approx_equal(moon_pos0[1], 500.0)

    # t=1: Planet moved north (500, 600), moon rotated 180 degrees (west of planet)
    moon_pos1 = moon.center_at_time(1)
    # Planet at (500, 600), moon 20 units west = (480, 600)
    assert approx_equal(moon_pos1[0], 480.0)
    assert approx_equal(moon_pos1[1], 600.0)

    print("  orbital_body_nested_orbit: PASS")

def test_orbiting_ship():
    """Test ship orbiting a body."""
    star = OrbitalBody(
        name="Star",
        surface_radius=10,
        orbit_ring_radius=50,
        parent=None,
        base_position=(500, 500)
    )

    ship = OrbitingShip(body=star, orbital_angle=0)

    # Ship at angle 0 should be east of star
    pos = ship.grid_position_at_time(0)
    assert pos == (550, 500)  # 500 + 50

    # Move ship along orbit
    ship.move_along_orbit(90)
    pos = ship.grid_position_at_time(0)
    assert pos == (500, 550)  # North of star

    # Set specific angle
    ship.set_orbit_angle(180)
    pos = ship.grid_position_at_time(0)
    assert pos == (450, 500)  # West of star

    print("  orbiting_ship: PASS")

def test_orbit_ring_cells():
    """Test orbit ring cell generation."""
    body = OrbitalBody(
        name="Planet",
        surface_radius=5,
        orbit_ring_radius=10,
        parent=None,
        base_position=(100, 100)
    )

    cells = body.orbit_ring_cells(0)

    # Should have cells on the ring
    assert len(cells) > 0

    # All cells should be approximately orbit_ring_radius from center
    for x, y in cells:
        dist = math.sqrt((x - 100) ** 2 + (y - 100) ** 2)
        assert 9.0 <= dist <= 11.0, f"Cell ({x},{y}) has distance {dist}"

    print("  orbit_ring_cells: PASS")

def test_surface_cells():
    """Test surface cell generation."""
    body = OrbitalBody(
        name="Planet",
        surface_radius=3,
        orbit_ring_radius=10,
        parent=None,
        base_position=(50, 50)
    )

    cells = body.surface_cells(0)

    # Center should be included
    assert (50, 50) in cells

    # All cells should be within surface_radius
    for x, y in cells:
        dist = math.sqrt((x - 50) ** 2 + (y - 50) ** 2)
        assert dist <= 3.5, f"Cell ({x},{y}) has distance {dist}"

    print("  surface_cells: PASS")

def test_nearest_orbit_entry():
    """Test finding nearest orbit entry point."""
    body = OrbitalBody(
        name="Planet",
        surface_radius=5,
        orbit_ring_radius=20,
        parent=None,
        base_position=(100, 100)
    )

    # Ship approaching from east
    ship_pos = (150, 100)
    entry_pos, angle = nearest_orbit_entry(ship_pos, body, 0)

    # Entry should be on the east side of orbit ring
    assert approx_equal(angle, 0.0)
    assert entry_pos == (120, 100)  # 100 + 20

    # Ship approaching from north-east
    ship_pos = (150, 150)
    entry_pos, angle = nearest_orbit_entry(ship_pos, body, 0)
    assert approx_equal(angle, 45.0)

    print("  nearest_orbit_entry: PASS")

def test_optimal_exit_heading():
    """Test finding optimal orbit exit toward target."""
    body = OrbitalBody(
        name="Planet",
        surface_radius=5,
        orbit_ring_radius=20,
        parent=None,
        base_position=(100, 100)
    )

    # Target to the west
    target = (0, 100)
    exit_angle, exit_pos = optimal_exit_heading(body, target, 0)

    assert approx_equal(exit_angle, 180.0)
    assert exit_pos == (80, 100)  # 100 - 20

    print("  optimal_exit_heading: PASS")

def test_is_viable_waypoint():
    """Test waypoint viability check."""
    body = OrbitalBody(
        name="Planet",
        surface_radius=5,
        orbit_ring_radius=10,
        parent=None,
        base_position=(100, 100)
    )

    ship_pos = (50, 100)  # West of body
    target_east = (200, 100)  # Far east
    target_west = (0, 100)  # Far west

    # Body is between ship and eastern target - viable
    assert is_viable_waypoint(ship_pos, body, target_east, 0, angle_threshold=90)

    # Body is NOT between ship and western target - not viable
    assert not is_viable_waypoint(ship_pos, body, target_west, 0, angle_threshold=45)

    print("  is_viable_waypoint: PASS")

def test_line_of_sight_blocked():
    """Test line of sight blocking by bodies."""
    blocker = OrbitalBody(
        name="Planet",
        surface_radius=10,
        orbit_ring_radius=20,
        parent=None,
        base_position=(100, 100)
    )

    # LOS through the planet should be blocked
    p1 = (50, 100)
    p2 = (150, 100)
    result = line_of_sight_blocked(p1, p2, [blocker], 0)
    assert result == blocker

    # LOS around the planet should be clear
    p1 = (50, 50)
    p2 = (150, 50)
    result = line_of_sight_blocked(p1, p2, [blocker], 0)
    assert result is None

    print("  line_of_sight_blocked: PASS")

def test_convenience_functions():
    """Test solar system creation helpers."""
    star = create_solar_system(1000, 1000, star_radius=15, star_orbit_radius=25)

    assert star.name == "Star"
    assert star.base_position == (500, 500)
    assert star.surface_radius == 15
    assert star.orbit_ring_radius == 25
    assert star.parent is None

    planet = create_planet(
        name="Terra",
        star=star,
        orbital_radius=200,
        surface_radius=10,
        orbit_ring_radius=20,
        angular_velocity=10,
        initial_angle=45
    )

    assert planet.name == "Terra"
    assert planet.parent == star
    assert planet.orbital_radius == 200

    moon = create_moon(
        name="Luna",
        planet=planet,
        orbital_radius=30,
        surface_radius=3,
        orbit_ring_radius=8,
        angular_velocity=30
    )

    assert moon.name == "Luna"
    assert moon.parent == planet

    print("  convenience_functions: PASS")

def test_discrete_movement():
    """Test that grid positions change at discrete thresholds."""
    star = OrbitalBody(
        name="Star",
        surface_radius=10,
        orbit_ring_radius=15,
        parent=None,
        base_position=(500, 500)
    )

    # Planet with moderate angular velocity
    planet = OrbitalBody(
        name="Planet",
        surface_radius=5,
        orbit_ring_radius=10,
        parent=star,
        orbital_radius=100,
        angular_velocity=1.0,  # 1 degree per turn
        initial_angle=0
    )

    # Positions should be deterministic
    pos0 = planet.grid_position_at_time(0)
    pos10 = planet.grid_position_at_time(10)
    pos10_again = planet.grid_position_at_time(10)

    # Same time = same position (deterministic)
    assert pos10 == pos10_again

    # Position should change over time
    assert pos0 != pos10

    # Full orbit (360 degrees / 1 deg per turn = 360 turns) should return to start
    pos360 = planet.grid_position_at_time(360)
    assert pos0 == pos360

    # Check the turns_until_position_changes function
    turns = planet.turns_until_position_changes(0)
    assert turns >= 1  # Should eventually change

    # Verify it actually changes at that turn
    pos_before = planet.grid_position_at_time(0)
    pos_after = planet.grid_position_at_time(turns)
    assert pos_before != pos_after

    print("  discrete_movement: PASS")

def run_all_tests():
    """Run all geometry tests."""
    print("Running geometry module tests...\n")

    print("Utility functions:")
    test_distance()
    test_distance_squared()
    test_angle_between()
    test_normalize_angle()
    test_angle_difference()
    test_lerp()
    test_clamp()
    test_point_on_circle()
    test_rotate_point()

    print("\nGrid algorithms:")
    test_bresenham_circle()
    test_bresenham_line()
    test_filled_circle()

    print("\nOrbital body system:")
    test_orbital_body_stationary()
    test_orbital_body_simple_orbit()
    test_orbital_body_nested_orbit()
    test_orbiting_ship()
    test_orbit_ring_cells()
    test_surface_cells()
    test_discrete_movement()

    print("\nPathfinding helpers:")
    test_nearest_orbit_entry()
    test_optimal_exit_heading()
    test_is_viable_waypoint()
    test_line_of_sight_blocked()

    print("\nConvenience functions:")
    test_convenience_functions()

    print("\n" + "=" * 50)
    print("All geometry tests PASSED!")
    print("=" * 50)

if __name__ == "__main__":
    run_all_tests()
