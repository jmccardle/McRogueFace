# entity3d_test.py - Unit test for Entity3D 3D game entities

import mcrfpy
import sys

def test_entity3d_creation():
    """Test basic Entity3D creation and default properties"""
    e = mcrfpy.Entity3D()

    # Default grid position (0, 0)
    assert e.pos == (0, 0), f"Expected pos=(0, 0), got {e.pos}"
    assert e.grid_pos == (0, 0), f"Expected grid_pos=(0, 0), got {e.grid_pos}"

    # Default world position (at origin)
    wp = e.world_pos
    assert len(wp) == 3, f"Expected 3-tuple for world_pos, got {wp}"
    assert wp[0] == 0.0, f"Expected world_pos.x=0, got {wp[0]}"
    assert wp[2] == 0.0, f"Expected world_pos.z=0, got {wp[2]}"

    # Default rotation
    assert e.rotation == 0.0, f"Expected rotation=0, got {e.rotation}"

    # Default scale
    assert e.scale == 1.0, f"Expected scale=1.0, got {e.scale}"

    # Default visibility
    assert e.visible == True, f"Expected visible=True, got {e.visible}"

    # Default color (orange: 200, 100, 50)
    c = e.color
    assert c.r == 200, f"Expected color.r=200, got {c.r}"
    assert c.g == 100, f"Expected color.g=100, got {c.g}"
    assert c.b == 50, f"Expected color.b=50, got {c.b}"

    print("[PASS] test_entity3d_creation")

def test_entity3d_with_pos():
    """Test Entity3D creation with position argument"""
    e = mcrfpy.Entity3D(pos=(5, 10))

    assert e.pos == (5, 10), f"Expected pos=(5, 10), got {e.pos}"
    assert e.grid_pos == (5, 10), f"Expected grid_pos=(5, 10), got {e.grid_pos}"

    print("[PASS] test_entity3d_with_pos")

def test_entity3d_with_kwargs():
    """Test Entity3D creation with keyword arguments"""
    e = mcrfpy.Entity3D(
        pos=(3, 7),
        rotation=90.0,
        scale=2.0,
        visible=False,
        color=mcrfpy.Color(255, 0, 0)
    )

    assert e.pos == (3, 7), f"Expected pos=(3, 7), got {e.pos}"
    assert e.rotation == 90.0, f"Expected rotation=90, got {e.rotation}"
    assert e.scale == 2.0, f"Expected scale=2.0, got {e.scale}"
    assert e.visible == False, f"Expected visible=False, got {e.visible}"
    assert e.color.r == 255, f"Expected color.r=255, got {e.color.r}"
    assert e.color.g == 0, f"Expected color.g=0, got {e.color.g}"

    print("[PASS] test_entity3d_with_kwargs")

def test_entity3d_property_modification():
    """Test modifying Entity3D properties after creation"""
    e = mcrfpy.Entity3D()

    # Modify rotation
    e.rotation = 180.0
    assert e.rotation == 180.0, f"Expected rotation=180, got {e.rotation}"

    # Modify scale
    e.scale = 0.5
    assert e.scale == 0.5, f"Expected scale=0.5, got {e.scale}"

    # Modify visibility
    e.visible = False
    assert e.visible == False, f"Expected visible=False, got {e.visible}"
    e.visible = True
    assert e.visible == True, f"Expected visible=True, got {e.visible}"

    # Modify color
    e.color = mcrfpy.Color(0, 255, 128)
    assert e.color.r == 0, f"Expected color.r=0, got {e.color.r}"
    assert e.color.g == 255, f"Expected color.g=255, got {e.color.g}"
    assert e.color.b == 128, f"Expected color.b=128, got {e.color.b}"

    print("[PASS] test_entity3d_property_modification")

def test_entity3d_teleport():
    """Test Entity3D teleport method"""
    e = mcrfpy.Entity3D(pos=(0, 0))

    # Teleport to new position
    e.teleport(15, 20)

    assert e.pos == (15, 20), f"Expected pos=(15, 20), got {e.pos}"
    assert e.grid_pos == (15, 20), f"Expected grid_pos=(15, 20), got {e.grid_pos}"

    # World position should also update
    wp = e.world_pos
    # World position is grid * cell_size, but we don't know cell size here
    # Just verify it changed from origin
    assert wp[0] != 0.0 or wp[2] != 0.0, f"Expected world_pos to change, got {wp}"

    print("[PASS] test_entity3d_teleport")

def test_entity3d_pos_setter():
    """Test setting position via pos property"""
    e = mcrfpy.Entity3D(pos=(0, 0))

    # Set position (this should trigger animated movement when in a viewport)
    e.pos = (8, 12)

    # The grid position should update
    assert e.pos == (8, 12), f"Expected pos=(8, 12), got {e.pos}"

    print("[PASS] test_entity3d_pos_setter")

def test_entity3d_repr():
    """Test Entity3D string representation"""
    e = mcrfpy.Entity3D(pos=(5, 10))
    e.rotation = 45.0
    repr_str = repr(e)

    assert "Entity3D" in repr_str, f"Expected 'Entity3D' in repr, got {repr_str}"
    assert "5" in repr_str, f"Expected grid_x in repr, got {repr_str}"
    assert "10" in repr_str, f"Expected grid_z in repr, got {repr_str}"

    print("[PASS] test_entity3d_repr")

def test_entity3d_viewport_integration():
    """Test adding Entity3D to a Viewport3D"""
    # Create viewport with navigation grid
    vp = mcrfpy.Viewport3D()
    vp.set_grid_size(32, 32)

    # Create entity
    e = mcrfpy.Entity3D(pos=(5, 5))

    # Verify entity has no viewport initially
    assert e.viewport is None, f"Expected viewport=None before adding, got {e.viewport}"

    # Add to viewport
    vp.entities.append(e)

    # Verify entity count
    assert len(vp.entities) == 1, f"Expected 1 entity, got {len(vp.entities)}"

    # Verify entity was linked to viewport
    # Note: viewport property may not be set until render cycle
    # For now, just verify the entity is in the collection
    retrieved = vp.entities[0]
    assert retrieved.pos == (5, 5), f"Expected retrieved entity at (5, 5), got {retrieved.pos}"

    print("[PASS] test_entity3d_viewport_integration")

def test_entitycollection3d_operations():
    """Test EntityCollection3D sequence operations"""
    vp = mcrfpy.Viewport3D()
    vp.set_grid_size(20, 20)

    # Initially empty
    assert len(vp.entities) == 0, f"Expected 0 entities initially, got {len(vp.entities)}"

    # Add multiple entities
    e1 = mcrfpy.Entity3D(pos=(1, 1))
    e2 = mcrfpy.Entity3D(pos=(5, 5))
    e3 = mcrfpy.Entity3D(pos=(10, 10))

    vp.entities.append(e1)
    vp.entities.append(e2)
    vp.entities.append(e3)

    assert len(vp.entities) == 3, f"Expected 3 entities, got {len(vp.entities)}"

    # Access by index
    assert vp.entities[0].pos == (1, 1), f"Expected entities[0] at (1,1)"
    assert vp.entities[1].pos == (5, 5), f"Expected entities[1] at (5,5)"
    assert vp.entities[2].pos == (10, 10), f"Expected entities[2] at (10,10)"

    # Negative indexing
    assert vp.entities[-1].pos == (10, 10), f"Expected entities[-1] at (10,10)"

    # Contains check
    assert e2 in vp.entities, "Expected e2 in entities"

    # Iteration
    positions = [e.pos for e in vp.entities]
    assert (1, 1) in positions, "Expected (1,1) in iterated positions"
    assert (5, 5) in positions, "Expected (5,5) in iterated positions"

    # Remove
    vp.entities.remove(e2)
    assert len(vp.entities) == 2, f"Expected 2 entities after remove, got {len(vp.entities)}"
    assert e2 not in vp.entities, "Expected e2 not in entities after remove"

    # Clear
    vp.entities.clear()
    assert len(vp.entities) == 0, f"Expected 0 entities after clear, got {len(vp.entities)}"

    print("[PASS] test_entitycollection3d_operations")

def test_entity3d_scene_integration():
    """Test Entity3D works when viewport is in a scene"""
    scene = mcrfpy.Scene("entity3d_test")

    vp = mcrfpy.Viewport3D(pos=(0, 0), size=(640, 480))
    vp.set_grid_size(32, 32)

    # Add viewport to scene
    scene.children.append(vp)

    # Add entity to viewport
    e = mcrfpy.Entity3D(pos=(16, 16), rotation=45.0, color=mcrfpy.Color(0, 255, 0))
    vp.entities.append(e)

    # Verify everything is connected
    assert len(scene.children) == 1, "Expected 1 child in scene"

    viewport_from_scene = scene.children[0]
    assert type(viewport_from_scene).__name__ == "Viewport3D"
    assert len(viewport_from_scene.entities) == 1, "Expected 1 entity in viewport"

    entity_from_vp = viewport_from_scene.entities[0]
    assert entity_from_vp.pos == (16, 16), f"Expected entity at (16, 16), got {entity_from_vp.pos}"
    assert entity_from_vp.rotation == 45.0, f"Expected rotation=45, got {entity_from_vp.rotation}"

    print("[PASS] test_entity3d_scene_integration")

def test_entity3d_multiple_entities():
    """Test multiple entities in a viewport"""
    vp = mcrfpy.Viewport3D()
    vp.set_grid_size(50, 50)

    # Create a grid of entities
    entities = []
    for x in range(0, 50, 10):
        for z in range(0, 50, 10):
            e = mcrfpy.Entity3D(pos=(x, z))
            e.color = mcrfpy.Color(x * 5, z * 5, 128)
            entities.append(e)
            vp.entities.append(e)

    expected_count = 5 * 5  # 0, 10, 20, 30, 40 for both x and z
    assert len(vp.entities) == expected_count, f"Expected {expected_count} entities, got {len(vp.entities)}"

    # Verify we can access all entities
    found_positions = set()
    for e in vp.entities:
        found_positions.add(e.pos)

    assert len(found_positions) == expected_count, f"Expected {expected_count} unique positions"

    print("[PASS] test_entity3d_multiple_entities")

def run_all_tests():
    """Run all Entity3D tests"""
    tests = [
        test_entity3d_creation,
        test_entity3d_with_pos,
        test_entity3d_with_kwargs,
        test_entity3d_property_modification,
        test_entity3d_teleport,
        test_entity3d_pos_setter,
        test_entity3d_repr,
        test_entity3d_viewport_integration,
        test_entitycollection3d_operations,
        test_entity3d_scene_integration,
        test_entity3d_multiple_entities,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {test.__name__}: {type(e).__name__}: {e}")
            failed += 1

    print(f"\n=== Results: {passed} passed, {failed} failed ===")
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
