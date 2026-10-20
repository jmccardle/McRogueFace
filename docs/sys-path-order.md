# The engine's `sys.path` order (#502)

The engine builds `sys.path` itself (isolated Python config, no `PYTHONPATH`; `site` runs only to add a launch venv's site-packages).
`E` is the directory of the real binary (symlinks are resolved: `/proc/self/exe` is
canonicalised). Asserted by `tests/regression/issue_502_sys_path_order_test.py`,
`tests/regression/issue_499_virtual_env_test.py`, `tests/regression/issue_510_virtual_env_policy_test.py` and
`tests/regression/issue_452_main_script_path_test.py`.

## Linux and Windows

| # | Entry | When |
|---|-------|------|
| 0 | `$VIRTUAL_ENV/lib/python3.X/site-packages` (`$VIRTUAL_ENV/Lib/site-packages` on Windows) | only if the environment variable `VIRTUAL_ENV` names a venv for this engine's Python, and the engine is not a packaged game (#499, #510); see *VIRTUAL_ENV* below |
| 1 | `E/venv/lib/python3.X/site-packages` (`E/venv/Lib/site-packages` on Windows) | only if that directory exists; a bare `E/venv/` is ignored |
| 2 | `E/scripts` | always; see *main script* below |
| 3 | `E/lib/Python/lib.<platform>-3.X` (extension modules) | always |
| 4 | `E/lib/Python` | always |
| 5 | `E/lib/Python/Lib` (stdlib) | always |
| 6 | `<V>/lib/python3.X/site-packages` (`<V>\Lib\site-packages` on Windows) | only if the engine was launched through a PEP 405 venv `<V>` and that directory exists; added by `site.py`, after the stdlib; see *Launching through a venv* below |

(On free-threaded builds `python3.X` is `python3.Xt`.) WASM has its own fixed list: `/scripts`, then the
Python home in the virtual filesystem.

## Main script (game mode and `mcrogueface dir/script.py`)

The main script's directory is `sys.path[0]` (#452), as with `python dir/script.py`. It
**replaces** the `E/scripts` entry (the engine's own `scripts/` is not importable from a game
unless the game is that directory). Game mode runs `scripts/game.py` from the working directory,
so its directory is the main script directory. Entries 0 and 1 stay behind it.

`--exec script.py` does not run a main script: `sys.path` is unchanged (`E/scripts` stays where
it is, entries 0 and 1 ahead of it). `-m module` follows the same list.

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
`.pth` files are untouched.

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

## Launching through a venv (#505)

`mcrogueface -m venv ENV` makes `ENV/bin/{mcrogueface,python,python3,python3.X}` symlinks to
the engine and a `pyvenv.cfg`. The engine finds the venv the way CPython does: from the
**unresolved launch path**. `argv[0]` is made absolute lexically (never `realpath`; with no `/`
it is searched on `PATH`, as `execvp` did) and handed to CPython as `PyConfig.executable`;
getpath looks for `pyvenv.cfg` beside it or one directory above. The real engine binary is
`PyConfig.base_executable`. Launched as `ENV/bin/python`:

- `sys.executable` is `ENV/bin/python`, `sys.prefix` is `ENV`, `sys.base_prefix` is `E/lib/Python`,
  `sys._base_executable` is the real engine; `sysconfig` paths and pip's install scheme follow
  `sys.prefix`, so nothing is ever installed into `E`.
- `site.py` adds `ENV/lib/python3.X/site-packages` (row 6), after the stdlib, as for CPython.
  Rows 0 and 1 are untouched and still come first.
- `E` (where `lib/`, `assets/`, `scripts/` live) remains the resolved binary directory.

A binary copied into a venv's `bin/` is found the same way. Windows keeps the real binary path
(no venv support there yet).

## `python*` basename: a plain interpreter (#505)

When `argv[0]`'s basename starts with `python` (the `ENV/bin/python` link), the engine is
headless and `python script.py [args]` runs the script and **exits** with its status: a
`SystemExit` code from `sys.exit(n)`, 1 after an uncaught exception's traceback. This is what lets
pip's console-script shebangs (`#!ENV/bin/python`, which cannot carry flags) work. `--run-forever`
keeps the process in the frame loop instead. Invoked as `mcrogueface`, a script is still game mode.

`sys.path` itself shows what was picked up.

## CPython interpreter flags (#505)

`mcrogueface` accepts the core `python` flags, so tools that re-invoke `sys.executable`
(ensurepip, pip, venv) work: `-I -E -s -S -B -u -q -v -O/-OO -W arg -X opt`. They may be
clustered (`-Es`), and `-W`/`-X` take their value attached (`-Wignore`) or as the next
argument and may repeat. Each sets the `PyConfig` field of the same meaning, so it shows in
`sys.flags`, `sys.warnoptions` and `sys._xoptions`, in the `-c`/`-m`/`--exec`/script path and
in the game path alike. Anything else still fails with `Unknown option`.

The engine's baseline is an isolated config (no `PYTHON*` environment variables, no user
site), so `-I`, `-E` and `-s` only restate what is already in force: `sys.flags.isolated`
reads 1 with or without `-I`. `-S`, `-B`, `-u`, `-q`, `-v`, `-O`, `-W` and `-X` change behaviour.
