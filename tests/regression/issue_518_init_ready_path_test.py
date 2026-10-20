"""#518: `mcrf_project init <dir>` printed "ready: cd <path>" relative to the engine
directory (the engine's cwd), not where the user ran it, so pasting it failed. The
printed path must name the project from any cwd: it is absolute."""
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ENGINE = Path(sys.executable).resolve()
ENV = {k: v for k, v in os.environ.items() if k not in ("DISPLAY", "WAYLAND_DISPLAY", "MCROGUEFACE")}
ENV["XDG_DATA_HOME"] = tempfile.mkdtemp()
ENV["ALSOFT_DRIVERS"] = "null"

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp).resolve()
    (tmp / "work" / "deep").mkdir(parents=True)
    out = subprocess.run([str(ENGINE), "-m", "mcrf_project", "init", "../elsewhere/my-game"],
                         cwd=str(tmp / "work" / "deep"), capture_output=True, text=True,
                         timeout=300, env=ENV)
    text = out.stdout + out.stderr
    assert out.returncode == 0, text
    m = re.search(r"ready: cd (\S+),", text)
    assert m, "no 'ready: cd' line in:\n" + text
    shown = Path(m.group(1))
    assert shown.is_absolute(), "ready path %s is not absolute" % shown
    assert shown == tmp / "work" / "elsewhere" / "my-game", shown
    assert (shown / "scripts" / "game.py").is_file(), "ready path is not the project"
print("PASS")
sys.exit(0)
