"""
Geometry module for turn-based games with orbital mechanics.

Designed for Pinships but reusable for any game needing:
- Circular orbit calculations
- Grid-aligned geometric primitives
- Recursive celestial body positioning
- Pathfinding helpers for orbital navigation

Philosophy: "C++ every frame, Python every game step"
This module handles game logic, not rendering.
"""

from __future__ import annotations
import math
from typing import Optional, List, Tuple, Set
from dataclasses import dataclass, field


# =============================================================================
# Basic Utility Functions
# =============================================================================

def distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Euclidean distance between two points."""
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return math.sqrt(dx * dx + dy * dy)


def distance_squared(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Squared distance (avoids sqrt, useful for comparisons)."""
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return dx * dx + dy * dy


def angle_between(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """
    Angle from p1 to p2 in degrees (0-360).
    0 degrees = east (+x), 90 = north (+y in screen coords, or south in math coords).
    """
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    angle = math.degrees(math.atan2(dy, dx))
    return normalize_angle(angle)


def normalize_angle(angle: float) -> float:
    """Normalize angle to 0-360 range."""
    angle = angle % 360
    if angle < 0:
        angle += 360
    return angle


def angle_difference(a1: float, a2: float) -> float:
    """
    Shortest angular distance between two angles (signed, -180 to 180).
    Positive = counterclockwise from a1 to a2.
    """
    diff = normalize_angle(a2) - normalize_angle(a1)
    if diff > 180:
        diff -= 360
    elif diff < -180:
        diff += 360
    return diff


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation from a to b by factor t (0-1)."""
    return a + (b - a) * t


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value to range [min_val, max_val]."""
    return max(min_val, min(max_val, value))


def point_on_circle(
    center: Tuple[float, float],
    radius: float,
    angle_degrees: float
) -> Tuple[float, float]:
    """Get point on circle at given angle (degrees)."""
    angle_rad = math.radians(angle_degrees)
    x = center[0] + radius * math.cos(angle_rad)
    y = center[1] + radius * math.sin(angle_rad)
    return (x, y)


def rotate_point(
    point: Tuple[float, float],
    center: Tuple[float, float],
    angle_degrees: float
) -> Tuple[float, float]:
    """Rotate point around center by angle (degrees)."""
    angle_rad = math.radians(angle_degrees)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)

    # Translate to origin
    px = point[0] - center[0]
    py = point[1] - center[1]

    # Rotate
    rx = px * cos_a - py * sin_a
    ry = px * sin_a + py * cos_a

    # Translate back
    return (rx + center[0], ry + center[1])


# =============================================================================
# Grid-Aligned Geometry (Bresenham algorithms)
# =============================================================================

def bresenham_circle(
    center: Tuple[int, int],
    radius: int
) -> List[Tuple[int, int]]:
    """
    Generate all grid cells on a circle's perimeter using Bresenham's algorithm.
    Returns cells in no particular order (use sort_circle_cells for ordering).
    """
    if radius <= 0:
        return [center]

    cx, cy = center
    cells: Set[Tuple[int, int]] = set()

    x = 0
    y = radius
    d = 3 - 2 * radius

    def add_circle_points(cx: int, cy: int, x: int, y: int):
        """Add all 8 symmetric points."""
        cells.add((cx + x, cy + y))
        cells.add((cx - x, cy + y))
        cells.add((cx + x, cy - y))
        cells.add((cx - x, cy - y))
        cells.add((cx + y, cy + x))
        cells.add((cx - y, cy + x))
        cells.add((cx + y, cy - x))
        cells.add((cx - y, cy - x))

    add_circle_points(cx, cy, x, y)

    while y >= x:
        x += 1
        if d > 0:
            y -= 1
            d = d + 4 * (x - y) + 10
        else:
            d = d + 4 * x + 6
        add_circle_points(cx, cy, x, y)

    return list(cells)


def sort_circle_cells(
    cells: List[Tuple[int, int]],
    center: Tuple[int, int]
) -> List[Tuple[int, int]]:
    """Sort circle cells by angle from center (for ordered traversal)."""
    return sorted(cells, key=lambda p: angle_between(center, p))


def bresenham_line(
    p1: Tuple[int, int],
    p2: Tuple[int, int]
) -> List[Tuple[int, int]]:
    """Generate all grid cells on a line using Bresenham's algorithm."""
    cells = []
    x1, y1 = p1
    x2, y2 = p2

    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy

    while True:
        cells.append((x1, y1))
        if x1 == x2 and y1 == y2:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x1 += sx
        if e2 < dx:
            err += dx
            y1 += sy

    return cells


def filled_circle(
    center: Tuple[int, int],
    radius: int
) -> List[Tuple[int, int]]:
    """Generate all grid cells within a filled circle."""
    if radius <= 0:
        return [center]

    cx, cy = center
    cells = []
    r_sq = radius * radius

    for y in range(cy - radius, cy + radius + 1):
        for x in range(cx - radius, cx + radius + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r_sq:
                cells.append((x, y))

    return cells


# =============================================================================
# Orbital Body System
# =============================================================================

@dataclass
class OrbitalBody:
    """
    A celestial body that may orbit another body.

    Supports recursive orbits: star -> planet -> moon -> moon-of-moon
    Position is calculated by walking up the parent chain.
    """

    name: str
    surface_radius: int  # Physical size of the body
    orbit_ring_radius: int  # Distance from center where ships can orbit

    # Orbital parameters (ignored if parent is None)
    parent: Optional[OrbitalBody] = None
    orbital_radius: float = 0.0  # Distance from parent's center
    angular_velocity: float = 0.0  # Degrees per turn
    initial_angle: float = 0.0  # Angle at t=0

    # Base position (only used if parent is None, i.e., the star)
    base_position: Tuple[int, int] = (0, 0)

    def center_at_time(self, t: int) -> Tuple[float, float]:
        """
        Get continuous (float) position at time t.
        Recursively calculates position through parent chain.
        """
        if self.parent is None:
            # Stationary body (star)
            return (float(self.base_position[0]), float(self.base_position[1]))

        # Get parent's position at this time
        parent_pos = self.parent.center_at_time(t)

        # Calculate our angle at time t
        angle = self.initial_angle + self.angular_velocity * t

        # Calculate offset from parent
        offset = point_on_circle((0, 0), self.orbital_radius, angle)

        return (parent_pos[0] + offset[0], parent_pos[1] + offset[1])

    def grid_position_at_time(self, t: int) -> Tuple[int, int]:
        """
        Get snapped grid position at time t.
        This is where the body appears on the discrete game grid.
        """
        cx, cy = self.center_at_time(t)
        return (round(cx), round(cy))

    def surface_cells(self, t: int) -> List[Tuple[int, int]]:
        """Get all grid cells occupied by this body's surface at time t."""
        return filled_circle(self.grid_position_at_time(t), self.surface_radius)

    def orbit_ring_cells(self, t: int) -> List[Tuple[int, int]]:
        """
        Get all grid cells forming the orbit ring at time t.
        Ships can occupy these cells while orbiting this body.
        """
        return bresenham_circle(self.grid_position_at_time(t), self.orbit_ring_radius)

    def orbit_ring_cells_sorted(self, t: int) -> List[Tuple[int, int]]:
        """Get orbit ring cells sorted by angle (for ordered traversal)."""
        center = self.grid_position_at_time(t)
        cells = bresenham_circle(center, self.orbit_ring_radius)
        return sort_circle_cells(cells, center)

    def position_in_orbit(self, t: int, angle: float) -> Tuple[int, int]:
        """
        Get the grid position for a ship orbiting this body at given angle.
        The ship moves with the body - this returns absolute grid coords.
        """
        center = self.grid_position_at_time(t)
        pos = point_on_circle(center, self.orbit_ring_radius, angle)
        return (round(pos[0]), round(pos[1]))

    def is_inside_surface(self, point: Tuple[int, int], t: int) -> bool:
        """Check if a grid point is inside this body's surface."""
        center = self.grid_position_at_time(t)
        return distance_squared(center, point) <= self.surface_radius ** 2

    def is_on_orbit_ring(self, point: Tuple[int, int], t: int) -> bool:
        """Check if a grid point is on this body's orbit ring."""
        return point in self.orbit_ring_cells(t)

    def nearest_orbit_angle(self, point: Tuple[float, float], t: int) -> float:
        """
        Get the angle on the orbit ring closest to the given point.
        Useful for determining where a ship would enter orbit.
        """
        center = self.grid_position_at_time(t)
        return angle_between(center, point)

    def turns_until_position_changes(self, current_t: int) -> int:
        """
        Calculate how many turns until this body's grid position changes.
        Returns 0 if it changes next turn, -1 if it never moves (star).
        """
        if self.parent is None:
            return -1  # Stars don't move

        current_pos = self.grid_position_at_time(current_t)

        # Check future turns (reasonable limit to avoid infinite loop)
        for dt in range(1, 1000):
            future_pos = self.grid_position_at_time(current_t + dt)
            if future_pos != current_pos:
                return dt

        return -1  # Essentially stationary (very slow orbit)


@dataclass
class OrbitingShip:
    """
    A ship that is currently in orbit around a body.

    When orbiting, position is relative to the body, not absolute grid coords.
    The ship moves with the body automatically.
    """

    body: OrbitalBody
    orbital_angle: float  # Position on orbit ring (degrees)

    def grid_position_at_time(self, t: int) -> Tuple[int, int]:
        """Get absolute grid position at time t."""
        return self.body.position_in_orbit(t, self.orbital_angle)

    def move_along_orbit(self, angle_delta: float) -> None:
        """Move ship along the orbit ring (free movement while orbiting)."""
        self.orbital_angle = normalize_angle(self.orbital_angle + angle_delta)

    def set_orbit_angle(self, angle: float) -> None:
        """Set ship to specific angle on orbit ring."""
        self.orbital_angle = normalize_angle(angle)


# =============================================================================
# Pathfinding Helpers
# =============================================================================

def nearest_orbit_entry(
    ship_pos: Tuple[float, float],
    body: OrbitalBody,
    t: int
) -> Tuple[Tuple[int, int], float]:
    """
    Find the nearest point on a body's orbit ring to enter.

    Returns:
        (grid_position, angle): Entry point and the orbital angle
    """
    angle = body.nearest_orbit_angle(ship_pos, t)
    entry_pos = body.position_in_orbit(t, angle)
    return (entry_pos, angle)


def optimal_exit_heading(
    body: OrbitalBody,
    target: Tuple[float, float],
    t: int
) -> Tuple[float, Tuple[int, int]]:
    """
    Find the best angle to exit an orbit when heading toward a target.

    Returns:
        (exit_angle, exit_position): Best exit angle and grid position
    """
    center = body.grid_position_at_time(t)
    exit_angle = angle_between(center, target)
    exit_pos = body.position_in_orbit(t, exit_angle)
    return (exit_angle, exit_pos)


def is_viable_waypoint(
    ship_pos: Tuple[float, float],
    body: OrbitalBody,
    target: Tuple[float, float],
    t: int,
    angle_threshold: float = 90.0
) -> bool:
    """
    Check if an orbital body is a useful waypoint toward a target.

    A body is viable if it's roughly "on the way" - the angle from
    ship to body to target isn't too sharp (would be backtracking).

    Args:
        ship_pos: Ship's current position
        body: Potential waypoint body
        target: Final destination
        t: Current time
        angle_threshold: Maximum deflection angle (degrees)

    Returns:
        True if using this body's orbit could help reach target
    """
    body_pos = body.grid_position_at_time(t)

    # Angle from ship to body
    angle_to_body = angle_between(ship_pos, body_pos)

    # Angle from ship to target
    angle_to_target = angle_between(ship_pos, target)

    # How much would we deviate from direct path?
    deviation = abs(angle_difference(angle_to_target, angle_to_body))

    return deviation <= angle_threshold


def project_body_positions(
    body: OrbitalBody,
    start_t: int,
    num_turns: int
) -> List[Tuple[int, Tuple[int, int]]]:
    """
    Project a body's grid positions over future turns.

    Returns:
        List of (turn, grid_position) tuples
    """
    positions = []
    for dt in range(num_turns):
        t = start_t + dt
        pos = body.grid_position_at_time(t)
        positions.append((t, pos))
    return positions


def find_intercept_turn(
    ship_pos: Tuple[float, float],
    ship_speed: float,
    body: OrbitalBody,
    start_t: int,
    max_turns: int = 100
) -> Optional[Tuple[int, Tuple[int, int]]]:
    """
    Find when a ship could intercept a moving body's orbit.

    Simple approach: check each future turn to see if ship could
    reach the body's orbit ring by then.

    Args:
        ship_pos: Ship's starting position
        ship_speed: Ship's movement per turn (grid units)
        body: Target body to intercept
        start_t: Current turn
        max_turns: Maximum turns to search

    Returns:
        (turn, intercept_position) or None if no intercept found
    """
    for dt in range(1, max_turns + 1):
        t = start_t + dt
        body_center = body.grid_position_at_time(t)

        # Distance ship could travel
        max_travel = ship_speed * dt

        # Distance to body's orbit ring
        dist_to_center = distance(ship_pos, body_center)
        dist_to_orbit = abs(dist_to_center - body.orbit_ring_radius)

        if dist_to_orbit <= max_travel:
            # Ship could reach orbit this turn
            entry_pos, _ = nearest_orbit_entry(ship_pos, body, t)
            return (t, entry_pos)

    return None


def line_of_sight_blocked(
    p1: Tuple[int, int],
    p2: Tuple[int, int],
    bodies: List[OrbitalBody],
    t: int
) -> Optional[OrbitalBody]:
    """
    Check if line of sight between two points is blocked by any body's surface.

    Returns:
        The blocking body, or None if LOS is clear
    """
    line_cells = set(bresenham_line(p1, p2))

    for body in bodies:
        surface = set(body.surface_cells(t))
        if line_cells & surface:  # Intersection
            return body

    return None


# =============================================================================
# Convenience Functions
# =============================================================================

def create_solar_system(
    grid_width: int,
    grid_height: int,
    star_radius: int = 10,
    star_orbit_radius: int = 15
) -> OrbitalBody:
    """
    Create a star at the center of the grid.

    Returns the star body (other bodies should use it as parent).
    """
    return OrbitalBody(
        name="Star",
        surface_radius=star_radius,
        orbit_ring_radius=star_orbit_radius,
        parent=None,
        base_position=(grid_width // 2, grid_height // 2)
    )


def create_planet(
    name: str,
    star: OrbitalBody,
    orbital_radius: float,
    surface_radius: int,
    orbit_ring_radius: int,
    angular_velocity: float,
    initial_angle: float = 0.0
) -> OrbitalBody:
    """Create a planet orbiting a star."""
    return OrbitalBody(
        name=name,
        surface_radius=surface_radius,
        orbit_ring_radius=orbit_ring_radius,
        parent=star,
        orbital_radius=orbital_radius,
        angular_velocity=angular_velocity,
        initial_angle=initial_angle
    )


def create_moon(
    name: str,
    planet: OrbitalBody,
    orbital_radius: float,
    surface_radius: int,
    orbit_ring_radius: int,
    angular_velocity: float,
    initial_angle: float = 0.0
) -> OrbitalBody:
    """Create a moon orbiting a planet (or another moon)."""
    return OrbitalBody(
        name=name,
        surface_radius=surface_radius,
        orbit_ring_radius=orbit_ring_radius,
        parent=planet,
        orbital_radius=orbital_radius,
        angular_velocity=angular_velocity,
        initial_angle=initial_angle
    )
