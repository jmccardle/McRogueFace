from dataclasses import dataclass

@dataclass
class ItemData:
    min_lv: int
    max_lv: int
    base_wt: float
    sprite: int
    base_value: int
    base_name: str
    affinity: str # player archetype that makes it more common
    handedness: int

itemdata = {
    "buckler":     ItemData(min_lv = 1, max_lv = 10, base_wt = 0.25, sprite=101, base_value=1,
                            base_name="Buckler", affinity="knight", handedness=1),

    "shield":      ItemData(min_lv = 2, max_lv = 99, base_wt = 0.15, sprite=102, base_value=2,
                            base_name="Shield", affinity="knight", handedness=1),

    "sword":       ItemData(min_lv = 1, max_lv = 10, base_wt = 0.25, sprite=103, base_value=1,
                            base_name="Shortsword", affinity="knight", handedness=1),

    "sword2":      ItemData(min_lv = 2, max_lv = 16, base_wt = 0.15, sprite=104, base_value=2,
                            base_name="Longsword", affinity="knight", handedness=1),

    "sword3":      ItemData(min_lv = 5, max_lv = 99, base_wt = 0.08, sprite=105, base_value=5,
                            base_name="Claymore", affinity="knight", handedness=2),

    "axe":         ItemData(min_lv = 1, max_lv = 10, base_wt = 0.25, sprite=119, base_value=1,
                            base_name="Hatchet", affinity="viking", handedness=1),

    "axe2":        ItemData(min_lv = 2, max_lv = 16, base_wt = 0.15, sprite=120, base_value=4,
                            base_name="Broad Axe", affinity="viking", handedness=2),

    "axe3":        ItemData(min_lv = 5, max_lv = 99, base_wt = 0.08, sprite=121, base_value=6,
                            base_name="Bearded Axe", affinity="viking", handedness=2),

    "wand":        ItemData(min_lv = 1, max_lv = 10, base_wt = 0.25, sprite=132, base_value=(1, 10),
                            base_name="Wand", affinity="wizard", handedness=1),

    "staff":       ItemData(min_lv = 2, max_lv = 16, base_wt = 0.15, sprite=130, base_value=(2, 8),
                            base_name="Sceptre", affinity="wizard", handedness=2),

    "staff2":      ItemData(min_lv = 5, max_lv = 99, base_wt = 0.08, sprite=131, base_value=(3, 7),
                            base_name="Wizard's Staff", affinity="wizard", handedness=2),

    "red_pot":     ItemData(min_lv = 1, max_lv = 99, base_wt = 0.25, sprite=115, base_value=1,
                            base_name="Health Potion", affinity=None, handedness=0),

    "blue_pot":    ItemData(min_lv = 1, max_lv = 99, base_wt = 0.10, sprite=116, base_value=1,
                            base_name="Sorcery Potion", affinity="wizard", handedness=0),

    "green_pot":   ItemData(min_lv = 1, max_lv = 99, base_wt = 0.10, sprite=114, base_value=1,
                            base_name="Strength Potion", affinity="viking", handedness=0),

    "grey_pot":    ItemData(min_lv = 1, max_lv = 99, base_wt = 0.10, sprite=113, base_value=1,
                            base_name="Defense Potion", affinity="knight", handedness=0),

    "sm_grey_pot": ItemData(min_lv = 1, max_lv = 99, base_wt = 0.05, sprite=125, base_value=1,
                            base_name="Luck Potion", affinity=None, handedness=0),
    }
