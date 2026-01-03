"""McRogueFace - Cell Highlighting (Targeting) (multi)

Documentation: https://mcrogueface.github.io/cookbook/grid_cell_highlighting
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/grid/grid_cell_highlighting_multi.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

def show_path_preview(start, end):
    """Highlight the path between two points."""
    path = find_path(start, end)  # Your pathfinding function

    if path:
        highlights.add('path', path)

        # Highlight destination specially
        highlights.add('select', [end])

def hide_path_preview():
    """Clear path display."""
    highlights.remove('path')
    highlights.remove('select')