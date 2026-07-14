"""Where the showcase scripts write their generated images (#372).

These scripts used to hardcode /opt/goblincorps/repos/mcrogueface.github.io -- an
absolute path outside the repo, on one developer's machine. Anyone else running them
got PermissionError, which is part of why they rotted unnoticed.

Resolution order:
  1. $MCRF_DOCS_REPO            -- explicit checkout of mcrogueface.github.io
  2. ../mcrogueface.github.io   -- the usual side-by-side checkout
  3. tests/demo/screenshots/    -- in-repo default, always writable
"""
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(_HERE))


def docs_repo():
    """Root of the documentation site checkout, or None if there isn't one."""
    env = os.environ.get("MCRF_DOCS_REPO")
    if env and os.path.isdir(env):
        return env
    sibling = os.path.join(os.path.dirname(_REPO_ROOT), "mcrogueface.github.io")
    if os.path.isdir(sibling):
        return sibling
    return None


def image_dir(*parts):
    """Directory for generated images, created if needed.

    parts: subpath under the docs site's images/ (e.g. "cookbook", "tutorials").
    """
    repo = docs_repo()
    if repo:
        target = os.path.join(repo, "images", *parts)
    else:
        target = os.path.join(_HERE, "screenshots", *parts)
    os.makedirs(target, exist_ok=True)
    return target
