# mcrf: objects=[Caption,Color,Easing,Scene,Timer] verified=0.2.8-dev status=ok
import mcrfpy

def show_damage(scene, x, y, amount, color=(255, 50, 50)):
    """Display floating damage number that rises and fades."""
    # Create the caption
    caption = mcrfpy.Caption(text=str(amount), x=x, y=y)
    caption.fill_color = mcrfpy.Color(color[0], color[1], color[2], 255)
    caption.font_size = 24
    scene.children.append(caption)

    # Animate upward movement
    caption.animate("y", float(y - 50), 0.8, mcrfpy.Easing.EASE_OUT)

    # Animate fade out
    caption.animate("opacity", 0.0, 0.8, mcrfpy.Easing.EASE_IN)

    # Remove caption after animation completes
    def cleanup(timer, runtime):
        try:
            scene.children.remove(caption)
        except ValueError:
            pass

    mcrfpy.Timer("cleanup_damage", cleanup, 850, once=True)

# Usage
game_scene = mcrfpy.Scene("game")
mcrfpy.current_scene = game_scene
show_damage(game_scene, 400, 300, 42)
