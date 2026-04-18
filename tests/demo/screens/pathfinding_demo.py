"""pathfinding_demo.py - Visual demo of the #315 pathfinding primitives.

Three panels side-by-side on one scene:
  [Panel 1] A* with selectable heuristic. Keys 1-5 cycle EUCLIDEAN, MANHATTAN,
            CHEBYSHEV, DIAGONAL, ZERO. Q/W bump the weight by 0.25.
  [Panel 2] Dijkstra flood from a cursor-controlled root. Arrow keys move the
            cursor; the distance field re-renders as a blue gradient.
  [Panel 3] Multi-root FLEE: three "guard" entities flee from a shared set of
            threats, using an inverted multi-root Dijkstra map. Animated one
            step per frame tick. Press T to drop a new threat on the panel.

Also exercises: DijkstraMap.invert(), DijkstraMap.descent_step(),
mcrfpy.Heuristic, Grid.find_path(heuristic=, weight=), Grid.get_dijkstra_map(
roots=...).
"""
import mcrfpy
import sys


GRID_W, GRID_H = 20, 20
CELL_PX = 14
PANEL_W_PX = GRID_W * CELL_PX
GAP = 20

SCREEN_W = 3 * PANEL_W_PX + 4 * GAP
SCREEN_H = GRID_H * CELL_PX + 140


scene = mcrfpy.Scene("pathfinding_demo")

bg = mcrfpy.Frame(pos=(0, 0), size=(SCREEN_W, SCREEN_H),
                  fill_color=mcrfpy.Color(18, 18, 26))
scene.children.append(bg)

title = mcrfpy.Caption(text="Pathfinding Next-Gen Demo (#315)", pos=(GAP, 10))
title.fill_color = mcrfpy.Color(240, 240, 255)
scene.children.append(title)


def make_open_grid(x_off):
    g = mcrfpy.Grid(grid_size=(GRID_W, GRID_H),
                    pos=(x_off, 50),
                    size=(PANEL_W_PX, GRID_H * CELL_PX))
    for y in range(GRID_H):
        for x in range(GRID_W):
            c = g.at(x, y)
            wall = (x in (0, GRID_W - 1)) or (y in (0, GRID_H - 1))
            c.walkable = not wall
            c.transparent = not wall
    # A small wedge of walls in the middle for visual interest.
    for y in range(4, 12):
        g.at(GRID_W // 2, y).walkable = False
        g.at(GRID_W // 2, y).transparent = False
    scene.children.append(g)
    return g


# =============================================================================
# Panel 1: A* with heuristic switching
# =============================================================================
g1 = make_open_grid(GAP)
astar_layer = mcrfpy.ColorLayer(z_index=1, name="astar_path")
g1.add_layer(astar_layer)

HEURISTICS = [
    (mcrfpy.Heuristic.EUCLIDEAN, "EUCLIDEAN"),
    (mcrfpy.Heuristic.MANHATTAN, "MANHATTAN"),
    (mcrfpy.Heuristic.CHEBYSHEV, "CHEBYSHEV"),
    (mcrfpy.Heuristic.DIAGONAL,  "DIAGONAL"),
    (mcrfpy.Heuristic.ZERO,      "ZERO"),
]
state_astar = {"hidx": 0, "weight": 1.0,
               "start": (2, 10), "end": (GRID_W - 3, 10)}

cap_astar = mcrfpy.Caption(text="A* heuristic: EUCLIDEAN  weight=1.00",
                           pos=(GAP, 50 + GRID_H * CELL_PX + 6))
cap_astar.fill_color = mcrfpy.Color(180, 220, 255)
scene.children.append(cap_astar)


def redraw_astar():
    h, hname = HEURISTICS[state_astar["hidx"]]
    astar_layer.fill(mcrfpy.Color(0, 0, 0, 0))
    p = g1.find_path(state_astar["start"], state_astar["end"],
                     heuristic=h, weight=state_astar["weight"])
    n_steps = 0
    if p is not None:
        for step in p:
            astar_layer.set((int(step.x), int(step.y)),
                            mcrfpy.Color(255, 220, 80, 220))
            n_steps += 1
    # Start/end markers.
    astar_layer.set(state_astar["start"], mcrfpy.Color(80, 255, 120, 255))
    astar_layer.set(state_astar["end"], mcrfpy.Color(255, 90, 90, 255))
    cap_astar.text = (f"A* heuristic: {hname}  "
                      f"weight={state_astar['weight']:.2f}  steps={n_steps}")


# =============================================================================
# Panel 2: Dijkstra flood
# =============================================================================
g2 = make_open_grid(GAP * 2 + PANEL_W_PX)
dij_layer = mcrfpy.ColorLayer(z_index=1, name="dij_flood")
g2.add_layer(dij_layer)

state_dij = {"root": (GRID_W // 2 - 3, GRID_H // 2)}

cap_dij = mcrfpy.Caption(text="Dijkstra flood (arrows move root)",
                         pos=(GAP * 2 + PANEL_W_PX, 50 + GRID_H * CELL_PX + 6))
cap_dij.fill_color = mcrfpy.Color(180, 255, 220)
scene.children.append(cap_dij)


def redraw_dijkstra():
    dij_layer.fill(mcrfpy.Color(0, 0, 0, 0))
    root = state_dij["root"]
    if not g2.at(root[0], root[1]).walkable:
        cap_dij.text = "Dijkstra root on wall - move with arrows"
        return
    dmap = g2.get_dijkstra_map(root)
    # Sample distances to find the maximum for normalization.
    max_dist = 0.0
    for y in range(1, GRID_H - 1):
        for x in range(1, GRID_W - 1):
            d = dmap.distance((x, y))
            if d is not None and d > max_dist:
                max_dist = d
    if max_dist <= 0:
        return
    for y in range(1, GRID_H - 1):
        for x in range(1, GRID_W - 1):
            d = dmap.distance((x, y))
            if d is None:
                continue
            t = min(1.0, d / max_dist)
            # Cool gradient: near-root = bright, far = dark.
            r = int(40 * t + 80 * (1 - t))
            gc = int(160 * (1 - t) + 40 * t)
            bc = int(240 * (1 - t) + 80 * t)
            dij_layer.set((x, y), mcrfpy.Color(r, gc, bc, 180))
    dij_layer.set(root, mcrfpy.Color(255, 255, 90, 255))
    cap_dij.text = f"Dijkstra flood max={max_dist:.1f}  root={root}"


# =============================================================================
# Panel 3: Multi-root FLEE
# =============================================================================
g3 = make_open_grid(GAP * 3 + 2 * PANEL_W_PX)
flee_layer = mcrfpy.ColorLayer(z_index=1, name="flee_layer")
g3.add_layer(flee_layer)

state_flee = {
    "threats": [(3, 3), (GRID_W - 4, GRID_H - 4)],
    "guards": [(10, 6), (10, 10), (10, 14)],
    "safety": None,
    "threat_map": None,
}

cap_flee = mcrfpy.Caption(text="Multi-root FLEE (T adds threat, R resets)",
                          pos=(GAP * 3 + 2 * PANEL_W_PX,
                               50 + GRID_H * CELL_PX + 6))
cap_flee.fill_color = mcrfpy.Color(255, 190, 190)
scene.children.append(cap_flee)


def recompute_flee():
    state_flee["threat_map"] = g3.get_dijkstra_map(roots=state_flee["threats"])
    state_flee["safety"] = state_flee["threat_map"].invert()


def redraw_flee():
    flee_layer.fill(mcrfpy.Color(0, 0, 0, 0))
    # Threats: red.
    for t in state_flee["threats"]:
        flee_layer.set(t, mcrfpy.Color(255, 60, 60, 255))
    # Guards: green.
    for gd in state_flee["guards"]:
        flee_layer.set(gd, mcrfpy.Color(80, 255, 120, 255))
    cap_flee.text = (f"FLEE: {len(state_flee['threats'])} threats  "
                     f"{len(state_flee['guards'])} guards")


def step_guards():
    if state_flee["safety"] is None:
        return
    new_guards = []
    for gd in state_flee["guards"]:
        nxt = state_flee["safety"].descent_step(gd)
        if nxt is None:
            new_guards.append(gd)
        else:
            candidate = (int(nxt.x), int(nxt.y))
            # Avoid landing on another guard or a threat.
            if candidate in new_guards or candidate in state_flee["threats"]:
                new_guards.append(gd)
            else:
                new_guards.append(candidate)
    state_flee["guards"] = new_guards
    redraw_flee()


# =============================================================================
# Key handling
# =============================================================================
instructions = [
    "Panel 1 (A*):   [1-5] heuristic   [Q/W] weight -/+",
    "Panel 2 (Dij):  [Arrow keys] move root",
    "Panel 3 (FLEE): [T] add threat   [R] reset   (guards auto-step)",
    "[ESC] quit",
]
for i, text in enumerate(instructions):
    c = mcrfpy.Caption(text=text, pos=(GAP, SCREEN_H - 90 + i * 22))
    c.fill_color = mcrfpy.Color(180, 180, 200)
    scene.children.append(c)


def on_key(key, state):
    if state != mcrfpy.InputState.PRESSED:
        return

    # Heuristic switching
    for i, digit in enumerate([mcrfpy.Key.Num1, mcrfpy.Key.Num2, mcrfpy.Key.Num3,
                               mcrfpy.Key.Num4, mcrfpy.Key.Num5]):
        if key == digit:
            state_astar["hidx"] = i
            redraw_astar()
            return

    if key == mcrfpy.Key.Q:
        state_astar["weight"] = max(0.25, state_astar["weight"] - 0.25)
        redraw_astar()
        return
    if key == mcrfpy.Key.W:
        state_astar["weight"] = min(5.0, state_astar["weight"] + 0.25)
        redraw_astar()
        return

    # Dijkstra root movement
    rx, ry = state_dij["root"]
    moved = False
    if key == mcrfpy.Key.LEFT:
        rx = max(1, rx - 1); moved = True
    elif key == mcrfpy.Key.RIGHT:
        rx = min(GRID_W - 2, rx + 1); moved = True
    elif key == mcrfpy.Key.UP:
        ry = max(1, ry - 1); moved = True
    elif key == mcrfpy.Key.DOWN:
        ry = min(GRID_H - 2, ry + 1); moved = True
    if moved:
        state_dij["root"] = (rx, ry)
        redraw_dijkstra()

    # FLEE panel: drop threat at a random walkable cell.
    if key == mcrfpy.Key.T:
        import random
        for _ in range(20):
            p = (random.randint(1, GRID_W - 2), random.randint(1, GRID_H - 2))
            if g3.at(p[0], p[1]).walkable and p not in state_flee["threats"]:
                state_flee["threats"].append(p)
                break
        recompute_flee()
        redraw_flee()

    if key == mcrfpy.Key.R:
        state_flee["threats"] = [(3, 3), (GRID_W - 4, GRID_H - 4)]
        state_flee["guards"] = [(10, 6), (10, 10), (10, 14)]
        recompute_flee()
        redraw_flee()

    if key == mcrfpy.Key.ESCAPE:
        mcrfpy.exit()


scene.on_key = on_key

# Step FLEE guards on a timer (6 ticks/sec is slow enough to watch).
def tick(timer, runtime):
    step_guards()


# Initial render
redraw_astar()
redraw_dijkstra()
recompute_flee()
redraw_flee()

mcrfpy.Timer("flee_tick", tick, 160)
mcrfpy.current_scene = scene

print("pathfinding_demo loaded - see on-screen instructions.")
