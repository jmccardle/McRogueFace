# Design note: how much should the engine listen to the user's environment? (#510)

> **Superseded by #505.** The engine no longer reads `VIRTUAL_ENV` at all (CPython doesn't): a
> venv is found from the launch path, `--use-virtual-env` and `mcrfpy.config.use_virtual_env` /
> `virtual_env_ignored` are gone, and `mcrfpy.config.virtual_env` now reports the venv the
> interpreter runs in. Current behavior: `docs/sys-path-order.md`. The text below is the
> record of the #510 policy, kept as history.

Status: proposal, needs John's decision. Context: #499 made the engine honour `$VIRTUAL_ENV`; the 0.3.4 cloud review (#510) showed the cost: an unrelated active venv of another Python makes the engine exit (test suite 0/230; a shipped game refuses to launch).

## The tension

McRogueFace plays two roles at once:

- **A transparent Python** for developers: `source .venv/bin/activate; mcrogueface script.py` should "just work", `pip install -e` should be visible, `mcrogueface -m pip` should do what `python -m pip` does.
- **An embedded host** for players: a packaged game is an application that owns its interpreter. The player's shell state is none of its business.

Blender and FreeCAD only have the second role. We have both, so the policy has to depend on *which role is running*.

## What others do

| Source | Position | What it teaches |
|---|---|---|
| **CPython / PEP 405** ([venv docs](https://docs.python.org/3/library/venv.html), [PEP 405](https://peps.python.org/pep-0405/)) | A venv is found by `pyvenv.cfg` next to the executable (or its parent), never by environment. The docs say outright: "`VIRTUAL_ENV` cannot be relied upon to determine whether a virtual environment is being used", and activation only prepends `PATH`. | `python3.15` run with a 3.11 venv active does not fail; it ignores the variable. Reading `VIRTUAL_ENV` at all is *our* extension. The standard mechanism is executable-relative. |
| **CPython embedding, PEP 587** ([PEP](https://peps.python.org/pep-0587/), [C API](https://docs.python.org/3/c-api/init_config.html)) | Two presets: *Python config* (honours environment, behaves like `python`) and *Isolated config* ("isolate Python from the system. For example, to embed Python into an application": ignores environment variables, argv, user site). A `._pth` file forces isolation. | The language itself endorses both of our roles and says the choice is per-application. We already use Isolated config (no `PYTHONPATH`); `VIRTUAL_ENV` is the one environment variable we re-admitted. |
| **Blender** ([2.82 commit](https://archive.blender.org/lists/bf-blender-cvs/2020-January/134221.html), [Deploying Blender](https://docs.blender.org/manual/en/dev/advanced/deploying_blender.html)) | Bundles its own Python and "does not interact with the system Python by default". Python environment variables were switched **off by default in 2.82** after users with a `PYTHONPATH` set for *other* projects could not start Blender (T72807); opt back in with `--python-use-system-env`. `os.environ` is untouched. | The closest precedent for exactly our bug, and the same fix we are considering: ambient variables are ignored, intent is expressed with a flag. Cost they accepted: power users must pass the flag. |
| **PyInstaller / frozen apps** ([runtime information](https://pyinstaller.org/en/stable/runtime-information.html)) | The bootloader marks the app (`sys.frozen`, `sys._MEIPASS`) and rewrites the library search path so the bundle wins; the original value is saved as `*_ORIG`. | An application bundle declares itself, and "am I packaged?" is a first-class fact the program can test. Preserve what you override. |
| **FreeCAD** ([Macro Packages](https://wiki.freecad.org/Macro_Packages), [AddonManager](https://github.com/FreeCAD/AddonManager)) | Add-on dependencies go to an app-owned `AdditionalPythonPackages` folder, in a per-Python-version subfolder; no venv. The AddonManager roadmap lists a venv-based approach as a *wish*. A user venv built on FreeCAD's Python imports fine until it touches FreeCAD's compiled modules, then fails ([forum](https://forum.ngsolve.org/t/conflicts-between-netgen-and-freecads-fem-module/2617)). | An app-owned dependency directory works and is simple, but invites people to try venvs anyway; the failure is a confusing DLL error, not a clear message. |
| **Krita / QGIS** ([Krita docs](https://docs.krita.org/en/untranslatable_pages/python_coding.html), [qgis-venv-creator](https://pypi.org/project/qgis-venv-creator)) | Developers use a *separate* venv for tooling/autocomplete; runtime packages go to an app-visible dir. QGIS on Windows ships its own Python, giving "multiple interpreters on one machine". | Dev-time convenience (an editor-visible venv) and run-time ownership are different problems; tools get built to bridge them (a venv *with the host's bindings*). |
| **Embedded-Python lore** ([cpython#78906 and friends](https://github.com/python/cpython/issues/78906)) | Embedders that rely on `sys.executable`/`site` to discover a venv get the wrong Python; the recommended answer is to set the path configuration explicitly. | Do not depend on ambient state for correctness; configure explicitly. |

Not verified in this pass: Houdini (`hython`), Maya (`mayapy`), Godot, Ren'Py. Blender's manual pages were too large to fetch whole; the Blender conclusions rest on the commit message and search summaries.

## What this says about #499

1. **Ambient `$VIRTUAL_ENV` is a weak signal.** CPython ignores it; the venv docs warn against it. Shells keep it set for hours, across unrelated projects.
2. **A *mismatched* venv cannot be the user's intent for this engine.** A 3.11 venv's packages cannot be loaded by Python 3.15. Real `python3.15` ignores it silently, and nobody calls that a bug. Erroring converts "unrelated shell state" into "engine won't start", the exact Blender T72807 failure.
3. **A *matching* but broken venv (no `pyvenv.cfg`, no `site-packages`) is a different case**: the user clearly meant this engine, so Fail Early is right.
4. **Packaged games should not read the player's environment at all.** Blender, PyInstaller and PEP 587 agree.

## Options

**A. Status quo.** Always honour, always error. Simple, loud, and breaks tests and players (#510).

**B. Blender's answer: ignore ambient `VIRTUAL_ENV`; opt in with a flag/variable.** `--use-virtual-env` (or `MCROGUEFACE_VENV=<dir>`, namespaced so it cannot be ambient by accident). `mcrf_project run` passes it. Cleanest rule, and it matches our Isolated-config stance. Cost: the "activate, then run `mcrogueface script.py`" transparency is gone until you add the flag, and #499's reported use case (pip install into a venv, run the game) needs one extra token.

**C. Honour by compatibility (recommended core).** Read `VIRTUAL_ENV`, then read its `pyvenv.cfg`:
- version (`major.minor`, plus free-threading) matches the engine's Python: honour it (today's behaviour).
- it names a different Python: it is not ours; **ignore it and say so once on stderr** (`VIRTUAL_ENV=... is for Python 3.11; this engine is 3.15; ignoring`), and record it in `mcrfpy.config` (`virtual_env`: the path honoured or `None`; `virtual_env_ignored`: the path and reason). Not silent, not fatal.
- it matches but is broken (no `pyvenv.cfg`, no `site-packages`): keep the hard error from #499.

**D. Add a package marker (recommended with C).** `mcrf_project dist` writes a marker into the package (the runtime definition in `src/pylib/mcrf_project/runtime.py` is the one place to add it; the engine already knows its own directory). When the marker is present the engine ignores `VIRTUAL_ENV` entirely and uses only the sibling `venv/`. Opt-out for modders: `--use-virtual-env`. This is the PyInstaller/Blender position for the player role, and it also closes the "a valid 3.15 venv would outrank the game's bundled `venv/`" hole.

**E. The long-term star: PEP 405, executable-relative (#505).** Make `mcrogueface` usable as a venv's own `python` (`pyvenv.cfg` + `home`, `sys.prefix` correct, `.pth` and `sysconfig` honoured). Then activation is unnecessary, `VIRTUAL_ENV` stops mattering, and "transparent Python" is true in the standard way. `mcrogueface -m venv .venv` would be the whole story. Larger, tracked separately.

## Tradeoffs in brief

| | Dev DX | Player UX | Surprise | Cost |
|---|---|---|---|---|
| A status quo | good until another venv is active, then fatal | fatal if any venv active | high | none |
| B opt-in only | one extra flag | none | low | breaks #499 convenience |
| C+D compat + package marker | unchanged for the matching case; mismatches warn instead of dying | none | lowest | ~60 lines: `pyvenv.cfg` version read, marker, config fields |
| E PEP 405 | best | none | none | #505-sized |

## Suggestion

Do **C + D now** (0.3.4 or 0.3.5), and keep **E** as the destination:

1. `virtual_env_site_packages()` (`src/McRFPy_API.cpp:~1355`): read `pyvenv.cfg` `version`; mismatch → ignore + one-line note + `mcrfpy.config` field; matching-but-broken → existing error.
2. Package marker written by `mcrf_project dist`/`package-engine`; present → no `VIRTUAL_ENV`. `--use-virtual-env` overrides.
3. `tests/run_tests.py` drops `VIRTUAL_ENV` from the child environment regardless (tests must not depend on shell state; that is independent of the policy).
4. Update `docs/sys-path-order.md` (the *VIRTUAL_ENV* section) and the 0.3.4 release notes.

Open questions for John: is a one-line stderr note enough for a mismatched venv, or should it be a `mcrfpy`-level warning object so tests can assert it? Should the opt-in spelling be a flag, a namespaced variable, or both?
