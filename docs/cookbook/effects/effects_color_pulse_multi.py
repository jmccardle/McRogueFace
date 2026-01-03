"""McRogueFace - Color Pulse Effect (multi)

Documentation: https://mcrogueface.github.io/cookbook/effects_color_pulse
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/effects/effects_color_pulse_multi.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

import mcrfpy

def ripple_effect(grid, center_x, center_y, color, max_radius=5, duration=1.0):
    """
    Create an expanding ripple effect.

    Args:
        grid: Grid with color layer
        center_x, center_y: Ripple origin
        color: RGB tuple
        max_radius: Maximum ripple size
        duration: Total animation time
    """
    # Get color layer
    color_layer = None
    for layer in grid.layers:
        if isinstance(layer, mcrfpy.ColorLayer):
            color_layer = layer
            break

    if not color_layer:
        grid.add_layer("color")
        color_layer = grid.layers[-1]

    step_duration = duration / max_radius

    for radius in range(max_radius + 1):
        # Get cells at this radius (ring, not filled)
        ring_cells = []
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                dist_sq = dx * dx + dy * dy
                # Include cells approximately on the ring edge
                if radius * radius - radius <= dist_sq <= radius * radius + radius:
                    cell = color_layer.at(center_x + dx, center_y + dy)
                    if cell:
                        ring_cells.append(cell)

        # Schedule this ring to animate
        def animate_ring(timer_name, cells=ring_cells, c=color):
            for cell in cells:
                cell.color = mcrfpy.Color(c[0], c[1], c[2], 200)
                # Fade out
                anim = mcrfpy.Animation("a", 0.0, step_duration * 2, "easeOut")
                anim.start(cell.color)

        delay = int(radius * step_duration * 1000)
        mcrfpy.Timer(f"ripple_{radius}", animate_ring, delay, once=True)


# Usage
ripple_effect(grid, 10, 10, (100, 200, 255), max_radius=6, duration=0.8)