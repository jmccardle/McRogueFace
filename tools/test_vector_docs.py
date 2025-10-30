import mcrfpy
import sys

# Check Vector.magnitude docstring
mag_doc = mcrfpy.Vector.magnitude.__doc__
print("magnitude doc:", mag_doc)
assert "magnitude()" in mag_doc
assert "Calculate the length/magnitude" in mag_doc
assert "Returns:" in mag_doc

# Check Vector.dot docstring
dot_doc = mcrfpy.Vector.dot.__doc__
print("dot doc:", dot_doc)
assert "dot(other: Vector)" in dot_doc
assert "Args:" in dot_doc
assert "other:" in dot_doc

# Check Vector.normalize docstring
normalize_doc = mcrfpy.Vector.normalize.__doc__
print("normalize doc:", normalize_doc)
assert "normalize()" in normalize_doc
assert "Return a unit vector" in normalize_doc
assert "Returns:" in normalize_doc
assert "Note:" in normalize_doc

print("SUCCESS: All docstrings present and complete")
sys.exit(0)
