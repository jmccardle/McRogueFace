import mcrfpy
import random
from cos_itemdata import itemdata
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
        self._entity = mcrfpy.Entity(grid_pos=(x, y), texture=t, sprite_index=sprite_num)
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
                self.grid.entities.pop(i)
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
            if e.draw_pos.x == old_pos.x and e.draw_pos.y == old_pos.y: e.ev_exit(self)
        for e in self.game.entities:
            if e is self: continue
            if e.draw_pos.x == tx and e.draw_pos.y == ty: e.ev_enter(self)

    def act(self):
        pass

    def ev_enter(self, other):
        pass

    def ev_exit(self, other):
        pass

    def try_move(self, dx, dy, test=False):
        x_max, y_max = self.grid.grid_size
        tx, ty = int(self.draw_pos.x + dx), int(self.draw_pos.y + dy)
        #for e in iterable_entities(self.grid):

        # sorting entities to test against the boulder instead of the button when they overlap.
        for e in sorted(self.game.entities, key = lambda i: i.draw_order, reverse = True):
            if e.draw_pos.x == tx and e.draw_pos.y == ty:
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
        tx, ty = int(self.draw_pos.x + dx), int(self.draw_pos.y + dy)
        #self.draw_pos = (tx, ty)
        self.do_move(tx, ty)

class Equippable:
    def __init__(self, hands = 0, hp_healing = 0, damage = 0, defense = 0, zap_damage = 1, zap_cooldown = 10, sprite = 129, boost=None, text="", text_color=(255, 255, 255), value=0):
        self.hands = hands
        self.hp_healing = hp_healing
        self.damage = damage
        self.defense = defense
        self.zap_damage = zap_damage
        self.zap_cooldown = zap_cooldown
        self.zap_cooldown_remaining = 0
        self.sprite = sprite
        self.quality = 0
        self.text = text
        self.text_color = text_color
        self.boost = boost
        self.value = value

    def tick(self):
        if self.zap_cooldown_remaining:
            self.zap_cooldown_remaining -= 1
            if self.zap_cooldown_remaining < 0: self.zap_cooldown_remaining = 0

    def __repr__(self):
        cooldown_str = f'({self.zap_cooldown_remaining} rounds until ready)'
        return f"<Equippable text={self.text}, hands={self.hands}, hp_healing={self.hp_healing}, damage={self.damage}, defense={self.defense}, zap_damage={self.zap_damage}, zap_cooldown={self.zap_cooldown}{cooldown_str if self.zap_cooldown_remaining else ''}, sprite={self.sprite}>"

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

    def consume(self, consumer):
        if self.boost == "green_pot":
            consumer.base_damage += self.value
        elif self.boost == "blue_pot":
            b = self.value
            while b: #split bonus between damage and faster cooldown
                bonus = random.choice(["damage", "cooldown", "range"])
                if bonus == "damage":
                    consumer.base_zap_damage += 1
                elif bonus == "cooldown":
                    consumer.base_zap_cooldown += 1
                else:
                    consumer.base_zap_range += 1
                b -= 1
        elif self.boost == "grey_pot":
            consumer.base_defense += self.value
        elif self.boost == "sm_grey_pot":
            consumer.luck += self.value
        elif self.hp_healing:
            consumer.hp += self.hp_healing
            if consumer.hp > consumer.max_hp: consumer.hp = consumer.max_hp

    def do_zap(self, caster, entities):
        if self.zap_damage == 0:
            print("This item can't zap.")
            return False
        if self.zap_cooldown_remaining != 0:
            print("zap is cooling down.")
            return False
        fx, fy = caster.draw_pos.x, caster.draw_pos.y
        x, y = int(fx), int (fy)
        dist = lambda tx, ty: abs(int(tx) - x) + abs(int(ty) - y)
        targets = []
        for e in entities:
            if type(e) != EnemyEntity: continue
            if dist(*e.draw_pos) > caster.base_zap_range:
                continue
            if e.hp <= 0: continue
            targets.append(e)
        if not targets:
            print("No targets found in range.")
            return False
        target = random.choice(targets)
        print(f"Zap! {target}")
        target.get_zapped(self.zap_damage)
        self.zap_cooldown_remaining = self.zap_cooldown
        return True

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
        self.base_zap_damage = 0
        self.base_zap_cooldown = 0
        self.base_zap_range = 4

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
            defense += i.defense
        return defense

    def do_zap(self):
        for i in self.equipped:
            if i.zap_damage and i.zap_cooldown_remaining == 0:
                if i.do_zap(self, self.game.entities):
                    break
        else:
            print("Couldn't zap")

    def bump(self, other, dx, dy, test=False):
        if type(other) == BoulderEntity:
            print("Boulder hit w/ knockback!")
            return self.game.pull_boulder_move((-dx, -dy), other)
        #print(f"oof, ouch, {other} bumped the player - {other.base_damage} damage from {other}")
        self.hp = max(self.hp - max(other.base_damage - self.calc_defense(), 0), 0)

    def receive(self, equip):
        print(equip)
        if (equip.hands == 0):
            if len([i for i in self.inventory if i is not None]) < 3:
                if None in self.inventory:
                    self.inventory[self.inventory.index(None)] = equip
                else:
                    self.inventory.append(equip)
                return
            else:
                print("something something, consumable GUI")
        elif (equip.hands == 1):
            if len(self.equipped) < 2:
                self.equipped.append(equip)
                return
            else:
                print("Something something, 1h GUI")
        else: # equip.hands == 2:
            if len(self.equipped) == 0:
                self.equipped.append(equip)
                return
            else:
                print("Something something, 2h GUI")

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
                if e.draw_pos.x == spawn[0] and e.draw_pos.y == spawn[1]: break
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
        tx, ty = int(self.draw_pos.x + dx), int(self.draw_pos.y + dy)
        # Is the boulder blocked the same direction as the bumper? If not, let's both move
        old_pos = int(self.draw_pos.x), int(self.draw_pos.y)
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
            pos = int(self.draw_pos.x), int(self.draw_pos.y)
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
                #print(f"welcome to level {self.game.depth}")
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
                old_pos = int(self.draw_pos.x), int(self.draw_pos.y)
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
            old_pos = int(self.draw_pos.x), int(self.draw_pos.y)
            if not test:
                other.do_move(*old_pos)
            return True

    def act(self):
        if self.hp > 0:
            # if player nearby: attack
            x, y = self.draw_pos.x, self.draw_pos.y
            px, py = self.game.player.draw_pos.x, self.game.player.draw_pos.y
            for d in ((1, 0), (0, 1), (-1, 0), (1, 0)):
                if int(x + d[0]) == int(px) and int(y + d[1]) == int(py):
                    self.try_move(*d)
                    return

            # slow movement (doesn't affect ability to attack)
            if self.moved_last > 0:
                self.moved_last -= 1
                #print(f"Deducting move cooldown, now {self.moved_last} / {self.move_cooldown}")
                return
            else:
                #print(f"Restaring move cooldown - {self.move_cooldown}")
                self.moved_last = self.move_cooldown

            # if player is not nearby, wander
            if abs(x - px) + abs(y - py) > self.sight:
                d = random.choice(((1, 0), (0, 1), (-1, 0), (1, 0)))
                self.try_move(*d)

            # if can_push and player in a line: KICK
            if self.can_push:
                if int(x) == int(px):# vertical kick
                    self.try_move(0, 1 if y < py else -1)
                elif int(y) == int(py):# horizontal kick
                    self.try_move(1 if x < px else -1, 0)

            # else, nearby pursue
            towards = []
            dist = lambda dx, dy: abs(px - (x + dx)) + abs(py - (y + dy))
            #current_dist = dist(0, 0)
            #for d in ((1, 0), (0, 1), (-1, 0), (1, 0)):
            #    if dist(*d) <= current_dist + 0.75: towards.append(d)
            #print(current_dist, towards)
            if px >= x:
                towards.append((1, 0))
            if px <= x:
                towards.append((-1, 0))
            if py >= y:
                towards.append((0, 1))
            if py <= y:
                towards.append((0, -1))
            towards = [p for p in towards if self.game.grid.at((int(x + p[0]), int(y + p[1]))).walkable]
            towards.sort(key = lambda p: dist(*p))
            target_dir = towards[0]
            self.try_move(*target_dir)

    def get_zapped(self, d):
        self.hp -= d
        self.hp = max(self.hp, 0)
        if self.hp == 0:
            self._entity.sprite_number = self.base_sprite + 246
            self.draw_order = 1
        print(f"Player zapped for {d}. HP = {self.hp}")


class TreasureEntity(COSEntity):
    def __init__(self, x, y, treasure_table=None, *, game):
        self.draw_order = 6
        super().__init__(game.grid, x, y, 89, game=game)
        self.popped = False
        self.treasure_table = treasure_table

    def generate(self):
        items = list(self.treasure_table.keys())
        weights = [self.treasure_table[k] for k in items]
        item = random.choices(items, weights=weights)[0]
        bonus_stats_max = (self.game.depth + (self.game.player.luck*2)) * 0.66
        bonus_stats = random.randint(0, int(bonus_stats_max))
        bonus_colors = {1: (192, 255, 192), 2: (128, 128, 192), 3: (255, 192, 255),
                        4: (255, 192, 192), 5: (255, 0, 0)}

        data = itemdata[item]
        if item in ("sword", "sword2", "sword3", "axe", "axe2", "axe3"):
            equip = Equippable(hands=data.handedness, sprite=data.sprite, damage=data.base_value+bonus_stats, text=data.base_name)
        elif item in ("buckler", "shield"):
            equip = Equippable(hands=data.handedness, sprite=data.sprite, defense=data.base_value+bonus_stats, text=data.base_name)
        elif item in ("wand", "staff", "staff2"):
            equip = Equippable(hands=data.handedness, sprite=data.sprite, zap_damage=data.base_value[0], zap_cooldown=data.base_value[1], text=data.base_name)
            if bonus_stats:
                b = bonus_stats
                while b: # split bonus between damage and faster cooldown
                    if equip.zap_cooldown == 2 or random.random() > 0.66:
                        equip.zap_damage += 1
                    else:
                        equip.zap_cooldown -= 1
                    b -= 1
        elif item == "red_pot":
            equip = Equippable(hands=data.handedness, sprite=data.sprite, hp_healing=data.base_value+bonus_stats, text=data.base_name)
        elif item in ("blue_pot", "green_pot", "grey_pot", "sm_grey_pot"):
            print(f"Permanent stat boost ({item})")
            equip = Equippable(hands=data.handedness, sprite=data.sprite, text=data.base_name, boost=item, value=data.base_value + bonus_stats)
        else:
            print(f"Unfound item: {item}")
            equip = Equippable()

        if bonus_stats:
            equip.text = equip.text + f" (+{bonus_stats})"
            equip.text_color = bonus_colors[bonus_stats if bonus_stats <=5 else 5]
        return equip

    def bump(self, other, dx, dy, test=False):
        if type(other) != PlayerEntity:
            return False
        if self.popped:
            print("It's already open.")
            return True
        print("Take me, I'm yours!")
        self._entity.sprite_number = 91
        self.popped = True
        #print(self.treasure_table)
        other.receive(self.generate())
        return False
