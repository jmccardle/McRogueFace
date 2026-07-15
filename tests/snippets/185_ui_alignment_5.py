# mcrf: objects=[Alignment,Caption,Color,Frame,Scene] verified=0.2.8-dev status=ok
import mcrfpy


def create_hud(scene):
    """Create HUD with elements in each corner."""
    # Full-screen container
    hud = mcrfpy.Frame(pos=(0, 0), size=(800, 600))
    hud.fill_color = mcrfpy.Color(0, 0, 0, 0)  # Transparent
    scene.children.append(hud)

    # Health in top-left
    health = mcrfpy.Frame(pos=(0, 0), size=(200, 40))
    health.align = mcrfpy.Alignment.TOP_LEFT
    health.margin = 10.0
    hud.children.append(health)

    # Score in top-right
    score = mcrfpy.Caption(text="Score: 0", pos=(0, 0))
    score.align = mcrfpy.Alignment.TOP_RIGHT
    score.margin = 10.0
    hud.children.append(score)

    # Inventory in bottom-left
    inventory = mcrfpy.Frame(pos=(0, 0), size=(150, 100))
    inventory.align = mcrfpy.Alignment.BOTTOM_LEFT
    inventory.margin = 10.0
    hud.children.append(inventory)

    # Minimap in bottom-right
    minimap = mcrfpy.Frame(pos=(0, 0), size=(120, 120))
    minimap.align = mcrfpy.Alignment.BOTTOM_RIGHT
    minimap.margin = 10.0
    hud.children.append(minimap)

    return hud


scene = mcrfpy.Scene("ui_alignment_hud")
mcrfpy.current_scene = scene
create_hud(scene)
