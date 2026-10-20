"""Regression test for #505 part 1 - CPython interpreter flags.

ensurepip/pip/venv re-invoke sys.executable with `-I -W ignore::DeprecationWarning ...`,
and the parser used to answer `Unknown option: -I`. Each flag now maps onto the PyConfig
field it means, and shows in sys.flags / sys.warnoptions / sys._xoptions. Unknown flags
still fail.

Runs the engine binary (sys.executable) as a subprocess for each case.
"""
import json
import os
import subprocess
import sys

import mcrfpy

failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


engine = sys.executable
cwd = os.path.dirname(engine)
env = dict(os.environ)
env["ALSOFT_DRIVERS"] = "null"
env.pop("PYTHONPATH", None)

PROBE = ("import sys, json; f = sys.flags; print(json.dumps({"
         "'isolated': f.isolated, 'ignore_environment': f.ignore_environment, "
         "'no_user_site': f.no_user_site, 'no_site': f.no_site, "
         "'dont_write_bytecode': f.dont_write_bytecode, 'verbose': f.verbose, "
         "'optimize': f.optimize, 'quiet': f.quiet, "
         "'unbuffered': not sys.stdout.line_buffering and sys.stdout.write_through, "
         "'warnoptions': sys.warnoptions, 'xoptions': {k: str(v) for k, v in sys._xoptions.items()}}))")


def run(*args, **kw):
    return subprocess.run([engine] + list(args), capture_output=True, text=True,
                          timeout=60, cwd=cwd, env=kw.get("env", env))


def probe(*flags):
    r = run(*flags, "-c", PROBE)
    if r.returncode != 0:
        print("  (stderr) " + r.stderr.strip()[:300])
        return None
    return json.loads(r.stdout.strip().splitlines()[-1])


def expect(flags, **want):
    got = probe(*flags)
    check(got is not None, "%s runs" % " ".join(flags))
    if got is None:
        return
    for k, v in want.items():
        check(got[k] == v, "%s -> %s == %r (got %r)" % (" ".join(flags), k, v, got[k]))


expect(["-I"], isolated=1, ignore_environment=1, no_user_site=1)
expect(["-E"], ignore_environment=1)
expect(["-s"], no_user_site=1)
expect(["-S"], no_site=1)
expect(["-B"], dont_write_bytecode=1)
expect(["-u"], unbuffered=True)
expect(["-q"], quiet=1)
expect(["-v"], verbose=1)
expect(["-vv"], verbose=2)
expect(["-O"], optimize=1)
expect(["-OO"], optimize=2)
expect(["-O", "-O"], optimize=2)
expect(["-W", "ignore::DeprecationWarning"], warnoptions=["ignore::DeprecationWarning"])
expect(["-Wignore::UserWarning", "-W", "error"], warnoptions=["ignore::UserWarning", "error"])
expect(["-X", "foo=bar", "-Xbaz"], xoptions={"foo": "bar", "baz": "True"})
expect(["-Es"], ignore_environment=1, no_user_site=1)
expect(["-IBu", "-W", "ignore"], isolated=1, dont_write_bytecode=1, unbuffered=True,
       warnoptions=["ignore"])

# The exact shape pip/ensurepip re-invokes sys.executable with.
r = run("-I", "-W", "ignore::DeprecationWarning", "-c", "import sys; print(sys.flags.isolated)")
check(r.returncode == 0 and r.stdout.strip() == "1", "-I -W ignore::DeprecationWarning -c works")

# -W is a real warning filter, not just recorded.
r = run("-W", "error", "-c", "import warnings; warnings.warn('x')")
check(r.returncode != 0 and "UserWarning" in r.stderr, "-W error turns a warning into an exception")

# -S really skips site: no 'site' module.
r = run("-S", "-c", "import sys; print('site' in sys.modules)")
check(r.stdout.strip() == "False", "-S does not import site")

# -OO really strips asserts.
r = run("-O", "-c", "assert False; print('ran')")
check(r.stdout.strip() == "ran", "-O strips asserts")

# -m accepts them too, and flags after -m belong to the module.
r = run("-I", "-m", "sysconfig")
check(r.returncode == 0, "-I -m sysconfig runs")

# --exec path (headless) honours them.
script = os.path.join(cwd, "_issue_505_exec_probe.py")
with open(script, "w") as f:
    f.write("import sys\nprint('FLAGS', sys.flags.isolated, sys.flags.dont_write_bytecode, sys.warnoptions)\nsys.exit(0)\n")
try:
    r = run("--headless", "-I", "-B", "-W", "ignore", "--exec", script)
    check("FLAGS 1 1 ['ignore']" in r.stdout, "--exec path sees -I -B -W (got %r %r)" % (r.stdout[-80:], r.stderr[-120:]))
finally:
    os.unlink(script)

# Errors stay errors.
r = run("-Z", "-c", "pass")
check(r.returncode != 0 and "Unknown option" in r.stderr, "unknown flag -Z still fails")
r = run("-IZ", "-c", "pass")
check(r.returncode != 0 and "Unknown option" in r.stderr, "unknown flag in a cluster fails")
r = run("-W")
check(r.returncode != 0 and "Argument expected for the -W option" in r.stderr, "-W without value fails")
r = run("--no-such-flag")
check(r.returncode != 0 and "Unknown option" in r.stderr, "unknown long flag still fails")

# --help documents them.
r = run("--help")
for flag in ("-I ", "-E ", "-s ", "-S ", "-B ", "-u ", "-W arg", "-X opt"):
    check(("  " + flag) in r.stdout, "--help lists " + flag.strip())

if failures:
    print("FAIL: %d check(s) failed" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
