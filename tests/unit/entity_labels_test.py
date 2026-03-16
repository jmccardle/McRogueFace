"""Unit test for #296: Entity label system."""
import mcrfpy
import sys

def test_labels_crud():
    """Basic add/remove/has operations."""
    e = mcrfpy.Entity()
    assert len(e.labels) == 0, "New entity should have no labels"

    e.add_label("solid")
    assert e.has_label("solid"), "Should have 'solid' after add"
    assert not e.has_label("npc"), "Should not have 'npc'"

    e.add_label("npc")
    assert len(e.labels) == 2

    e.remove_label("solid")
    assert not e.has_label("solid"), "Should not have 'solid' after remove"
    assert e.has_label("npc"), "'npc' should remain"
    print("PASS: labels CRUD")

def test_labels_frozenset():
    """Labels getter returns frozenset."""
    e = mcrfpy.Entity()
    e.add_label("a")
    e.add_label("b")
    labels = e.labels
    assert isinstance(labels, frozenset), f"Expected frozenset, got {type(labels)}"
    assert labels == frozenset({"a", "b"})
    print("PASS: labels returns frozenset")

def test_labels_setter():
    """Labels setter accepts any iterable of strings."""
    e = mcrfpy.Entity()
    e.labels = ["x", "y", "z"]
    assert e.labels == frozenset({"x", "y", "z"})

    e.labels = {"replaced"}
    assert e.labels == frozenset({"replaced"})

    e.labels = frozenset()
    assert len(e.labels) == 0
    print("PASS: labels setter")

def test_labels_constructor():
    """Labels kwarg in constructor."""
    e = mcrfpy.Entity(labels={"solid", "npc"})
    assert e.has_label("solid")
    assert e.has_label("npc")
    assert len(e.labels) == 2
    print("PASS: labels constructor kwarg")

def test_labels_duplicate_add():
    """Adding same label twice is idempotent."""
    e = mcrfpy.Entity()
    e.add_label("solid")
    e.add_label("solid")
    assert len(e.labels) == 1
    print("PASS: duplicate add is idempotent")

def test_labels_remove_missing():
    """Removing non-existent label is a no-op."""
    e = mcrfpy.Entity()
    e.remove_label("nonexistent")  # Should not raise
    print("PASS: remove missing label is no-op")

if __name__ == "__main__":
    test_labels_crud()
    test_labels_frozenset()
    test_labels_setter()
    test_labels_constructor()
    test_labels_duplicate_add()
    test_labels_remove_missing()
    print("All #296 tests passed")
    sys.exit(0)
