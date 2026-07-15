# mcrf: objects=[Alignment,Caption,Color,Frame,Scene] verified=0.2.8-dev status=ok
import mcrfpy


def show_modal(scene, title, message):
    """Display a centered modal dialog."""
    # Overlay background
    overlay = mcrfpy.Frame(pos=(0, 0), size=(800, 600))
    overlay.fill_color = mcrfpy.Color(0, 0, 0, 128)
    scene.children.append(overlay)

    # Dialog box - centered
    dialog = mcrfpy.Frame(pos=(0, 0), size=(300, 200))
    dialog.fill_color = mcrfpy.Color(40, 40, 50)
    dialog.outline = 2
    dialog.outline_color = mcrfpy.Color(100, 100, 120)
    dialog.align = mcrfpy.Alignment.CENTER
    overlay.children.append(dialog)

    # Title - centered at top of dialog
    title_caption = mcrfpy.Caption(text=title, pos=(0, 0))
    title_caption.align = mcrfpy.Alignment.TOP_CENTER
    title_caption.vert_margin = 20.0
    dialog.children.append(title_caption)

    # Message - centered
    msg_caption = mcrfpy.Caption(text=message, pos=(0, 0))
    msg_caption.align = mcrfpy.Alignment.CENTER
    dialog.children.append(msg_caption)

    return overlay


scene = mcrfpy.Scene("ui_alignment_modal")
mcrfpy.current_scene = scene
show_modal(scene, "Game Over", "You have died.")
