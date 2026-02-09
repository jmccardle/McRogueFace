"""Base class for interactive procedural generation demos.

Provides the core framework for:
- Step-by-step generation with forward/backward navigation
- State snapshots for true backward navigation
- Parameter management with regeneration on change
- Layer visibility management
- UI layout with control panel
"""

import mcrfpy
from dataclasses import dataclass, field
from typing import List, Dict, Any, Callable, Optional, Tuple
from abc import ABC, abstractmethod
from .parameter import Parameter
from .widgets import Stepper, Slider, LayerToggle
from .viewport import ViewportController


@dataclass
class StepDef:
    """Definition of a generation step.

    Attributes:
        name: Display name for the step
        function: Callable that executes the step
        description: Optional longer description/tooltip
    """
    name: str
    function: Callable
    description: str = ""


@dataclass
class LayerDef:
    """Definition of a visualization layer.

    Attributes:
        name: Internal name (for grid.layers access)
        display: Display name in UI
        type: 'color' or 'tile'
        z_index: Render order (-1 = below entities, 1 = above)
        visible: Initial visibility
        description: Optional tooltip
    """
    name: str
    display: str
    type: str = "color"
    z_index: int = -1
    visible: bool = True
    description: str = ""


@dataclass
class StateSnapshot:
    """Captured state at a specific step for backward navigation.

    Stores HeightMap data as lists for restoration.
    """
    step_index: int
    heightmaps: Dict[str, List[float]] = field(default_factory=dict)
    layer_colors: Dict[str, List[Tuple[int, int, int, int]]] = field(default_factory=dict)
    extra_data: Dict[str, Any] = field(default_factory=dict)


class ProcgenDemoBase(ABC):
    """Abstract base class for procedural generation demos.

    Subclasses must implement:
    - name: Demo display name
    - description: Demo description
    - define_steps(): Return list of StepDef
    - define_parameters(): Return list of Parameter
    - define_layers(): Return list of LayerDef

    The framework provides:
    - Step navigation (forward/backward)
    - State snapshot capture and restoration
    - Parameter UI widgets
    - Layer visibility toggles
    - Viewport pan/zoom
    """

    # Subclass must set these
    name: str = "Unnamed Demo"
    description: str = ""

    # Default map size - subclasses can override
    MAP_SIZE: Tuple[int, int] = (256, 256)

    # Layout constants
    GRID_WIDTH = 700
    GRID_HEIGHT = 525
    PANEL_WIDTH = 300
    PANEL_X = 720

    def __init__(self):
        """Initialize the demo framework."""
        # Get definitions from subclass
        self.steps = self.define_steps()
        self.parameters = {p.name: p for p in self.define_parameters()}
        self.layer_defs = self.define_layers()

        # State tracking
        self.current_step = 0
        self.state_history: List[StateSnapshot] = []
        self.heightmaps: Dict[str, mcrfpy.HeightMap] = {}

        # UI elements
        self.scene = None
        self.grid = None
        self.layers: Dict[str, Any] = {}
        self.viewport = None
        self.widgets: Dict[str, Any] = {}

        # Build the scene
        self._build_scene()

        # Wire up parameter change handlers
        for param in self.parameters.values():
            param._on_change = self._on_parameter_change

    @abstractmethod
    def define_steps(self) -> List[StepDef]:
        """Define the generation steps. Subclass must implement."""
        pass

    @abstractmethod
    def define_parameters(self) -> List[Parameter]:
        """Define configurable parameters. Subclass must implement."""
        pass

    @abstractmethod
    def define_layers(self) -> List[LayerDef]:
        """Define visualization layers. Subclass must implement."""
        pass

    def _build_scene(self):
        """Build the scene with grid, layers, and control panel."""
        self.scene = mcrfpy.Scene(f"procgen_{self.name.lower().replace(' ', '_')}")
        ui = self.scene.children

        # Background
        bg = mcrfpy.Frame(
            pos=(0, 0),
            size=(1024, 768),
            fill_color=mcrfpy.Color(25, 25, 30)
        )
        ui.append(bg)

        # Grid for visualization
        self.grid = mcrfpy.Grid(
            grid_size=self.MAP_SIZE,
            pos=(10, 10),
            size=(self.GRID_WIDTH, self.GRID_HEIGHT)
        )
        ui.append(self.grid)

        # Add layers from definitions
        for layer_def in self.layer_defs:
            if layer_def.type == "color":
                layer = mcrfpy.ColorLayer(z_index=layer_def.z_index, grid_size=self.MAP_SIZE)
            else:
                layer = mcrfpy.TileLayer(z_index=layer_def.z_index, grid_size=self.MAP_SIZE)
            self.grid.add_layer(layer)
            layer.visible = layer_def.visible
            self.layers[layer_def.name] = layer

        # Keyboard handler - set BEFORE viewport so viewport can chain to it
        self.scene.on_key = self._on_key

        # Set up viewport controller (handles scroll wheel via on_click, chains keyboard to us)
        self.viewport = ViewportController(
            self.grid, self.scene,
            on_zoom_change=self._on_zoom_change
        )

        # Build control panel
        self._build_control_panel(ui)

    def _build_control_panel(self, ui):
        """Build the right-side control panel."""
        panel_y = 10

        # Title
        title = mcrfpy.Caption(
            text=f"Demo: {self.name}",
            pos=(self.PANEL_X, panel_y),
            font_size=20,
            fill_color=mcrfpy.Color(220, 220, 230)
        )
        ui.append(title)
        panel_y += 35

        # Separator
        sep1 = mcrfpy.Frame(
            pos=(self.PANEL_X, panel_y),
            size=(self.PANEL_WIDTH, 2),
            fill_color=mcrfpy.Color(60, 60, 70)
        )
        ui.append(sep1)
        panel_y += 10

        # Step navigation
        step_label = mcrfpy.Caption(
            text="Step:",
            pos=(self.PANEL_X, panel_y),
            font_size=14,
            fill_color=mcrfpy.Color(150, 150, 160)
        )
        ui.append(step_label)
        panel_y += 20

        # Step display and navigation
        self._step_display = mcrfpy.Caption(
            text=self._format_step_display(),
            pos=(self.PANEL_X, panel_y),
            font_size=16,
            fill_color=mcrfpy.Color(200, 200, 210)
        )
        ui.append(self._step_display)

        # Step nav buttons
        btn_prev = mcrfpy.Frame(
            pos=(self.PANEL_X + 200, panel_y - 5),
            size=(30, 25),
            fill_color=mcrfpy.Color(60, 60, 70),
            outline=1,
            outline_color=mcrfpy.Color(100, 100, 110)
        )
        prev_label = mcrfpy.Caption(text="<", pos=(10, 3), font_size=14,
                                     fill_color=mcrfpy.Color(200, 200, 210))
        btn_prev.children.append(prev_label)
        btn_prev.on_click = lambda p, b, a: self._on_step_prev() if b == mcrfpy.MouseButton.LEFT and a == mcrfpy.InputState.RELEASED else None
        ui.append(btn_prev)

        btn_next = mcrfpy.Frame(
            pos=(self.PANEL_X + 235, panel_y - 5),
            size=(30, 25),
            fill_color=mcrfpy.Color(60, 60, 70),
            outline=1,
            outline_color=mcrfpy.Color(100, 100, 110)
        )
        next_label = mcrfpy.Caption(text=">", pos=(10, 3), font_size=14,
                                     fill_color=mcrfpy.Color(200, 200, 210))
        btn_next.children.append(next_label)
        btn_next.on_click = lambda p, b, a: self._on_step_next() if b == mcrfpy.MouseButton.LEFT and a == mcrfpy.InputState.RELEASED else None
        ui.append(btn_next)

        panel_y += 30

        # Current step name
        self._step_name = mcrfpy.Caption(
            text="",
            pos=(self.PANEL_X, panel_y),
            font_size=12,
            fill_color=mcrfpy.Color(120, 150, 180)
        )
        ui.append(self._step_name)
        panel_y += 30

        # Separator
        sep2 = mcrfpy.Frame(
            pos=(self.PANEL_X, panel_y),
            size=(self.PANEL_WIDTH, 2),
            fill_color=mcrfpy.Color(60, 60, 70)
        )
        ui.append(sep2)
        panel_y += 15

        # Parameters section
        if self.parameters:
            param_header = mcrfpy.Caption(
                text="Parameters",
                pos=(self.PANEL_X, panel_y),
                font_size=14,
                fill_color=mcrfpy.Color(150, 150, 160)
            )
            ui.append(param_header)
            panel_y += 25

            for param in self.parameters.values():
                # Parameter label
                param_label = mcrfpy.Caption(
                    text=param.display + ":",
                    pos=(self.PANEL_X, panel_y),
                    font_size=12,
                    fill_color=mcrfpy.Color(180, 180, 190)
                )
                ui.append(param_label)
                panel_y += 20

                # Widget based on type
                if param.type == 'int':
                    widget = Stepper(param, pos=(self.PANEL_X, panel_y),
                                    width=180, on_change=self._on_widget_change)
                else:  # float
                    widget = Slider(param, pos=(self.PANEL_X, panel_y),
                                   width=200, on_change=self._on_widget_change)
                ui.append(widget.frame)
                self.widgets[param.name] = widget
                panel_y += 35

        panel_y += 10

        # Separator
        sep3 = mcrfpy.Frame(
            pos=(self.PANEL_X, panel_y),
            size=(self.PANEL_WIDTH, 2),
            fill_color=mcrfpy.Color(60, 60, 70)
        )
        ui.append(sep3)
        panel_y += 15

        # Layers section
        if self.layer_defs:
            layer_header = mcrfpy.Caption(
                text="Layers",
                pos=(self.PANEL_X, panel_y),
                font_size=14,
                fill_color=mcrfpy.Color(150, 150, 160)
            )
            ui.append(layer_header)
            panel_y += 25

            for layer_def in self.layer_defs:
                layer = self.layers.get(layer_def.name)
                toggle = LayerToggle(
                    layer_def.display, layer,
                    pos=(self.PANEL_X, panel_y),
                    width=180,
                    initial=layer_def.visible,
                    on_change=self._on_layer_toggle
                )
                ui.append(toggle.frame)
                self.widgets[f"layer_{layer_def.name}"] = toggle
                panel_y += 30

        panel_y += 15

        # View section
        sep4 = mcrfpy.Frame(
            pos=(self.PANEL_X, panel_y),
            size=(self.PANEL_WIDTH, 2),
            fill_color=mcrfpy.Color(60, 60, 70)
        )
        ui.append(sep4)
        panel_y += 15

        view_header = mcrfpy.Caption(
            text="View",
            pos=(self.PANEL_X, panel_y),
            font_size=14,
            fill_color=mcrfpy.Color(150, 150, 160)
        )
        ui.append(view_header)
        panel_y += 25

        self._zoom_display = mcrfpy.Caption(
            text="Zoom: 1.00x",
            pos=(self.PANEL_X, panel_y),
            font_size=12,
            fill_color=mcrfpy.Color(180, 180, 190)
        )
        ui.append(self._zoom_display)
        panel_y += 25

        # Reset view button
        btn_reset = mcrfpy.Frame(
            pos=(self.PANEL_X, panel_y),
            size=(100, 25),
            fill_color=mcrfpy.Color(60, 60, 70),
            outline=1,
            outline_color=mcrfpy.Color(100, 100, 110)
        )
        reset_label = mcrfpy.Caption(text="Reset View", pos=(15, 5), font_size=12,
                                      fill_color=mcrfpy.Color(200, 200, 210))
        btn_reset.children.append(reset_label)
        btn_reset.on_click = lambda p, b, a: self.viewport.reset_view() if b == mcrfpy.MouseButton.LEFT and a == mcrfpy.InputState.RELEASED else None
        ui.append(btn_reset)
        panel_y += 40

        # Instructions at bottom
        instructions = [
            "Left/Right: Step nav",
            "Middle-drag: Pan",
            "Scroll: Zoom",
            "1-9: Toggle layers",
            "R: Reset view",
            "Esc: Menu"
        ]
        for instr in instructions:
            instr_caption = mcrfpy.Caption(
                text=instr,
                pos=(self.PANEL_X, panel_y),
                font_size=10,
                fill_color=mcrfpy.Color(100, 100, 110)
            )
            ui.append(instr_caption)
            panel_y += 15

    def _format_step_display(self) -> str:
        """Format step counter display."""
        return f"{self.current_step}/{len(self.steps)}"

    def _update_step_display(self):
        """Update step navigation display."""
        self._step_display.text = self._format_step_display()
        if 0 < self.current_step <= len(self.steps):
            self._step_name.text = self.steps[self.current_step - 1].name
        else:
            self._step_name.text = "(not started)"

    def _on_zoom_change(self, zoom: float):
        """Handle zoom level change."""
        self._zoom_display.text = f"Zoom: {zoom:.2f}x"

    def _on_step_prev(self):
        """Go to previous step."""
        self.reverse_step()

    def _on_step_next(self):
        """Go to next step."""
        self.advance_step()

    def _on_widget_change(self, param: Parameter):
        """Handle parameter widget change."""
        # Parameter already updated, trigger regeneration
        self.regenerate_from(param.affects_step)

    def _on_parameter_change(self, param: Parameter):
        """Handle direct parameter value change."""
        # Update widget display if exists
        widget = self.widgets.get(param.name)
        if widget:
            widget.update_display()

    def _on_layer_toggle(self, name: str, visible: bool):
        """Handle layer visibility toggle."""
        # Layer visibility already updated by widget
        pass

    def _on_key(self, key, action):
        """Handle keyboard input."""
        # Only process on key press
        if action != mcrfpy.InputState.PRESSED:
            return

        # Check specific keys using enums
        if key == mcrfpy.Key.LEFT:
            self.reverse_step()
        elif key == mcrfpy.Key.RIGHT:
            self.advance_step()
        elif key == mcrfpy.Key.R:
            self.viewport.reset_view()
        elif key == mcrfpy.Key.ESCAPE:
            self._return_to_menu()
        else:
            # Number keys for layer toggles - convert to string for parsing
            key_str = str(key) if not isinstance(key, str) else key
            if key_str.startswith("Key.NUM") or (len(key_str) == 1 and key_str.isdigit()):
                try:
                    num = int(key_str[-1])
                    if 1 <= num <= len(self.layer_defs):
                        layer_def = self.layer_defs[num - 1]
                        toggle = self.widgets.get(f"layer_{layer_def.name}")
                        if toggle:
                            toggle.toggle()
                except (ValueError, IndexError):
                    pass

    def _return_to_menu(self):
        """Return to demo menu."""
        try:
            from ..main import show_menu
            show_menu()
        except ImportError:
            pass

    # === State Management ===

    def capture_state(self) -> StateSnapshot:
        """Capture current state for later restoration."""
        snapshot = StateSnapshot(step_index=self.current_step)

        # Capture HeightMap data
        for name, hmap in self.heightmaps.items():
            data = []
            w, h = hmap.size
            for y in range(h):
                for x in range(w):
                    data.append(hmap[x, y])
            snapshot.heightmaps[name] = data

        # Capture layer colors
        for name, layer in self.layers.items():
            if hasattr(layer, 'at'):  # ColorLayer
                colors = []
                w, h = layer.grid_size
                for y in range(h):
                    for x in range(w):
                        c = layer.at(x, y)
                        colors.append((c.r, c.g, c.b, c.a))
                snapshot.layer_colors[name] = colors

        return snapshot

    def restore_state(self, snapshot: StateSnapshot):
        """Restore state from snapshot."""
        # Restore HeightMap data
        for name, data in snapshot.heightmaps.items():
            if name in self.heightmaps:
                hmap = self.heightmaps[name]
                w, h = hmap.size
                idx = 0
                for y in range(h):
                    for x in range(w):
                        hmap[x, y] = data[idx]
                        idx += 1

        # Restore layer colors
        for name, colors in snapshot.layer_colors.items():
            if name in self.layers:
                layer = self.layers[name]
                if hasattr(layer, 'set'):  # ColorLayer
                    w, h = layer.grid_size
                    idx = 0
                    for y in range(h):
                        for x in range(w):
                            r, g, b, a = colors[idx]
                            layer.set((x, y), mcrfpy.Color(r, g, b, a))
                            idx += 1

        self.current_step = snapshot.step_index
        self._update_step_display()

    def advance_step(self):
        """Execute the next generation step."""
        if self.current_step >= len(self.steps):
            return  # Already at end

        # Capture state before this step
        snapshot = self.capture_state()
        self.state_history.append(snapshot)

        # Execute the step
        step = self.steps[self.current_step]
        step.function()
        self.current_step += 1
        self._update_step_display()

    def reverse_step(self):
        """Restore to previous step's state."""
        if not self.state_history:
            return  # No history to restore

        snapshot = self.state_history.pop()
        self.restore_state(snapshot)

    def regenerate_from(self, step: int):
        """Re-run generation from a specific step after parameter change."""
        # Find the snapshot for the step before target
        while self.state_history and self.state_history[-1].step_index >= step:
            self.state_history.pop()

        # Restore to just before target step
        if self.state_history:
            snapshot = self.state_history[-1]
            self.restore_state(snapshot)
        else:
            # No history - reset to beginning
            self.current_step = 0
            self._reset_state()

        # Re-run steps up to where we were
        target = min(step + 1, len(self.steps))
        while self.current_step < target:
            self.advance_step()

    def _reset_state(self):
        """Reset all state to initial. Override in subclass if needed."""
        for hmap in self.heightmaps.values():
            hmap.fill(0.0)
        for layer in self.layers.values():
            if hasattr(layer, 'fill'):
                layer.fill(mcrfpy.Color(0, 0, 0, 0))

    # === Activation ===

    def activate(self):
        """Activate this demo's scene."""
        mcrfpy.current_scene = self.scene
        self._update_step_display()

    def run(self):
        """Activate and run through first step."""
        self.activate()

    # === Utility Methods for Subclasses ===

    def get_param(self, name: str) -> Any:
        """Get current value of a parameter."""
        param = self.parameters.get(name)
        return param.value if param else None

    def create_heightmap(self, name: str, fill: float = 0.0) -> mcrfpy.HeightMap:
        """Create and register a HeightMap."""
        hmap = mcrfpy.HeightMap(self.MAP_SIZE, fill=fill)
        self.heightmaps[name] = hmap
        return hmap

    def get_layer(self, name: str):
        """Get a layer by name."""
        return self.layers.get(name)
