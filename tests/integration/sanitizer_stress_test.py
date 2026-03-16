"""Stress test for sanitizer builds: exercises new Phase 1-4 code paths."""
import mcrfpy
import sys

def stress_entity_lifecycle():
    """Create/destroy many entities, exercise spatial hash and labels."""
    scene = mcrfpy.Scene("stress_lifecycle")
    mcrfpy.current_scene = scene
    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(50, 50), texture=tex, pos=(0, 0), size=(400, 400))
    scene.children.append(grid)

    for y in range(50):
        for x in range(50):
            grid.at(x, y).walkable = True
            grid.at(x, y).transparent = True

    # Create many entities
    entities = []
    for i in range(100):
        e = mcrfpy.Entity((i % 48 + 1, i // 48 + 1), grid=grid,
                          labels={"test", f"group_{i % 5}"})
        e.cell_pos = (i % 48 + 1, i // 48 + 1)
        entities.append(e)

    # Verify spatial hash
    cell_ents = grid.at(1, 1).entities
    assert len(cell_ents) >= 1, f"Expected entities at (1,1), got {len(cell_ents)}"

    # Move entities around
    for i, e in enumerate(entities):
        new_x = (i * 7 + 3) % 48 + 1
        new_y = (i * 13 + 5) % 48 + 1
        e.cell_pos = (new_x, new_y)

    # Remove half via die()
    for e in entities[:50]:
        e.die()

    # Verify remaining
    assert len(grid.entities) == 50
    print("PASS: entity lifecycle stress")

def stress_behavior_stepping():
    """Run many steps with various behaviors."""
    scene = mcrfpy.Scene("stress_behavior")
    mcrfpy.current_scene = scene
    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(30, 30), texture=tex, pos=(0, 0), size=(300, 300))
    scene.children.append(grid)

    for y in range(30):
        for x in range(30):
            grid.at(x, y).walkable = True
            grid.at(x, y).transparent = True
    # Walls on border
    for i in range(30):
        grid.at(0, i).walkable = False
        grid.at(29, i).walkable = False
        grid.at(i, 0).walkable = False
        grid.at(i, 29).walkable = False

    # Noise entities
    for i in range(20):
        e = mcrfpy.Entity((5 + i, 10), grid=grid)
        e.set_behavior(int(mcrfpy.Behavior.NOISE4))
        e.move_speed = 0

    # Sleep entity with callback
    triggered = []
    sleeper = mcrfpy.Entity((15, 15), grid=grid)
    sleeper.set_behavior(int(mcrfpy.Behavior.SLEEP), turns=3)
    sleeper.step = lambda t, d: triggered.append(int(t))

    # Run 10 steps
    grid.step(n=10)

    assert len(triggered) == 1, f"Expected 1 DONE trigger, got {len(triggered)}"
    assert triggered[0] == int(mcrfpy.Trigger.DONE)
    print("PASS: behavior stepping stress")

def stress_gridview_lifecycle():
    """Create and destroy multiple GridViews referencing same grid."""
    scene = mcrfpy.Scene("stress_gridview")
    mcrfpy.current_scene = scene
    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(20, 20), texture=tex, pos=(0, 0), size=(200, 200))
    scene.children.append(grid)

    # Create and destroy views repeatedly
    for i in range(20):
        view = mcrfpy.GridView(grid=grid, pos=(220, i * 10), size=(100, 100), zoom=0.5 + i * 0.1)
        scene.children.append(view)

    # Scene should have grid + 20 views
    assert len(scene.children) == 21

    # Clear scene children (destroys all views)
    # Use a new scene instead (children released when scene is replaced)
    scene2 = mcrfpy.Scene("stress_gridview2")
    mcrfpy.current_scene = scene2

    # Grid should still be valid
    assert grid.grid_w == 20
    print("PASS: GridView lifecycle stress")

def stress_fov_dedup():
    """Hammer FOV computation with same and different params."""
    scene = mcrfpy.Scene("stress_fov")
    mcrfpy.current_scene = scene
    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(50, 50), texture=tex, pos=(0, 0), size=(400, 400))
    scene.children.append(grid)

    for y in range(50):
        for x in range(50):
            grid.at(x, y).walkable = True
            grid.at(x, y).transparent = True

    # Same params - should hit dedup cache
    for _ in range(100):
        grid.compute_fov((25, 25), radius=10)

    # Different params each time
    for i in range(50):
        grid.compute_fov((i, 25), radius=5)

    # Change map then recompute (dirty flag)
    grid.at(20, 25).transparent = False
    grid.compute_fov((25, 25), radius=10)
    assert not grid.is_in_fov((15, 25))  # Blocked by wall
    print("PASS: FOV dedup stress")

def stress_cell_pos_spatial_hash():
    """Churn entity positions, verify spatial hash integrity."""
    scene = mcrfpy.Scene("stress_spatial")
    mcrfpy.current_scene = scene
    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(100, 100), texture=tex, pos=(0, 0), size=(400, 400))
    scene.children.append(grid)

    for y in range(100):
        for x in range(100):
            grid.at(x, y).walkable = True

    # Create entities
    ents = []
    for i in range(50):
        e = mcrfpy.Entity((i + 1, 1), grid=grid)
        ents.append(e)

    # Move them all to the same cell
    for e in ents:
        e.cell_pos = (50, 50)

    assert len(grid.at(50, 50).entities) == 50

    # Scatter them
    for i, e in enumerate(ents):
        e.cell_pos = (i + 1, 50)

    assert len(grid.at(50, 50).entities) == 1  # Only entity at index 49
    assert len(grid.at(1, 50).entities) == 1
    print("PASS: spatial hash churn stress")

if __name__ == "__main__":
    stress_entity_lifecycle()
    stress_behavior_stepping()
    stress_gridview_lifecycle()
    stress_fov_dedup()
    stress_cell_pos_spatial_hash()
    print("All sanitizer stress tests passed")
    sys.exit(0)
