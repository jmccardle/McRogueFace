"""#501: mcrfpy.config exposes the engine's run configuration to scripts.

Under --exec, sys.argv is the script's, so engine flags were invisible. mcrfpy.config is a
read-only view of the parsed flags, plus one runtime setting: exit_on_exception.
"""
import json
import os
import subprocess
import sys
import tempfile

import mcrfpy

failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


cfg = mcrfpy.config
check(type(cfg).__name__ == "EngineConfig", "mcrfpy.config is an EngineConfig (%s)" % type(cfg).__name__)
check(cfg.headless is True, "headless")
check(cfg.exit_on_exception is True, "exit_on_exception defaults to True")
check(cfg.run_forever is False, "run_forever")
check(cfg.interactive is False, "interactive")
check(isinstance(cfg.exec_scripts, tuple) and len(cfg.exec_scripts) == 1
      and cfg.exec_scripts[0].endswith("engine_config_test.py"), "exec_scripts %r" % (cfg.exec_scripts,))
check(cfg.script_path is None, "script_path is None without a script argument")
check(cfg.script_args == (), "script_args")
check(cfg.screenshot_path is None, "screenshot_path")
check(isinstance(cfg.audio_enabled, bool), "audio_enabled is a bool")

# read-only except exit_on_exception; unknown attributes are errors
for name in ("headless", "run_forever", "interactive", "exec_scripts", "script_path",
             "script_args", "screenshot_path", "audio_enabled"):
    try:
        setattr(cfg, name, 1)
        check(False, "%s is read-only" % name)
    except AttributeError:
        check(True, "%s is read-only" % name)
try:
    cfg.nonsense = 1
    check(False, "unknown attributes are rejected")
except AttributeError:
    check(True, "unknown attributes are rejected")

# exit_on_exception: writable, bool only
cfg.exit_on_exception = False
check(cfg.exit_on_exception is False, "exit_on_exception is writable")
for bad in (0, 1, "no", None):
    try:
        cfg.exit_on_exception = bad
        check(False, "exit_on_exception rejects %r" % (bad,))
    except TypeError:
        check(True, "exit_on_exception rejects %r" % (bad,))
check(cfg.exit_on_exception is False, "a rejected assignment changes nothing")
try:
    del cfg.exit_on_exception
    check(False, "exit_on_exception can't be deleted")
except (TypeError, AttributeError):
    check(True, "exit_on_exception can't be deleted")
cfg.exit_on_exception = True

# flags are seen by a fresh engine process
PROBE = ("import json, sys, mcrfpy\n"
         "c = mcrfpy.config\n"
         "print('CFG ' + json.dumps(dict(headless=c.headless, exit_on_exception=c.exit_on_exception,\n"
         "  run_forever=c.run_forever, exec=list(c.exec_scripts), script=c.script_path,\n"
         "  args=list(c.script_args))))\n"
         "sys.exit(0)\n")
env = dict(os.environ, ALSOFT_DRIVERS="null")


def run(args):
    out = subprocess.run([sys.executable, "--headless"] + args, capture_output=True, text=True,
                         timeout=30, env=env)
    for line in out.stdout.splitlines():
        if line.startswith("CFG "):
            return json.loads(line[4:])
    print(out.stdout, out.stderr)
    return None


with tempfile.TemporaryDirectory() as tmp:
    probe = os.path.join(tmp, "probe.py")
    with open(probe, "w") as f:
        f.write(PROBE)
    c = run(["--continue-after-exceptions", "--exec", probe])
    check(c is not None and c["exit_on_exception"] is False and c["headless"] is True,
          "--continue-after-exceptions -> exit_on_exception False (%r)" % (c,))
    c = run(["--exec", probe])
    check(c is not None and c["exit_on_exception"] is True, "default -> exit_on_exception True")
    c = run([probe, "a", "b"])
    check(c is not None and c["script"] == probe and c["args"] == ["a", "b"] and c["exec"] == [],
          "script mode: script_path and script_args (%r)" % (c,))
    c = run(["--run-forever", "--exec", probe])
    # --run-forever would never exit; the probe exits itself
    check(c is not None and c["run_forever"] is True, "--run-forever -> run_forever True")

# the setting is live: in a real (windowed) frame loop, a raising timer callback ends the
# process unless the script has set exit_on_exception False. Needs a display, like the suite.
LIVE = ("import mcrfpy\n"
        "mcrfpy.config.exit_on_exception = %s\n"
        "def boom(timer, ms):\n    raise ValueError('boom')\n"
        "t = mcrfpy.Timer('boom', boom, 10)\n")
with tempfile.TemporaryDirectory() as tmp:
    for value, keeps_running in (("False", True), ("True", False)):
        live = os.path.join(tmp, "live.py")
        with open(live, "w") as f:
            f.write(LIVE % value)
        try:
            subprocess.run([sys.executable, "--exec", live], capture_output=True, text=True,
                           timeout=6, env=env)
            ran_on = False
        except subprocess.TimeoutExpired:
            ran_on = True
        check(ran_on == keeps_running,
              "exit_on_exception=%s set from the script: process keeps running=%s" % (value, keeps_running))

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
