# mcrf: objects=[Caption,Color,ColorLayer,Entity,Frame,Grid,InputState,MouseButton,Scene,TileLayer] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("game")
ui = scene.children

texture = mcrfpy.default_texture
terrain = mcrfpy.TileLayer(name="terrain", z_index=-2, texture=texture)
highlight = mcrfpy.ColorLayer(name="highlight", z_index=-1)
overlay = mcrfpy.ColorLayer(name="overlay", z_index=1)

grid = mcrfpy.Grid(
    grid_size=(20, 15),
    pos=(50, 50),
    size=(640, 480),
    layers=[terrain, highlight, overlay]
)
grid.fill_color = mcrfpy.Color(20, 20, 30)
ui.append(grid)

player = mcrfpy.Entity(grid_pos=(10, 7), sprite_index=0)
grid.entities.append(player)

mcrfpy.current_scene = scene

# --- Tile Inspector Panel ---
inspector = mcrfpy.Frame(pos=(700, 50), size=(200, 150),
                          fill_color=mcrfpy.Color(30, 30, 40, 230))
inspector.outline = 1
inspector.outline_color = mcrfpy.Color(80, 80, 100)
inspector.visible = False
ui.append(inspector)

title = mcrfpy.Caption(text="Cell Info", pos=(10, 8))
title.fill_color = mcrfpy.Color(180, 180, 200)
inspector.children.append(title)

info_lines = []
for i in range(4):
    line = mcrfpy.Caption(text="", pos=(10, 30 + i * 20))
    line.fill_color = mcrfpy.Color(160, 160, 180)
    inspector.children.append(line)
    info_lines.append(line)

def on_cell_click(cell_pos, button, action):
    if button == mcrfpy.MouseButton.LEFT and action == mcrfpy.InputState.PRESSED:
        x, y = int(cell_pos.x), int(cell_pos.y)
        point = grid.at(x, y)

        title.text = f"Cell ({x}, {y})"
        info_lines[0].text = f"Walkable: {point.walkable}"
        info_lines[1].text = f"Transparent: {point.transparent}"

        entities_here = [e for e in grid.entities
                         if int(e.grid_x) == x and int(e.grid_y) == y]
        info_lines[2].text = f"Entities: {len(entities_here)}"

        if entities_here:
            info_lines[3].text = f"  {entities_here[0].name or 'unnamed'}"
        else:
            info_lines[3].text = ""

        inspector.visible = True

grid.on_cell_click = on_cell_click
