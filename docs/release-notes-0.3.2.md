# McRogueFace 0.3.2 — release notes

> Work since the `0.3.1` tag. Draft: rows are added as changes merge.

## Breaking changes and upgrade notes

| Change | What to do |
|---|---|
| **`Entity3D.animate()` names are attributes, in their units** (#449), as on every 2D type since 0.3.0 (#423). Its world position animates as `world_x`/`world_y`/`world_z`; `scale_x`/`scale_y`/`scale_z` and `sprite_index` are new readable attributes. | The old names `x`/`y`/`z` and `rot_y` raise `ValueError` naming the replacement: use `world_x`/`world_y`/`world_z`. |
