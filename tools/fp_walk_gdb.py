"""Walk the frame-pointer chain exactly like `perf --call-graph fp` does (#421).

A gdb Python script: stop in an mcrfpy binding, then follow saved-%rbp links
by hand ([rbp] = caller's rbp, [rbp+8] = return address) -- no DWARF, no
gdb unwinder -- and symbolize each return address. Python frames are named
from the perf trampoline map (/tmp/perf-<pid>.map) when the workload ran with
MCRF_PERF_TRAMPOLINE=1. Needs no perf permissions, so it's how we verify the
chain on a box where kernel.perf_event_paranoid blocks perf.

Usage (from a build dir):
  MCRF_PERF_TRAMPOLINE=1 gdb -q -batch -x ../tools/fp_walk_gdb.py \\
      --args ./mcrogueface --headless --exec ../tests/benchmarks/fp_loop_workload.py

Environment:
  FP_WALK_BREAK   function to stop in (default UIDrawable::set_float_member)
  FP_WALK_SKIP    breakpoint hits to skip first, so the workload is warm (default 50)

Exit status: 0 if the chain reaches main(), 1 if it breaks before that. The walk
normally ends one frame past main, in glibc's __libc_start_call_main (Debian's
libc is built without frame pointers), and reports that as "BROKEN" -- expected.
gdb places a breakpoint after a recognised `push %rbp; mov %rsp,%rbp`
prologue, so at the stop %rbp is the binding's own frame (FP builds). In a
build without frame pointers %rbp is a general-purpose register and the walk
reads garbage or stops short -- that is the failure this demonstrates.
"""
import bisect
import os

import gdb

BREAK = os.environ.get("FP_WALK_BREAK", "UIDrawable::set_float_member")
SKIP = int(os.environ.get("FP_WALK_SKIP", "50"))
MAX_DEPTH = 256

for cmd in ("set pagination off", "set confirm off", "set breakpoint pending on",
            "set print asm-demangle on", "set print thread-events off",
            "set startup-with-shell off"):
    gdb.execute(cmd)

bp = gdb.Breakpoint(BREAK)
bp.ignore_count = SKIP
gdb.execute("run")
if not bp.hit_count:
    print(f"fp_walk: breakpoint {BREAK!r} never hit")
    gdb.execute("kill")
    gdb.execute("quit 2")

inf = gdb.selected_inferior()
frame = gdb.selected_frame()


def u64(addr):
    return int.from_bytes(inf.read_memory(addr, 8).tobytes(), "little")


def load_perf_map(pid):
    entries = []
    try:
        with open(f"/tmp/perf-{pid}.map") as fh:
            for line in fh:
                start, size, name = line.rstrip("\n").split(" ", 2)
                entries.append((int(start, 16), int(size, 16), name))
    except FileNotFoundError:
        pass
    entries.sort()
    return entries


perf_map = load_perf_map(inf.pid)
perf_starts = [e[0] for e in perf_map]


def symbolize(addr):
    i = bisect.bisect_right(perf_starts, addr) - 1
    if i >= 0 and addr < perf_map[i][0] + perf_map[i][1]:
        return perf_map[i][2]
    text = gdb.execute(f"info symbol {addr:#x}", to_string=True).strip()
    if text.startswith("No symbol"):
        return "??"
    name, _, where = text.partition(" in section ")
    lib = os.path.basename(where.split(" of ")[-1]) if " of " in where else "mcrogueface"
    return f"{name}  [{lib}]"


pc = int(frame.read_register("pc"))
rbp = int(frame.read_register("rbp"))
chain = [pc]
broken = None
while len(chain) < MAX_DEPTH:
    if rbp == 0:
        break                       # outermost frame: _start clears %rbp
    try:
        ret, nxt = u64(rbp + 8), u64(rbp)
    except gdb.MemoryError:
        broken = f"rbp={rbp:#x} is not a readable stack address"
        break
    if ret == 0:
        break
    chain.append(ret)
    if nxt != 0 and nxt <= rbp:
        broken = f"saved rbp {nxt:#x} does not move up the stack from {rbp:#x}"
        break
    rbp = nxt

names = [symbolize(a) for a in chain]
for depth, (addr, name) in enumerate(zip(chain, names)):
    print(f"#{depth:<3} {addr:#014x}  {name}")

reached_main = any(n.split("  [")[0].split(" + ")[0] == "main" for n in names)
python_frames = sum(1 for n in names if n.startswith("py::"))
print(f"\nfp_walk: depth={len(chain)} python_frames={python_frames} "
      f"perf_map={'yes' if perf_map else 'no'} reached_main={reached_main}"
      + (f" BROKEN: {broken}" if broken else ""))
gdb.execute("kill")
gdb.execute(f"quit {0 if reached_main else 1}")
