"""Sokoban puzzle solvability checker using BFS."""
from collections import deque


def can_reach(grid, start, goal, boulders, w, h, obstacles=frozenset()):
    """BFS check if start can reach goal, treating boulders and obstacles as walls."""
    if start == goal:
        return True
    visited = {start}
    queue = deque([start])
    while queue:
        px, py = queue.popleft()
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nx, ny = px + dx, py + dy
            if (nx, ny) == goal:
                return True
            if nx < 0 or nx >= w or ny < 0 or ny >= h:
                continue
            if not grid.at((nx, ny)).walkable:
                continue
            if (nx, ny) in boulders:
                continue
            if (nx, ny) in obstacles:
                continue
            if (nx, ny) not in visited:
                visited.add((nx, ny))
                queue.append((nx, ny))
    return False


def is_solvable(grid, player_pos, boulder_positions, button_positions, exit_pos,
                max_states=500000, obstacles=None):
    """BFS through Sokoban state space. Returns True if solvable.

    Args:
        grid: mcrfpy.Grid with walkability set
        player_pos: (x, y) tuple for player start
        boulder_positions: list of (x, y) tuples for boulders
        button_positions: list of (x, y) tuples for buttons
        exit_pos: (x, y) tuple for exit
        max_states: maximum states to explore before giving up
        obstacles: list of (x, y) tuples for immovable obstacles (treasures, etc.)

    Returns:
        True if the puzzle is solvable, False otherwise
    """
    w, h = int(grid.grid_size.x), int(grid.grid_size.y)
    obstacle_set = frozenset(obstacles) if obstacles else frozenset()

    def is_cell_open(x, y):
        """Check if a cell is in-bounds and walkable."""
        if x < 0 or x >= w or y < 0 or y >= h:
            return False
        return grid.at((x, y)).walkable

    def player_can_walk(x, y, boulders):
        """Check if player can walk to (x,y). Players can pass through obstacles (chests)."""
        if not is_cell_open(x, y):
            return False
        if (x, y) in boulders:
            return False
        return True

    def boulder_can_land(x, y, boulders):
        """Check if a boulder can be pushed to (x,y). Boulders cannot pass through obstacles."""
        if not is_cell_open(x, y):
            return False
        if (x, y) in boulders:
            return False
        if (x, y) in obstacle_set:
            return False
        return True

    initial = (player_pos, frozenset(boulder_positions))
    target_buttons = frozenset(button_positions)
    visited = {initial}
    queue = deque([initial])
    states_explored = 0

    while queue:
        if states_explored >= max_states:
            return True  # Too many states - assume solvable
        states_explored += 1
        (px, py), boulders = queue.popleft()

        # Win condition: all buttons covered by boulders
        if target_buttons <= boulders:
            if can_reach(grid, (px, py), exit_pos, boulders, w, h):
                return True

        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nx, ny = px + dx, py + dy

            if (nx, ny) in boulders:
                # Push boulder - boulder landing site must be obstacle-free
                bx, by = nx + dx, ny + dy
                if boulder_can_land(bx, by, boulders):
                    new_boulders = frozenset(boulders - {(nx, ny)} | {(bx, by)})
                    state = ((nx, ny), new_boulders)
                    if state not in visited:
                        visited.add(state)
                        queue.append(state)
            elif player_can_walk(nx, ny, boulders):
                state = ((nx, ny), boulders)
                if state not in visited:
                    visited.add(state)
                    queue.append(state)

    return False
