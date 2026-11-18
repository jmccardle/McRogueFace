# mcrf: objects=[Easing,Entity,Grid,Scene] verified=0.3.6 status=ok
import mcrfpy

scene = mcrfpy.Scene("melee_basics")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(
    grid_size=(16, 12),
    texture=mcrfpy.default_texture,
    pos=(0, 0),
    size=(1024, 768),
    zoom=4.0,
)
scene.children.append(grid)

for gy in range(12):
    for gx in range(16):
        grid.at(gx, gy).tilesprite = 48 if (gx + gy) % 2 == 0 else 49

hero_sprite = mcrfpy.Entity(grid_pos=(4, 6), texture=mcrfpy.default_texture, sprite_index=84)
victim_sprite = mcrfpy.Entity(grid_pos=(8, 6), texture=mcrfpy.default_texture, sprite_index=112)
grid.entities.append(hero_sprite)
grid.entities.append(victim_sprite)


# region: fighter
from dataclasses import dataclass

@dataclass
class Fighter:
    """Combat statistics for an entity."""
    hp: int
    max_hp: int
    attack: int
    defense: int

    def is_alive(self) -> bool:
        return self.hp > 0

    def heal(self, amount: int):
        """Heal up to max HP."""
        self.hp = min(self.max_hp, self.hp + amount)

    def take_damage(self, amount: int) -> int:
        """Take damage and return actual damage dealt."""
        actual = min(self.hp, amount)
        self.hp -= actual
        return actual
# endregion


# region: attack
def attack(attacker: Fighter, defender: Fighter) -> dict:
    """
    Resolve an attack between two fighters.

    Returns dict with attack results for UI/logging.
    """
    # Calculate base damage
    damage = max(0, attacker.attack - defender.defense)

    # Apply damage
    actual_damage = defender.take_damage(damage)

    return {
        "attacker": attacker,
        "defender": defender,
        "damage": actual_damage,
        "blocked": attacker.attack - damage,
        "killed": not defender.is_alive()
    }
# endregion


# region: variance
import random

def calculate_damage(attacker: Fighter, defender: Fighter) -> dict:
    """
    Calculate damage with variance and critical hits.

    Formula: (ATK * variance) - DEF, minimum 1
    Critical: 10% chance for 2x damage, ignores defense
    """
    # Base damage with variance (+/- 20%)
    variance = random.uniform(0.8, 1.2)
    base_damage = int(attacker.attack * variance)

    # Critical hit check
    crit_chance = 0.10
    is_critical = random.random() < crit_chance

    if is_critical:
        # Critical hits deal double damage and ignore defense
        final_damage = base_damage * 2
    else:
        # Normal hit - subtract defense
        final_damage = max(1, base_damage - defender.defense)

    return {
        "damage": final_damage,
        "is_critical": is_critical,
        "base_roll": base_damage
    }


def attack_with_variance(attacker: Fighter, defender: Fighter) -> dict:
    """Perform attack with variance and crits."""
    result = calculate_damage(attacker, defender)
    actual = defender.take_damage(result["damage"])

    return {
        "damage": actual,
        "is_critical": result["is_critical"],
        "killed": not defender.is_alive()
    }
# endregion


# region: die_animation
def die_with_animation(entity):
    # Fade the sprite out, then detach the entity from its grid
    entity.animate("opacity", 0.0, 0.5, mcrfpy.Easing.LINEAR,
                   callback=lambda target, prop, value: target.die())
# endregion


# region: advanced
@dataclass
class AdvancedFighter(Fighter):
    fire_resist: float = 0.0
    ice_resist: float = 0.0
    physical_resist: float = 0.0
# endregion


# What a reader does with the pieces above: one swing, then the loser fades out.
hero = AdvancedFighter(hp=20, max_hp=20, attack=6, defense=2)
rat = Fighter(hp=8, max_hp=8, attack=3, defense=0)
print(attack(hero, rat)["damage"], attack_with_variance(hero, rat)["damage"])
die_with_animation(victim_sprite)
