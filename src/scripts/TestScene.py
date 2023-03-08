import UIMenu
import Grid
import mcrfpy
from random import randint
print("TestScene imported")
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED, GREEN, BLUE = (255, 0, 0), (0, 255, 0), (0, 0, 255)
DARKRED, DARKGREEN, DARKBLUE = (192, 0, 0), (0, 192, 0), (0, 0, 192)

class TestScene:
    def __init__(self, ui_name = "demobox1", grid_name = "demogrid"):
        # Texture & Sound Loading
        mcrfpy.createTexture("./assets/test_portraits.png", 32, 8, 8) #0 - portraits
        self.ui_name = ui_name
        self.grid_name = grid_name

        # Create dialog UI
        mcrfpy.createMenu(ui_name, 20, 520, 500, 200)
        mcrfpy.createCaption(ui_name, "Hello There", 18, BLACK)
        mcrfpy.createCaption(ui_name, "", 18, BLACK)
        mcrfpy.createButton(ui_name, 250, 20, 100, 50, DARKBLUE, (0, 0, 0), "clicky", "testaction")
        mcrfpy.createButton(ui_name, 250, 20, 100, 50, DARKRED, (0, 0, 0), "REPL", "startrepl")
        mcrfpy.createButton(ui_name, 250, 20, 100, 50, DARKGREEN, (0, 0, 0), "map gen", "gridgen")
        mcrfpy.createButton(ui_name, 250, 20, 100, 50, DARKBLUE, (192, 0, 0), "anim", "animtest")
        mcrfpy.createSprite(ui_name, 0, randint(0, 3), 300, 20, 5.0)
        self.menus = mcrfpy.listMenus()
        self.menus[0].visible = True
        mcrfpy.modMenu(self.menus[0])

        # Button behavior
        self.clicks = 0
        mcrfpy.registerPyAction("testaction", self.click)
        mcrfpy.registerPyAction("gridgen", self.gridgen)
        mcrfpy.registerPyAction("animtest", lambda: mcrfpy.createAnimation())

        # create grid (title, gx, gy, gs, x, y, w, h)
        mcrfpy.createGrid(grid_name, 20, 20, 16, 20, 20, 800, 500)
        self.grids = mcrfpy.listGrids()

    def click(self):
        self.clicks += 1
        self.menus[0].captions[1].text = f"Clicks: {self.clicks}"
        self.menus[0].sprites[0].sprite_index = randint(0, 3)
        mcrfpy.modMenu(self.menus[0])

    def gridgen(self):
        print(f"[Python] modifying {len(self.grids[0].points)} grid points")
        for p in self.grids[0].points:
            p.color = (randint(0, 255), randint(64, 192), 0)
        print("[Python] Modifying:")
        self.grids[0].visible = True
        mcrfpy.modGrid(self.grids[0])
scene = None
def start():
    global scene
    print("TestScene.start called")
    scene = TestScene()

