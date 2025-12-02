"""Grid system demonstration."""
import mcrfpy
from .base import DemoScreen

class GridDemo(DemoScreen):
    name = "Grid System"
    description = "Tile-based grid with entities, FOV, and pathfinding"

    def setup(self):
        self.add_title("Grid System")
        self.add_description("Multi-layer rendering with camera, zoom, and children support")

        # Create a grid with no default layers
        grid = mcrfpy.Grid(grid_size=(15, 10), pos=(50, 120), size=(400, 280), layers={})
        grid.fill_color = mcrfpy.Color(20, 20, 40)

        # Add a color layer for the checkerboard pattern (z_index=-1 = below entities)
        color_layer = grid.add_layer("color", z_index=-1)

        # Center camera on middle of grid (in pixel coordinates: cells * cell_size / 2)
        # For 15x10 grid with 16x16 cells: center = (15*16/2, 10*16/2) = (120, 80)
        grid.center = (120, 80)
        self.ui.append(grid)

        # Set tile colors via the color layer to create a pattern
        for x in range(15):
            for y in range(10):
                point = grid.at(x, y)
                # Checkerboard pattern
                if (x + y) % 2 == 0:
                    color_layer.set(x, y, mcrfpy.Color(40, 40, 60))
                else:
                    color_layer.set(x, y, mcrfpy.Color(30, 30, 50))

                # Border
                if x == 0 or x == 14 or y == 0 or y == 9:
                    color_layer.set(x, y, mcrfpy.Color(80, 60, 40))
                    point.walkable = False

        # Add some children to the grid
        highlight = mcrfpy.Circle(center=(7*16 + 8, 5*16 + 8), radius=12,
                                  fill_color=mcrfpy.Color(255, 255, 0, 80),
                                  outline_color=mcrfpy.Color(255, 255, 0),
                                  outline=2)
        grid.children.append(highlight)

        label = mcrfpy.Caption(text="Grid Child", pos=(5*16, 3*16))
        label.fill_color = mcrfpy.Color(255, 200, 100)
        grid.children.append(label)

        # Info panel
        info = mcrfpy.Frame(pos=(480, 120), size=(280, 280))
        info.fill_color = mcrfpy.Color(40, 40, 50)
        info.outline = 1
        info.outline_color = mcrfpy.Color(80, 80, 100)
        self.ui.append(info)

        props = [
            "grid_size: (15, 10)",
            "layers: [ColorLayer]",
            "center: (120, 80)",
            "",
            "Features:",
            "- Multi-layer rendering",
            "- Camera pan/zoom",
            "- Children collection",
            "- FOV/pathfinding",
        ]
        for i, text in enumerate(props):
            cap = mcrfpy.Caption(text=text, pos=(10, 10 + i*22))
            cap.fill_color = mcrfpy.Color(180, 180, 200)
            info.children.append(cap)

        # Code example
        code = """# Grid with layers
grid = mcrfpy.Grid(grid_size=(20, 15), pos=(50, 50), size=(320, 240), layers={})
layer = grid.add_layer("color", z_index=-1)  # Below entities
layer.set(5, 5, mcrfpy.Color(255, 0, 0))  # Red tile
grid.children.append(mcrfpy.Caption("Label", pos=(80, 48)))"""
        self.add_code_example(code, y=420)
