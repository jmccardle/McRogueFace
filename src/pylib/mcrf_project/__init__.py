"""McRogueFace project tool: create, run and package games, and package the engine.

Run it with the engine's own interpreter, which is the engine it works with:

    mcrogueface -m mcrf_project init my-game
    mcrogueface -m mcrf_project run          (in my-game/)
    mcrogueface -m mcrf_project dist
    mcrogueface -m mcrf_project info

`package-engine` builds the engine's own release packages (tools/package.sh). Games and the
engine are packaged by the same code (runtime.py), so a game ships exactly the runtime the
engine does.
"""
from .errors import ProjectError
from .runtime import Runtime
from .project import Project

__all__ = ["ProjectError", "Runtime", "Project"]
