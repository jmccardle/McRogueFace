"""McRogueFace - Cell Highlighting (Targeting) (animated)

Documentation: https://mcrogueface.github.io/cookbook/grid_cell_highlighting
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/grid/grid_cell_highlighting_animated.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

class TargetingSystem:
    """Handle ability targeting with visual feedback."""

    def __init__(self, grid, player):
        self.grid = grid
        self.player = player
        self.highlights = HighlightManager(grid)
        self.current_ability = None
        self.valid_targets = set()

    def start_targeting(self, ability):
        """Begin targeting for an ability."""
        self.current_ability = ability
        px, py = self.player.pos

        # Get valid targets based on ability
        if ability.target_type == 'self':
            self.valid_targets = {(px, py)}
        elif ability.target_type == 'adjacent':
            self.valid_targets = get_adjacent(px, py)
        elif ability.target_type == 'ranged':
            self.valid_targets = get_radius_range(px, py, ability.range)
        elif ability.target_type == 'line':
            self.valid_targets = get_line_range(px, py, ability.range)

        # Filter to visible tiles only
        self.valid_targets = {
            (x, y) for x, y in self.valid_targets
            if grid.is_in_fov(x, y)
        }

        # Show valid targets
        self.highlights.add('attack', self.valid_targets)

    def update_hover(self, x, y):
        """Update when cursor moves."""
        if not self.current_ability:
            return

        # Clear previous AoE preview
        self.highlights.remove('danger')

        if (x, y) in self.valid_targets:
            # Valid target - highlight it
            self.highlights.add('select', [(x, y)])

            # Show AoE if applicable
            if self.current_ability.aoe_radius > 0:
                aoe = get_radius_range(x, y, self.current_ability.aoe_radius, True)
                self.highlights.add('danger', aoe)
        else:
            self.highlights.remove('select')

    def confirm_target(self, x, y):
        """Confirm target selection."""
        if (x, y) in self.valid_targets:
            self.cancel_targeting()
            return (x, y)
        return None

    def cancel_targeting(self):
        """Cancel targeting mode."""
        self.current_ability = None
        self.valid_targets = set()
        self.highlights.clear()