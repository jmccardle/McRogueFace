# Grid Coordinate Spaces & the Overlay Pattern

Clarifies which coordinate space `UIDrawable` children are positioned in depending on
their parent, and how to build screen-space UI (HUDs, dialogs) that sits on top of a
panning/zooming `Grid`. See issue #360.

## The short version

- **`Frame.children`** are positioned **frame-local**: relative to the Frame's
  top-left corner. A `Frame` has no camera and cannot pan its content, so
  frame-local is effectively already screen space.
- **`Grid.children`** are positioned in the grid's **pixel-world coordinates** — the
  same origin as `Entity` positions — **not** in the grid widget's on-screen pixels.
  They pan and zoom with the grid's camera (`grid.center`, `grid.zoom`), exactly like
  entities and tiles do.

This is not an inconsistency to "fix": a `Frame` genuinely has no notion of a camera,
so there is no other coordinate space its children could reasonably use. A `Grid`
does have a camera, and its children are deliberately anchored to grid content (the
world), not to the viewport. Entities are positioned by cell; grid-world pixel
coordinates share that same origin, so a `Grid` child can be placed precisely next to
an entity (using `entity.pos`, itself documented as "pixel position relative to
grid") and will continue to track that entity's neighborhood as the camera moves.

The use case for `Grid.children` is **diegetic** UI: speech bubbles, damage numbers,
range indicators, path markers — things that belong to a place or an entity in the
world and should move/zoom with it.

```python
# A speech bubble anchored near an entity, in grid-world pixels.
# entity.pos is already "pixel position relative to grid" -- the same origin
# Grid.children use.
bubble = mcrfpy.Caption(text="Hello!", pos=(entity.pos.x, entity.pos.y - 20))
grid.children.append(bubble)
```

If you instead want UI that floats over the grid at a fixed screen position
regardless of where the camera is pointed — a health bar HUD, an inventory panel, a
modal dialog — **`Grid.children` is the wrong tool**, because those children would
pan and zoom right along with everything else and drift off screen.

## The overlay pattern

Put a `Frame` as a **sibling** of the `Grid` (not a child of it), sized and
positioned to match the `Grid`, and draw your screen-space UI as children of that
Frame instead. Give the overlay Frame a later `z_index` (or simply append it after
the Grid) so it draws on top.

```
Scene (or a container Frame)
├── Grid                      # pan, zoom, entities, diegetic children
│   ├── entities: positioned by cell
│   └── children: positioned in grid-world pixels (pan/zoom with camera)
└── Frame (overlay)           # same pos/size as the Grid, drawn after it
    └── children: positioned in frame-local coordinates (screen space)
```

```python
import mcrfpy

scene = mcrfpy.Scene("game")
ui = scene.children

grid = mcrfpy.Grid(grid_size=(40, 30), pos=(0, 0), size=(640, 480))
ui.append(grid)

# Diegetic marker: lives in the grid's world, pans/zooms with the camera.
marker = mcrfpy.Caption(text="!", pos=(160, 96))
grid.children.append(marker)

# Screen-space HUD: same pos/size as the grid, but its own children are
# frame-local, so they stay put no matter how grid.center/grid.zoom change.
overlay = mcrfpy.Frame(pos=(0, 0), size=(640, 480))
overlay.fill_color = mcrfpy.Color(0, 0, 0, 0)  # transparent container
ui.append(overlay)  # appended after grid -> draws on top

health_bar = mcrfpy.Frame(pos=(10, 10), size=(200, 20))
health_bar.fill_color = mcrfpy.Color(200, 40, 40)
overlay.children.append(health_bar)
```

Panning or zooming `grid` (`grid.center = ...`, `grid.zoom = ...`) moves `marker`
along with the world; `health_bar` never moves, because it belongs to `overlay`, not
to `grid`.

## See also

- `Grid.children` / `Frame.children` docstrings (`mcrfpy.Grid.children.__doc__`,
  `mcrfpy.Frame.children.__doc__`) for the API-level statement of this contract.
- `Entity.draw_pos` / `Entity.cell_pos` for the cell-vs-pixel distinction on the
  entity side of the same coordinate system.
