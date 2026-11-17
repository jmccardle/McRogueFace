# mcrf: objects=[Caption,Color,Entity,Grid,Scene] verified=0.3.6-dev status=ok
import mcrfpy
import random

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(grid_size=(16, 12), pos=(0, 0), size=(640, 480))
scene.children.append(grid)

for y in range(12):
    for x in range(16):
        grid.at(x, y).tilesprite = 48


# Supporting pieces the recipe assumes from the other combat pages.
class Fighter:
    def __init__(self, hp=10, attack=5, defense=2, name=None):
        self.hp = hp
        self.max_hp = hp
        self.attack = attack
        self.defense = defense

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)


def show_heal_number(target, amount):
    label = mcrfpy.Caption(text=f"+{amount}",
                           pos=(target.entity.grid_x * 40, target.entity.grid_y * 40 - 20))
    label.fill_color = mcrfpy.Color(80, 255, 80)
    scene.children.append(label)


def distance_to(a, b):
    return abs(a.entity.grid_x - b.entity.grid_x) + abs(a.entity.grid_y - b.entity.grid_y)


# region: status_effect
class StatusEffect:
    """A temporary effect applied to an entity."""

    def __init__(self, name, duration, on_tick=None, on_apply=None, on_expire=None):
        """
        Args:
            name: Effect identifier
            duration: Turns remaining
            on_tick: Called each turn (receives target)
            on_apply: Called when effect is applied (receives target)
            on_expire: Called when effect expires (receives target)
        """
        self.name = name
        self.duration = duration
        self.on_tick = on_tick
        self.on_apply = on_apply
        self.on_expire = on_expire

    def tick(self, target):
        """Process one turn of the effect."""
        if self.on_tick:
            self.on_tick(target)

        self.duration -= 1
        return self.duration > 0  # Return False when expired

    def apply(self, target):
        """Called when effect is first applied."""
        if self.on_apply:
            self.on_apply(target)

    def expire(self, target):
        """Called when effect expires."""
        if self.on_expire:
            self.on_expire(target)
# endregion


# region: effect_manager
class EffectManager:
    """Manages status effects for an entity."""

    def __init__(self, owner):
        self.owner = owner
        self.effects = []  # List of active StatusEffects

    def add_effect(self, effect):
        """Add a new effect, stacking or refreshing as appropriate."""
        # Check for existing effect of same type
        for existing in self.effects:
            if existing.name == effect.name:
                # Refresh duration (take the longer one)
                existing.duration = max(existing.duration, effect.duration)
                return

        # New effect
        self.effects.append(effect)
        effect.apply(self.owner)

    def remove_effect(self, name):
        """Remove an effect by name."""
        for effect in self.effects[:]:
            if effect.name == name:
                effect.expire(self.owner)
                self.effects.remove(effect)

    def has_effect(self, name):
        """Check if entity has an effect."""
        return any(e.name == name for e in self.effects)

    def get_effect(self, name):
        """Get an effect by name."""
        for effect in self.effects:
            if effect.name == name:
                return effect
        return None

    def tick_all(self):
        """Process all effects for one turn."""
        expired = []

        for effect in self.effects:
            still_active = effect.tick(self.owner)
            if not still_active:
                expired.append(effect)

        # Remove expired effects
        for effect in expired:
            effect.expire(self.owner)
            self.effects.remove(effect)

    def clear_all(self):
        """Remove all effects."""
        for effect in self.effects:
            effect.expire(self.owner)
        self.effects.clear()
# endregion


# region: confusion
import random

def create_confusion(duration=3):
    """Target moves randomly instead of intentionally."""

    def on_apply(target):
        print(f"{target.name} is confused!")
        target.confused = True

    def on_expire(target):
        print(f"{target.name} snaps out of confusion.")
        target.confused = False

    return StatusEffect("confusion", duration,
                       on_apply=on_apply, on_expire=on_expire)


# In AI/movement code:
def get_move_direction(entity):
    if hasattr(entity, 'confused') and entity.confused:
        # Random direction instead of intended
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        return random.choice(directions)
    else:
        return entity.intended_direction
# endregion


# region: stun
def create_stun(duration=2):
    """Target cannot act."""

    def on_apply(target):
        print(f"{target.name} is stunned!")
        target.can_act = False

    def on_expire(target):
        print(f"{target.name} recovers from stun.")
        target.can_act = True

    return StatusEffect("stun", duration,
                       on_apply=on_apply, on_expire=on_expire)


# In turn processing:
def process_turn(entity):
    if not getattr(entity, 'can_act', True):
        print(f"{entity.name} is stunned and cannot act!")
        return  # Skip turn
    # Normal turn processing...
# endregion


# region: buffs
def create_strength_buff(bonus=5, duration=5):
    """Temporarily increase attack."""

    def on_apply(target):
        print(f"{target.name} gains +{bonus} attack!")
        target.fighter.attack += bonus

    def on_expire(target):
        print(f"{target.name}'s strength returns to normal.")
        target.fighter.attack -= bonus

    return StatusEffect("strength", duration,
                       on_apply=on_apply, on_expire=on_expire)


def create_weakness(penalty=3, duration=4):
    """Temporarily decrease attack."""

    def on_apply(target):
        print(f"{target.name} feels weakened!")
        target.fighter.attack = max(1, target.fighter.attack - penalty)

    def on_expire(target):
        print(f"{target.name}'s strength returns.")
        target.fighter.attack += penalty

    return StatusEffect("weakness", duration,
                       on_apply=on_apply, on_expire=on_expire)


def create_armor_buff(bonus=3, duration=5):
    """Temporarily increase defense."""

    def on_apply(target):
        print(f"{target.name} gains +{bonus} defense!")
        target.fighter.defense += bonus

    def on_expire(target):
        target.fighter.defense -= bonus

    return StatusEffect("armored", duration,
                       on_apply=on_apply, on_expire=on_expire)
# endregion


# region: regeneration
def create_regeneration(heal_amount=2, duration=5):
    """Heal each turn."""

    def on_tick(target):
        old_hp = target.fighter.hp
        target.fighter.heal(heal_amount)
        actual_heal = target.fighter.hp - old_hp

        if actual_heal > 0:
            print(f"{target.name} regenerates {actual_heal} HP.")
            show_heal_number(target, actual_heal)

    return StatusEffect("regeneration", duration, on_tick=on_tick)
# endregion


# region: invisibility
def create_invisibility(duration=5):
    """Enemies cannot see or target entity."""

    def on_apply(target):
        print(f"{target.name} becomes invisible!")
        target.invisible = True
        # Visual: make sprite semi-transparent
        target.entity.opacity = 0.3

    def on_expire(target):
        print(f"{target.name} becomes visible again.")
        target.invisible = False
        target.entity.opacity = 1.0

    return StatusEffect("invisibility", duration,
                       on_apply=on_apply, on_expire=on_expire)


# In AI targeting:
def find_target(enemy, potential_targets):
    visible_targets = [t for t in potential_targets
                       if not getattr(t, 'invisible', False)]
    if not visible_targets:
        return None
    # Return nearest visible target
    return min(visible_targets, key=lambda t: distance_to(enemy, t))
# endregion


# region: combat_entity
class CombatEntity:
    """Entity with combat and effect support."""

    def __init__(self, grid, x, y, texture, sprite_index, **stats):
        self.entity = mcrfpy.Entity((x, y), texture, sprite_index)
        grid.entities.append(self.entity)
        self.grid = grid

        # Combat stats
        self.fighter = Fighter(**stats)
        self.name = stats.get('name', 'Entity')

        # Status effects
        self.effects = EffectManager(self)

        # State flags (set by effects)
        self.can_act = True
        self.confused = False
        self.invisible = False

    def start_turn(self):
        """Called at the start of this entity's turn."""
        # Process all status effects
        self.effects.tick_all()

    def apply_effect(self, effect):
        """Apply a status effect."""
        self.effects.add_effect(effect)

    def has_effect(self, name):
        """Check for an effect."""
        return self.effects.has_effect(name)
# endregion


# Tips: the same entity, with the two methods the tips add.
class TipsEntity(CombatEntity):
    immunities = {"stun"}
    resistances = {"strength"}

    # region: tip_die
    def die(self):
        self.effects.clear_all()
        # Rest of death logic...
    # endregion

    # region: tip_immunity
    def apply_effect(self, effect):
        if effect.name in self.immunities:
            print(f"{self.name} is immune to {effect.name}!")
            return
        if effect.name in self.resistances:
            effect.duration //= 2  # Half duration
        self.effects.add_effect(effect)
    # endregion


# region: tip_save
def serialize_effects(effect_manager):
    return [{"name": e.name, "duration": e.duration}
            for e in effect_manager.effects]
# endregion


# Two combatants on the grid, with a few effects applied and one turn ticked.
hero = CombatEntity(grid, 3, 6, mcrfpy.default_texture, 84, hp=20, attack=6, defense=2, name="Hero")
goblin = TipsEntity(grid, 8, 6, mcrfpy.default_texture, 112, hp=12, attack=4, defense=1, name="Goblin")

hero.fighter.hp = 14
hero.apply_effect(create_strength_buff(bonus=3, duration=4))
hero.apply_effect(create_regeneration(heal_amount=2, duration=3))
goblin.apply_effect(create_stun(duration=2))   # immune: refused by the override above
goblin.apply_effect(create_weakness(penalty=2, duration=3))

hero.start_turn()
goblin.start_turn()
print(serialize_effects(hero.effects))
