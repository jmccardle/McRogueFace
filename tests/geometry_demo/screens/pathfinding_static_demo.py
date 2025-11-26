"""Static pathfinding demonstration with planets and orbit rings."""
import mcrfpy
import math
from .base import (GeometryDemoScreen, OrbitalBody, bresenham_circle, filled_circle,
                   angle_between, distance, point_on_circle, is_viable_waypoint,
                   nearest_orbit_entry, optimal_exit_heading)


class PathfindingStaticDemo(GeometryDemoScreen):
    """Demonstrate optimal path through a static solar system."""

    name = "Static Pathfinding"
    description = "Optimal path using orbital slingshots"

    def setup(self):
        self.add_title("Pathfinding Through Orbital Bodies")
        self.add_description("Using free orbital movement to optimize travel paths")

        # Create a scenario with multiple planets
        # Ship needs to go from bottom-left to top-right
        # Optimal path uses planetary orbits as "free repositioning stations"

        self.cell_size = 8
        self.offset_x = 50
        self.offset_y = 100

        # Background
        bg = mcrfpy.Frame(pos=(30, 80), size=(740, 480))
        bg.fill_color = mcrfpy.Color(5, 5, 15)
        bg.outline = 1
        bg.outline_color = mcrfpy.Color(40, 40, 80)
        self.ui.append(bg)

        # Define planets (center_x, center_y, surface_radius, orbit_radius, name)
        self.planets = [
            (20, 45, 8, 14, "Alpha"),
            (55, 25, 5, 10, "Beta"),
            (70, 50, 6, 12, "Gamma"),
        ]

        # Ship start and end
        self.ship_start = (5, 55)
        self.ship_end = (85, 10)

        # Draw grid reference (faint)
        self._draw_grid_reference()

        # Draw planets with surfaces and orbit rings
        for px, py, sr, orbit_r, name in self.planets:
            self._draw_planet(px, py, sr, orbit_r, name)

        # Calculate and draw optimal path
        self._draw_optimal_path()

        # Draw ship and target
        self._draw_ship_and_target()

        # Legend
        self._draw_legend()

    def _to_screen(self, gx, gy):
        """Convert grid coords to screen coords."""
        return (self.offset_x + gx * self.cell_size,
                self.offset_y + gy * self.cell_size)

    def _draw_grid_reference(self):
        """Draw faint grid lines for reference."""
        for i in range(0, 91, 10):
            # Vertical lines
            x = self.offset_x + i * self.cell_size
            line = mcrfpy.Line(
                start=(x, self.offset_y),
                end=(x, self.offset_y + 60 * self.cell_size),
                color=mcrfpy.Color(30, 30, 50),
                thickness=1
            )
            self.ui.append(line)

        for i in range(0, 61, 10):
            # Horizontal lines
            y = self.offset_y + i * self.cell_size
            line = mcrfpy.Line(
                start=(self.offset_x, y),
                end=(self.offset_x + 90 * self.cell_size, y),
                color=mcrfpy.Color(30, 30, 50),
                thickness=1
            )
            self.ui.append(line)

    def _draw_planet(self, cx, cy, surface_r, orbit_r, name):
        """Draw a planet with surface and orbit ring."""
        sx, sy = self._to_screen(cx, cy)

        # Orbit ring (using mcrfpy.Circle for smooth rendering)
        orbit = mcrfpy.Circle(
            center=(sx, sy),
            radius=orbit_r * self.cell_size,
            fill_color=mcrfpy.Color(0, 0, 0, 0),
            outline_color=mcrfpy.Color(50, 150, 50, 150),
            outline=2
        )
        self.ui.append(orbit)

        # Also draw Bresenham orbit cells for accuracy demo
        orbit_cells = bresenham_circle((cx, cy), orbit_r)
        for gx, gy in orbit_cells:
            px, py = self._to_screen(gx, gy)
            cell = mcrfpy.Frame(
                pos=(px, py),
                size=(self.cell_size - 1, self.cell_size - 1)
            )
            cell.fill_color = mcrfpy.Color(40, 100, 40, 100)
            self.ui.append(cell)

        # Planet surface (filled circle)
        surface_cells = filled_circle((cx, cy), surface_r)
        for gx, gy in surface_cells:
            px, py = self._to_screen(gx, gy)
            dist = math.sqrt((gx - cx)**2 + (gy - cy)**2)
            intensity = int(180 * (1 - dist / (surface_r + 1)))
            cell = mcrfpy.Frame(
                pos=(px, py),
                size=(self.cell_size - 1, self.cell_size - 1)
            )
            cell.fill_color = mcrfpy.Color(60 + intensity, 80 + intensity//2, 150)
            self.ui.append(cell)

        # Planet label
        self.add_label(name, sx - 15, sy - surface_r * self.cell_size - 15, (150, 150, 200))

    def _draw_optimal_path(self):
        """Calculate and draw the optimal path using orbital waypoints."""
        # The optimal path:
        # 1. Ship starts at (5, 55)
        # 2. Direct line to Alpha's orbit entry
        # 3. Free arc around Alpha to optimal exit
        # 4. Direct line to Gamma's orbit entry
        # 5. Free arc around Gamma to optimal exit
        # 6. Direct line to target (85, 10)

        path_segments = []

        # Current position
        current = self.ship_start

        # For this demo, manually define the path through Alpha and Gamma
        # (In a real implementation, this would be computed by the pathfinder)

        # Planet Alpha (20, 45, orbit_r=14)
        alpha_center = (20, 45)
        alpha_orbit = 14

        # Entry to Alpha
        entry_angle_alpha = angle_between(alpha_center, current)
        entry_alpha = point_on_circle(alpha_center, alpha_orbit, entry_angle_alpha)

        # Draw line: start -> Alpha entry
        self._draw_path_line(current, entry_alpha, (100, 200, 255))
        current = entry_alpha

        # Exit from Alpha toward Gamma
        gamma_center = (70, 50)
        exit_angle_alpha = angle_between(alpha_center, gamma_center)
        exit_alpha = point_on_circle(alpha_center, alpha_orbit, exit_angle_alpha)

        # Draw arc on Alpha's orbit
        self._draw_orbit_arc(alpha_center, alpha_orbit, entry_angle_alpha, exit_angle_alpha)
        current = exit_alpha

        # Planet Gamma (70, 50, orbit_r=12)
        gamma_orbit = 12

        # Entry to Gamma
        entry_angle_gamma = angle_between(gamma_center, current)
        entry_gamma = point_on_circle(gamma_center, gamma_orbit, entry_angle_gamma)

        # Draw line: Alpha exit -> Gamma entry
        self._draw_path_line(current, entry_gamma, (100, 200, 255))
        current = entry_gamma

        # Exit from Gamma toward target
        exit_angle_gamma = angle_between(gamma_center, self.ship_end)
        exit_gamma = point_on_circle(gamma_center, gamma_orbit, exit_angle_gamma)

        # Draw arc on Gamma's orbit
        self._draw_orbit_arc(gamma_center, gamma_orbit, entry_angle_gamma, exit_angle_gamma)
        current = exit_gamma

        # Final segment to target
        self._draw_path_line(current, self.ship_end, (100, 200, 255))

        # For comparison, draw direct path (inefficient)
        direct_start = self._to_screen(*self.ship_start)
        direct_end = self._to_screen(*self.ship_end)
        direct_line = mcrfpy.Line(
            start=direct_start, end=direct_end,
            color=mcrfpy.Color(255, 100, 100, 80),
            thickness=1
        )
        self.ui.append(direct_line)

    def _draw_path_line(self, p1, p2, color):
        """Draw a path segment line."""
        s1 = self._to_screen(p1[0], p1[1])
        s2 = self._to_screen(p2[0], p2[1])
        line = mcrfpy.Line(
            start=s1, end=s2,
            color=mcrfpy.Color(*color),
            thickness=3
        )
        self.ui.append(line)

    def _draw_orbit_arc(self, center, radius, start_angle, end_angle):
        """Draw an arc showing orbital movement (free movement)."""
        sx, sy = self._to_screen(center[0], center[1])

        # Normalize angles for drawing
        # Screen coordinates have Y inverted, so negate angles
        arc = mcrfpy.Arc(
            center=(sx, sy),
            radius=radius * self.cell_size,
            start_angle=-start_angle,
            end_angle=-end_angle,
            color=mcrfpy.Color(255, 255, 100),
            thickness=4
        )
        self.ui.append(arc)

    def _draw_ship_and_target(self):
        """Draw ship start and target end positions."""
        # Ship
        ship_x, ship_y = self._to_screen(*self.ship_start)
        ship = mcrfpy.Circle(
            center=(ship_x + self.cell_size//2, ship_y + self.cell_size//2),
            radius=10,
            fill_color=mcrfpy.Color(255, 200, 100),
            outline_color=mcrfpy.Color(255, 255, 200),
            outline=2
        )
        self.ui.append(ship)
        self.add_label("SHIP", ship_x - 10, ship_y + 20, (255, 200, 100))

        # Target
        target_x, target_y = self._to_screen(*self.ship_end)
        target = mcrfpy.Circle(
            center=(target_x + self.cell_size//2, target_y + self.cell_size//2),
            radius=10,
            fill_color=mcrfpy.Color(255, 100, 100),
            outline_color=mcrfpy.Color(255, 200, 200),
            outline=2
        )
        self.ui.append(target)
        self.add_label("TARGET", target_x - 15, target_y + 20, (255, 100, 100))

    def _draw_legend(self):
        """Draw legend explaining the visualization."""
        leg_x = 50
        leg_y = 520

        # Blue line = movement cost
        line1 = mcrfpy.Line(
            start=(leg_x, leg_y + 10), end=(leg_x + 30, leg_y + 10),
            color=mcrfpy.Color(100, 200, 255),
            thickness=3
        )
        self.ui.append(line1)
        self.add_label("Impulse movement (costs energy)", leg_x + 40, leg_y + 3, (150, 150, 150))

        # Yellow arc = free movement
        arc1 = mcrfpy.Arc(
            center=(leg_x + 15, leg_y + 45), radius=15,
            start_angle=0, end_angle=180,
            color=mcrfpy.Color(255, 255, 100),
            thickness=3
        )
        self.ui.append(arc1)
        self.add_label("Orbital movement (FREE)", leg_x + 40, leg_y + 35, (255, 255, 100))

        # Red line = direct (inefficient)
        line2 = mcrfpy.Line(
            start=(leg_x + 300, leg_y + 10), end=(leg_x + 330, leg_y + 10),
            color=mcrfpy.Color(255, 100, 100, 80),
            thickness=1
        )
        self.ui.append(line2)
        self.add_label("Direct path (for comparison)", leg_x + 340, leg_y + 3, (150, 150, 150))

        # Green cells = orbit ring
        cell1 = mcrfpy.Frame(pos=(leg_x + 300, leg_y + 35), size=(15, 15))
        cell1.fill_color = mcrfpy.Color(40, 100, 40)
        self.ui.append(cell1)
        self.add_label("Orbit ring cells (valid ship positions)", leg_x + 320, leg_y + 35, (150, 150, 150))
