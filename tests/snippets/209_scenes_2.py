# mcrf: objects=[Caption,Color,Entity,Frame,Grid,InputState,Key,Scene] verified=0.2.8-dev status=ok
import mcrfpy

class TitleScene(mcrfpy.Scene):
    def __init__(self):
        super().__init__("title")

        # Background
        bg = mcrfpy.Frame(pos=(0, 0), size=(800, 600))
        bg.fill_color = mcrfpy.Color(20, 20, 40)
        self.children.append(bg)

        # Title
        title = mcrfpy.Caption(pos=(400, 150), text="DUNGEON EXPLORER")
        title.fill_color = mcrfpy.Color(255, 215, 0)
        self.children.append(title)

        # Subtitle
        subtitle = mcrfpy.Caption(pos=(400, 220), text="A McRogueFace Demo")
        subtitle.fill_color = mcrfpy.Color(180, 180, 180)
        self.children.append(subtitle)

        # Instructions
        start_text = mcrfpy.Caption(pos=(400, 400), text="Press SPACE to start")
        start_text.fill_color = mcrfpy.Color(100, 255, 100)
        self.children.append(start_text)

        self.on_key = self.handle_key

    def handle_key(self, key, action):
        if action == mcrfpy.InputState.PRESSED and key == mcrfpy.Key.SPACE:
            game.activate()


class GameScene(mcrfpy.Scene):
    def __init__(self):
        super().__init__("game")
        self.grid = None
        self.player = None
        self.setup_game()
        self.on_key = self.handle_key

    def setup_game(self):
        # Create grid
        self.grid = mcrfpy.Grid(
            grid_size=(40, 30),
            texture=mcrfpy.default_texture,
            pos=(0, 0),
            size=(800, 600)
        )
        self.children.append(self.grid)

        # Initialize map
        for y in range(30):
            for x in range(40):
                point = self.grid.at(x, y)
                if x == 0 or x == 39 or y == 0 or y == 29:
                    point.tilesprite = 1
                    point.walkable = False
                else:
                    point.tilesprite = 0
                    point.walkable = True

        # Create player
        self.player = mcrfpy.Entity(
            grid_pos=(20, 15),
            texture=mcrfpy.default_texture,
            sprite_index=64
        )
        self.grid.entities.append(self.player)
        self.grid.center = self.player.pos

    def on_enter(self):
        print("Game started!")

    def on_exit(self):
        print("Game paused")

    def handle_key(self, key, action):
        if action != mcrfpy.InputState.PRESSED:
            return

        if key == mcrfpy.Key.ESCAPE:
            title.activate()
            return

        dx, dy = 0, 0
        if key in (mcrfpy.Key.UP, mcrfpy.Key.W): dy = -1
        elif key in (mcrfpy.Key.DOWN, mcrfpy.Key.S): dy = 1
        elif key in (mcrfpy.Key.LEFT, mcrfpy.Key.A): dx = -1
        elif key in (mcrfpy.Key.RIGHT, mcrfpy.Key.D): dx = 1

        if dx or dy:
            self.move_player(dx, dy)

    def move_player(self, dx, dy):
        new_x = self.player.grid_x + dx
        new_y = self.player.grid_y + dy

        if self.grid.at(new_x, new_y).walkable:
            self.player.grid_pos = (new_x, new_y)
            self.grid.center = self.player.pos


# Create and activate scenes
title = TitleScene()
game = GameScene()

title.activate()
