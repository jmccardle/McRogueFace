import UIMenu
import Grid
import mcrfpy
from random import randint, choice
from pprint import pprint
#print("TestScene imported")
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED, GREEN, BLUE = (255, 0, 0), (0, 255, 0), (0, 0, 255)
DARKRED, DARKGREEN, DARKBLUE = (192, 0, 0), (0, 192, 0), (0, 0, 192)

animations_in_progress = 0

# don't load grid over and over, use the global scene
scene = None

class TestEntity:
    def __init__(self, grid, label, tex_index, basesprite, x, y, texture_width=64, walk_frames=5, attack_frames=6, do_fov=False):
        self.grid = grid
        self.basesprite = basesprite
        self.texture_width = texture_width
        self.walk_frames = walk_frames
        self.attack_frames = attack_frames
        self.x = x
        self.y = y
        self.facing_direction = 0
        self.do_fov = do_fov
        self.label = label
        self.inventory = []
        #print(f"Calling C++ with: {repr((self.grid, label, tex_index, self.basesprite, x, y, self))}")
        grids = mcrfpy.listGrids()
        for g in grids:
            if g.title == self.grid:
                self.entity_index = len(g.entities)
        mcrfpy.createEntity(self.grid, label, tex_index, self.basesprite, x, y, self)
        
    def ai_act(self):
        return # no AI motion
        #if self.label == "player": return
        self.move(randint(-1, 1), randint(-1, 1))
        scene.actors += 1
        
    def player_act(self):
        #print("I'M INTERVENING")
        mcrfpy.unlockPlayerInput()
        scene.updatehints()
        
    def die(self):
        #self.x = -2
        #self.y = -2
        self.move(-1000,-1000)
        self.animate(0,animove=(-1000,-1000))
        self.x = -1000
        self.y = -1000
        self.label = "dead"
        
    def interact(self, initiator, callback):
        print(f"Interacted with {self.label}. ", end='')
        if self.label == 'item':
            print("'taking' item.")
            callback()
            self.die()
        else:
            print("blocking movement.")
    
    def move(self, dx, dy, force=False):
        # select animation direction
        # prefer left or right for diagonals.
        #grids = mcrfpy.listGrids()
        for g in scene.grids:
            if g.title == self.grid:
                if not force and g.at(self.x + dx, self.y + dy) is None or not g.at(self.x + dx, self.y + dy).walkable:
                    #print("Blocked at target location.")
                    return
                if not force: # entities can be stepped on when force=True (like collecting items!)
                    for entity in scene.tes:
                        if (entity.x, entity.y) == (self.x + dx, self.y + dy):
                            print(f"Blocked by entity {entity.label} at ({entity.x}, {entity.y})")
                            return entity.interact(self, lambda: self.move(dx, dy, force=True))
        if self.label == "player": 
            mcrfpy.lockPlayerInput()
            scene.updatehints()
        if (dx == 0 and dy == 0):
            direction = self.facing_direction # TODO, jump straight to computer turn
        elif (dx):
            direction = 2 if dx == +1 else 3
        else:
            direction = 0 if dy == +1 else 1
        self.animate(direction, move=True, animove=(self.x + dx, self.y+dy))
        self.facing_direction = direction
        if (self.do_fov): mcrfpy.refreshFov()

        
    def animate(self, direction, attacking=False, move=False, animove=None):
        start_sprite = self.basesprite + (self.texture_width * (direction + (4 if attacking else 0)))
        animation_frames = [start_sprite + i for i in range((self.attack_frames if attacking else self.walk_frames))]
        mcrfpy.createAnimation(
            0.15, # duration, seconds
            self.grid, # parent: a UIMenu or Grid key
            "entity", # target type: 'menu', 'grid', 'caption', 'button', 'sprite', or 'entity'
            self.entity_index, # target id: integer index for menu or grid objs; None for grid/menu
            "sprite", # field: 'position', 'size', 'bgcolor', 'textcolor', or 'sprite'
            self.animation_done, #callback: callable once animation is complete
            False, #loop: repeat indefinitely
            animation_frames # values: iterable of frames for 'sprite', lerp target for others
        )
        #global animations_in_progress
        #animations_in_progress += 1
        if move:
            pos = [self.x, self.y]
            if (direction == 0): pos[1] += 1
            elif (direction == 1): pos[1] -= 1
            elif (direction == 2): pos[0] += 1
            elif (direction == 3): pos[0] -= 1
            if not animove: 
                self.x, self.y = pos
                animove = pos
            else: 
                pos = animove
                self.x, self.y = animove
            #scene.move_entity(self.grid, self.entity_index, pos)
            #for g in mcrfpy.listGrids():
            for g in scene.grids:
                if g.title == self.grid:
                    g.entities[self.entity_index].x = pos[0]
                    g.entities[self.entity_index].y = pos[1]
                    mcrfpy.modGrid(g, True)
        if animove:
            mcrfpy.createAnimation(
                0.25, # duration, seconds
                self.grid, # parent: a UIMenu or Grid key
                "entity", # target type: 'menu', 'grid', 'caption', 'button', 'sprite', or 'entity'
                self.entity_index, # target id: integer index for menu or grid objs; None for grid/menu
                "position", # field: 'position', 'size', 'bgcolor', 'textcolor', or 'sprite'
                self.animation_done, #callback: callable once animation is complete
                False, #loop: repeat indefinitely
                animove # values: iterable of frames for 'sprite', lerp target for others
            )
            #animations_in_progress += 1

        
    def animation_done(self):
        #global animations_in_progress
        #animations_in_progress -= 1
        scene.actors -= 1
        #print(f"{self} done animating - {scene.actors} remaining")
        if scene.actors <= 0:
            scene.actors = 0
            mcrfpy.unlockPlayerInput()
            scene.updatehints()

class TestItemEntity(TestEntity):
    def __init__(self, grid, label, tex_index, basesprite, x, y, texture_width=64, walk_frames=5, attack_frames=6, do_fov=False, item="Nothing"):
        super().__init__(grid, label, tex_index, basesprite, x, y, texture_width, walk_frames, attack_frames, do_fov)
        self.item = item
    
    def interact(self, initiator, callback):
        if self.label == 'dead': return super().interact(initiator, callback)
        print(f"Interacted with {self.label}, an item. Adding {self.item} to {initiator.label}'s inventory")
        initiator.inventory.append(self.item)
        callback()
        scene.itemguis()
        self.die()
        
class TestDoorEntity(TestEntity):
    def __init__(self, grid, label, tex_index, basesprite, x, y, texture_width=64, walk_frames=5, attack_frames=6, do_fov=False, key="Nothing"):
        super().__init__(grid, label, tex_index, basesprite, x, y, texture_width, walk_frames, attack_frames, do_fov)
        self.key = key
        
    def interact(self, initiator, callback):
        if self.label == 'dead': return super().interact(initiator, callback)
        print(f"Interacted with {self.label}, a Door. ", end='')
        if self.key in initiator.inventory:
            initiator.inventory.remove(self.key)
            print("Taking key & passing.")
            callback()
            scene.itemguis()
            self.die()
        else:
            print("The door is locked.")

class TestScene:
    def __init__(self, ui_name = "demobox1", grid_name = "demogrid"):
        # Texture & Sound Loading
        self.actors = 0
        #print("Load textures")
        mcrfpy.createTexture("./assets/test_portraits.png", 32, 8, 8) #0 - portraits
        mcrfpy.createTexture("./assets/alives_other.png", 16, 64, 64) #1 - TinyWorld NPCs
        mcrfpy.createTexture("./assets/alives_other.png", 32, 32, 32) #2 - TinyWorld NPCs - 2x2 sprite
        mcrfpy.createTexture("./assets/custom_player.png", 16, 5, 13) #3 - player
        mcrfpy.createTexture("./assets/Sprite-0001.png", 80, 10, 10) #4 - LGJ2023 keycard + other icons
        mcrfpy.createTexture("./assets/tiny_keycards.png", 16, 8, 8) #5 - tiny keycards (ground items)
        self.ui_name = ui_name
        self.grid_name = grid_name

        # Menu index = 0
        #print("Create UI")
        # Create dialog UI
        mcrfpy.createMenu(ui_name, 20, 540, 500, 200)
        #mcrfpy.createCaption(ui_name, "Hello There", 18, BLACK)
        mcrfpy.createCaption(ui_name, "", 24, RED)
        #mcrfpy.createButton(ui_name, 250, 20, 100, 50, DARKBLUE, (0, 0, 0), "clicky", "testaction")
        mcrfpy.createButton(ui_name, 250, 0, 130, 40, DARKRED, (0, 0, 0), "REPL", "startrepl")
        ##mcrfpy.createButton(ui_name, 250, 0, 130, 40, DARKGREEN, (0, 0, 0), "map gen", "gridgen")
        #mcrfpy.createButton(ui_name, 250, 20, 100, 50, DARKGREEN, (0, 0, 0), "mapL", "gridgen2")
        #mcrfpy.createButton(ui_name, 250, 20, 100, 50, DARKBLUE, (192, 0, 0), "a_menu", "animtest")
        #mcrfpy.createButton(ui_name, 250, 20, 100, 50, DARKRED, GREEN, "a_spr", "animtest2")
        #mcrfpy.createButton(ui_name, 250, 0, 130, 40, DARKBLUE, GREEN, "Next sp", "nextsp")
        #mcrfpy.createButton(ui_name, 250, 0, 130, 40, DARKBLUE, RED, "Prev sp", "prevsp")
        #mcrfpy.createButton(ui_name, 250, 0, 130, 40, DARKBLUE, DARKGREEN, "+16 sp", "skipsp")
        mcrfpy.createButton(ui_name, 250, 0, 130, 40, DARKGREEN, (0, 0, 0), "Next", "nextsp")
        mcrfpy.createButton(ui_name, 250, 0, 130, 40, DARKBLUE, (0, 0, 0), "Prev", "prevsp")
        mcrfpy.createSprite(ui_name, 4, 1, 10, 10, 2.0)
        
        # Menu index = 1
        #print("Create UI 2")
        entitymenu = "entitytestmenu"
        mcrfpy.createMenu(entitymenu, 840, 20, 20, 500)
        mcrfpy.createButton(entitymenu, 0, 10, 150, 40, DARKBLUE, BLACK, "Up", "test_up")
        mcrfpy.createButton(entitymenu, 0, 60, 150, 40, DARKBLUE, BLACK, "Down", "test_down")
        mcrfpy.createButton(entitymenu, 0, 110, 150, 40, DARKBLUE, BLACK, "Left", "test_left")
        mcrfpy.createButton(entitymenu, 0, 160, 150, 40, DARKBLUE, BLACK, "Right", "test_right")
        mcrfpy.createButton(entitymenu, 0, 210, 150, 40, DARKBLUE, BLACK, "Attack", "test_attack")
        mcrfpy.createButton(entitymenu, 0, 210, 150, 40, DARKBLUE, RED, "TE", "testent")
        
        # Menu index = 2
        mcrfpy.createMenu(   "gridtitlemenu", 0, -10, 0, 0)
        mcrfpy.createCaption("gridtitlemenu", "<grid name>", 18, WHITE)
        #mcrfpy.createCaption("gridtitlemenu", "<camstate>", 16, WHITE)
        
        # Menu index = 3
        mcrfpy.createMenu(   "hintsmenu", 0, 505, 0, 0)
        mcrfpy.createCaption("hintsmenu", "<hintline>", 16, WHITE)
        
        # Menu index = 4
        # menu names must be created in alphabetical order (?!) - thanks, C++ hash map
        mcrfpy.createMenu(   "i",            600, 20, 0, 0)
        #mcrfpy.createMenu(   "camstatemenu", 600, 20, 0, 0)
        mcrfpy.createCaption("i", "<camstate>", 16, WHITE)
        
        # Menu index = 5
        mcrfpy.createMenu( "j", 600, 500, 0, 0)
        mcrfpy.createButton( "j", 0, 0, 80, 40, DARKBLUE, WHITE, "Recenter", "activatecamfollow")
        
        # Menu index = 6, 7, 8, 9, 10: keycard sprites
        mcrfpy.createMenu("k", 540, 540, 80, 80) #6
        mcrfpy.createSprite("k", 4, 0, 10, 10, 1.0)
        
        mcrfpy.createMenu("l", 540 + (80 * 1), 540, 80, 80) #7
        mcrfpy.createSprite("l", 4, 1, 10, 10, 1.0)
        
        mcrfpy.createMenu("m", 540 + (80 * 2), 540, 80, 80) #8
        mcrfpy.createSprite("m", 4, 2, 10, 10, 1.0)
        
        mcrfpy.createMenu("n", 540 + (80 * 3), 540, 80, 80) #9
        mcrfpy.createSprite("n", 4, 3, 10, 10, 1.0)
        
        mcrfpy.createMenu("o", 540 + (80 * 4), 540, 80, 80) #10
        mcrfpy.createSprite("o", 4, 4, 10, 10, 1.0)
        
        mcrfpy.createMenu("p", 20, 20, 40, 40) #11
        #mcrfpy.createButton("p", 0, 0, 130, 40, DARKGREEN, (0, 0, 0), "Register", "keyregistration")
        mcrfpy.createButton("p", 0, 0, 130, 40, DARKGREEN, (0, 0, 0), "Register", "startrepl")
        mcrfpy.registerPyAction("keyregistration", keyregistration)
        #print("Make UIs visible")
        self.menus = mcrfpy.listMenus()
        self.menus[0].visible = True
        self.menus[1].w = 170
        self.menus[1].visible = True
        self.menus[2].visible = True
        
        for mn in range(2, 6):
            self.menus[mn].bgcolor = BLACK
            self.menus[mn].visible = True
            mcrfpy.modMenu(self.menus[mn])
        
        for mn in range(6, 11):
            self.menus[mn].bgcolor = BLACK
            self.menus[mn].visible = False
            mcrfpy.modMenu(self.menus[mn])
        
        self.menus[11].visible=True
        mcrfpy.modMenu(self.menus[11])
                                            
        #self.menus[2].bgcolor = BLACK
        #self.menus[3].visible = True
        #self.menus[3].bgcolor = BLACK
        #self.menus[4].visible = True
        #self.menus[4].bgcolor = BLACK
        #self.menus[5].visible = True
        #mcrfpy.modMenu(self.menus[0])
        #mcrfpy.modMenu(self.menus[1])
        #mcrfpy.modMenu(self.menus[2])
        #mcrfpy.modMenu(self.menus[3])
        #mcrfpy.modMenu(self.menus[4])
        #mcrfpy.modMenu(self.menus[5])
        #pprint(mcrfpy.listMenus())
        #print(f"UI 1 gave back this sprite: {self.menus[0].sprites}")

        #print("Create grid")
        # create grid (title, gx, gy, gs, x, y, w, h)
        mcrfpy.createGrid(grid_name, 100, 100, 16, 20, 20, 800, 500)
        self.grids = mcrfpy.listGrids()
        #print(self.grids)
        
        #print("Create entities")
        #mcrfpy.createEntity("demogrid", "dragon", 2, 545, 10, 10, lambda: None)
        #mcrfpy.createEntity("demogrid", "tinyenemy", 1, 1538, 3, 6, lambda: None)
        
        #print("Create fancy entity")
        self.player = TestEntity("demogrid", "player", 3, 20, 17, 3, 5, walk_frames=4, attack_frames=5, do_fov=True)
        self.tes = [
            TestEntity("demogrid", "classtest", 1, 1538, 5, 7, 64, walk_frames=5, attack_frames=6),
            TestEntity("demogrid", "classtest", 1, 1545, 7, 9, 64, walk_frames=5, attack_frames=6),
            TestEntity("demogrid", "classtest", 1, 1552, 9, 11, 64, walk_frames=5, attack_frames=6),
            TestEntity("demogrid", "classtest", 1, 1566, 11, 13, 64, walk_frames=4, attack_frames=6),
            #TestEntity("demogrid", "item", 1, 1573, 13, 15, 64, walk_frames=4, attack_frames=6),
            TestEntity("demogrid", "classtest", 1, 1583, 15, 17, 64, walk_frames=4, attack_frames=6),
            TestEntity("demogrid", "classtest", 1, 130, 9, 7, 64, walk_frames=5, attack_frames=6),
            TestEntity("demogrid", "classtest", 1, 136, 11, 9, 64, walk_frames=5, attack_frames=6),
            TestEntity("demogrid", "classtest", 1, 143, 13, 11, 64, walk_frames=5, attack_frames=6),
            TestEntity("demogrid", "classtest", 1, 158, 15, 13, 64, walk_frames=5, attack_frames=6),
            TestEntity("demogrid", "classtest", 1, 165, 17, 15, 64, walk_frames=5, attack_frames=6),
            self.player,
            
            TestItemEntity("demogrid", "GreenKeyCard", 5, 0, 19, 3, texture_width=64,
                           walk_frames=5, attack_frames=6, do_fov=False, item="Green Keycard"),
            TestItemEntity("demogrid", "BlueKeyCard", 5, 1, 21, 3, texture_width=64,
                           walk_frames=5, attack_frames=6, do_fov=False, item="Blue Keycard"),
            TestItemEntity("demogrid", "RedKeyCard", 5, 2, 23, 3, texture_width=64,
                           walk_frames=5, attack_frames=6, do_fov=False, item="Red Keycard"),
            TestItemEntity("demogrid", "OrangeKeyCard", 5, 3, 25, 3, texture_width=64,
                           walk_frames=5, attack_frames=6, do_fov=False, item="Orange Keycard"),
            TestItemEntity("demogrid", "DevilKeyCard", 5, 4, 27, 3, texture_width=64,
                           walk_frames=5, attack_frames=6, do_fov=False, item="Devil Keycard"),
            
             TestDoorEntity("demogrid", "GreenKeyDoor",  5, 8,   19, 5, texture_width=64,
                            walk_frames=5, attack_frames=6, do_fov=False, key="Green Keycard"),
             TestDoorEntity("demogrid", "BlueKeyDoor",   5, 9,   21, 5, texture_width=64,
                            walk_frames=5, attack_frames=6, do_fov=False, key="Blue Keycard"),
             TestDoorEntity("demogrid", "RedKeyDoor",    5, 10,  23, 5, texture_width=64,
                            walk_frames=5, attack_frames=6, do_fov=False, key="Red Keycard"),
             TestDoorEntity("demogrid", "OrangeKeyDoor", 5, 11,  25, 5, texture_width=64,
                            walk_frames=5, attack_frames=6, do_fov=False, key="Orange Keycard"),
             TestDoorEntity("demogrid", "DevilKeyDoor",  5, 12,  27, 5, texture_width=64,
                            walk_frames=5, attack_frames=6, do_fov=False, key="Devil Keycard")
            ]
        self.grids = mcrfpy.listGrids()
        
        self.entity_direction = 0
        mcrfpy.registerPyAction("test_down",   lambda: [te.animate(0, False, True) for te in self.tes])
        mcrfpy.registerPyAction("test_up",     lambda: [te.animate(1, False, True) for te in self.tes])
        mcrfpy.registerPyAction("test_right",  lambda: [te.animate(2, False, True) for te in self.tes])
        mcrfpy.registerPyAction("test_left",   lambda: [te.animate(3, False, True) for te in self.tes])
        mcrfpy.registerPyAction("test_attack", lambda: [te.animate(0, True) for te in self.tes])
        mcrfpy.registerPyAction("testent",     lambda: [te.animate(2, True) for te in self.tes])
        mcrfpy.registerPyAction("activatecamfollow", lambda: mcrfpy.camFollow(True))

        # Button behavior
        self.clicks = 0
        self.sprite_index = 0
        #mcrfpy.registerPyAction("testaction", self.click)
        mcrfpy.registerPyAction("gridgen", self.gridgen)
        #mcrfpy.registerPyAction("gridgen2", lambda: self.gridgen())
        #mcrfpy.registerPyAction("animtest", lambda: self.createAnimation())
        #mcrfpy.registerPyAction("animtest2", lambda: self.createAnimation2())
        mcrfpy.registerPyAction("nextsp", lambda: self.changesprite(1))
        mcrfpy.registerPyAction("prevsp", lambda: self.changesprite(-1))
        mcrfpy.registerPyAction("skipsp", lambda: self.changesprite(16))
        mcrfpy.unlockPlayerInput()
        mcrfpy.setActiveGrid("demogrid")
        self.gridgen()
        self.updatehints()
        mcrfpy.camFollow(True)
        
    def itemguis(self):
        print(self.player.inventory)
        items = ["Green Keycard", "Blue Keycard", "Red Keycard", "Orange Keycard", "Devil Keycard"]
        for mn in range(6, 11):
            self.menus[mn].visible = items[mn-6] in self.player.inventory
            mcrfpy.modMenu(self.menus[mn])

    def animate_entity(self, direction, attacking=False):
        if direction is None:
            direction = self.entity_direction
        else:
            self.entity_direction = direction
        
        dragon_sprite = 545 + (32 * (direction + (4 if attacking else 0)))
        dragon_animation = [dragon_sprite + i for i in range((5 if attacking else 4))]
        mcrfpy.createAnimation(
            1.0, # duration, seconds
            "demogrid", # parent: a UIMenu or Grid key
            "entity", # target type: 'menu', 'grid', 'caption', 'button', 'sprite', or 'entity'
            0, # target id: integer index for menu or grid objs; None for grid/menu
            "sprite", # field: 'position', 'size', 'bgcolor', 'textcolor', or 'sprite'
            lambda: self.animation_done("demobox1"), #callback: callable once animation is complete
            False, #loop: repeat indefinitely
            dragon_animation # values: iterable of frames for 'sprite', lerp target for others
        )
        
        orc_sprite = 1538 + (64 * (direction + (4 if attacking else 0)))
        orc_animation = [orc_sprite + i for i in range((5 if attacking else 4))]
        mcrfpy.createAnimation(
            1.0, # duration, seconds
            "demogrid", # parent: a UIMenu or Grid key
            "entity", # target type: 'menu', 'grid', 'caption', 'button', 'sprite', or 'entity'
             1, # target id: integer index for menu or grid objs; None for grid/menu
             "sprite", # field: 'position', 'size', 'bgcolor', 'textcolor', or 'sprite'
             lambda: self.animation_done("demobox1"), #callback: callable once animation is complete
             False, #loop: repeat indefinitely
             orc_animation # values: iterable of frames for 'sprite', lerp target for others
        )
        
    #def move_entity(self, targetgrid, entity_index, position):
    #    for i, g in enumerate(self.grids):
    #        if g.title == targetgrid:
    #            g.entities[entity_index].x = position[0]
    #            g.entities[entity_index].y = position[1]
    #            #pts = g.points
    #            g.visible = True
    #            mcrfpy.modGrid(g)
    #            self.grids = mcrfpy.listGrids()
    #            #self.grids[i].points = pts
    #            return
        
        
    def changesprite(self, n):
        self.sprite_index += n
        self.menus[0].captions[0].text = f"Sprite #{self.sprite_index}"
        self.menus[0].sprites[0].sprite_index = self.sprite_index
        mcrfpy.modMenu(self.menus[0])
        
    def click(self):
        self.clicks += 1
        self.menus[0].captions[0].text = f"Clicks: {self.clicks}"
        self.menus[0].sprites[0].sprite_index = randint(0, 3)
        mcrfpy.modMenu(self.menus[0])
        
    def updatehints(self):
        self.menus[2].captions[0].text=mcrfpy.activeGrid()
        mcrfpy.modMenu(self.menus[2])
        
        self.menus[3].captions[0].text=mcrfpy.inputMode()
        mcrfpy.modMenu(self.menus[3])
        #self.menus[4].captions[0].text=f"follow: {mcrfpy.camFollow()}"
        
        self.menus[4].captions[0].text="following" if mcrfpy.camFollow() else "free"
        mcrfpy.modMenu(self.menus[4])
        
        self.menus[5].visible = not mcrfpy.camFollow()
        mcrfpy.modMenu(self.menus[5])
        

    def gridgen(self):
        
        #print(f"[Python] modifying {len(self.grids[0].points)} grid points")
        for p in self.grids[0].points:
            #p.color = (randint(0, 255), randint(64, 192), 0)
            p.color = (0,0,0)
            p.walkable = False
            p.transparent = False
            
        room_centers = [(randint(0, self.grids[0].grid_x-1), randint(0, self.grids[0].grid_y-1)) for i in range(20)] + [(17, 3), (20,10) + (20,5)]
        #room_centers.append((3, 5))
        for r in room_centers:
            # random hallway
            target = choice(room_centers)
            length1 = abs(target[0] - r[0])
            
            xbase = min(target[0], r[0])
            for x in range(length1):
                gpoint = self.grids[0].at(x, r[1])
                if gpoint is None: continue
                gpoint.walkable = True
                gpoint.transparent = True
                gpoint.color = (192, 192, 192)
            
            length2 = abs(target[1] - r[1])
            ybase = min(target[1], r[1])
            for y in range(length2):
                gpoint = self.grids[0].at(r[0], y)
                if gpoint is None: continue
                gpoint.walkable = True
                gpoint.transparent = True
                gpoint.color = (192, 192, 192)
                
        for r in room_centers:
            #print(r)
            room_color = (randint(16, 24)*8, randint(16, 24)*8, randint(16, 24)*8)
            #self.grids[0].at(r[0], r[1]).walkable = True
            #self.grids[0].at(r[0], r[1]).color = room_color
            halfx, halfy = randint(2, 11), randint(2,11)
            for p_x in range(r[0] - halfx, r[0] + halfx):
                for p_y in range(r[1] - halfy, r[1] + halfy):
                    gpoint = self.grids[0].at(p_x, p_y)
                    if gpoint is None: continue
                    gpoint.walkable = True
                    gpoint.transparent = True
                    gpoint.color = room_color
            #print()
                    
        #print("[Python] Modifying:")
        self.grids[0].at(10, 10).color = (255, 255, 255)
        self.grids[0].at(10, 10).walkable = False
        self.grids[0].visible = True
        mcrfpy.modGrid(self.grids[0])
        #self.grids = mcrfpy.listGrids()
        #print(f"Sent grid: {repr(self.grids[0])}")
        #print(f"Received grid: {repr(mcrfpy.listGrids()[0])}")
        
    def animation_done(self, s):
        print(f"The `{s}` animation completed.")
        #self.menus = mcrfpy.listMenus()
        
    # if (!PyArg_ParseTuple(args, "fsssiOOO", &duration, &parent, &target_type, &target_id, &field, &callback, &loop_obj, &values_obj)) return NULL;
    def createAnimation(self):
        print(self.menus)
        self.menus = mcrfpy.listMenus()
        self.menus[0].w = 500
        self.menus[0].h = 200
        print(self.menus)
        mcrfpy.modMenu(self.menus[0])
        print(self.menus)
        mcrfpy.createAnimation(
            3.0, # duration, seconds
            "demobox1", # parent: a UIMenu or Grid key
            "menu", # target type: 'menu', 'grid', 'caption', 'button', 'sprite', or 'entity'
            0, # target id: integer index for menu or grid objs; None for grid/menu
            "size", # field: 'position', 'size', 'bgcolor', 'textcolor', or 'sprite'
            lambda: self.animation_done("demobox1"), #callback: callable once animation is complete
            False, #loop: repeat indefinitely
            [150, 100] # values: iterable of frames for 'sprite', lerp target for others
        )
        
    def createAnimation2(self):
        mcrfpy.createAnimation(
            5,
            "demobox1",
            "sprite",
            0,
            "sprite",
            lambda: self.animation_done("sprite change"),
            False,
            [0, 1, 2, 1, 2, 0]
        )

def keytest():
    print("Key tested.")

def keyregistration():
    print("Registering 'keytest'")
    mcrfpy.registerPyAction("keytest", keytest)
    print("Registering input")
    print(mcrfpy.registerInputAction(15, "keytest")) # 15 = P
    
    mcrfpy.registerPyAction("player_move_up", lambda: scene.player.move(0, -1))
    mcrfpy.registerPyAction("player_move_left", lambda: scene.player.move(-1, 0))
    mcrfpy.registerPyAction("player_move_down", lambda: scene.player.move(0, 1))
    mcrfpy.registerPyAction("player_move_right", lambda: scene.player.move(1, 0))
    
    mcrfpy.registerInputAction(ord('w') - ord('a'), "player_move_up")
    mcrfpy.registerInputAction(ord('a') - ord('a'), "player_move_left")
    mcrfpy.registerInputAction(ord('s') - ord('a'), "player_move_down")
    mcrfpy.registerInputAction(ord('d') - ord('a'), "player_move_right")
    

def start():
    global scene
    #print("TestScene.start called")
    scene = TestScene()
    mcrfpy.refreshFov()
    
    
    scene.updatehints()
