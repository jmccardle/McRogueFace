"""#421: the engine and its embedded CPython both keep the frame-pointer chain.

PEP 831 (CPython 3.15) builds the interpreter with frame pointers and asks
embedders to do the same: a frame-pointer unwinder (perf --call-graph fp,
eBPF, the -Xperf trampolines) stops at the first function that omits one.
Without them in the engine, a profile sampled inside an mcrfpy binding is cut
off at the C++ dispatcher that called into Python (Timer::test, runSimFrame,
doFrame) -- see tools/fp_walk_gdb.py for the end-to-end demonstration.

Checks:
 1. The embedded interpreter was configured with the PEP 831 flags.
 2. Every engine function that makes a call sets up a frame pointer.
    Frameless *leaf* functions are allowed: GCC omits the frame for leaves
    with no stack frame even under -mno-omit-leaf-frame-pointer, which hides
    at most the leaf's immediate caller and never breaks the chain.

A build configured with -DMCRF_FRAME_POINTERS=OFF fails this test on purpose.
"""
import os
import platform
import re
import shutil
import subprocess
import sys
import sysconfig

FP_FLAGS = ("-fno-omit-frame-pointer", "-mno-omit-leaf-frame-pointer")
# Instruction that establishes the frame pointer, per architecture.
FP_SETUP = {
    "x86_64": re.compile(r"mov\s+%rsp,%rbp"),
    "aarch64": re.compile(r"mov\s+x29,\s*sp"),
}
CALL = re.compile(r"^(call|bl|blr)\b")
# Process entry: has no caller frame to link to.
ALLOWED_FRAMELESS_CALLERS = {"_start"}

failures = []

# 1. The interpreter.
basecflags = sysconfig.get_config_var("BASECFLAGS") or ""
for flag in FP_FLAGS:
    if flag not in basecflags.split():
        failures.append(f"embedded CPython BASECFLAGS lacks {flag}: {basecflags!r}")

# 2. The engine binary.
arch = platform.machine()
if arch not in FP_SETUP:
    failures.append(f"no frame-pointer prologue pattern for {arch}; extend FP_SETUP")
objdump = shutil.which("objdump")
if objdump is None:
    failures.append("objdump not found (binutils is part of the build toolchain)")

if not failures:
    exe = os.path.realpath("/proc/self/exe")
    dis = subprocess.run([objdump, "-d", "--no-show-raw-insn", "-j", ".text", exe],
                         capture_output=True, text=True, check=True).stdout
    functions = {}
    current = None
    for line in dis.splitlines():
        header = re.match(r"^[0-9a-f]+ <(.+)>:$", line)
        if header:
            current = functions.setdefault(header.group(1), [])
        elif current is not None and "\t" in line:
            current.append(line.split("\t", 1)[1].strip())

    setup = FP_SETUP[arch]
    framed = leaves = 0
    offenders = []
    for name, insns in functions.items():
        if ".cold" in name:
            continue                    # split-off cold path; runs inside its parent's frame
        if any(setup.match(i) for i in insns):
            framed += 1
        elif not any(CALL.match(i) for i in insns):
            leaves += 1
        elif name not in ALLOWED_FRAMELESS_CALLERS:
            offenders.append(name)

    print(f"{exe}: {framed} framed, {leaves} frameless leaves, "
          f"{len(offenders)} frameless callers")
    if not functions:
        failures.append(f"objdump found no functions in {exe}")
    if offenders:
        failures.append(f"{len(offenders)} functions call out without a frame pointer "
                        f"(was the build configured with -DMCRF_FRAME_POINTERS=OFF?), "
                        f"e.g. {offenders[:5]}")

if failures:
    for f in failures:
        print("FAIL:", f)
    sys.exit(1)
print("PASS")
sys.exit(0)
