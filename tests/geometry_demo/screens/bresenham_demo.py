"""Bresenham circle algorithm demonstration on a grid."""
import mcrfpy
import math
from .base import GeometryDemoScreen, bresenham_circle, bresenham_line, filled_circle, SCREEN_WIDTH, SCREEN_HEIGHT


class BresenhamDemo(GeometryDemoScreen):
    """Demonstrate Bresenham circle and line algorithms on a grid."""

    name = "Bresenham Algorithms"
    description = "Grid-aligned circle and line rasterization"

    def setup(self):
        self.add_title("Bresenham Circle & Line Algorithms")
        self.add_description("Grid-aligned geometric primitives for orbit rings and LOS calculations")

        cell_size = 16
        margin = 30
        frame_gap = 20

        # Calculate frame dimensions for 2x2 layout
        # Available width: 1024 - 2*margin = 964, split into 2 with gap
        frame_width = (SCREEN_WIDTH - 2 * margin - frame_gap) // 2  # ~472 each
        # Available height for frames: 768 - 80 (top) - 30 (bottom margin)
        top_area = 80
        bottom_margin = 30
        available_height = SCREEN_HEIGHT - top_area - bottom_margin - frame_gap
        frame_height = available_height // 2  # ~314 each

        # Top-left: Bresenham Circle
        self._draw_circle_demo(margin, top_area, frame_width, frame_height, cell_size)

        # Top-right: Bresenham Lines
        self._draw_lines_demo(margin + frame_width + frame_gap, top_area, frame_width, frame_height, cell_size)

        # Bottom-left: Filled Circle
        self._draw_filled_demo(margin, top_area + frame_height + frame_gap, frame_width, frame_height, cell_size)

        # Bottom-right: Planet + Orbit Ring
        self._draw_combined_demo(margin + frame_width + frame_gap, top_area + frame_height + frame_gap,
                                 frame_width, frame_height, cell_size)

    def _draw_circle_demo(self, x, y, w, h, cell_size):
        """Draw Bresenham circle demonstration."""
        bg = mcrfpy.Frame(pos=(x, y), size=(w, h))
        bg.fill_color = mcrfpy.Color(15, 15, 25)
        bg.outline = 1
        bg.outline_color = mcrfpy.Color(60, 60, 100)
        self.ui.append(bg)

        self.add_label("Bresenham Circle (radius=8)", x + 10, y + 5, (255, 200, 100))
        self.add_label("Center: (12, 9)", x + 10, y + 25, (150, 150, 150))

        # Grid origin for this demo
        grid_x = x + 20
        grid_y = y + 50

        center = (12, 9)
        radius = 8
        circle_cells = bresenham_circle(center, radius)

        # Draw each cell
        for cx, cy in circle_cells:
            px = grid_x + cx * cell_size
            py = grid_y + cy * cell_size
            cell_rect = mcrfpy.Frame(pos=(px, py), size=(cell_size - 1, cell_size - 1))
            cell_rect.fill_color = mcrfpy.Color(100, 200, 255)
            cell_rect.outline = 0
            self.ui.append(cell_rect)

        # Draw center point
        cx_px = grid_x + center[0] * cell_size
        cy_px = grid_y + center[1] * cell_size
        center_rect = mcrfpy.Frame(pos=(cx_px, cy_px), size=(cell_size - 1, cell_size - 1))
        center_rect.fill_color = mcrfpy.Color(255, 100, 100)
        self.ui.append(center_rect)

        # Draw actual circle outline for comparison (centered on cells)
        actual_circle = mcrfpy.Circle(
            center=(grid_x + center[0] * cell_size + cell_size // 2,
                   grid_y + center[1] * cell_size + cell_size // 2),
            radius=radius * cell_size,
            fill_color=mcrfpy.Color(0, 0, 0, 0),
            outline_color=mcrfpy.Color(255, 255, 100, 128),
            outline=2
        )
        self.ui.append(actual_circle)

    def _draw_lines_demo(self, x, y, w, h, cell_size):
        """Draw Bresenham lines demonstration."""
        bg = mcrfpy.Frame(pos=(x, y), size=(w, h))
        bg.fill_color = mcrfpy.Color(15, 15, 25)
        bg.outline = 1
        bg.outline_color = mcrfpy.Color(60, 60, 100)
        self.ui.append(bg)

        self.add_label("Bresenham Lines", x + 10, y + 5, (255, 200, 100))

        grid_x = x + 20
        grid_y = y + 40

        # Draw multiple lines at different angles
        lines_data = [
            ((2, 2), (17, 5), (255, 100, 100)),   # Shallow
            ((2, 7), (17, 14), (100, 255, 100)),  # Diagonal-ish
            ((2, 12), (10, 17), (100, 100, 255)), # Steep
        ]

        for start, end, color in lines_data:
            line_cells = bresenham_line(start, end)
            for cx, cy in line_cells:
                px = grid_x + cx * cell_size
                py = grid_y + cy * cell_size
                cell_rect = mcrfpy.Frame(pos=(px, py), size=(cell_size - 1, cell_size - 1))
                cell_rect.fill_color = mcrfpy.Color(*color)
                self.ui.append(cell_rect)

            # Draw the actual line for comparison (through cell centers)
            line = mcrfpy.Line(
                start=(grid_x + start[0] * cell_size + cell_size // 2,
                       grid_y + start[1] * cell_size + cell_size // 2),
                end=(grid_x + end[0] * cell_size + cell_size // 2,
                     grid_y + end[1] * cell_size + cell_size // 2),
                color=mcrfpy.Color(255, 255, 255, 128),
                thickness=1
            )
            self.ui.append(line)

    def _draw_filled_demo(self, x, y, w, h, cell_size):
        """Draw filled circle demonstration."""
        bg = mcrfpy.Frame(pos=(x, y), size=(w, h))
        bg.fill_color = mcrfpy.Color(15, 15, 25)
        bg.outline = 1
        bg.outline_color = mcrfpy.Color(60, 60, 100)
        self.ui.append(bg)

        self.add_label("Filled Circle (radius=5)", x + 10, y + 5, (255, 200, 100))
        self.add_label("Planet surface representation", x + 10, y + 25, (150, 150, 150))

        grid_x = x + 50
        grid_y = y + 60

        fill_center = (8, 8)
        fill_radius = 5
        filled_cells = filled_circle(fill_center, fill_radius)

        for cx, cy in filled_cells:
            px = grid_x + cx * cell_size
            py = grid_y + cy * cell_size
            # Gradient based on distance from center
            dist = math.sqrt((cx - fill_center[0])**2 + (cy - fill_center[1])**2)
            intensity = int(255 * (1 - dist / (fill_radius + 1)))
            cell_rect = mcrfpy.Frame(pos=(px, py), size=(cell_size - 1, cell_size - 1))
            cell_rect.fill_color = mcrfpy.Color(intensity, intensity // 2, 50)
            self.ui.append(cell_rect)

    def _draw_combined_demo(self, x, y, w, h, cell_size):
        """Draw planet + orbit ring demonstration."""
        bg = mcrfpy.Frame(pos=(x, y), size=(w, h))
        bg.fill_color = mcrfpy.Color(15, 15, 25)
        bg.outline = 1
        bg.outline_color = mcrfpy.Color(60, 60, 100)
        self.ui.append(bg)

        self.add_label("Planet + Orbit Ring", x + 10, y + 5, (255, 200, 100))
        self.add_label("Surface (r=3) + Orbit (r=8)", x + 10, y + 25, (150, 150, 150))

        grid_x = x + 60
        grid_y = y + 50

        planet_center = (12, 10)
        surface_radius = 3
        orbit_radius = 8

        # Draw orbit ring (behind planet)
        orbit_cells = bresenham_circle(planet_center, orbit_radius)
        for cx, cy in orbit_cells:
            px = grid_x + cx * cell_size
            py = grid_y + cy * cell_size
            cell_rect = mcrfpy.Frame(pos=(px, py), size=(cell_size - 1, cell_size - 1))
            cell_rect.fill_color = mcrfpy.Color(50, 150, 50, 180)
            self.ui.append(cell_rect)

        # Draw planet surface (on top)
        surface_cells = filled_circle(planet_center, surface_radius)
        for cx, cy in surface_cells:
            px = grid_x + cx * cell_size
            py = grid_y + cy * cell_size
            dist = math.sqrt((cx - planet_center[0])**2 + (cy - planet_center[1])**2)
            intensity = int(200 * (1 - dist / (surface_radius + 1)))
            cell_rect = mcrfpy.Frame(pos=(px, py), size=(cell_size - 1, cell_size - 1))
            cell_rect.fill_color = mcrfpy.Color(50 + intensity, 100 + intensity // 2, 200)
            self.ui.append(cell_rect)

        # Legend in bottom-left of frame
        leg_x = x + 10
        leg_y = y + h - 50

        leg1 = mcrfpy.Frame(pos=(leg_x, leg_y), size=(12, 12))
        leg1.fill_color = mcrfpy.Color(100, 150, 200)
        self.ui.append(leg1)
        self.add_label("Planet", leg_x + 18, leg_y - 2, (150, 150, 150))

        leg2 = mcrfpy.Frame(pos=(leg_x, leg_y + 20), size=(12, 12))
        leg2.fill_color = mcrfpy.Color(50, 150, 50)
        self.ui.append(leg2)
        self.add_label("Orbit ring", leg_x + 18, leg_y + 18, (150, 150, 150))
