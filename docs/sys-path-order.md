# The engine's `sys.path` order (#502)

The engine builds `sys.path` itself (isolated Python config, no `PYTHONPATH`; `site` runs only to add a launch venv's site-packages).
`E` is the directory of the real binary (symlinks are resolved: `/proc/self/exe` is
canonicalised). Asserted by `tests/regression/issue_502_sys_path_order_test.py`,
`tests/regression/issue_505_virtual_env_ignored_test.py` and
`tests/regression/issue_452_main_script_path_test.py`.

For setting up a project venv and running games and tools through it, see [python-environments.md](python-environments.md).

(Rows are numbered from 1; there is no row 0. Row 0 was `$VIRTUAL_ENV`'s site-packages, removed in #505.)

## Linux and Windows

| # | Entry | When |
|---|-------|------|
| 1 | `E/venv/lib/python3.X/site-packages` (`E/venv/Lib/site-packages` on Windows) | only if that directory exists (a bare `E/venv/` is ignored), and the engine is not running in a PEP 405 venv whose `pyvenv.cfg` lacks `include-system-site-packages = true`; see *The sibling `venv/` rule* |
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
so its directory is the main script directory. Entry 1 stays behind it.

`--exec script.py` does not run a main script: `sys.path` is unchanged (`E/scripts` stays where
it is, entry 1 ahead of it). `-m module` follows the same list.

## The sibling `venv/` rule

`E/venv/...` is for self-contained deployments: a venv created next to the packaged binary. It
is honoured silently and wins over everything but the main script directory, **including when
`E` is the engine's own `build/`**. A venv created there for other purposes (for example a
terminal host's dependencies) therefore changes `sys.path` for every test and script run from
that build. 
**A venv isolates from it (#505).** `E/venv/` is the engine's equivalent of the base
interpreter's site-packages. A PEP 405 venv made from the engine (`ENV/bin/python`) has
`include-system-site-packages = false` by default, and then, as for CPython, does not see it:
row 1 is absent, and pip in the new venv sees only what the venv holds. With
`include-system-site-packages = true` row 1 is present as for a direct launch. Whether the
engine runs in a venv is CPython's verdict (getpath found a `pyvenv.cfg` from the launch path:
`sys.prefix` differs from `sys.base_prefix`); the engine then reads that one `pyvenv.cfg` for
the key. getpath only runs inside interpreter start-up, so the engine adds the row to the
configuration and removes it from `sys.path` right after start-up when the venv excludes it.

Do not put project dependencies in the engine directory; the engine tree is
read-only to projects. Tests must not depend on the contents of the engine directory: they run
a private engine layout (a copied binary with symlinks to `lib/`, `assets/`, `scripts/`).

## `VIRTUAL_ENV` is not read (#505)

The engine never looks at the `VIRTUAL_ENV` environment variable, as CPython doesn't: an
activated shell, a variable naming a valid venv, a broken directory or another Python's venv
all change nothing (same `sys.path`, same `sys.prefix`, no message, exit status 0). A venv is
found from the **launch path** (below); the way to use one is to run its own `bin/python` or
`bin/mcrogueface`, which `mcrf_project run` does with the project's `.venv`. This replaces the
#499/#510 policy (honour, ignore-with-a-note, hard error, `--use-virtual-env`); see the note
at the top of `design-virtualenv-policy.md`.

`mcrfpy.config.virtual_env` is the venv the interpreter runs in (`sys.prefix` when it differs
from `sys.base_prefix`), or `None`. It is read from what CPython computed, not from the
environment. `--use-virtual-env`, `mcrfpy.config.use_virtual_env` and
`mcrfpy.config.virtual_env_ignored` no longer exist.

A packaged game still has `mcrf-game.json` beside the binary (`runtime.GAME_MARKER`), for tools;
the engine does not read it.

The test runner (`tests/run_tests.py`) still removes `VIRTUAL_ENV` from the environment of every
test, so an activated venv in the shell can't leak into child Pythons that do read it.

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
  Row 1 is untouched and still comes first (but see the isolation rule above).
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
