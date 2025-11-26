"""Static pathfinding demonstration with planets and orbit rings."""
import mcrfpy
import math
from .base import (GeometryDemoScreen, bresenham_circle, filled_circle,
                   screen_angle_between, distance, SCREEN_WIDTH, SCREEN_HEIGHT)


class PathfindingStaticDemo(GeometryDemoScreen):
    """Demonstrate optimal path through a static solar system."""

    name = "Static Pathfinding"
    description = "Optimal path using orbital slingshots"

    def setup(self):
        self.add_title("Pathfinding Through Orbital Bodies")
        self.add_description("Using free orbital movement to optimize travel paths")

        margin = 30
        top_area = 80
        legend_height = 70

        # Main display area - use most of screen
        frame_width = SCREEN_WIDTH - 2 * margin
        frame_height = SCREEN_HEIGHT - top_area - margin - legend_height

        self.cell_size = 8
        self.grid_x = margin + 20
        self.grid_y = top_area + 20

        # Background
        bg = mcrfpy.Frame(pos=(margin, top_area), size=(frame_width, frame_height))
        bg.fill_color = mcrfpy.Color(5, 5, 15)
        bg.outline = 1
        bg.outline_color = mcrfpy.Color(40, 40, 80)
        self.ui.append(bg)

        # Define planets (center_x, center_y, surface_radius, orbit_radius, name)
        self.planets = [
            (25, 50, 6, 12, "Alpha"),
            (60, 25, 4, 9, "Beta"),
            (85, 55, 5, 11, "Gamma"),
        ]

        # Ship start and end
        self.ship_start = (8, 65)
        self.ship_end = (105, 15)

        # Draw grid reference
        self._draw_grid_reference()

        # Draw planets
        for px, py, sr, orbit_r, name in self.planets:
            self._draw_planet(px, py, sr, orbit_r, name)

        # Draw optimal path
        self._draw_optimal_path()

        # Draw ship and target
        self._draw_ship_and_target()

        # Legend at bottom
        self._draw_legend(margin, top_area + frame_height + 10)

    def _to_screen(self, gx, gy):
        """Convert grid coords to screen coords (center of cell)."""
        return (self.grid_x + gx * self.cell_size + self.cell_size // 2,
                self.grid_y + gy * self.cell_size + self.cell_size // 2)

    def _to_screen_corner(self, gx, gy):
        """Convert grid coords to screen coords (corner of cell)."""
        return (self.grid_x + gx * self.cell_size,
                self.grid_y + gy * self.cell_size)

    def _draw_grid_reference(self):
        """Draw faint grid lines for reference."""
        max_x = 115
        max_y = 75
        for i in range(0, max_x + 1, 10):
            x = self.grid_x + i * self.cell_size
            line = mcrfpy.Line(
                start=(x, self.grid_y),
                end=(x, self.grid_y + max_y * self.cell_size),
                color=mcrfpy.Color(30, 30, 50),
                thickness=1
            )
            self.ui.append(line)

        for i in range(0, max_y + 1, 10):
            y = self.grid_y + i * self.cell_size
            line = mcrfpy.Line(
                start=(self.grid_x, y),
                end=(self.grid_x + max_x * self.cell_size, y),
                color=mcrfpy.Color(30, 30, 50),
                thickness=1
            )
            self.ui.append(line)

    def _draw_planet(self, cx, cy, surface_r, orbit_r, name):
        """Draw a planet with surface and orbit ring."""
        sx, sy = self._to_screen(cx, cy)

        # Orbit ring (smooth circle)
        orbit = mcrfpy.Circle(
            center=(sx, sy),
            radius=orbit_r * self.cell_size,
            fill_color=mcrfpy.Color(0, 0, 0, 0),
            outline_color=mcrfpy.Color(50, 150, 50, 150),
            outline=2
        )
        self.ui.append(orbit)

        # Bresenham orbit cells
        orbit_cells = bresenham_circle((cx, cy), orbit_r)
        for gx, gy in orbit_cells:
            px, py = self._to_screen_corner(gx, gy)
            cell = mcrfpy.Frame(
                pos=(px, py),
                size=(self.cell_size - 1, self.cell_size - 1)
            )
            cell.fill_color = mcrfpy.Color(40, 100, 40, 100)
            self.ui.append(cell)

        # Planet surface
        surface_cells = filled_circle((cx, cy), surface_r)
        for gx, gy in surface_cells:
            px, py = self._to_screen_corner(gx, gy)
            dist = math.sqrt((gx - cx)**2 + (gy - cy)**2)
            intensity = int(180 * (1 - dist / (surface_r + 1)))
            cell = mcrfpy.Frame(
                pos=(px, py),
                size=(self.cell_size - 1, self.cell_size - 1)
            )
            cell.fill_color = mcrfpy.Color(60 + intensity, 80 + intensity//2, 150)
            self.ui.append(cell)

        # Planet label (below planet to avoid overlap)
        self.add_label(name, sx - 15, sy + (surface_r + 2) * self.cell_size, (150, 150, 200))

    def _draw_optimal_path(self):
        """Draw the optimal path using orbital waypoints."""
        # The path:
        # 1. Ship at (8, 65) -> Alpha orbit entry
        # 2. Arc around Alpha -> exit toward Gamma
        # 3. Straight to Gamma orbit entry
        # 4. Arc around Gamma -> exit toward target
        # 5. Straight to target (105, 15)

        # Alpha: center (25, 50), orbit_r=12
        alpha_center = (25, 50)
        alpha_orbit = 12

        # Gamma: center (85, 55), orbit_r=11
        gamma_center = (85, 55)
        gamma_orbit = 11

        ship_screen = self._to_screen(*self.ship_start)
        target_screen = self._to_screen(*self.ship_end)

        # --- Segment 1: Ship to Alpha orbit entry ---
        # Entry angle: direction from Alpha to ship
        entry_angle_alpha = screen_angle_between(
            self._to_screen(*alpha_center),
            ship_screen
        )
        entry_alpha = (
            alpha_center[0] + alpha_orbit * math.cos(math.radians(entry_angle_alpha)),
            alpha_center[1] - alpha_orbit * math.sin(math.radians(entry_angle_alpha))  # Screen Y inverted
        )
        entry_alpha_screen = self._to_screen(*entry_alpha)

        self._draw_path_line(ship_screen, entry_alpha_screen, (100, 200, 255))

        # --- Segment 2: Arc around Alpha toward Gamma ---
        exit_angle_alpha = screen_angle_between(
            self._to_screen(*alpha_center),
            self._to_screen(*gamma_center)
        )
        exit_alpha = (
            alpha_center[0] + alpha_orbit * math.cos(math.radians(exit_angle_alpha)),
            alpha_center[1] - alpha_orbit * math.sin(math.radians(exit_angle_alpha))
        )
        exit_alpha_screen = self._to_screen(*exit_alpha)

        self._draw_orbit_arc(self._to_screen(*alpha_center), alpha_orbit * self.cell_size,
                            entry_angle_alpha, exit_angle_alpha)

        # --- Segment 3: Alpha exit to Gamma entry ---
        entry_angle_gamma = screen_angle_between(
            self._to_screen(*gamma_center),
            exit_alpha_screen
        )
        entry_gamma = (
            gamma_center[0] + gamma_orbit * math.cos(math.radians(entry_angle_gamma)),
            gamma_center[1] - gamma_orbit * math.sin(math.radians(entry_angle_gamma))
        )
        entry_gamma_screen = self._to_screen(*entry_gamma)

        self._draw_path_line(exit_alpha_screen, entry_gamma_screen, (100, 200, 255))

        # --- Segment 4: Arc around Gamma toward target ---
        exit_angle_gamma = screen_angle_between(
            self._to_screen(*gamma_center),
            target_screen
        )
        exit_gamma = (
            gamma_center[0] + gamma_orbit * math.cos(math.radians(exit_angle_gamma)),
            gamma_center[1] - gamma_orbit * math.sin(math.radians(exit_angle_gamma))
        )
        exit_gamma_screen = self._to_screen(*exit_gamma)

        self._draw_orbit_arc(self._to_screen(*gamma_center), gamma_orbit * self.cell_size,
                            entry_angle_gamma, exit_angle_gamma)

        # --- Segment 5: Gamma exit to target ---
        self._draw_path_line(exit_gamma_screen, target_screen, (100, 200, 255))

        # Draw direct path for comparison
        direct_line = mcrfpy.Line(
            start=ship_screen, end=target_screen,
            color=mcrfpy.Color(255, 100, 100, 80),
            thickness=1
        )
        self.ui.append(direct_line)

    def _draw_path_line(self, p1, p2, color):
        """Draw a path segment line."""
        line = mcrfpy.Line(
            start=p1, end=p2,
            color=mcrfpy.Color(*color),
            thickness=3
        )
        self.ui.append(line)

    def _draw_orbit_arc(self, center, radius, start_angle, end_angle):
        """Draw an arc showing orbital movement (free movement)."""
        # Ensure we draw the shorter arc
        diff = end_angle - start_angle
        if diff > 180:
            start_angle, end_angle = end_angle, start_angle
        elif diff < -180:
            start_angle, end_angle = end_angle, start_angle

        arc = mcrfpy.Arc(
            center=center,
            radius=radius,
            start_angle=min(start_angle, end_angle),
            end_angle=max(start_angle, end_angle),
            color=mcrfpy.Color(255, 255, 100),
            thickness=4
        )
        self.ui.append(arc)

    def _draw_ship_and_target(self):
        """Draw ship and target markers."""
        ship_screen = self._to_screen(*self.ship_start)
        target_screen = self._to_screen(*self.ship_end)

        # Ship
        ship = mcrfpy.Circle(
            center=ship_screen,
            radius=10,
            fill_color=mcrfpy.Color(255, 200, 100),
            outline_color=mcrfpy.Color(255, 255, 200),
            outline=2
        )
        self.ui.append(ship)
        self.add_label("SHIP", ship_screen[0] - 15, ship_screen[1] + 15, (255, 200, 100))

        # Target
        target = mcrfpy.Circle(
            center=target_screen,
            radius=10,
            fill_color=mcrfpy.Color(255, 100, 100),
            outline_color=mcrfpy.Color(255, 200, 200),
            outline=2
        )
        self.ui.append(target)
        self.add_label("TARGET", target_screen[0] - 25, target_screen[1] + 15, (255, 100, 100))

    def _draw_legend(self, x, y):
        """Draw legend."""
        # Blue line = movement cost
        line1 = mcrfpy.Line(
            start=(x, y + 15), end=(x + 40, y + 15),
            color=mcrfpy.Color(100, 200, 255),
            thickness=3
        )
        self.ui.append(line1)
        self.add_label("Impulse movement (costs energy)", x + 50, y + 8, (150, 150, 150))

        # Yellow arc = free movement
        arc1 = mcrfpy.Arc(
            center=(x + 20, y + 50), radius=18,
            start_angle=0, end_angle=180,
            color=mcrfpy.Color(255, 255, 100),
            thickness=3
        )
        self.ui.append(arc1)
        self.add_label("Orbital movement (FREE)", x + 50, y + 40, (255, 255, 100))

        # Red line = direct
        line2 = mcrfpy.Line(
            start=(x + 400, y + 15), end=(x + 440, y + 15),
            color=mcrfpy.Color(255, 100, 100, 80),
            thickness=1
        )
        self.ui.append(line2)
        self.add_label("Direct path (comparison)", x + 450, y + 8, (150, 150, 150))

        # Green cells = orbit ring
        cell1 = mcrfpy.Frame(pos=(x + 400, y + 40), size=(15, 15))
        cell1.fill_color = mcrfpy.Color(40, 100, 40)
        self.ui.append(cell1)
        self.add_label("Orbit ring (ship positions)", x + 420, y + 40, (150, 150, 150))
