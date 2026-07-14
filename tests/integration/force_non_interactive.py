#!/usr/bin/env python3
"""Verify that --exec scripts run Python non-interactively.

Historically this file *forced* non-interactive mode (deleting sys.ps1/ps2 and
mangling termios) because the embedded interpreter could drop into a REPL and
hang the engine. That workaround is gone; the property it was protecting is now
an engine guarantee, so this asserts it instead of forcing it:

  - the interpreter is not in REPL mode (no sys.ps1 / sys.ps2)
  - it will not drop into a REPL after the script (-i / inspect not set)
  - stdin is not an interactive terminal, and is not consumed by the engine
  - the script, not a prompt, decides when the process ends (#350 exit contract)
"""
import sys
import os
import mcrfpy

failures = []


def check(label, condition, detail=""):
    if condition:
        print("  ok   : %s" % label)
    else:
        print("  FAIL : %s %s" % (label, detail))
        failures.append(label)


print("Checking non-interactive execution of --exec scripts...")

# 1. REPL prompts only exist when the interpreter is interactive. Their presence
#    would mean the engine handed us an interactive interpreter.
check("sys.ps1 absent", not hasattr(sys, "ps1"))
check("sys.ps2 absent", not hasattr(sys, "ps2"))

# 2. Interpreter flags: -i / PYTHONINSPECT would make Python drop to a prompt
#    *after* the script finishes, hanging a headless run.
check("sys.flags.interactive == 0", sys.flags.interactive == 0,
      "got %r" % (sys.flags.interactive,))
check("sys.flags.inspect == 0", sys.flags.inspect == 0,
      "got %r" % (sys.flags.inspect,))
check("PYTHONINSPECT not set in env", not os.environ.get("PYTHONINSPECT"))

# 3. stdin must not be an interactive terminal driving a REPL.
#    NOTE: deliberately no blocking read here -- under a test runner stdin is an
#    open pipe that never sends EOF, so sys.stdin.read() would hang forever. The
#    thing worth asserting is that no prompt is bound to it.
check("stdin is not a tty", sys.stdin is None or not sys.stdin.isatty())

# 4. The engine must not be running its own read-eval-print loop over our script:
#    module scope is ordinary script scope, and the headless clock only advances
#    when we ask it to (#350). One step() must not spin into an interactive loop.
scene = mcrfpy.Scene("force_non_interactive")
mcrfpy.current_scene = scene
fired = []
mcrfpy.Timer("tick", lambda timer, runtime: fired.append(runtime), 50)
for _ in range(4):
    mcrfpy.step(0.05)
check("headless clock advances under script control", len(fired) >= 1,
      "timer fired %d time(s)" % len(fired))

if failures:
    print("FAIL: %d check(s) failed: %s" % (len(failures), ", ".join(failures)))
    sys.exit(1)

print("PASS")
sys.exit(0)
