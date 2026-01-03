"""McRogueFace - Status Effects (basic)

Documentation: https://mcrogueface.github.io/cookbook/combat_status_effects
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/combat/combat_status_effects_basic.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

class StackableEffect(StatusEffect):
    """Effect that stacks intensity."""

    def __init__(self, name, duration, intensity=1, max_stacks=5, **kwargs):
        super().__init__(name, duration, **kwargs)
        self.intensity = intensity
        self.max_stacks = max_stacks
        self.stacks = 1

    def add_stack(self):
        """Add another stack."""
        if self.stacks < self.max_stacks:
            self.stacks += 1
            return True
        return False


class StackingEffectManager(EffectManager):
    """Effect manager with stacking support."""

    def add_effect(self, effect):
        if isinstance(effect, StackableEffect):
            # Check for existing stacks
            for existing in self.effects:
                if existing.name == effect.name:
                    if existing.add_stack():
                        # Refresh duration
                        existing.duration = max(existing.duration, effect.duration)
                        return
                    else:
                        return  # Max stacks

        # Default behavior
        super().add_effect(effect)


# Stacking poison example
def create_stacking_poison(base_damage=1, duration=5):
    def on_tick(target):
        # Find the poison effect to get stack count
        effect = target.effects.get_effect("poison")
        if effect:
            damage = base_damage * effect.stacks
            target.hp -= damage
            print(f"{target.name} takes {damage} poison damage! ({effect.stacks} stacks)")

    return StackableEffect("poison", duration, on_tick=on_tick, max_stacks=5)