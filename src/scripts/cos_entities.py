import mcrfpy
import random
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
        return f"<{self.__class__.__name__} ({self.draw_pos})>"

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

    def act(self):
        pass

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

class Equippable:
    def __init__(self, hands = 0, hp_healing = 0, damage = 0, defense = 0, zap_damage = 1, zap_cooldown = 10, sprite = 129):
        self.hands = hands
        self.hp_healing = hp_healing
        self.damage = damage
        self.defense = defense
        self.zap_damage = zap_damage
        self.zap_cooldown = zap_cooldown
        self.zap_cooldown_remaining = 0
        self.sprite = self.sprite
        self.quality = 0

    def tick(self):
        if self.zap_cooldown_remaining:
            self.zap_cooldown_remaining -= 1
            if self.zap_cooldown_remaining < 0: self.zap_cooldown_remaining = 0

    def __repr__(self):
        cooldown_str = f'({self.zap_cooldown_remaining} rounds until ready)'
        return f"<Equippable hands={self.hands}, hp_healing={self.hp_healing}, damage={self.damage}, defense={self.defense}, zap_damage={self.zap_damage}, zap_cooldown={self.zap_cooldown}{cooldown_str if self.zap_cooldown_remaining else ''}, sprite={self.sprite}>"

    def classify(self):
        categories = []
        if self.hands==0:
            categories.append("consumable")
        elif self.damage > 0:
            categories.append(f"{self.hands}-handed weapon")
        elif self.defense > 0:
            categories.append(f"defense")
        elif self.zap_damage > 0:
            categories.append("{self.hands}-handed magic weapon")
        if len(categories) == 0:
            return "unclassifiable"
        elif len(categories) == 1:
            return categories[0]
        else:
            return "Erratic: " + ', '.join(categories)

    #def compare(self, other):
    #    my_class = self.classify()
    #    o_class = other.classify()
    #    if my_class == "unclassifiable" or o_class == "unclassifiable":
    #        return None
    #    if my_class == "consumable":
    #        return other.hp_healing - self.hp_healing


class PlayerEntity(COSEntity):
    def __init__(self, *, game):
        #print(f"spawn at origin")
        self.draw_order = 10
        super().__init__(game.grid, 0, 0, sprite_num=84, game=game)
        self.hp = 10
        self.max_hp = 10
        self.base_damage = 1
        self.base_defense = 0
        self.luck = 0
        self.archetype = None
        self.equipped = []
        self.inventory = []

    def tick(self):
        for i in self.equipped:
            i.tick()

    def calc_damage(self):
        dmg = self.base_damage
        for i in self.equipped:
            dmg += i.damage
        return dmg

    def calc_defense(self):
        defense = self.base_defense
        for i in self.equipped:
            defense += i.damage
        return defense

    def do_zap(self):
        pass

    def bump(self, other, dx, dy, test=False):
        if type(other) == BoulderEntity:
            print("Boulder hit w/ knockback!")
            return self.game.pull_boulder_move((-dx, -dy), other)
        print(f"oof, ouch, {other} bumped the player - {other.base_damage} damage from {other}")
        self.hp = max(self.hp - max(other.base_damage - self.calc_defense(), 0), 0)

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
        elif type(other) == EnemyEntity:
            if not other.can_push: return False
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
        super().__init__(game.grid, x, y, 250, game=game)
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
            pos = int(self.draw_pos[0]), int(self.draw_pos[1])
            other.do_move(*pos)
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
                self.game.depth += 1
                print(f"welcome to level {self.game.depth}")
                self.game.create_level(self.game.depth)
                self.game.swap_level(self.game.level, self.game.spawn_point)

class EnemyEntity(COSEntity):
    def __init__(self, x, y, hp=2, base_damage=1, base_defense=0, sprite=123, can_push=False, crushable=True, sight=8, move_cooldown=1, *, game):
        self.draw_order = 7
        super().__init__(game.grid, x, y, sprite, game=game)
        self.hp = hp
        self.base_damage = base_damage
        self.base_defense = base_defense
        self.base_sprite = sprite
        self.can_push = can_push
        self.crushable = crushable
        self.sight = sight
        self.move_cooldown = move_cooldown
        self.moved_last = 0

    def bump(self, other, dx, dy, test=False):
        if self.hp == 0:
            if not test:
                old_pos = int(self.draw_pos[0]), int(self.draw_pos[1])
                other.do_move(*old_pos)
            return True
        if type(other) == PlayerEntity:
            # TODO - get damage from player, take damage, decide to die or not
            d = other.calc_damage()
            self.hp -= d
            self.hp = max(self.hp, 0)
            if self.hp == 0:
                self._entity.sprite_number = self.base_sprite + 246
                self.draw_order = 1
            print(f"Player hit for {d}. HP = {self.hp}")
            #self.hp = 0
            return False
        elif type(other) == BoulderEntity:
            if not self.crushable and self.hp > 0:
                print("Uncrushable!")
                return False
            if self.hp > 0:
                print("Ouch, my entire body!!")
            self._entity.sprite_number = self.base_sprite + 246
            self.hp = 0
            old_pos = int(self.draw_pos[0]), int(self.draw_pos[1])
            if not test:
                other.do_move(*old_pos)
            return True

    def act(self):
        if self.hp > 0:
            # if player nearby: attack
            x, y = self.draw_pos
            px, py = self.game.player.draw_pos
            for d in ((1, 0), (0, 1), (-1, 0), (1, 0)):
                if int(x + d[0]) == int(px) and int(y + d[1]) == int(py):
                    self.try_move(*d)
                    return

            # slow movement (doesn't affect ability to attack)
            if self.moved_last < 0:
                self.moved_last -= 1
                return
            else:
                self.moved_last = self.move_cooldown

            # if player is not nearby, wander
            if abs(x - px) + abs(y - py) > self.sight:
                d = random.choice(((1, 0), (0, 1), (-1, 0), (1, 0)))
                self.try_move(*d)

            # if can_push and player in a line: KICK
            if self.can_push:
                if int(x) == int(px):
                    pass # vertical kick
                elif int(y) == int(py):
                    pass # horizontal kick

            # else, nearby pursue
            towards = []
            dist = lambda dx, dy: abs(px - (x + dx)) + abs(py - (y + dy))
            current_dist = dist(0, 0)
            for d in ((1, 0), (0, 1), (-1, 0), (1, 0)):
                if dist(*d) <= current_dist + 0.75: towards.append(d)
            print(current_dist, towards)
            target_dir = random.choice(towards)
            self.try_move(*target_dir)


class TreasureEntity(COSEntity):
    def __init__(self, x, y, treasure_table=None, *, game):
        self.draw_order = 6
        super().__init__(game.grid, x, y, 89, game=game)
        self.popped = False

    def bump(self, other, dx, dy, test=False):
        if type(other) != PlayerEntity:
            return False
        if self.popped:
            print("It's already open.")
            return
        print("Take me, I'm yours!")
        self._entity.sprite_number = 91
        self.popped = True

