import mcrfpy
#t = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16) # 12, 11)
#t = mcrfpy.Texture("assets/kenney_TD_MR_IP.png", 16, 16) # 12, 11)
font = mcrfpy.Font("assets/JetbrainsMono.ttf")

frame_color = (64, 64, 128)

import random
import cos_entities as ce
import cos_level as cl
#import cos_tiles as ct

class Crypt:
    def __init__(self):
        mcrfpy.createScene("play")
        self.ui = mcrfpy.sceneUI("play")
        mcrfpy.setScene("play")
        mcrfpy.keypressScene(self.cos_keys)

        entity_frame = mcrfpy.Frame(815, 10, 194, 595, fill_color = frame_color)
        inventory_frame = mcrfpy.Frame(10, 610, 800, 143, fill_color = frame_color)
        stats_frame = mcrfpy.Frame(815, 610, 194, 143, fill_color = frame_color)

        #self.level = cl.Level(30, 23)
        self.entities = []
        self.depth=1
        self.create_level(self.depth)
        #self.grid = mcrfpy.Grid(20, 15, t, (10, 10), (1014, 758))
        self.player = ce.PlayerEntity(game=self)
        self.swap_level(self.level, self.spawn_point)

        # Test Entities
        #ce.BoulderEntity(9, 7, game=self)
        #ce.BoulderEntity(9, 8, game=self)
        #ce.ExitEntity(12, 6, 14, 4, game=self)
        # scene setup


        [self.ui.append(e) for e in (self.grid,)] # entity_frame, inventory_frame, stats_frame)]

        self.possibilities = None # track WFC possibilities between rounds

    def add_entity(self, e:ce.COSEntity):
        self.entities.append(e)
        self.entities.sort(key = lambda e: e.draw_order, reverse=False)
        # hack / workaround for grid.entities not interable
        while len(self.grid.entities): # while there are entities on the grid,
            self.grid.entities.remove(0) # remove the 1st ("0th")
        for e in self.entities:
            self.grid.entities.append(e._entity)

    def create_level(self, depth):
        #if depth < 3:
        #    features = None
        self.level = cl.Level(30, 23)
        self.grid = self.level.grid
        coords = self.level.generate()
        self.entities = []
        for k, v in coords.items():
            if k == "spawn":
                self.spawn_point = v
            elif k == "boulder":
                ce.BoulderEntity(v[0], v[1], game=self)
            elif k == "button":
                pass
            elif k == "exit":
                ce.ExitEntity(v[0], v[1], coords["button"][0], coords["button"][1], game=self)

    def cos_keys(self, key, state):
        d = None
        if state == "end": return
        elif key == "W": d = (0, -1)
        elif key == "A": d = (-1, 0)
        elif key == "S": d = (0, 1)
        elif key == "D": d = (1, 0)
        elif key == "M": self.level.generate()
        elif key == "R":
            self.level.reset()
            self.possibilities = None
        elif key == "T":
            self.level.split()
            self.possibilities = None
        elif key == "Y": self.level.split(single=True)
        elif key == "U": self.level.highlight(+1)
        elif key == "I": self.level.highlight(-1)
        elif key == "O":
            self.level.wall_rooms()
            self.possibilities = None
        #elif key == "P": ct.format_tiles(self.grid)
        elif key == "P":
            self.possibilities = ct.wfc_pass(self.grid, self.possibilities)
        if d: self.player.try_move(*d)

    def swap_level(self, new_level, spawn_point):
        self.level = new_level
        self.grid = self.level.grid
        self.grid.zoom = 2.0
        # TODO, make an entity mover function
        self.add_entity(self.player)
        self.player.grid = self.grid
        self.player.draw_pos = spawn_point
        self.grid.entities.append(self.player._entity)
        try:
            self.ui.remove(0)
        except:
            pass
        self.ui.append(self.grid)

crypt = Crypt()
