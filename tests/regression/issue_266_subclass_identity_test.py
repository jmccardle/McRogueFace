"""Regression test: Python subclass identity preservation in grid.entities.

Tests that Entity subclasses retain their Python type and custom methods
when accessed via grid.entities iteration, indexing, and pop(). This
pattern is critical for games like Liber Noster (7DRL 2026) where
subclasses like GameEntity, ZoneExit, Combatant add custom behavior.

Related issues: #266 (self-reference cycle), #275 (tp_dealloc)
"""
import mcrfpy
import gc
import sys

PASS = 0
FAIL = 0

def test(name, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS: {name}")
    else:
        FAIL += 1
        print(f"  FAIL: {name}")


# --- Define subclass hierarchy mimicking Liber Noster ---

class GameEntity(mcrfpy.Entity):
    """Base game entity with custom methods."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.entity_name = kwargs.get("name", "unnamed")
        self.description = "A game entity"

    def tooltip(self):
        return f"{self.entity_name}: {self.description}"


class ZoneExit(GameEntity):
    """Teleportation entity."""
    def __init__(self, target_zone="unknown", **kwargs):
        super().__init__(**kwargs)
        self.target_zone = target_zone
        self.description = f"Exit to {target_zone}"

    def send(self, target_entity):
        return f"Sending {target_entity} to {self.target_zone}"


class AnimatedEntity(GameEntity):
    """Entity with animation state."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.moving = False
        self.facing_dir = 0

    def anim(self, direction):
        self.facing_dir = direction
        return f"Animating {self.entity_name} dir={direction}"


class Combatant:
    """Mixin class for combat (not an Entity subclass)."""
    def __init_combatant__(self, hp=10, atk=3, dfn=1):
        self.hp = hp
        self.atk = atk
        self.dfn = dfn
        self.alive = True

    def bump(self, target):
        damage = max(0, self.atk - target.dfn)
        target.hp -= damage
        if target.hp <= 0:
            target.alive = False
        return {"damage": damage, "defeated": not target.alive}


class Enemy(AnimatedEntity, Combatant):
    """Combines animation and combat."""
    def __init__(self, hp=10, atk=3, dfn=1, **kwargs):
        AnimatedEntity.__init__(self, **kwargs)
        self.__init_combatant__(hp=hp, atk=atk, dfn=dfn)


# --- Tests ---

print("Testing Entity subclass identity preservation...")

# Create a grid and scene
scene = mcrfpy.Scene("test_identity")
grid = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(400, 400))
scene.children.append(grid)
mcrfpy.current_scene = scene

# Test 1: Basic subclass creation and grid addition
zexit = ZoneExit(target_zone="dungeon", grid_pos=(5, 5))
grid.entities.append(zexit)
test("ZoneExit added to grid", len(grid.entities) == 1)

# Test 2: Access via index preserves type
e = grid.entities[0]
test("grid.entities[0] returns ZoneExit type", type(e).__name__ == "ZoneExit")
test("grid.entities[0] has send() method", hasattr(e, "send"))
test("grid.entities[0].send() works", e.send("player") == "Sending player to dungeon")
test("grid.entities[0].tooltip() works", "dungeon" in e.tooltip())
del e

# Test 3: Access via iteration preserves type
for e in grid.entities:
    test("iteration returns ZoneExit type", type(e).__name__ == "ZoneExit")
    test("iteration has send() method", hasattr(e, "send"))
    test("iteration has target_zone attr", hasattr(e, "target_zone"))

# Test 4: Drop the original Python reference, force GC
del zexit
gc.collect()
gc.collect()

# This is the critical test: after GC, the subclass should survive
e = grid.entities[0]
test("after GC: type preserved", type(e).__name__ == "ZoneExit")
test("after GC: send() works", e.send("hero") == "Sending hero to dungeon")
test("after GC: target_zone preserved", e.target_zone == "dungeon")
test("after GC: tooltip() works", "dungeon" in e.tooltip())
del e

# Test 5: Multiple subclass types in same grid
enemy1 = Enemy(hp=20, atk=5, dfn=2, name="goblin", grid_pos=(3, 3))
enemy2 = Enemy(hp=15, atk=4, dfn=1, name="skeleton", grid_pos=(7, 7))
anim = AnimatedEntity(name="npc", grid_pos=(10, 10))

grid.entities.append(enemy1)
grid.entities.append(enemy2)
grid.entities.append(anim)

# Drop Python refs, force GC
del enemy1, enemy2, anim
gc.collect()
gc.collect()

test("multiple types: 4 entities in grid", len(grid.entities) == 4)

# Check each entity's type via iteration
types_found = []
for e in grid.entities:
    types_found.append(type(e).__name__)

test("type list correct", types_found == ["ZoneExit", "Enemy", "Enemy", "AnimatedEntity"])

# Test 6: isinstance checks (Liber Noster pattern: find Combatants)
combatants = []
for e in grid.entities:
    if isinstance(e, Combatant) and e.alive:
        combatants.append(e)

test("isinstance(Combatant) finds 2 enemies", len(combatants) == 2)
test("combatant has bump()", hasattr(combatants[0], "bump"))
test("combatant has hp", hasattr(combatants[0], "hp"))

# Test 7: Combat between entities retrieved from grid
attacker = combatants[0]
defender = combatants[1]
result = attacker.bump(defender)
test("combat returns result dict", "damage" in result)
test("combat deals damage", defender.hp < 15)
del attacker, defender, combatants

# Test 8: hasattr checks (Liber Noster pattern: tooltip, pickup)
gc.collect()
for e in grid.entities:
    if hasattr(e, "tooltip"):
        tip = e.tooltip()
        test(f"tooltip() on {type(e).__name__}", tip is not None)
        break  # Just test one

# Test 9: die() releases identity, allows GC
pre_count = len(grid.entities)
e = grid.entities[0]  # ZoneExit
test("before die: is ZoneExit", type(e).__name__ == "ZoneExit")
e.die()
test("after die: entity count decreased", len(grid.entities) == pre_count - 1)
del e
gc.collect()

# Test 10: Remaining entities still have correct types
types_after_die = [type(e).__name__ for e in grid.entities]
test("types after die()", types_after_die == ["Enemy", "Enemy", "AnimatedEntity"])

# Test 11: pop() preserves identity
e = grid.entities.pop(0)
test("pop() returns Enemy", type(e).__name__ == "Enemy")
test("pop() entity has combat attrs", hasattr(e, "hp"))
del e

# Test 12: Entity created with grid= kwarg
zexit2 = ZoneExit(target_zone="tower", grid_pos=(1, 1), grid=grid)
del zexit2
gc.collect()
gc.collect()
e = grid.entities[-1]
test("grid= kwarg: type preserved after GC", type(e).__name__ == "ZoneExit")
test("grid= kwarg: send() works", "tower" in e.send("x"))
del e

# Test 13: remove() releases identity
enemy_ref = None
for e in grid.entities:
    if isinstance(e, Enemy):
        enemy_ref = e
        break
test("found Enemy for remove test", enemy_ref is not None)
if enemy_ref:
    grid.entities.remove(enemy_ref)
    del enemy_ref
    gc.collect()

# Test 14: Stress test - create many entities, drop refs, verify all survive
for i in range(20):
    ent = ZoneExit(target_zone=f"zone_{i}", grid_pos=(i % 20, i // 20))
    grid.entities.append(ent)
    # Don't hold any Python reference
del ent
gc.collect()
gc.collect()

zone_exits_found = 0
for e in grid.entities:
    if isinstance(e, ZoneExit) and hasattr(e, "target_zone"):
        zone_exits_found += 1

test("stress: all 21 ZoneExits preserved", zone_exits_found == 21)

# Summary
print(f"\n{'='*50}")
total = PASS + FAIL
if FAIL == 0:
    print(f"PASS: all {PASS} subclass identity tests passed")
    sys.exit(0)
else:
    print(f"FAIL: {FAIL}/{total} tests failed")
    sys.exit(1)
