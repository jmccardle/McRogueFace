# Python environments: venv, pip, console scripts (#505, #517)

The engine is a CPython 3.15 interpreter that can also run a game. It finds a venv the way
CPython does, so the usual recipe works. (Linux; see the end for Windows and web.)

## Project setup

```bash
mcrogueface -m venv .venv                      # a real PEP 405 venv; bin/ holds links to the engine
.venv/bin/python -m pip install some-package   # or: pip install -r requirements.txt
.venv/bin/mcrogueface game.py                  # run the game with those packages
```

Or activate it, as with any venv; activation only puts `.venv/bin` on `PATH`:

```bash
source .venv/bin/activate
mcrogueface game.py        # game mode
python tool.py             # plain interpreter (below)
some-console-script        # anything pip installed into .venv/bin
```

The engine does not read `VIRTUAL_ENV` (CPython does not either). What counts is the path it was
launched by: a `pyvenv.cfg` beside, or one directory above, that unresolved path (`.venv/bin/mcrogueface`;
a bare `mcrogueface` is looked up on `PATH`, which is why activation works). Running the real
binary with a venv merely "active" in the environment, or through a link outside the venv, does not use it.
Nothing is ever installed into the engine's own directory.

By default a venv is isolated, as in CPython: the engine's sibling `venv/` (the packaged-game
rule in [sys-path-order.md](sys-path-order.md)) is not on `sys.path` unless the venv's
`pyvenv.cfg` says `include-system-site-packages = true`.

## `python` versus `mcrogueface`

The same binary behaves by the name it is launched under:

| Launched as | `name script.py` | Typical use |
|---|---|---|
| `mcrogueface` | game mode: opens a window, runs until closed (`--headless` for no window) | running a game |
| `python`, `python3`, `python3.15` (what `.venv/bin/` contains) | plain interpreter: runs the script headless and **exits** | tools, pip, console scripts |

`python --run-forever script.py` keeps a headless run alive; `mcrogueface --headless script.py`
is a headless game (it runs until the script calls `sys.exit()`). `-c` and `-m` are always
headless run-and-exit. This is why pip console scripts work: their shebang is
`#!/path/.venv/bin/python`, which cannot carry flags.

## The managed route: `mcrf_project`

```bash
mcrogueface -m mcrf_project deps    # makes <project>/.venv with the engine and pip-installs
                                    # mcrf.toml's requirements / requirements-file into it
mcrogueface -m mcrf_project run     # launches the game through .venv/bin/mcrogueface
mcrogueface -m mcrf_project dist    # packages the game
```

`deps` is the recipe above done for you (it replaces `.venv` if it is empty or its own, and refuses
other directories). Console scripts in `.venv/bin` work. `dist` ships the venv's
`site-packages` as the package's `venv/lib/python3.X/site-packages`, never its `bin/`.

## Packaged games

A package from `dist` has its own sibling `venv/` next to the binary and ignores the player's shell:
no `VIRTUAL_ENV`, no active venv, no `pip`. Players just run the game.

## Windows

Documented, not polished. `mcrf_project deps` refuses a Windows engine, and the engine ships no
launcher that `venv` could use on Windows (no `python.exe` redirection). Unsupported for now. A
packaged Windows game's sibling `venv\Lib\site-packages` rule is unchanged.

## Web

Not applicable: packages are preloaded into the virtual filesystem at build time
([web-parity-matrix.md](web-parity-matrix.md)).

Gate: `tests/integration/venv_pip_end_to_end_test.py` (venv, wheel install, console script, game run).
