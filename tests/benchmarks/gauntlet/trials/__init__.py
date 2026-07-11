"""Trial base class and ordered TRIALS registry for The Gauntlet.

Each trial stress-tests one engine subsystem. The harness owns all Timers; a
trial only implements setup / set_load / tick / teardown and holds no timers of
its own, so teardown fully disposes its scene contents and trials never
contaminate each other.
"""


class Trial:
    # -- identity (override in subclasses) --------------------------------
    key = "trial"
    name = "TRIAL"
    unit = "units"
    accent = (200, 200, 200)
    description = "one line"

    # -- ramp parameters --------------------------------------------------
    base_load = 50
    growth = 1.6

    # -- safety (see safety.py) -------------------------------------------
    # Absolute hard cap on load; the ramp will not set a load above this even
    # if the frame budget still holds. None = no explicit cap (the RSS watchdog
    # and address-space backstop still apply). Trials whose cost grows faster
    # than their frame time (e.g. grid side -> S*S cells) MUST set this.
    max_load = None

    def predict_bytes(self, load):
        """Estimate the resident footprint (bytes) this trial would allocate at
        `load`. Return None if unpredictable. The ramp refuses a load whose
        prediction exceeds the memory budget BEFORE allocating it, so a
        geometric jump cannot OOM between two frame-time samples."""
        return None

    # -- lifecycle --------------------------------------------------------
    def __init__(self):
        self.scene = None
        self.ui = None
        self.load = 0

    def setup(self, scene, ui):
        """Build the arena under `scene`. `ui` is scene.children."""
        self.scene = scene
        self.ui = ui

    def set_load(self, level_value):
        """Create/destroy stress objects so the live load matches level_value."""
        raise NotImplementedError

    def tick(self, dt_ms):
        """Periodic simulation work (100 ms sim cadence). Default: no-op."""
        pass

    def teardown(self):
        """Remove everything this trial created."""
        if self.scene is not None:
            children = self.scene.children
            # Clear any grids' entity collections first.
            for child in list(children):
                ents = getattr(child, "entities", None)
                if ents is not None:
                    try:
                        while len(ents):
                            ents.remove(ents[len(ents) - 1])
                    except Exception:
                        pass
            while len(children):
                children.remove(children[len(children) - 1])
        self.scene = None
        self.ui = None
        self.load = 0

    # -- helpers ----------------------------------------------------------
    def _count_children(self):
        return len(self.ui) if self.ui is not None else 0


# Populated at import time from the individual trial modules.
from .entity_swarm import EntitySwarm
from .animation_storm import AnimationStorm
from .grid_titan import GridTitan
from .pathfinder_rush import PathfinderRush
from .ui_avalanche import UIAvalanche
from .sightline_siege import SightlineSiege

TRIALS = [
    EntitySwarm,
    AnimationStorm,
    GridTitan,
    PathfinderRush,
    UIAvalanche,
    SightlineSiege,
]


def make_trials():
    """Return a fresh instance of every trial, in order."""
    return [cls() for cls in TRIALS]
