"""Bresenham circle algorithm demonstration on a grid."""
import mcrfpy
from .base import GeometryDemoScreen, bresenham_circle, bresenham_line, filled_circle


class BresenhamDemo(GeometryDemoScreen):
    """Demonstrate Bresenham circle and line algorithms on a grid."""

    name = "Bresenham Algorithms"
    description = "Grid-aligned circle and line rasterization"

    def setup(self):
        self.add_title("Bresenham Circle & Line Algorithms")
        self.add_description("Grid-aligned geometric primitives for orbit rings and LOS calculations")

        # Create a grid for circle demo
        grid_w, grid_h = 25, 18
        cell_size = 16

        # We need a texture for the grid - create a simple one
        # Actually, let's use Grid's built-in cell coloring via GridPoint

        # Create display area with Frame background
        bg1 = mcrfpy.Frame(pos=(30, 80), size=(420, 310))
        bg1.fill_color = mcrfpy.Color(15, 15, 25)
        bg1.outline = 1
        bg1.outline_color = mcrfpy.Color(60, 60, 100)
        self.ui.append(bg1)

        self.add_label("Bresenham Circle (radius=8)", 50, 85, (255, 200, 100))
        self.add_label("Center: (12, 9)", 50, 105, (150, 150, 150))

        # Draw circle using UICircle primitives to show the cells
        center = (12, 9)
        radius = 8
        circle_cells = bresenham_circle(center, radius)

        # Draw each cell as a small rectangle
        for x, y in circle_cells:
            px = 40 + x * cell_size
            py = 120 + y * cell_size
            cell_rect = mcrfpy.Frame(pos=(px, py), size=(cell_size - 1, cell_size - 1))
            cell_rect.fill_color = mcrfpy.Color(100, 200, 255)
            cell_rect.outline = 0
            self.ui.append(cell_rect)

        # Draw center point
        cx_px = 40 + center[0] * cell_size
        cy_px = 120 + center[1] * cell_size
        center_rect = mcrfpy.Frame(pos=(cx_px, cy_px), size=(cell_size - 1, cell_size - 1))
        center_rect.fill_color = mcrfpy.Color(255, 100, 100)
        self.ui.append(center_rect)

        # Draw the actual circle outline for comparison
        actual_circle = mcrfpy.Circle(
            center=(40 + center[0] * cell_size + cell_size // 2,
                   120 + center[1] * cell_size + cell_size // 2),
            radius=radius * cell_size,
            fill_color=mcrfpy.Color(0, 0, 0, 0),
            outline_color=mcrfpy.Color(255, 255, 100, 128),
            outline=2
        )
        self.ui.append(actual_circle)

        # Second demo: Bresenham line
        bg2 = mcrfpy.Frame(pos=(470, 80), size=(310, 310))
        bg2.fill_color = mcrfpy.Color(15, 15, 25)
        bg2.outline = 1
        bg2.outline_color = mcrfpy.Color(60, 60, 100)
        self.ui.append(bg2)

        self.add_label("Bresenham Lines", 490, 85, (255, 200, 100))

        # Draw multiple lines at different angles
        lines_data = [
            ((2, 2), (17, 5), (255, 100, 100)),   # Shallow
            ((2, 7), (17, 14), (100, 255, 100)),  # Diagonal-ish
            ((2, 12), (10, 17), (100, 100, 255)), # Steep
        ]

        for start, end, color in lines_data:
            line_cells = bresenham_line(start, end)
            for x, y in line_cells:
                px = 480 + x * cell_size
                py = 110 + y * cell_size
                cell_rect = mcrfpy.Frame(pos=(px, py), size=(cell_size - 1, cell_size - 1))
                cell_rect.fill_color = mcrfpy.Color(*color)
                self.ui.append(cell_rect)

            # Draw the actual line for comparison
            line = mcrfpy.Line(
                start=(480 + start[0] * cell_size + cell_size // 2,
                       110 + start[1] * cell_size + cell_size // 2),
                end=(480 + end[0] * cell_size + cell_size // 2,
                     110 + end[1] * cell_size + cell_size // 2),
                color=mcrfpy.Color(255, 255, 255, 128),
                thickness=1
            )
            self.ui.append(line)

        # Third demo: Filled circle (planet surface)
        bg3 = mcrfpy.Frame(pos=(30, 410), size=(200, 170))
        bg3.fill_color = mcrfpy.Color(15, 15, 25)
        bg3.outline = 1
        bg3.outline_color = mcrfpy.Color(60, 60, 100)
        self.ui.append(bg3)

        self.add_label("Filled Circle (radius=4)", 50, 415, (255, 200, 100))
        self.add_label("Planet surface representation", 50, 435, (150, 150, 150))

        fill_center = (6, 5)
        fill_radius = 4
        filled_cells = filled_circle(fill_center, fill_radius)

        for x, y in filled_cells:
            px = 40 + x * cell_size
            py = 460 + y * cell_size
            cell_rect = mcrfpy.Frame(pos=(px, py), size=(cell_size - 1, cell_size - 1))
            # Gradient based on distance from center
            dist = ((x - fill_center[0])**2 + (y - fill_center[1])**2) ** 0.5
            intensity = int(255 * (1 - dist / (fill_radius + 1)))
            cell_rect.fill_color = mcrfpy.Color(intensity, intensity // 2, 50)
            self.ui.append(cell_rect)

        # Fourth demo: Combined - planet with orbit ring
        bg4 = mcrfpy.Frame(pos=(250, 410), size=(530, 170))
        bg4.fill_color = mcrfpy.Color(15, 15, 25)
        bg4.outline = 1
        bg4.outline_color = mcrfpy.Color(60, 60, 100)
        self.ui.append(bg4)

        self.add_label("Planet + Orbit Ring", 270, 415, (255, 200, 100))
        self.add_label("Surface (r=3) + Orbit (r=7)", 270, 435, (150, 150, 150))

        planet_center = (16, 5)
        surface_radius = 3
        orbit_radius = 7

        # Draw orbit ring (behind planet)
        orbit_cells = bresenham_circle(planet_center, orbit_radius)
        for x, y in orbit_cells:
            px = 260 + x * cell_size
            py = 460 + y * cell_size
            cell_rect = mcrfpy.Frame(pos=(px, py), size=(cell_size - 1, cell_size - 1))
            cell_rect.fill_color = mcrfpy.Color(50, 150, 50, 180)
            self.ui.append(cell_rect)

        # Draw planet surface (on top)
        surface_cells = filled_circle(planet_center, surface_radius)
        for x, y in surface_cells:
            px = 260 + x * cell_size
            py = 460 + y * cell_size
            cell_rect = mcrfpy.Frame(pos=(px, py), size=(cell_size - 1, cell_size - 1))
            dist = ((x - planet_center[0])**2 + (y - planet_center[1])**2) ** 0.5
            intensity = int(200 * (1 - dist / (surface_radius + 1)))
            cell_rect.fill_color = mcrfpy.Color(50 + intensity, 100 + intensity // 2, 200)
            self.ui.append(cell_rect)

        # Legend
        self.add_label("Legend:", 600, 455, (200, 200, 200))

        leg1 = mcrfpy.Frame(pos=(600, 475), size=(12, 12))
        leg1.fill_color = mcrfpy.Color(100, 150, 200)
        self.ui.append(leg1)
        self.add_label("Planet surface", 620, 473, (150, 150, 150))

        leg2 = mcrfpy.Frame(pos=(600, 495), size=(12, 12))
        leg2.fill_color = mcrfpy.Color(50, 150, 50)
        self.ui.append(leg2)
        self.add_label("Orbit ring (ship positions)", 620, 493, (150, 150, 150))
