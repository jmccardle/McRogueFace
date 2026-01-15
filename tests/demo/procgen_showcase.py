#!/usr/bin/env python3
"""Generate screenshots for procgen cookbook recipes.

Uses Frame-based visualization since Grid cell colors use ColorLayer API.
"""
import mcrfpy
from mcrfpy import automation
import sys

OUTPUT_DIR = "/opt/goblincorps/repos/mcrogueface.github.io/images/cookbook"

# Simple PRNG
_seed = 42

def random():
    global _seed
    _seed = (_seed * 1103515245 + 12345) & 0x7fffffff
    return (_seed >> 16) / 32768.0

def seed(n):
    global _seed
    _seed = n

def choice(lst):
    return lst[int(random() * len(lst))]


def screenshot_cellular_caves():
    """Generate cellular automata caves visualization."""
    print("Generating cellular automata caves...")

    scene = mcrfpy.Scene("caves")
    scene.activate()
    mcrfpy.step(0.1)

    # Background
    bg = mcrfpy.Frame(pos=(0, 0), size=(640, 500))
    bg.fill_color = mcrfpy.Color(15, 15, 25)
    scene.children.append(bg)

    width, height = 50, 35
    cell_size = 12
    seed(42)

    # Store cell data
    cells = [[False for _ in range(width)] for _ in range(height)]

    # Step 1: Random noise (45% walls)
    for y in range(height):
        for x in range(width):
            if x == 0 or x == width-1 or y == 0 or y == height-1:
                cells[y][x] = True  # Border walls
            else:
                cells[y][x] = random() < 0.45

    # Step 2: Smooth with cellular automata (5 iterations)
    for _ in range(5):
        new_cells = [[cells[y][x] for x in range(width)] for y in range(height)]
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                wall_count = sum(
                    1 for dy in [-1, 0, 1] for dx in [-1, 0, 1]
                    if not (dx == 0 and dy == 0) and cells[y + dy][x + dx]
                )
                if wall_count >= 5:
                    new_cells[y][x] = True
                elif wall_count <= 3:
                    new_cells[y][x] = False
        cells = new_cells

    # Find largest connected region
    visited = set()
    regions = []

    def flood_fill(start_x, start_y):
        result = []
        stack = [(start_x, start_y)]
        while stack:
            x, y = stack.pop()
            if (x, y) in visited or x < 0 or x >= width or y < 0 or y >= height:
                continue
            if cells[y][x]:  # Wall
                continue
            visited.add((x, y))
            result.append((x, y))
            stack.extend([(x+1, y), (x-1, y), (x, y+1), (x, y-1)])
        return result

    for y in range(height):
        for x in range(width):
            if (x, y) not in visited and not cells[y][x]:
                region = flood_fill(x, y)
                if region:
                    regions.append(region)

    largest = max(regions, key=len) if regions else []
    largest_set = set(largest)

    # Draw cells as colored frames
    for y in range(height):
        for x in range(width):
            px = 20 + x * cell_size
            py = 20 + y * cell_size
            cell = mcrfpy.Frame(pos=(px, py), size=(cell_size - 1, cell_size - 1))

            if cells[y][x]:
                cell.fill_color = mcrfpy.Color(60, 40, 30)  # Wall
            elif (x, y) in largest_set:
                cell.fill_color = mcrfpy.Color(50, 90, 100)  # Main cave
            else:
                cell.fill_color = mcrfpy.Color(45, 35, 30)  # Filled region

            scene.children.append(cell)

    # Title
    title = mcrfpy.Caption(text="Cellular Automata Caves", pos=(20, 445))
    title.fill_color = mcrfpy.Color(200, 200, 200)
    title.font_size = 18
    scene.children.append(title)

    subtitle = mcrfpy.Caption(text="45% fill, 5 iterations, largest region preserved", pos=(20, 468))
    subtitle.fill_color = mcrfpy.Color(130, 130, 140)
    subtitle.font_size = 12
    scene.children.append(subtitle)

    mcrfpy.step(0.1)
    automation.screenshot(OUTPUT_DIR + "/procgen_cellular_caves.png")
    print("Saved: procgen_cellular_caves.png")


def screenshot_wfc():
    """Generate WFC pattern visualization."""
    print("Generating WFC patterns...")

    scene = mcrfpy.Scene("wfc")
    scene.activate()
    mcrfpy.step(0.1)

    # Background
    bg = mcrfpy.Frame(pos=(0, 0), size=(640, 500))
    bg.fill_color = mcrfpy.Color(15, 20, 15)
    scene.children.append(bg)

    width, height = 40, 28
    cell_size = 15
    seed(123)

    GRASS, DIRT, WATER, SAND = 0, 1, 2, 3
    colors = {
        GRASS: mcrfpy.Color(60, 120, 50),
        DIRT: mcrfpy.Color(100, 70, 40),
        WATER: mcrfpy.Color(40, 80, 140),
        SAND: mcrfpy.Color(180, 160, 90)
    }

    rules = {
        GRASS: {'N': [GRASS, DIRT, SAND], 'S': [GRASS, DIRT, SAND],
                'E': [GRASS, DIRT, SAND], 'W': [GRASS, DIRT, SAND]},
        DIRT:  {'N': [GRASS, DIRT], 'S': [GRASS, DIRT],
                'E': [GRASS, DIRT], 'W': [GRASS, DIRT]},
        WATER: {'N': [WATER, SAND], 'S': [WATER, SAND],
                'E': [WATER, SAND], 'W': [WATER, SAND]},
        SAND:  {'N': [GRASS, WATER, SAND], 'S': [GRASS, WATER, SAND],
                'E': [GRASS, WATER, SAND], 'W': [GRASS, WATER, SAND]}
    }

    tiles = set(rules.keys())
    possibilities = {(x, y): set(tiles) for y in range(height) for x in range(width)}
    result = {}

    # Seed water lake
    for x in range(22, 32):
        for y in range(8, 18):
            possibilities[(x, y)] = {WATER}
            result[(x, y)] = WATER

    # Seed dirt path
    for y in range(10, 18):
        possibilities[(3, y)] = {DIRT}
        result[(3, y)] = DIRT

    directions = {'N': (0, -1), 'S': (0, 1), 'E': (1, 0), 'W': (-1, 0)}

    def propagate(sx, sy):
        stack = [(sx, sy)]
        while stack:
            x, y = stack.pop()
            current = possibilities[(x, y)]
            for dir_name, (dx, dy) in directions.items():
                nx, ny = x + dx, y + dy
                if not (0 <= nx < width and 0 <= ny < height):
                    continue
                neighbor = possibilities[(nx, ny)]
                if len(neighbor) == 1:
                    continue
                allowed = set()
                for tile in current:
                    if dir_name in rules[tile]:
                        allowed.update(rules[tile][dir_name])
                new_opts = neighbor & allowed
                if new_opts and new_opts != neighbor:
                    possibilities[(nx, ny)] = new_opts
                    stack.append((nx, ny))

    # Propagate from seeds
    for x in range(22, 32):
        for y in range(8, 18):
            propagate(x, y)
    for y in range(10, 18):
        propagate(3, y)

    # Collapse
    for _ in range(width * height):
        best, best_e = None, 1000.0
        for pos, opts in possibilities.items():
            if len(opts) > 1:
                e = len(opts) + random() * 0.1
                if e < best_e:
                    best_e, best = e, pos

        if best is None:
            break

        x, y = best
        opts = list(possibilities[(x, y)])
        if not opts:
            break

        weights = {GRASS: 5, DIRT: 2, WATER: 1, SAND: 2}
        weighted = []
        for t in opts:
            weighted.extend([t] * weights.get(t, 1))
        chosen = choice(weighted) if weighted else GRASS

        possibilities[(x, y)] = {chosen}
        result[(x, y)] = chosen
        propagate(x, y)

    # Fill remaining
    for y in range(height):
        for x in range(width):
            if (x, y) not in result:
                opts = list(possibilities[(x, y)])
                result[(x, y)] = choice(opts) if opts else GRASS

    # Draw
    for y in range(height):
        for x in range(width):
            px = 20 + x * cell_size
            py = 20 + y * cell_size
            cell = mcrfpy.Frame(pos=(px, py), size=(cell_size - 1, cell_size - 1))
            cell.fill_color = colors[result[(x, y)]]
            scene.children.append(cell)

    # Title
    title = mcrfpy.Caption(text="Wave Function Collapse", pos=(20, 445))
    title.fill_color = mcrfpy.Color(200, 200, 200)
    title.font_size = 18
    scene.children.append(title)

    subtitle = mcrfpy.Caption(text="Constraint-based terrain (seeded lake + path)", pos=(20, 468))
    subtitle.fill_color = mcrfpy.Color(130, 140, 130)
    subtitle.font_size = 12
    scene.children.append(subtitle)

    # Legend
    for i, (name, tid) in enumerate([("Grass", GRASS), ("Dirt", DIRT), ("Sand", SAND), ("Water", WATER)]):
        lx, ly = 480, 445 + i * 14
        swatch = mcrfpy.Frame(pos=(lx, ly), size=(12, 12))
        swatch.fill_color = colors[tid]
        scene.children.append(swatch)
        label = mcrfpy.Caption(text=name, pos=(lx + 16, ly))
        label.fill_color = mcrfpy.Color(150, 150, 150)
        label.font_size = 11
        scene.children.append(label)

    mcrfpy.step(0.1)
    automation.screenshot(OUTPUT_DIR + "/procgen_wfc.png")
    print("Saved: procgen_wfc.png")


if __name__ == "__main__":
    screenshot_cellular_caves()
    screenshot_wfc()
    print("\nDone!")
    sys.exit(0)
