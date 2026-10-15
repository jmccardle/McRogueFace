# The engine's `sys.path` order (#502)

The engine builds `sys.path` itself (isolated Python config, no `site`, no `PYTHONPATH`).
`E` is the directory of the real binary (symlinks are resolved: `/proc/self/exe` is
canonicalised). Asserted by `tests/regression/issue_502_sys_path_order_test.py`,
`tests/regression/issue_499_virtual_env_test.py` and
`tests/regression/issue_452_main_script_path_test.py`.

## Linux and Windows

| # | Entry | When |
|---|-------|------|
| 0 | `$VIRTUAL_ENV/lib/python3.X/site-packages` (`$VIRTUAL_ENV/Lib/site-packages` on Windows) | only if the environment variable `VIRTUAL_ENV` is set and non-empty (#499); see *VIRTUAL_ENV* below |
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

## `VIRTUAL_ENV` (#499)

An activated virtualenv is honoured: row 0, behind only the main script directory and ahead
of the sibling `venv/`. It is the **only** project-level lookup; the engine never searches for
directories named `.venv` or `venv` (callers name the environment: `mcrf_project run` sets
`VIRTUAL_ENV` to the `.venv` that `mcrf_project deps` created, which carries a `pyvenv.cfg`).
Only `sys.path` changes: `sys.prefix`, `sysconfig`, `.pth` files and command-line flags are
untouched (#505).

It fails early. If `VIRTUAL_ENV` is set but the directory has no `pyvenv.cfg`, or has no
`site-packages` for this engine's Python (`python3.X`, `python3.Xt` when free-threaded), the
engine prints a one-line error naming the path to stderr and exits with status 1. It does not
fall back or skip the entry. An empty `VIRTUAL_ENV` counts as unset. WASM has a fixed list and
ignores the variable.

## Known gap: row 2 through a symlink (#505)

Row 2 looks at the directory above `E`, and `E` is the symlink-resolved binary directory. A
`venv/bin/mcrogueface` that is a symlink to an engine elsewhere therefore resolves to that
engine's directory and row 2 does **not** fire; it fires only when the real binary (or a copy)
sits in a venv's `bin/`. Use `VIRTUAL_ENV` (activate the venv) instead. Tracked in #505.

`sys.path` itself shows what was picked up.
