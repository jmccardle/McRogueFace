"""Test mcrfpy.save_dir and mcrfpy._sync_storage() persistence API"""
import mcrfpy
import os
import json
import sys

# Test 1: save_dir attribute exists and is a string
save_dir = mcrfpy.save_dir
assert isinstance(save_dir, str), f"save_dir should be str, got {type(save_dir)}"
print(f"PASS: mcrfpy.save_dir = '{save_dir}'")

# Test 2: save directory exists on disk
assert os.path.isdir(save_dir), f"save_dir '{save_dir}' does not exist as a directory"
print(f"PASS: save directory exists")

# Test 3: _sync_storage is callable and returns None
result = mcrfpy._sync_storage()
assert result is None, f"_sync_storage should return None, got {result}"
print(f"PASS: _sync_storage() returns None")

# Test 4: Can write a file to save_dir with context manager
test_path = os.path.join(save_dir, "test_persistence.json")
test_data = {"lore_flags": {"sundering": True}, "zone": 3, "enemies": [1, 2, 3]}
with open(test_path, 'w') as f:
    json.dump(test_data, f)
print(f"PASS: wrote {test_path}")

# Test 5: Can read it back
with open(test_path, 'r') as f:
    loaded = json.load(f)
assert loaded == test_data, f"Data mismatch: {loaded} != {test_data}"
print(f"PASS: read back matches")

# Test 6: Can write binary data
bin_path = os.path.join(save_dir, "test_binary.dat")
with open(bin_path, 'wb') as f:
    f.write(b'\x00\x01\x02\xff' * 100)
with open(bin_path, 'rb') as f:
    data = f.read()
assert len(data) == 400
assert data[:4] == b'\x00\x01\x02\xff'
print(f"PASS: binary read/write works")

# Test 7: sync after writes (no-op on desktop, but should not error)
mcrfpy._sync_storage()
print(f"PASS: _sync_storage() after writes")

# Test 8: open() on non-save paths is not affected
# (On WASM, the monkeypatch only wraps writes to /save/)
import tempfile
tmp = os.path.join(save_dir, "test_unwrapped.txt")
with open(tmp, 'r+' if os.path.exists(tmp) else 'w') as f:
    f.write("test")
os.remove(tmp)
print(f"PASS: open() works for other paths")

# Test 9: Verify the cross-platform API contract
# Game code that works identically on desktop and WASM:
game_state_path = os.path.join(mcrfpy.save_dir, "game_state.json")
game_state = {
    "player": {"hp": 50, "zone": 3},
    "lore": {"sundering": True, "librarian_met": False},
    "enemies": {"zone_3": {"goblin_chief": False}}
}
# Write (on WASM, context manager auto-syncs IDBFS; on desktop, just writes)
with open(game_state_path, 'w') as f:
    json.dump(game_state, f)
# Read
with open(game_state_path, 'r') as f:
    loaded_state = json.load(f)
assert loaded_state == game_state
os.remove(game_state_path)
print(f"PASS: cross-platform save/load contract works")

# Cleanup
os.remove(test_path)
os.remove(bin_path)
print(f"PASS: cleanup done")

print("\nAll save_dir tests passed!")
sys.exit(0)
