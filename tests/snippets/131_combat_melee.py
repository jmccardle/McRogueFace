# mcrf: objects=[Caption,Color,Easing,Entity,Frame,Grid,Scene,Timer] verified=0.2.8-dev status=ok
# Melee combat cookbook recipe - Fighter stats, attack resolution, CombatEntity,
# health bars, and floating damage numbers, all combined into one runnable demo.
import random
from dataclasses import dataclass

import mcrfpy


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


def calculate_damage(attacker: Fighter, defender: Fighter) -> dict:
    """
    Calculate damage with variance and critical hits.

    Formula: (ATK * variance) - DEF, minimum 1
    Critical: 10% chance for 2x damage, ignores defense
    """
    variance = random.uniform(0.8, 1.2)
    base_damage = int(attacker.attack * variance)

    crit_chance = 0.10
    is_critical = random.random() < crit_chance

    if is_critical:
        final_damage = base_damage * 2
    else:
        final_damage = max(1, base_damage - defender.defense)

    return {
        "damage": final_damage,
        "is_critical": is_critical,
        "base_roll": base_damage,
    }


def attack_with_variance(attacker: Fighter, defender: Fighter) -> dict:
    """Perform attack with variance and crits."""
    result = calculate_damage(attacker, defender)
    actual = defender.take_damage(result["damage"])

    return {
        "damage": actual,
        "is_critical": result["is_critical"],
        "killed": not defender.is_alive(),
    }


class CombatEntity:
    """Game entity with combat capabilities."""

    def __init__(self, grid, x, y, texture, sprite_index,
                 hp=10, attack=5, defense=2, name="Entity"):
        # Create visual entity
        self.entity = mcrfpy.Entity((x, y), texture, sprite_index)
        grid.entities.append(self.entity)
        self.grid = grid

        # Combat stats
        self.fighter = Fighter(hp=hp, max_hp=hp, attack=attack, defense=defense)
        self.name = name

        # State
        self.alive = True

    @property
    def x(self):
        return self.entity.grid_x

    @property
    def y(self):
        return self.entity.grid_y

    @property
    def hp(self):
        return self.fighter.hp

    @hp.setter
    def hp(self, value):
        self.fighter.hp = value
        if self.fighter.hp <= 0:
            self.die()

    def attack_target(self, target: 'CombatEntity') -> dict:
        """Attack another combat entity."""
        result = attack_with_variance(self.fighter, target.fighter)

        if result["is_critical"]:
            print(f"{self.name} CRITICALLY hits {target.name} for {result['damage']}!")
        else:
            print(f"{self.name} hits {target.name} for {result['damage']}.")

        if result["killed"]:
            target.die()

        return result

    def die(self):
        """Handle death."""
        if not self.alive:
            return

        self.alive = False
        print(f"{self.name} has died!")

        # Remove from grid (Entity.die() detaches it from its grid)
        try:
            self.entity.die()
        except Exception:
            pass

    def heal(self, amount: int):
        """Restore HP."""
        old_hp = self.fighter.hp
        self.fighter.heal(amount)
        healed = self.fighter.hp - old_hp
        print(f"{self.name} heals for {healed} HP.")


class HealthBar:
    """Visual health bar for an entity."""

    def __init__(self, scene, combat_entity, offset_y=-10, width=32, height=4):
        self.scene = scene
        self.entity = combat_entity
        self.offset_x = 0
        self.offset_y = offset_y
        self.width = width
        self.height = height

        # Background (red/empty)
        self.bg = mcrfpy.Frame(pos=(0, 0), size=(width, height))
        self.bg.fill_color = mcrfpy.Color(100, 0, 0)
        scene.children.append(self.bg)

        # Foreground (green/full)
        self.fg = mcrfpy.Frame(pos=(0, 0), size=(width, height))
        self.fg.fill_color = mcrfpy.Color(0, 200, 0)
        scene.children.append(self.fg)

        self.update()

    def update(self):
        """Update health bar position and fill."""
        screen_x = self.entity.x * 16 + self.offset_x
        screen_y = self.entity.y * 16 + self.offset_y

        self.bg.x = screen_x
        self.bg.y = screen_y

        self.fg.x = screen_x
        self.fg.y = screen_y

        hp_percent = self.entity.fighter.hp / self.entity.fighter.max_hp
        self.fg.w = self.width * hp_percent

        if hp_percent > 0.6:
            self.fg.fill_color = mcrfpy.Color(0, 200, 0)  # Green
        elif hp_percent > 0.3:
            self.fg.fill_color = mcrfpy.Color(200, 200, 0)  # Yellow
        else:
            self.fg.fill_color = mcrfpy.Color(200, 0, 0)  # Red

    def remove(self):
        """Remove health bar from UI."""
        for elem in (self.bg, self.fg):
            try:
                self.scene.children.remove(elem)
            except ValueError:
                pass


def show_damage_number(scene, x, y, damage, is_critical=False):
    """Display floating damage number."""
    text = f"{damage}" if not is_critical else f"CRIT {damage}!"
    color = mcrfpy.Color(255, 255, 0) if is_critical else mcrfpy.Color(255, 100, 100)

    caption = mcrfpy.Caption(text=text, x=x, y=y)
    caption.fill_color = color
    scene.children.append(caption)

    # Animate upward and fade out
    caption.animate("y", float(y - 30), 0.8, mcrfpy.Easing.EASE_OUT)

    # Remove after animation
    def cleanup(timer, runtime):
        try:
            scene.children.remove(caption)
        except ValueError:
            pass

    mcrfpy.Timer(f"dmg_{id(caption)}", cleanup, 800)


scene = mcrfpy.Scene("combat_demo")
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
        grid.at(gx, gy).tilesprite = 48

hero = CombatEntity(grid, 3, 6, mcrfpy.default_texture, 84,
                     hp=20, attack=6, defense=2, name="Hero")
goblin = CombatEntity(grid, 5, 6, mcrfpy.default_texture, 112,
                       hp=12, attack=4, defense=1, name="Goblin")

hero_bar = HealthBar(scene, hero)
goblin_bar = HealthBar(scene, goblin)

result = hero.attack_target(goblin)
goblin_bar.update()
show_damage_number(scene, goblin.x * 16, goblin.y * 16, result["damage"], result["is_critical"])
