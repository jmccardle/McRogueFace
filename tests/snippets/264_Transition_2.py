# mcrf: objects=[Caption,Scene,Transition] verified=0.2.8-dev status=ok
import mcrfpy


class GameScene(mcrfpy.Scene):
    def __init__(self):
        super().__init__("game")
        self.setup_ui()

    def setup_ui(self):
        self.children.append(mcrfpy.Caption(text="Game", pos=(10, 10)))

    def on_enter(self):
        """Called after transition completes."""
        print("Game scene active!")

    def on_exit(self):
        """Called before transition to another scene."""
        print("Leaving game scene...")


class MenuScene(mcrfpy.Scene):
    def __init__(self, game_scene):
        super().__init__("menu")
        self.game_scene = game_scene
        self.setup_menu()

    def setup_menu(self):
        self.children.append(mcrfpy.Caption(text="Menu", pos=(10, 10)))

    def start_game(self):
        self.game_scene.activate(mcrfpy.Transition.FADE, duration=0.5)


# Usage
game = GameScene()
menu = MenuScene(game)
menu.activate()  # Start at menu
