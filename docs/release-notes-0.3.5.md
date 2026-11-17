# McRogueFace 0.3.5 — release notes

> Changes since the `0.3.4` tag.

## Breaking changes and upgrade notes

| Change | What to do |
|---|---|
| **The Linux package needs Debian 13 / Ubuntu 24.04 or newer** (glibc 2.38+). The 0.3.4 package was built against glibc 2.35 but only started where the host had `libFLAC.so.8`. | On an older distribution, build from source (`BUILD_FROM_SOURCE.md`). The host packages the binary needs are listed in `README.md`. |
| **The engine no longer reads `VIRTUAL_ENV`** (#505). A virtual environment is found the way CPython finds one: from the path the engine was launched by (`.venv/bin/mcrogueface`, a symlink) and its `pyvenv.cfg`. `--use-virtual-env` is now an unknown-option error, and `mcrfpy.config.use_virtual_env` / `virtual_env_ignored` are removed. `mcrfpy.config.virtual_env` is the venv the interpreter is running in, or `None`. | Launch through the venv's `bin/mcrogueface`. `mcrf_project run` does so when the project has requirements. |
| **`mcrf_project deps` makes a real PEP 405 venv** in the project's `.venv` (#517), with `bin/mcrogueface`, `bin/python` and working console scripts. | Re-run `mcrf_project deps` once per project; it replaces the `.venv` it made before. It refuses only a `.venv` it did not create; move that aside first. Linux engines only: `deps` refuses a Windows engine. |
| **`src/scripts/mcrf_venv.py` is removed.** It was the pre-venv `pip --target` helper (#137). | Use `mcrf_project deps`, or `mcrogueface -m venv` and `pip`. |
| **`Texture.from_bytes`, `composite` and `hsl_shift` raise `ValueError`** instead of returning an unusable Texture (#514): sprite size below 1x1 or larger than the image, or an image over the GPU's maximum texture size. | Catch `ValueError` where you relied on an empty result. |
| **`Grid.apply_threshold` / `apply_ranges` validate ranges** (#523): `min > max` raises `ValueError`, as does a range that is not exactly two values. | Fix the call; the message names the bad argument. |
| **`DiscreteMap.add` / `subtract` check their operand** (#520): anything but an int or a DiscreteMap raises `TypeError`; huge ints saturate instead of wrapping. | Pass an int or a DiscreteMap. |

## Python environments (#505, #517)

- **The engine is a venv's Python.** `mcrogueface -m venv DIR` (or `mcrf_project deps`) makes an environment whose `bin/python` is the engine; `pip install`, console scripts and `python -m` work from it. A venv is isolated from the engine's bundled sibling `venv/` unless its `pyvenv.cfg` says `include-system-site-packages = true`.
- **`python*` basename mode.** Launched under a name starting with `python` (as a venv's `bin/python` is), the engine is a plain interpreter: headless, runs the script or module, exits (`--run-forever` keeps it alive). Under its own name it stays a game engine.
- **CPython interpreter flags** are accepted and mapped onto `PyConfig`: `-I -E -s -S -B -u -W -X -q -v -O -i`, clustered or not (an unknown flag is an error), so tools that re-launch `sys.executable` with flags (pip, venv, ensurepip) work.
- An `argv[0]` that names no file means the real binary, not a refusal to start.
- The order of `sys.path` is in `docs/sys-path-order.md`; the recipe is `docs/python-environments.md`. `-m venv` is not supported on Windows.

## Grid and procgen fixes

- **The default camera follows `zoom` and widget size** (#530, #532). A Grid whose camera was never set keeps cell (0,0) at its top-left when `zoom` is assigned after construction and when the widget is resized (`size`, `w`/`h`, `animate`, `resize()`). Explicit cameras keep their centre.
- **`TileLayer` accepts every int tile index** (#524) through `set`, `fill`, `fill_rect`, `layer[x, y] =`, `apply_threshold` and `apply_ranges`. Negative or too-large indices are not drawn; writing an index above the texture's last sprite warns once per call with `mcrfpy.TextureWarning`. A non-int raises `TypeError`, an int beyond a C int `OverflowError`.
- `HeightMap` / `DiscreteMap` operations read an aliased operand as it was before the operation (`a.add(a)`), and negative `DiscreteMap` scalars work.
- `Grid.apply_threshold` / `apply_ranges` accept a list as well as a tuple for a range (#523). A `ColorLayer.apply_ranges` gradient pair may be `Color` objects or colour names (#522).

## Packaging

- **The Linux package starts on a clean system** (#525). It bundles the FLAC library SFML's audio module was built against, the SFML libraries find each other and it by `$ORIGIN` (no build-host paths), and `./mcrogueface` works without `run.sh`. The release pipeline now runs the unpacked package in clean Debian 13 and Ubuntu 24.04 containers.
- **The Windows package no longer ships `python3NN.zip`** (26.5 MB to 21.8 MB, no behaviour change), and the packaged networking stdlib is tested under Wine when a Windows build is present.
- `assets/tinydungeon.tsx` loads (#527): it pointed at an image on the author's machine, and was missing from a clean checkout.
- The web build compiles again (#531); it was broken on `master` by the venv work, never in a release. `tools/release.sh` now builds it right after the desktop build.

## Docs and tooling

- `TileLayer` / `ColorLayer` class docstrings show the real call shapes: `set(pos, value)`, `fill_rect((x, y), (w, h), value)`, constructor order `name, z_index, ...` (#528). The examples in them are now executed by a test.
- `mcrf_project init` prints the new project's absolute path (#518).

## Known gaps

- `fill_rect` on layers takes only real tuples for `pos` and `size`, not a `Vector` or list (#533).
- A `ColorLayer` over a non-opaque background applies alpha twice; `Billboard.sprite_index` has no visible effect; headless `--screenshot` does not exit by itself; a failed `--exec` script can exit 0 in windowed mode. All are older than 0.3.4 and planned for 0.3.6.
- Web key input is tested in headless Chromium only; IME / dead-key text, Firefox and non-US layouts are still manual (`docs/web-key-test-sheet.md`).
- Two frame-lock timing tests fail on an overloaded machine (#535).
