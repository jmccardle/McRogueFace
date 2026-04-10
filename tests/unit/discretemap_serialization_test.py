"""Test DiscreteMap to_bytes/from_bytes serialization - issue #293"""
import mcrfpy
import sys

PASS = True

def check(name, condition):
    global PASS
    if not condition:
        print(f"FAIL: {name}")
        PASS = False
    else:
        print(f"  ok: {name}")

# Test 1: Basic to_bytes
dmap = mcrfpy.DiscreteMap((10, 10), fill=42)
data = dmap.to_bytes()
check("to_bytes returns bytes", isinstance(data, bytes))
check("to_bytes length matches dimensions", len(data) == 100)
check("to_bytes values correct", all(b == 42 for b in data))

# Test 2: to_bytes with varied data
dmap2 = mcrfpy.DiscreteMap((5, 3), fill=0)
dmap2.set(0, 0, 10)
dmap2.set(4, 2, 200)
dmap2.set(2, 1, 128)
data2 = dmap2.to_bytes()
check("varied data length", len(data2) == 15)
check("varied data [0,0]=10", data2[0] == 10)
check("varied data [4,2]=200", data2[14] == 200)
check("varied data [2,1]=128", data2[7] == 128)

# Test 3: from_bytes basic roundtrip
dmap3 = mcrfpy.DiscreteMap.from_bytes(data2, (5, 3))
check("from_bytes creates DiscreteMap", isinstance(dmap3, mcrfpy.DiscreteMap))
check("from_bytes size correct", dmap3.size == (5, 3))
check("from_bytes [0,0] preserved", dmap3.get(0, 0) == 10)
check("from_bytes [4,2] preserved", dmap3.get(4, 2) == 200)
check("from_bytes [2,1] preserved", dmap3.get(2, 1) == 128)
check("from_bytes [1,0] is zero", dmap3.get(1, 0) == 0)

# Test 4: Full roundtrip preserves all data
dmap4 = mcrfpy.DiscreteMap((20, 15), fill=0)
for y in range(15):
    for x in range(20):
        dmap4.set(x, y, (x * 7 + y * 13) % 256)
data4 = dmap4.to_bytes()
dmap4_restored = mcrfpy.DiscreteMap.from_bytes(data4, (20, 15))
data4_check = dmap4_restored.to_bytes()
check("full roundtrip data identical", data4 == data4_check)

# Test 5: from_bytes with enum
from enum import IntEnum
class Terrain(IntEnum):
    WATER = 0
    GRASS = 1
    MOUNTAIN = 2

raw = bytes([0, 1, 2, 1, 0, 2])
dmap5 = mcrfpy.DiscreteMap.from_bytes(raw, (3, 2), enum=Terrain)
check("from_bytes with enum", dmap5.enum_type is Terrain)
val = dmap5.get(1, 0)
check("enum value returned", val == Terrain.GRASS)

# Test 6: Error - wrong data length
try:
    mcrfpy.DiscreteMap.from_bytes(b"\x00\x01\x02", (2, 2))
    check("rejects wrong length", False)
except ValueError:
    check("rejects wrong length", True)

# Test 7: Error - invalid dimensions
try:
    mcrfpy.DiscreteMap.from_bytes(b"\x00", (0, 1))
    check("rejects zero dimension", False)
except ValueError:
    check("rejects zero dimension", True)

# Test 8: Large map roundtrip
big = mcrfpy.DiscreteMap((100, 100), fill=255)
big_data = big.to_bytes()
check("large map serializes", len(big_data) == 10000)
big_restored = mcrfpy.DiscreteMap.from_bytes(big_data, (100, 100))
check("large map roundtrips", big_restored.to_bytes() == big_data)

if PASS:
    print("PASS")
    sys.exit(0)
else:
    sys.exit(1)
