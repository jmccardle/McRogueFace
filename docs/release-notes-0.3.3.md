# McRogueFace 0.3.3 — release notes

> Changes since the `0.3.2` tag.

## Breaking changes and upgrade notes

| Change | What to do |
|---|---|
| **A Caption's `pos` is the top of its line** (#478). The first baseline sits at `pos.y` + the font's ascent (`TextBaseline.TOP`, the new default), so a Caption placed at a grid cell's top-left draws exactly over that cell's tile glyph, and text sits inside a background of its line height. It used to sit at `pos.y + font_size` (SFML's rule), which put text `font_size − ascent` px lower: 4 px for a 16 px VGA font, 1 px for the default font at size 48, 0 for the default font up to size 33. The new `Caption.baseline` / `Caption(baseline=...)` chooses the anchor per caption: `TOP`, `BASELINE` (`pos.y` is the baseline, so mixed fonts and sizes line up), or `EM_TOP` (the old placement, pixel for pixel). `bounds`, `w`, `h` and `advance` follow the drawn text. | For the old placement everywhere, add `mcrfpy.default_text_baseline = mcrfpy.TextBaseline.EM_TOP` at startup, before creating captions. A caption copies the default when it is made, so set it first; per caption, pass `baseline=mcrfpy.TextBaseline.EM_TOP`. |
| **`Font(path)` raises `IOError` when the file can't be loaded** (#478). It used to return a Font that drew nothing. | Check the path; catch `IOError` if a missing font is expected. |

## Fixes and additions

- **`Caption.advance` no longer includes the caption's position** (#479). 0.3.2 added `pos.x` to the advance (found by mcrf-term); it is now the pure pen advance, unchanged by `pos`.
- **Font metrics from Python** (#478): `Caption.ascent`, `Caption.descent` (positive, below the baseline) and `Caption.line_height` (the baseline-to-baseline distance multi-line text uses) at the caption's font and size; `Caption.baseline_y`, the y of the first baseline in parent coordinates for the caption's mode; and `Font.metrics(size)` → `(ascent, descent, line_height)` for layout without a Caption. They read the same FreeType metrics the layout uses, on desktop and web. `tests/demo/standalone/baseline_ruled_lines_demo.py` places text on ruled lines from these alone (`MCRF_DEMO_FONTS=path[@size]:...` to try any font).
