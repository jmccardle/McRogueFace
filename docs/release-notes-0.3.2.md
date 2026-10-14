# McRogueFace 0.3.2 — release notes

> Changes since the `0.3.1` tag.

## Headline: sprites fill their cells

Tile and entity sprites now stretch to the grid's `cell_size` (#480). A grid whose cells
aren't the texture's sprite size — an 8×8 font drawn into 40×48 cells to emulate CGA's
pixel aspect, a 9×14 MDA font at ×2/×3, an 8×8 sheet on 16×16 cells — draws every tile
filling its cell, instead of the sprite sitting at its own size in the cell's top-left
corner.

- **Tile layers** fit each tile to the cell: `scale = cell_size / that layer's texture's
  sprite size`. An oversized tile no longer overhangs its neighbours (or shows seams at
  64-cell chunk edges).
- **Entities** scale by the *grid* texture's factor, so an entity with its own taller
  sprite (16×24 on 16×16 cells) keeps its proportions.
- **`sprite_offset`** is in texture pixels and is stretched with the sprite.
- Grid children (Caption, Frame) are not stretched.

## Breaking changes and upgrade notes

| Change | What to do |
|---|---|
| **Setting an entity's cell moves its sprite** (#431). `grid_pos` / `grid_x` / `grid_y` and the `cell_*` aliases snap `draw_pos` to the new cell, as `grid.step()` always did. They used to change only the logical cell, so the entity stayed where it was drawn. | Smooth movement is animating `draw_pos`. To slide to a new cell: save `draw_pos`, set the cell, restore `draw_pos`, then `animate("draw_pos", cell, t)` — or animate first and set the cell when it ends. |
| **The spatial hash is keyed on the cell** (#431). `entities_in_radius` measures from each entity's cell, not from where its sprite is drawn, so an entity mid-animation is found at its logical position. `GridPoint.entities` no longer misses an entity whose sprite sits in a different bucket than its cell. | — |
| **Integer cell setters** (#431) accept an int or a whole-number float (`5.0`, a Vector component). A fractional, NaN or infinite float raises `ValueError` (`grid_pos=(5.5, 1)` used to truncate silently); a non-number raises `TypeError` (`cell_pos = 5` used to mean `Vector(5)`). | Round explicitly where you meant to truncate. |
| **Sprites stretch to `cell_size`** (#480; see above). A grid whose texture's sprite size differs from its cell size used to draw small sprites in the top-left of each cell. | If you relied on that, set `cell_size` to the texture's sprite size. Re-author `sprite_offset` in texture pixels. |
| **`Entity3D.animate()` names are attributes, in their units** (#449), as on every 2D type since 0.3.0 (#423). Its world position animates as `world_x`/`world_y`/`world_z`; `scale_x`/`scale_y`/`scale_z` and `sprite_index` are new readable attributes. | The old names `x`/`y`/`z` and `rot_y` raise `ValueError` naming the replacement: use `world_x`/`world_y`/`world_z`. |
| **One package per platform** (#435, #399). The light/full stdlib presets shipped the same stdlib and are gone: `McRogueFace-<v>-Linux.tar.gz` and `McRogueFace-<v>-Windows.zip` (no `-full`). `make package-linux` / `package-windows` / `package-all` replace the `-light`/`-full` targets. The networking/async guarantee now names `make package-linux`. | Update download links and scripts that name `-full`. |

## Fixes and additions

- **`Caption.advance`** (#479): the pen advance of the text — glyph advances plus kerning, trailing spaces included, widest line for multi-line text — for laying out runs of captions side by side. `w` remains the ink width.
- **`mcrfpy.lock()` serves each thread once per frame** (#410). A safe window closes against late arrivals, so polite background threads (sleeping between acquires) can no longer hold it open together and starve the main loop. See `docs/frame-lock.md`.
- **A grid layer chunk whose `RenderTexture` can't be created** (larger than the GPU's maximum texture size) warns once with `mcrfpy.TextureWarning`, naming the layer and chunk, and draws cell by cell. It used to retry, and print SFML's error, every frame (#470).
- **The engine releases its Python references before the interpreter finalizes** (#468): scenes, timers, animations, audio, the default font/texture and the module. `__del__` methods of objects the engine held now run at exit, and ASan runs report no exit leaks. Exposed and fixed on the way: re-running a drawable's `__init__` broke the wrapper cache (a use-after-free) and leaked a Frame's old children. After teardown, `step()` / `advance()` raise `RuntimeError`.
- **The shipped templates work** (#380): all three crashed on load or first input (pre-0.3.0 scene API, positional constructors, string key names). They're now gated by `tests/integration/template_programs_test.py`, which runs every template it finds.
- The 19 orphan scripts in `tests/demo/screens/`: 13 moved to `tests/demo/standalone/`, where every script is a gated test, and 6 retired (#374). EngineRandom's stream decorrelation is gated by a test (#409).
