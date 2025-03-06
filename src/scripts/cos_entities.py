import mcrfpy
#t = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
t = mcrfpy.Texture("assets/kenney_TD_MR_IP.png", 16, 16)
#def iterable_entities(grid):
#    """Workaround for UIEntityCollection bug; see issue #72"""
#    entities = []
#    for i in range(len(grid.entities)):
#        entities.append(grid.entities[i])
#    return entities

class COSEntity():  #mcrfpy.Entity): # Fake mcrfpy.Entity integration; engine bugs workarounds
    def __init__(self, g:mcrfpy.Grid, x=0, y=0, sprite_num=86, *, game):
        #self.e = mcrfpy.Entity((x, y), t, sprite_num)
        #super().__init__((x, y), t, sprite_num)
        self._entity = mcrfpy.Entity((x, y), t, sprite_num)
        #grid.entities.append(self.e)
        self.grid = g
        #g.entities.append(self._entity)
        self.game = game
        self.game.add_entity(self)

    ## Wrapping mcfrpy.Entity properties to emulate derived class... see issue #76
    @property
    def draw_pos(self):
        return self._entity.draw_pos

    @draw_pos.setter
    def draw_pos(self, value):
        self._entity.draw_pos = value

    @property
    def sprite_number(self):
        return self._entity.sprite_number

    @sprite_number.setter
    def sprite_number(self, value):
        self._entity.sprite_number = value

    def __repr__(self):
        return f"<COSEntity ({self.draw_pos}) on {self.grid}>"

    def die(self):
        # ugly workaround! grid.entities isn't really iterable (segfaults)
        for i in range(len(self.grid.entities)):
            e = self.grid.entities[i]
            if e == self._entity:
            #if e == self:
                self.grid.entities.remove(i)
                break
        else:
            print(f"!!! {self!r} wasn't removed from grid on call to die()")

    def bump(self, other, dx, dy, test=False):
        raise NotImplementedError

    def do_move(self, tx, ty):
        """Base class method to move this entity
        Assumes try_move succeeded, for everyone!
        from: self._entity.draw_pos
        to: (tx, ty)
        calls ev_exit for every entity at (draw_pos)
        calls ev_enter for every entity at (tx, ty)
        """
        old_pos = self.draw_pos
        self.draw_pos = (tx, ty)
        for e in self.game.entities:
            if e is self: continue
            if e.draw_pos == old_pos: e.ev_exit(self)
        for e in self.game.entities:
            if e is self: continue
            if e.draw_pos == (tx, ty): e.ev_enter(self)
        

    def ev_enter(self, other):
        pass

    def ev_exit(self, other):
        pass

    def try_move(self, dx, dy, test=False):
        x_max, y_max = self.grid.grid_size
        tx, ty = int(self.draw_pos[0] + dx), int(self.draw_pos[1] + dy)
        #for e in iterable_entities(self.grid):

        # sorting entities to test against the boulder instead of the button when they overlap.
        for e in sorted(self.game.entities, key = lambda i: i.draw_order, reverse = True):
            if e.draw_pos == (tx, ty):
                #print(f"bumping {e}")
                return e.bump(self, dx, dy)

        if tx < 0 or tx >= x_max:
            return False
        if ty < 0 or ty >= y_max:
            return False
        if self.grid.at((tx, ty)).walkable == True:
            if not test:
                #self.draw_pos = (tx, ty)
                self.do_move(tx, ty)
            return True
        else:
            #print("Bonk")
            return False

    def _relative_move(self, dx, dy):
        tx, ty = int(self.draw_pos[0] + dx), int(self.draw_pos[1] + dy)
        #self.draw_pos = (tx, ty)
        self.do_move(tx, ty)

class PlayerEntity(COSEntity):
    def __init__(self, *, game):
        #print(f"spawn at origin")
        self.draw_order = 10
        super().__init__(game.grid, 0, 0, sprite_num=84, game=game)

    def respawn(self, avoid=None):
        # find spawn point
        x_max, y_max = g.size
        spawn_points = []
        for x in range(x_max):
            for y in range(y_max):
                if g.at((x, y)).walkable:
                    spawn_points.append((x, y))
        random.shuffle(spawn_points)
        ## TODO - find other entities to avoid spawning on top of
        for spawn in spawn_points:
            for e in avoid or []:
                if e.draw_pos == spawn: break
            else:
                break
        self.draw_pos = spawn

    def __repr__(self):
        return f"<PlayerEntity {self.draw_pos}, {self.grid}>"


class BoulderEntity(COSEntity):
    def __init__(self, x, y, *, game):
        self.draw_order = 8
        super().__init__(game.grid, x, y, 66, game=game)

    def bump(self, other, dx, dy, test=False):
        if type(other) == BoulderEntity:
            #print("Boulders can't push boulders")
            return False
        #tx, ty = int(self.e.position[0] + dx), int(self.e.position[1] + dy)
        tx, ty = int(self.draw_pos[0] + dx), int(self.draw_pos[1] + dy)
        # Is the boulder blocked the same direction as the bumper? If not, let's both move
        old_pos = int(self.draw_pos[0]), int(self.draw_pos[1])
        if self.try_move(dx, dy, test=test):
            if not test:
                other.do_move(*old_pos)
                #other.draw_pos = old_pos
            return True

class ButtonEntity(COSEntity):
    def __init__(self, x, y, exit_entity, *, game):
        self.draw_order = 1
        super().__init__(game.grid, x, y, 42, game=game)
        self.exit = exit_entity

    def ev_enter(self, other):
        print("Button makes a satisfying click!")
        self.exit.unlock()

    def ev_exit(self, other):
        print("Button makes a disappointing click.")
        self.exit.lock()

    def bump(self, other, dx, dy, test=False):
        #if type(other) == BoulderEntity:
        #    self.exit.unlock()
        # TODO: unlock, and then lock again, when player steps on/off
        if not test:
            other._relative_move(dx, dy)
        return True

class ExitEntity(COSEntity):
    def __init__(self, x, y, bx, by, *, game):
        self.draw_order = 2
        super().__init__(game.grid, x, y, 45, game=game)
        self.my_button = ButtonEntity(bx, by, self, game=game)
        self.unlocked = False
        #global cos_entities
        #cos_entities.append(self.my_button)

    def unlock(self):
        self.sprite_number = 21
        self.unlocked = True

    def lock(self):
        self.sprite_number = 45
        self.unlocked = False

    def bump(self, other, dx, dy, test=False):
        if type(other) == BoulderEntity:
            return False
        if self.unlocked:
            if not test:
                other._relative_move(dx, dy)
            #TODO - player go down a level logic
            if type(other) == PlayerEntity:
                self.game.create_level(self.game.depth + 1)
                self.game.swap_level(self.game.level, self.game.spawn_point)
