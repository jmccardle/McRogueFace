# McRogueFace 0.3.3 — release notes

> Changes since the `0.3.2` tag.

## Breaking changes and upgrade notes

| Change | What to do |
|---|---|
| **A Caption's `pos` is the top of its line** (#478). The first baseline sits at `pos.y` + the font's ascent (`TextBaseline.TOP`, the new default), so a Caption placed at a grid cell's top-left draws exactly over that cell's tile glyph, and text sits inside a background of its line height. It used to sit at `pos.y + font_size` (SFML's rule), which put text `font_size − ascent` px lower: 4 px for a 16 px VGA font, 1 px for the default font at size 48, 0 for the default font up to size 33. The new `Caption.baseline` / `Caption(baseline=...)` chooses the anchor per caption: `TOP`, `BASELINE` (`pos.y` is the baseline, so mixed fonts and sizes line up), or `EM_TOP` (the old placement, pixel for pixel). `bounds`, `w`, `h` and `advance` follow the drawn text. | For the old placement everywhere, add `mcrfpy.default_text_baseline = mcrfpy.TextBaseline.EM_TOP` at startup, before creating captions. A caption copies the default when it is made, so set it first; per caption, pass `baseline=mcrfpy.TextBaseline.EM_TOP`. |
| **`Font(path)` raises `IOError` when the file can't be loaded** (#478). It used to return a Font that drew nothing. | Check the path; catch `IOError` if a missing font is expected. |
