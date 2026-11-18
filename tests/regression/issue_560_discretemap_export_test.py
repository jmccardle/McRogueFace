"""#560 B: a DiscreteMap buffer export must block re-initialisation (BufferError, as bytearray)."""
import sys
import mcrfpy

fails = []
def check(c, m):
    if not c: fails.append(m)

def raises_buffer(fn, label):
    try:
        fn(); fails.append(label + ": no BufferError")
    except BufferError:
        pass

dm = mcrfpy.DiscreteMap((50, 50), fill=3)
m = memoryview(dm)
raises_buffer(lambda: dm.__init__((2, 2)), "__init__ with a memoryview alive")
m[49, 49] = 7                       # was a segfault after the re-init
check(dm[49, 49] == 7, "write through the view still lands")
check(dm.size == (50, 50), "size unchanged after refused re-init")
m.release()
dm.__init__((2, 2))                 # no exports left: allowed
check(dm.size == (2, 2), "re-init allowed once the view is released")

# mask(): a view of the storage with the same lifetime rule
d2 = mcrfpy.DiscreteMap((10, 10), fill=42)
mk = d2.mask()
check(len(mk) == 100 and mk[0] == 42, "mask() is a flat 100 byte view")
raises_buffer(lambda: d2.__init__((1, 1)), "__init__ with a mask() view alive")
mk[50] = 99
check(d2[0, 5] == 99, "mask() view writes through")
del mk
d2.__init__((1, 1))

# a mask() view must keep the map alive: dropping the last name used to free the buffer under it
d3 = mcrfpy.DiscreteMap((100, 100), fill=5)
mk3 = d3.mask()
del d3
import gc; gc.collect()
check(mk3[0] == 5 and mk3[9999] == 5, "mask() view outlives the map's last name")
print("FAIL: " + "; ".join(fails) if fails else "PASS")
sys.exit(1 if fails else 0)
