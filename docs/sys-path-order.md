# The engine's `sys.path` order (#502)

The engine builds `sys.path` itself (isolated Python config, no `site`, no `PYTHONPATH`).
`E` is the directory of the real binary (symlinks are resolved: `/proc/self/exe` is
canonicalised). Asserted by `tests/regression/issue_502_sys_path_order_test.py`,
`tests/regression/issue_499_virtual_env_test.py`, `tests/regression/issue_510_virtual_env_policy_test.py` and
`tests/regression/issue_452_main_script_path_test.py`.

## Linux and Windows

| # | Entry | When |
|---|-------|------|
| 0 | `$VIRTUAL_ENV/lib/python3.X/site-packages` (`$VIRTUAL_ENV/Lib/site-packages` on Windows) | only if the environment variable `VIRTUAL_ENV` names a venv for this engine's Python, and the engine is not a packaged game (#499, #510); see *VIRTUAL_ENV* below |
| 1 | `E/venv/lib/python3.X/site-packages` (`E/venv/Lib/site-packages` on Windows) | only if that directory exists; a bare `E/venv/` is ignored |
| 2 | `<V>/lib/python3.X/site-packages` | only if `E/..` holds a `pyvenv.cfg` (the real binary sits in a venv's `bin/`); listed even if the directory does not exist; skipped when it is the same directory as row 0 |
| 3 | `E/scripts` | always; see *main script* below |
| 4 | `E/lib/Python/lib.<platform>-3.X` (extension modules) | always |
| 5 | `E/lib/Python` | always |
| 6 | `E/lib/Python/Lib` (stdlib) | always |

(On free-threaded builds `python3.X` is `python3.Xt`.) WASM has its own fixed list: `/scripts`, then the
Python home in the virtual filesystem.

## Main script (game mode and `mcrogueface dir/script.py`)

The main script's directory is `sys.path[0]` (#452), as with `python dir/script.py`. It
**replaces** the `E/scripts` entry (the engine's own `scripts/` is not importable from a game
unless the game is that directory). Game mode runs `scripts/game.py` from the working directory,
so its directory is the main script directory. Entries 0, 1 and 2 stay behind it.

`--exec script.py` does not run a main script: `sys.path` is unchanged (`E/scripts` stays where
it is, entries 0, 1 and 2 ahead of it). `-m module` follows the same list.

## The sibling `venv/` rule

`E/venv/...` is for self-contained deployments: a venv created next to the packaged binary. It
is honoured silently and wins over everything but the main script directory, **including when
`E` is the engine's own `build/`**. A venv created there for other purposes (for example a
terminal host's dependencies) therefore changes `sys.path` for every test and script run from
that build. Do not put project dependencies in the engine directory; the engine tree is
read-only to projects. Tests must not depend on the contents of the engine directory: they run
a private engine layout (a copied binary with symlinks to `lib/`, `assets/`, `scripts/`).

## `VIRTUAL_ENV` (#499, #510)

An activated virtualenv for this engine's Python is honoured: row 0, behind only the main
script directory and ahead of the sibling `venv/`. It is the **only** project-level lookup;
the engine never searches for directories named `.venv` or `venv` (callers name the
environment: `mcrf_project run` sets `VIRTUAL_ENV` to the `.venv` that `mcrf_project deps`
created, which carries a `pyvenv.cfg`). Only `sys.path` changes: `sys.prefix`, `sysconfig`,
`.pth` files and command-line flags are untouched (#505).

`VIRTUAL_ENV` is ambient shell state, often left over from another project, so what the
engine does depends on whether the venv can be meant for it (#510):

| `VIRTUAL_ENV` names | Result |
|---|---|
| nothing (unset or empty) | nothing changes |
| a venv for **another Python**: `pyvenv.cfg` says so (`version = 3.11.4` from `venv`, `version_info = 3.11.4.final.0` from virtualenv/uv), or, with no version line, its only site-packages is under another `lib/pythonX.Y`; also the same version's other build (`python3.X` vs free-threaded `python3.Xt`) | **ignored**: its packages could not load here. One line on stderr (`mcrogueface: ignoring VIRTUAL_ENV=...: it is for Python 3.11; this engine is 3.15`), and `mcrfpy.config.virtual_env_ignored` is `(path, reason)` |
| a venv for **this Python** with its site-packages | **honoured**: row 0; `mcrfpy.config.virtual_env` is its path |
| a directory with no `pyvenv.cfg`, or a venv for this Python with no site-packages | **fatal**: the engine prints one line naming the path to stderr and exits with status 1. It was meant for this engine and is broken; it does not fall back or skip the entry |

An empty `VIRTUAL_ENV` counts as unset. WASM has a fixed list and ignores the variable.

### Packaged games

A game package made by `mcrf_project dist` has `mcrf-game.json` beside the binary
(`runtime.GAME_MARKER`). A packaged game owns its interpreter: it ignores `VIRTUAL_ENV`
entirely, and silently (a player has nothing to fix), so its own
`venv/` (row 1) is what it imports, even when a valid venv for the same Python is active.
`mcrfpy.config.virtual_env_ignored` still records it. A modder who wants a venv in front of
the game's own packages passes `--use-virtual-env`; the rules above then apply as for a
development engine. Engine release packages (`package-engine`) are not game packages and
carry no marker: they are a developer's engine, and `mcrf_project run` relies on
`VIRTUAL_ENV` there.

The test runner (`tests/run_tests.py`) removes `VIRTUAL_ENV` from the environment of every
test, so an activated venv in the shell can't change a result; tests about it set it
themselves.

## Known gap: row 2 through a symlink (#505)

Row 2 looks at the directory above `E`, and `E` is the symlink-resolved binary directory. A
`venv/bin/mcrogueface` that is a symlink to an engine elsewhere therefore resolves to that
engine's directory and row 2 does **not** fire; it fires only when the real binary (or a copy)
sits in a venv's `bin/`. Use `VIRTUAL_ENV` (activate the venv) instead. Tracked in #505.

`sys.path` itself shows what was picked up.
