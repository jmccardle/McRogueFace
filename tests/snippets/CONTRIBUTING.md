# Adding or converting a docs snippet (#541)

Everything in this directory is published code. A snippet is a *display script*: it builds a
scene and stops, with no `sys.exit()`, so a reader can paste it into their own game
(`_harness.py` supplies the ending). The cookbook pages on the docs site do not keep their
own copy of that code: a page fence is **injected** from the snippet
(`tools/inject_snippets.py` in the site repo), so there is exactly one text, and it runs.

This file is the recipe for the two kinds of work:

* **Page conversion**: every python fence of a site page `cookbook/<page>.md` becomes backed by
  a snippet.
* **Demo conversion**: a script from `docs/cookbook/procgen/` becomes a snippet.

Both end with the same gate (last section). Read "Must not" and "Stop and report" first.

## Facts

* A snippet is `tests/snippets/NNN_name.py`. `NNN` is a number **you were assigned**; use
  only numbers from your range, never "the next free one" (parallel agents collide).
  Name: `NNN_<page-stem>_<n>.py` (page conversion) or `NNN_procgen_<name>.py` (demo).
* The first line `# mcrf: objects=[...] verified=... status=ok` is written by
  `tools/stamp_snippets.py`. Never type it, never edit it. A new file has no header until
  you stamp it.
* A snippet must be self-contained: its own `import mcrfpy`, its own
  `scene = mcrfpy.Scene("demo")`, `mcrfpy.current_scene = scene`, and it must leave
  something in `scene.children` (the harness fails an empty scene).
* Every `mcrfpy.X` must exist in `api/manifest.json` (`objects`, `functions`,
  `module_attributes`). `grep -n '"X"' api/manifest.json` before you assume a name.
* Regions: a snippet may mark the part a page should show:

  ```python
  # region: manager
  class Thing: ...
  # endregion
  ```

  Names are `[A-Za-z][A-Za-z0-9_-]*`; regions never nest; a name is used once per file;
  the markers are exact (`# region: NAME`, `# endregion`). The injector removes marker lines
  and dedents the region. Regions may sit side by side.

## The environment you are given

The orchestrator gives you `MCRF_BUILD_DIR` (a built engine, read-only: **you do not build**),
the engine worktree you edit, the site worktree, and `BASE`, the commit your work started
from. Run everything with a display stub:

```bash
export ALSOFT_DRIVERS=null MCRF_BUILD_DIR=<given>
W="xvfb-run -a -s -noreset"      # same as xvfb-run -a -s "-noreset"
```

## Recipe A: converting a page

For each `python` fence of the page, top to bottom, decide which row applies. Keep a list of
the decision for the report.

| Situation | Do | Report |
|---|---|---|
| An existing snippet of the page equals the fence | marker `<!-- snippet: NNN_name -->`, nothing else | reused |
| An existing snippet contains the fence plus extra setup (a Scene, a container the fence assumed from an earlier fence, `scene.activate()`) | same marker, whole snippet. **The snippet wins**; the page gains the setup lines | reused + the extra lines |
| An existing snippet contains the fence as a fragment and the setup is long | add `# region: x` / `# endregion` comments around the fragment in the existing snippet (comments only, no code change), marker `region=x` | region added |
| An existing snippet and the fence disagree in code (different API use, different numbers, different behaviour) | **snippet wins**, use it | the exact diff |
| No snippet has it | write a new snippet (below) | new, with number |

Several fences may share one new snippet (a class, then a function that uses it): put the
class outside regions or in the first region, give each fence its own region. A fence that
only works because an earlier fence defined `grid`, `scene`, `shaker`, `HealthBar`: copy that
definition into the new snippet **above** the region (outside it), so the page shows what it
showed and the file still runs.

### Writing a new snippet

1. Start from the fence text, unchanged.
2. Put each fence's own `import` lines **inside its region** (a duplicated `import mcrfpy` in
   a file is fine); the page keeps showing them.
3. Add only what is needed to run: Scene, `current_scene`, a Grid/Frame the fence assumed,
   its content. Placeholder calls in the fence (`player_moves()`, `...`, undefined helpers):
   replace with a real statement that does the thing, and report it.
4. Allowed API renames, and nothing else. Each is listed in the report.

   | Old | New |
   |---|---|
   | `grid.add_layer("color", z_index=-1)` | `layer = mcrfpy.ColorLayer(z_index=-1, name="x")` then `grid.add_layer(layer)` (`TileLayer(...)` likewise) |
   | `mcrfpy.setTimer("n", cb, ms)` | `mcrfpy.Timer("n", cb, ms)`; callback is `(timer, runtime)`; keep the Timer in a variable if it must live |
   | `Animation(...).start(x)` | `x.animate("prop", target, duration, mcrfpy.Easing.X)` |
   | `createScene` / `setScene` / `sceneUI` / `keypressScene` | `scene = mcrfpy.Scene("n")`, `mcrfpy.current_scene = scene` (or `scene.activate()`), `scene.children`, `scene.on_key = fn` |
   | `automation.position()` polling | not an API for readers: use `on_enter` / `on_exit` / `on_move`, or report |

   Anything not in this table that the manifest rejects: stop and report.
5. The scene must show something on a screenshot (see the gate); add visible content (tiles
   from `grid.at(x, y).tilesprite = N`, a Frame, a Caption) instead of an empty Grid.

### Editing the page (site worktree)

Wrap each fence in marker lines **on lines of their own, fence directly under the marker, closing
marker directly under the fence** (no blank lines between):

````markdown
<!-- snippet: 283_effects_screen_shake_manager region=manager -->
```python
anything: this body is overwritten
```
<!-- /snippet -->
````

Then run, from the site checkout, with your page as the only argument:

```bash
python3 tools/inject_snippets.py --engine <engine worktree> cookbook/<page>.md   # writes bodies, lowers the page's ratchet
python3 tools/inject_snippets.py --engine <engine worktree> --check              # must say "ok"
```

Never edit text inside a marked fence by hand, and never edit `tools/ungated_fences.json`:
the first command lowers your page's entry. A fence you cannot convert stays unmarked and
the page's ratchet entry stays above 0 (report it; do not delete the fence).

When every fence of the page is marked, remove the page's stale January extractions
`docs/cookbook/<dir>/<page-stem>_*.py` (`git rm`) **only if** each of their `def`/`class` names
appears in the page's snippets (`grep -w NAME tests/snippets/*`). Otherwise keep the file and
report which names are missing.

## Recipe B: converting a `docs/cookbook/procgen/` demo

Each of these 20 scripts builds a scene, then ends with `automation.screenshot(...)`,
`print(...)` and `sys.exit(0)`. They fail today on `add_layer("color", ...)`.

1. `git mv docs/cookbook/procgen/NN_name.py tests/snippets/NNN_procgen_name.py` (your number).
2. Delete the trailing `automation.screenshot(...)`, "Screenshot saved" prints, `sys.exit`, and
   the `from mcrfpy import automation` / `import sys` lines that only served them. Keep
   `print`s that show results (a snippet may print).
3. Apply the renames in the table above, and nothing else. Keep the module docstring.
4. Every function and class of the original must still exist. If the original is too broken to
   keep a function, stop and report; do not delete it.
5. Gate (below) with `--pair docs/cookbook/procgen/NN_name.py:tests/snippets/NNN_procgen_name.py`.

## Must not

* Wrap anything in `try`/`except` (a snippet fails loudly or it is not done).
* Add `exit()`, `sys.exit()`, `mcrfpy.exit()`, or any `automation.` use.
* Write stubs, `pass` bodies, or "TODO"s to make something run; delete a function or class to
  make a file pass; change numbers/behaviour to dodge an error.
* Hand-edit the `# mcrf:` header.
* Edit `_harness.py`, `_screenshot.py`, `_seed.py`, `tools/`, `src/`, `api/`, or the
  `OVERRIDES` table in `tools/generate_snippet_shots.py`; build the engine; touch a snippet
  number outside your range; edit an existing snippet's code (comments for regions only).
* Skip a step of the gate, or report a file as done when the gate did not say so.

## Stop and report (do not work around)

* The snippet fails and the cause is not one of the allowed renames (an engine bug, a removed
  feature, a changed signature): paste the traceback's last lines.
* A fence uses a name the manifest does not have and the table has no rename for it.
* Making a fence run would change what it demonstrates (not just its setup).
* The screenshot is blank or wrong after you added visible content, or the effect only shows
  with timing the capture cannot reach (the orchestrator edits `OVERRIDES`).
* `lint_snippet_batch.py` reports something you cannot fix without a "Must not".
* A page claims behaviour the snippet visibly does not have (the page text is wrong): report
  the sentence, do not rewrite prose.
* You ran out of numbers in your range.

## The gate

All must pass, in this order, with the exact output noted. `NNN,NNN` are the snippets you
created or changed; `BASE` is your starting commit.

```bash
# 1. run each snippet through the harness and stamp its header
$W python3 tools/stamp_snippets.py --only NNN,NNN          # "N/N snippets ok"

# 2. the batch lint: no try/except/exit/automation, manifest names, defs survive
python3 tools/lint_snippet_batch.py --base BASE [--pair OLD:NEW ...]   # "0 with violations"

# 3. screenshot each new snippet, and LOOK at the PNG (snippet-shots/NNN_*.png, gitignored)
$W python3 tools/generate_snippet_shots.py NNN NNN         # "0 failed"; a blank image is a failure

# 4. page conversion only: site checkout
python3 tools/inject_snippets.py --engine <engine worktree> --check

# 5. before you finish, the whole corpus (about 75 s)
$W python3 tools/stamp_snippets.py --check                  # "N/N snippets ok"
```

`stamp_snippets.py --check` is what `make check-snippets` runs; use the script directly so
nothing builds. Commit message: "Addresses #541", never a closing keyword.

## Report format

Per fence: `reused 147` / `reused 191 (+scene, +activate)` / `region added to 160` /
`new 283 region=manager`, then every place page and snippet disagreed and what a reader sees
differently, the snippets' screenshots you looked at, and anything you stopped on.
