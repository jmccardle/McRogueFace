"""Interactive Procedural Generation Demo System

An educational, interactive framework for exploring procedural generation
techniques in McRogueFace.

Features:
- 256x256 maps with click-drag pan and scroll-wheel zoom
- Interactive parameter controls (steppers, sliders)
- Layer visibility toggles for masks/overlays
- Step forward/backward through generation stages
- State snapshots for true backward navigation
"""

from .core.demo_base import ProcgenDemoBase, StepDef, LayerDef, StateSnapshot
from .core.parameter import Parameter
from .core.widgets import Stepper, Slider, LayerToggle
from .core.viewport import ViewportController

__all__ = [
    'ProcgenDemoBase',
    'StepDef',
    'LayerDef',
    'StateSnapshot',
    'Parameter',
    'Stepper',
    'Slider',
    'LayerToggle',
    'ViewportController',
]
