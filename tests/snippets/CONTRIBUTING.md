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

Both end with the same gate (last section), which includes `tools/lint_snippet_batch.py`: a
tool that judges your whole batch from `git`, not from your report. Read "Must not" and
"Stop and report" first.

## What you may change (the lint enforces this)

| Path | Allowed |
|---|---|
| `tests/snippets/NNN_*.py` that does **not exist at BASE** | create it, **only with NNN inside the range you were assigned** |
| `tests/snippets/*.py` that **exists at BASE** | add or remove `# region: NAME` / `# endregion` comment lines (and let `stamp_snippets.py` rewrite the `# mcrf:` header). Nothing else: not code, not other comments. Numbers outside your range are fine for this and only this |
| a snippet at BASE | never delete it, never rename it |
| `docs/cookbook/**` | delete (rule below), or `git mv` a procgen demo into `tests/snippets/` (conversion). No edits |
| anything else (`tools/`, `src/`, `api/`, `_harness.py`, `_screenshot.py`, `_seed.py`, `generate_snippet_shots.py`, this file...) | no |

## Facts

* A snippet is `tests/snippets/NNN_name.py`. `NNN` is a number **you were assigned**; never
  "the next free one" (parallel agents collide). Name: `NNN_<page-stem>_<n>.py` (page
  conversion) or `NNN_procgen_<name>.py` (demo).
* The first line `# mcrf: objects=[...] verified=... status=ok` is written by
  `tools/stamp_snippets.py`. Never type it, never edit it. A new file has no header until you
  stamp it.
* A snippet must be self-contained and leave something in `scene.children` (the harness fails
  an empty scene). **Scenes:** setup *you add* uses `scene = mcrfpy.Scene("demo")` and
  `mcrfpy.current_scene = scene` (the form 250 of the corpus's snippets use;
  `scene.activate()` is used by 44). If a fence you are keeping builds and activates its own
  scene (`Scene("game")` ... `scene.activate()`), its text stays exactly as the page has it;
  you do not rewrite it to match.
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

## What the gate can and cannot see (read this)

`_harness.py` advances the simulation **one frame** and checks the scene is not empty. So:

* Code that runs when the file is executed is verified.
* **Callback bodies are not executed**: `Timer` callbacks, `on_key` / `on_click` / `on_enter`
  handlers, animation callbacks, `scene.update`, anything that runs on a later frame or an
  input event. A wrong method name or a removed API inside one passes the gate.

Therefore, **for every callback body in a snippet you create or convert, read it line by line
against `api/manifest.json`** (every `mcrfpy.X`, and every method/property you call on an
engine object: `grep -n '"name"' api/manifest.json`) and say in your report that you did, and
which callbacks. The lint's manifest check covers `mcrfpy.X` spelled out; it does not know that
`frame.nonexistent()` is wrong. If you can cheaply make a callback run (call the function
yourself once, at the end of the file, only if that is what a reader would do) you may, but a
snippet must not contain code that exists only to be tested.

## The environment you are given

The orchestrator gives you `MCRF_BUILD_DIR` (a built engine, read-only: **you do not build**),
the engine worktree you edit, the site worktree, `BASE` (the commit your work started from) and
your number range `A-B`. Run everything with a display stub:

```bash
export ALSOFT_DRIVERS=null MCRF_BUILD_DIR=<given>
W="xvfb-run -a -s -noreset"      # same as xvfb-run -a -s "-noreset"
```

The engine writes into its working directory (`save/`, `imgui.ini`). `stamp_snippets.py` and
`generate_snippet_shots.py` therefore run it in a private scratch directory per invocation
(symlinks to the build directory's contents, so `assets/` resolves as usual) and delete it at
exit; concurrent agents sharing one build directory do not touch each other or it. Screenshots
go to `snippet-shots/` in *your* worktree (gitignored). If you run the engine binary yourself
instead of through these tools, do it from a scratch directory you made, not from the build
directory.

## Recipe A: converting a page

For each `python` fence of the page, top to bottom, decide which row applies. Keep a list of
the decision for the report.

| Situation | Do | Report |
|---|---|---|
| An existing snippet of the page equals the fence | marker `<!-- snippet: NNN_name -->`, nothing else | reused |
| An existing snippet contains the fence plus extra setup (a Scene, a container the fence assumed from an earlier fence, `scene.activate()`) | same marker, whole snippet. **The snippet wins**; the page gains the setup lines | reused + the extra lines |
| An existing snippet contains the fence as a fragment and the setup is long | add `# region: x` / `# endregion` lines around the fragment in the existing snippet (marker lines only; the lint rejects any other edit), marker `region=x` | region added |
| An existing snippet and the fence disagree in code (different API use, different numbers, different behaviour) | **snippet wins**, use it | the exact diff |
| No snippet has it | write a new snippet (below), number from your range | new, with number |

Several fences may share one new snippet (a class, then a function that uses it): give each
fence its own region. A fence that only works because an earlier fence defined `grid`,
`scene`, `shaker`, `HealthBar`: copy that definition into the new snippet **above** the region
(outside it), so the page shows what it showed and the file still runs.

### Writing a new snippet

1. Start from the fence text, unchanged.
2. Put each fence's own `import` lines **inside its region** (a duplicated `import mcrfpy` in
   a file is fine); the page keeps showing them.
3. Add only what is needed to run: Scene, `current_scene`, a Grid/Frame the fence assumed,
   its content. Placeholder calls in the fence (`player_moves()`, `...`, undefined helpers):
   replace with a real statement that does the thing, and report it.
4. **Make the comments true.** If the text says five presets run, five must run (a snippet
   that calls five things back to back where only the first can act is a lie); if a comment
   says "checkerboard", the screenshot must show one. Fix the code, not the comment, when the
   behaviour is the point of the sample; report the change.
5. Allowed API renames, and nothing else. Each is listed in the report.

   | Old | New |
   |---|---|
   | `grid.add_layer("color", z_index=-1)` | `layer = mcrfpy.ColorLayer(z_index=-1, name="x")` then `grid.add_layer(layer)` (`TileLayer(...)` likewise) |
   | `mcrfpy.setTimer("n", cb, ms)` | `mcrfpy.Timer("n", cb, ms)`; callback is `(timer, runtime)`; keep the Timer in a variable if it must live |
   | `Animation(...).start(x)` | `x.animate("prop", target, duration, mcrfpy.Easing.X)` |
   | `createScene` / `setScene` / `sceneUI` / `keypressScene` | `scene = mcrfpy.Scene("n")`, `mcrfpy.current_scene = scene` (or `scene.activate()`), `scene.children`, `scene.on_key = fn` |
   | `automation.position()` polling | not an API for readers: use `on_enter` / `on_exit` / `on_move`, or report |

   Anything not in this table that the manifest rejects: stop and report.
6. The scene must show something on a screenshot (see the gate); add visible content (a
   `ColorLayer` checkerboard, `grid.at(x, y).tilesprite = N` tiles that actually differ from
   each other, a Frame, a Caption) instead of an empty Grid. A grid you shake or scroll must be
   larger than the view, or the screenshot shows the black edge of the world.

### Editing the page (site worktree)

Wrap each fence in marker lines **on lines of their own, fence directly under the marker,
closing marker directly under the fence** (no blank lines between):

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

* Never edit text inside a marked fence by hand. **Never edit `tools/ungated_fences.json`**:
  the first command lowers your page's entry.
* Do not change a fence's language to something else, delete a fence, or edit prose: the
  orchestrator runs `--check --base <rev>`, which fails the page. A fence you cannot convert
  stays as it is, unmarked (report it).
* If the snippet text contains a line of three backticks, injection refuses (it would close
  the page's fence). Use a four-backtick page fence for that one fence, or change the snippet.
* Do not commit `__pycache__/` or `.pyc` files (the site's `.gitignore` covers them; `git status`
  before you commit).

### Deleting a page's stale extractions

When every fence of the page is marked, you may `git rm` the page's stale January extractions
`docs/cookbook/<dir>/<page-stem>_*.py` **only if** every function and class name each one
*defines* (a `def` or `class` statement) is *defined* in that page's snippets. A name that is
merely called, or that appears in a comment or string, does not count. The lint enforces
this: pass `--page-snippets <page-stem>=N,N,...` listing the page's snippet numbers (existing
and yours); it names every uncovered def. If a file fails the rule, keep it and report the
names. Do not rationalise ("that loop was replaced"): the orchestrator decides.

## Recipe B: converting a `docs/cookbook/procgen/` demo

Each of these 20 scripts builds a scene, then ends with `automation.screenshot(...)`,
`print(...)` and `sys.exit(0)`. They fail today on `add_layer("color", ...)`.

1. `git mv docs/cookbook/procgen/NN_name.py tests/snippets/NNN_procgen_name.py` (your number).
   The lint detects the conversion from the rename, so every function and class of the original
   must still be defined in the new file.
2. Delete the trailing `automation.screenshot(...)`, "Screenshot saved" prints, `sys.exit`, and
   the `from mcrfpy import automation` / `import sys` lines that only served them. Keep
   `print`s that show results (a snippet may print).
3. Apply the renames in the table above, and nothing else. Keep the module docstring.
4. If the original is too broken to keep a function, stop and report; do not delete it.

## Must not

* Wrap anything in `try`/`except`, use `contextlib.suppress`, or reference `SystemExit`.
* Add `exit()`, `sys.exit()`, `mcrfpy.exit()`, `atexit`, `automation.`, `open(` or network/file
  modules; hide names (`import mcrfpy as m`, `from mcrfpy import x as y`, `getattr(mcrfpy, ...)`,
  assigning to `mcrfpy.Something`); use dead-code blocks (`if False:`); write the words
  `SNIPPET_OK` / `SHOT_OK` anywhere.
* Write stubs, `pass` bodies, or "TODO"s to make something run; delete a function or class to
  make a file pass; change numbers/behaviour to dodge an error.
* Hand-edit the `# mcrf:` header.
* Edit anything in the table above marked "no"; build the engine; use a number outside your
  range for a new file.
* Run the full-corpus check (`stamp_snippets.py --check` with no `--only`): the orchestrator
  does that once. Use `--only` with your own numbers.
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

All must pass, in this order. `NNN,NNN` are the snippets you created or whose region markers
you changed; `BASE` is your starting commit; `A-B` your range.

```bash
# 1. run each of YOUR snippets through the harness and stamp its header (never the whole corpus)
$W python3 tools/stamp_snippets.py --only NNN,NNN          # "N/N snippets ok"

# 2. the batch lint: judges everything that differs from BASE
python3 tools/lint_snippet_batch.py --base BASE --range A-B \
    [--page-snippets <page-stem>=N,N,...]                  # "0 violation(s)"; warnings must be explained

# 3. screenshot each new snippet, and LOOK at the PNG (snippet-shots/NNN_*.png, gitignored)
$W python3 tools/generate_snippet_shots.py NNN NNN         # fails on an unknown number; a blank image is a failure

# 4. page conversion only: site checkout
python3 tools/inject_snippets.py --engine <engine worktree> --check
```

Step 1 rewrites the `# mcrf:` header of the numbers you name, so name only snippets you
created or edited. `stamp_snippets.py` is what `make check-snippets` runs; use the script
directly so nothing builds. Commit message: "Addresses #541", never a closing keyword.

## Report format

Per fence: `reused 147` / `reused 191 (+scene, +activate)` / `region added to 160` /
`new 283 region=manager`, then every place page and snippet disagreed and what a reader sees
differently, the callbacks you read against the manifest, the screenshots you looked at, any
lint warning and why it is fine, and anything you stopped on.
