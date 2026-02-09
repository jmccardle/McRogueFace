"""Viewport controller for pan and zoom on large maps.

Provides click-drag pan (middle mouse button) and scroll-wheel zoom
for navigating 256x256 or larger maps within a smaller viewport.
"""

import mcrfpy
from typing import Optional, Callable


class ViewportController:
    """Click-drag pan and scroll-wheel zoom for Grid.

    Features:
    - Middle-click drag to pan the viewport
    - Scroll wheel to zoom in/out (0.25x to 4.0x range)
    - Optional zoom level display callback

    Args:
        grid: The mcrfpy.Grid to control
        scene: The scene for keyboard event chaining
        min_zoom: Minimum zoom level (default 0.25)
        max_zoom: Maximum zoom level (default 4.0)
        zoom_factor: Multiplier per scroll tick (default 1.15)
        on_zoom_change: Optional callback(zoom_level) when zoom changes

    Note:
        Scroll wheel events are delivered via on_click with MouseButton.SCROLL_UP
        and MouseButton.SCROLL_DOWN (#231, #232).
    """

    def __init__(self, grid, scene,
                 min_zoom: float = 0.25,
                 max_zoom: float = 4.0,
                 zoom_factor: float = 1.15,
                 on_zoom_change: Optional[Callable] = None):
        self.grid = grid
        self.scene = scene
        self.min_zoom = min_zoom
        self.max_zoom = max_zoom
        self.zoom_factor = zoom_factor
        self.on_zoom_change = on_zoom_change

        # Drag state
        self.dragging = False
        self.drag_start_center = (0, 0)
        self.drag_start_mouse = (0, 0)

        # Store original handlers to chain
        self._original_on_click = getattr(grid, 'on_click', None)
        self._original_on_move = getattr(grid, 'on_move', None)
        self._original_on_key = getattr(scene, 'on_key', None)

        # Bind our handlers
        grid.on_click = self._on_click
        grid.on_move = self._on_move
        scene.on_key = self._on_key

    def _on_click(self, pos, button, action):
        """Handle drag start/end with middle mouse button, and scroll wheel zoom."""
        # Middle-click for panning
        if button == mcrfpy.MouseButton.MIDDLE:
            if action == mcrfpy.InputState.PRESSED:
                self.dragging = True
                self.drag_start_center = (self.grid.center.x, self.grid.center.y)
                self.drag_start_mouse = (pos.x, pos.y)
            elif action == mcrfpy.InputState.RELEASED:
                self.dragging = False
            return  # Don't chain middle-click to other handlers

        # Scroll wheel for zooming (#231, #232 - scroll is now a click event)
        if button == mcrfpy.MouseButton.SCROLL_UP:
            self._zoom_in()
            return
        elif button == mcrfpy.MouseButton.SCROLL_DOWN:
            self._zoom_out()
            return

        # Chain to original handler for other buttons
        if self._original_on_click:
            self._original_on_click(pos, button, action)

    def _on_move(self, pos):
        """Update center during drag."""
        if self.dragging:
            # Calculate mouse movement delta
            dx = pos.x - self.drag_start_mouse[0]
            dy = pos.y - self.drag_start_mouse[1]

            # Move center opposite to mouse movement, scaled by zoom
            # When zoomed in (zoom > 1), movement should be smaller
            # When zoomed out (zoom < 1), movement should be larger
            zoom = self.grid.zoom if hasattr(self.grid, 'zoom') else 1.0
            self.grid.center = (
                self.drag_start_center[0] - dx / zoom,
                self.drag_start_center[1] - dy / zoom
            )
        else:
            # Chain to original handler when not dragging
            if self._original_on_move:
                self._original_on_move(pos)

    def _on_key(self, key, action):
        """Handle keyboard input - chain to original handler.

        Note: Scroll wheel zoom is now handled in _on_click via
        MouseButton.SCROLL_UP/SCROLL_DOWN (#231, #232).
        """
        # Chain to original handler
        if self._original_on_key:
            self._original_on_key(key, action)

    def _zoom_in(self):
        """Increase zoom level."""
        current = self.grid.zoom if hasattr(self.grid, 'zoom') else 1.0
        new_zoom = min(self.max_zoom, current * self.zoom_factor)
        self.grid.zoom = new_zoom
        if self.on_zoom_change:
            self.on_zoom_change(new_zoom)

    def _zoom_out(self):
        """Decrease zoom level."""
        current = self.grid.zoom if hasattr(self.grid, 'zoom') else 1.0
        new_zoom = max(self.min_zoom, current / self.zoom_factor)
        self.grid.zoom = new_zoom
        if self.on_zoom_change:
            self.on_zoom_change(new_zoom)

    def reset_view(self):
        """Reset to default view (zoom=1, centered)."""
        self.grid.zoom = 1.0
        # Center on map center
        grid_size = self.grid.grid_size
        cell_w = self.grid.texture.sprite_size[0] if self.grid.texture else 16
        cell_h = self.grid.texture.sprite_size[1] if self.grid.texture else 16
        self.grid.center = (grid_size[0] * cell_w / 2, grid_size[1] * cell_h / 2)
        if self.on_zoom_change:
            self.on_zoom_change(1.0)

    def center_on_cell(self, cell_x: int, cell_y: int):
        """Center the viewport on a specific cell."""
        cell_w = self.grid.texture.sprite_size[0] if self.grid.texture else 16
        cell_h = self.grid.texture.sprite_size[1] if self.grid.texture else 16
        self.grid.center = (
            (cell_x + 0.5) * cell_w,
            (cell_y + 0.5) * cell_h
        )

    @property
    def zoom(self) -> float:
        """Get current zoom level."""
        return self.grid.zoom if hasattr(self.grid, 'zoom') else 1.0

    @zoom.setter
    def zoom(self, value: float):
        """Set zoom level within bounds."""
        self.grid.zoom = max(self.min_zoom, min(self.max_zoom, value))
        if self.on_zoom_change:
            self.on_zoom_change(self.grid.zoom)
