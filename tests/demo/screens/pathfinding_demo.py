"""pathfinding_demo.py - Visual explainer for the pathfinding primitives (#315).

Three panels side-by-side, each a self-contained grid with a visible backdrop,
floor/wall base layer, a title above, and a short live readout below:

  [Panel 1] A* with a selectable heuristic. Keys 1-5 cycle EUCLIDEAN, MANHATTAN,
            CHEBYSHEV, DIAGONAL, ZERO; Q/W nudge the weight by 0.25. The route and
            its length change with the heuristic/weight - ZERO degenerates A* to
            Dijkstra, higher weight trades optimality for a more direct search.

  [Panel 2] Dijkstra flood from a cursor-controlled root. Arrow keys move the root;
            the distance field re-renders as a gradient (bright = near, dark = far).

  [Panel 3] Multi-root FLEE. One inverted multi-root Dijkstra map feeds EVERY guard
            at once - the whole point of compute_multi: one O(N) pass serves all M
            goals instead of M separate floods. Guards descend the safety gradient
            away from the threats. T drops a new threat, R resets.

Exercises: Grid.find_path(heuristic=, weight=), Grid.get_dijkstra_map(root / roots=),
DijkstraMap.distance(), DijkstraMap.invert(), DijkstraMap.descent_step(),
mcrfpy.Heuristic.
"""
import mcrfpy
import sys

GRID_W, GRID_H = 20, 20
CELL_PX = 15
PANEL_W_PX = GRID_W * CELL_PX
GRID_Y = 70
GAP = 20

# Headless renders at a fixed 1024x768; lay the three panels out inside that.
SCREEN_W = 1024
SCREEN_H = 768
CONTENT_BOTTOM = GRID_Y + GRID_H * CELL_PX

# Palette
C_BG = mcrfpy.Color(16, 16, 24)
C_PANEL = mcrfpy.Color(28, 30, 42)
C_FLOOR = mcrfpy.Color(46, 50, 66)
C_WALL = mcrfpy.Color(12, 12, 18)
C_CLEAR = mcrfpy.Color(0, 0, 0, 0)

scene = mcrfpy.Scene("pathfinding_demo")
bg = mcrfpy.Frame(pos=(0, 0), size=(SCREEN_W, SCREEN_H), fill_color=C_BG)
scene.children.append(bg)

title = mcrfpy.Caption(text="Pathfinding primitives: custom A* heuristics + multi-root Dijkstra", pos=(GAP, 16))
title.fill_color = mcrfpy.Color(240, 240, 255)
scene.children.append(title)


def panel_x(i):
    return GAP + i * (PANEL_W_PX + GAP)


def make_panel(i, title_text, title_color):
    """Backdrop frame + grid + base floor/wall layer + a dynamic overlay layer."""
    x_off = panel_x(i)
    backdrop = mcrfpy.Frame(pos=(x_off - 3, GRID_Y - 3),
                            size=(PANEL_W_PX + 6, GRID_H * CELL_PX + 6),
                            fill_color=C_PANEL)
    scene.children.append(backdrop)

    g = mcrfpy.Grid(grid_size=(GRID_W, GRID_H), pos=(x_off, GRID_Y),
                    size=(PANEL_W_PX, GRID_H * CELL_PX))
    base = mcrfpy.ColorLayer(z_index=0, name="base")
    overlay = mcrfpy.ColorLayer(z_index=1, name="overlay")
    g.add_layer(base)
    g.add_layer(overlay)

    # Border walls + a wedge obstacle, drawn into the base layer so every panel
    # reads as a full grid with visible geometry.
    for y in range(GRID_H):
        for x in range(GRID_W):
            wall = (x in (0, GRID_W - 1)) or (y in (0, GRID_H - 1))
            c = g.at(x, y)
            c.walkable = not wall
            c.transparent = not wall
            base.set((x, y), C_WALL if wall else C_FLOOR)
    for y in range(4, 13):
        g.at(GRID_W // 2, y).walkable = False
        g.at(GRID_W // 2, y).transparent = False
        base.set((GRID_W // 2, y), C_WALL)
    scene.children.append(g)

    cap_title = mcrfpy.Caption(text=title_text, pos=(x_off, GRID_Y - 24))
    cap_title.fill_color = title_color
    scene.children.append(cap_title)

    readout = mcrfpy.Caption(text="", pos=(x_off, GRID_Y + GRID_H * CELL_PX + 8))
    readout.fill_color = mcrfpy.Color(190, 195, 215)
    scene.children.append(readout)
    return g, overlay, readout


# =============================================================================
# Panel 1: A* with heuristic switching
# =============================================================================
g1, layer1, read1 = make_panel(0, "1. A* heuristic", mcrfpy.Color(180, 220, 255))
HEURISTICS = [
    (mcrfpy.Heuristic.EUCLIDEAN, "EUCLIDEAN"),
    (mcrfpy.Heuristic.MANHATTAN, "MANHATTAN"),
    (mcrfpy.Heuristic.CHEBYSHEV, "CHEBYSHEV"),
    (mcrfpy.Heuristic.DIAGONAL, "DIAGONAL"),
    (mcrfpy.Heuristic.ZERO, "ZERO (=Dijkstra)"),
]
state_astar = {"hidx": 0, "weight": 1.0, "start": (2, 10), "end": (GRID_W - 3, 10)}


def redraw_astar():
    h, hname = HEURISTICS[state_astar["hidx"]]
    layer1.fill(C_CLEAR)
    p = g1.find_path(state_astar["start"], state_astar["end"],
                     heuristic=h, weight=state_astar["weight"])
    n_steps = 0
    if p is not None:
        for step in p:
            layer1.set((int(step.x), int(step.y)), mcrfpy.Color(255, 220, 80, 230))
            n_steps += 1
    layer1.set(state_astar["start"], mcrfpy.Color(80, 255, 120, 255))
    layer1.set(state_astar["end"], mcrfpy.Color(255, 90, 90, 255))
    read1.text = f"{hname}  w={state_astar['weight']:.2f}  len={n_steps}"


# =============================================================================
# Panel 2: Dijkstra flood
# =============================================================================
g2, layer2, read2 = make_panel(1, "2. Dijkstra flood", mcrfpy.Color(180, 255, 220))
state_dij = {"root": (GRID_W // 2 - 3, GRID_H // 2)}


def redraw_dijkstra():
    layer2.fill(C_CLEAR)
    root = state_dij["root"]
    if not g2.at(root[0], root[1]).walkable:
        read2.text = "root on wall - move with arrows"
        return
    dmap = g2.get_dijkstra_map(root)
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
            r = int(40 * t + 90 * (1 - t))
            gc = int(180 * (1 - t) + 30 * t)
            bc = int(255 * (1 - t) + 70 * t)
            layer2.set((x, y), mcrfpy.Color(r, gc, bc, 210))
    layer2.set(root, mcrfpy.Color(255, 255, 90, 255))
    read2.text = f"root={root}  max dist={max_dist:.1f}"


# =============================================================================
# Panel 3: Multi-root FLEE
# =============================================================================
g3, layer3, read3 = make_panel(2, "3. Multi-root flee", mcrfpy.Color(255, 190, 190))
state_flee = {
    "threats": [(3, 3), (GRID_W - 4, GRID_H - 4)],
    "guards": [(10, 6), (10, 10), (10, 14)],
    "safety": None,
}


def recompute_flee():
    # ONE multi-root Dijkstra map from all threats, inverted into a safety map.
    threat_map = g3.get_dijkstra_map(roots=state_flee["threats"])
    state_flee["safety"] = threat_map.invert()


def redraw_flee():
    layer3.fill(C_CLEAR)
    if state_flee["safety"] is not None:
        # Faint safety gradient backdrop (bright = safer).
        max_s = 0.0
        for y in range(1, GRID_H - 1):
            for x in range(1, GRID_W - 1):
                s = state_flee["safety"].distance((x, y))
                if s is not None and s > max_s:
                    max_s = s
        if max_s > 0:
            for y in range(1, GRID_H - 1):
                for x in range(1, GRID_W - 1):
                    s = state_flee["safety"].distance((x, y))
                    if s is None:
                        continue
                    t = min(1.0, s / max_s)
                    layer3.set((x, y), mcrfpy.Color(int(60 * t), int(90 * t), int(50 * t), 160))
    for t in state_flee["threats"]:
        layer3.set(t, mcrfpy.Color(255, 60, 60, 255))
    for gd in state_flee["guards"]:
        layer3.set(gd, mcrfpy.Color(80, 255, 120, 255))
    read3.text = (f"1 pass -> {len(state_flee['guards'])} guards flee "
                  f"{len(state_flee['threats'])} threats")


def step_guards():
    if state_flee["safety"] is None:
        return
    new_guards = []
    for gd in state_flee["guards"]:
        nxt = state_flee["safety"].descent_step(gd)
        if nxt is None:
            new_guards.append(gd)
            continue
        candidate = (int(nxt.x), int(nxt.y))
        if candidate in new_guards or candidate in state_flee["threats"]:
            new_guards.append(gd)
        else:
            new_guards.append(candidate)
    state_flee["guards"] = new_guards
    redraw_flee()


# =============================================================================
# Controls + key handling
# =============================================================================
instructions = [
    "Panel 1:  [1-5] heuristic    [Q/W] weight -/+",
    "Panel 2:  [arrow keys] move the Dijkstra root",
    "Panel 3:  [T] add threat    [R] reset    (guards auto-step)        [ESC] quit",
]
for i, text in enumerate(instructions):
    c = mcrfpy.Caption(text=text, pos=(GAP, CONTENT_BOTTOM + 44 + i * 24))
    c.fill_color = mcrfpy.Color(170, 172, 190)
    scene.children.append(c)


def on_key(key, state):
    if state != mcrfpy.InputState.PRESSED:
        return
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


def tick(timer, runtime):
    step_guards()


redraw_astar()
redraw_dijkstra()
recompute_flee()
redraw_flee()
mcrfpy.Timer("flee_tick", tick, 200)
mcrfpy.current_scene = scene
print("pathfinding_demo loaded - see on-screen instructions.")
