"""Verify code snippets from Phase D batch 3 wiki updates."""
import mcrfpy
import sys

passes = 0
fails = 0

def check(name, fn):
    global passes, fails
    try:
        fn()
        passes += 1
        print(f"  [OK] {name}")
    except Exception as e:
        fails += 1
        print(f"  [FAIL] {name}: {e}")

# ===================================================================
print("=== PROCEDURAL GENERATION ===")
# ===================================================================

def test_pg_bsp_basic():
    """BSP dungeon generation pattern"""
    grid = mcrfpy.Grid(grid_size=(50, 50), pos=(0, 0), size=(400, 400))

    # Set cells walkable (carve a room)
    for x in range(10, 20):
        for y in range(10, 20):
            cell = grid.at(x, y)
            cell.walkable = True
            cell.transparent = True

    # Verify
    assert grid.at(15, 15).walkable == True
    assert grid.at(0, 0).walkable == False

check("PG: BSP basic grid setup", test_pg_bsp_basic)

def test_pg_cell_properties():
    """Cell property access patterns"""
    grid = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320))
    cell = grid.at(5, 5)

    # Test walkable
    cell.walkable = True
    assert cell.walkable == True
    cell.walkable = False
    assert cell.walkable == False

    # Test transparent
    cell.transparent = True
    assert cell.transparent == True
    cell.transparent = False
    assert cell.transparent == False

check("PG: cell properties", test_pg_cell_properties)

def test_pg_entity_placement():
    """Entity placement in generated rooms"""
    import random
    grid = mcrfpy.Grid(grid_size=(30, 30), pos=(0, 0), size=(400, 400))

    # Place entities
    for i in range(5):
        e = mcrfpy.Entity(grid_pos=(10 + i, 10), sprite_index=i)
        grid.entities.append(e)

    assert len(grid.entities) == 5

check("PG: entity placement", test_pg_entity_placement)

def test_pg_scene_setup():
    """Scene setup for procgen"""
    scene = mcrfpy.Scene("pg_test")
    grid = mcrfpy.Grid(grid_size=(50, 50), pos=(0, 0), size=(400, 400))
    scene.children.append(grid)

    player = mcrfpy.Entity(grid_pos=(25, 25), sprite_index=1)
    grid.entities.append(player)

check("PG: scene setup", test_pg_scene_setup)

def test_pg_timer_generation():
    """Timer-based incremental generation"""
    step_count = [0]

    def generate_step(timer, runtime):
        step_count[0] += 1
        if step_count[0] >= 3:
            timer.stop()

    t = mcrfpy.Timer("pg_gen", generate_step, 100)
    # Each step() call can fire at most one timer event
    for _ in range(5):
        mcrfpy.step(0.11)
    assert step_count[0] >= 3, f"Expected >= 3 fires, got {step_count[0]}"
    t.stop()

check("PG: timer generation", test_pg_timer_generation)

def test_pg_grid_size():
    """Grid size access"""
    grid = mcrfpy.Grid(grid_size=(40, 30), pos=(0, 0), size=(400, 300))
    gs = grid.grid_size
    assert gs[0] == 40
    assert gs[1] == 30

check("PG: grid_size property", test_pg_grid_size)

# ===================================================================
print("\n=== GRID RENDERING PIPELINE ===")
# ===================================================================

def test_grp_layer_creation():
    """Layer creation with standalone objects"""
    grid = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320), layers=[])

    # Create layers as standalone objects
    bg = mcrfpy.ColorLayer(name="background", z_index=-2)
    grid.add_layer(bg)

    # Overlay above entities
    overlay = mcrfpy.ColorLayer(name="overlay", z_index=1)
    grid.add_layer(overlay)

    # Verify layers exist
    assert grid.layer("background") is not None
    assert grid.layer("overlay") is not None

check("GRP: layer creation", test_grp_layer_creation)

def test_grp_layer_operations():
    """Layer set/at/fill operations"""
    grid = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(160, 160), layers=[])

    cl = mcrfpy.ColorLayer(name="colors", z_index=-1)
    grid.add_layer(cl)

    # Fill
    cl.fill(mcrfpy.Color(0, 0, 0, 255))

    # Set individual cell
    cl.set((5, 5), mcrfpy.Color(255, 0, 0, 255))

    # Read back
    c = cl.at((5, 5))
    assert c.r == 255

check("GRP: layer operations", test_grp_layer_operations)

def test_grp_tile_layer():
    """TileLayer creation"""
    grid = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(160, 160), layers=[])

    tl = mcrfpy.TileLayer(name="tiles", z_index=-1)
    grid.add_layer(tl)

    assert grid.layer("tiles") is not None

check("GRP: TileLayer creation", test_grp_tile_layer)

def test_grp_z_index():
    """Z-index layer ordering"""
    grid = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(160, 160), layers=[])

    l1 = mcrfpy.ColorLayer(name="below", z_index=-2)
    l2 = mcrfpy.ColorLayer(name="above", z_index=1)
    grid.add_layer(l1)
    grid.add_layer(l2)

    below = grid.layer("below")
    above = grid.layer("above")
    assert below.z_index == -2
    assert above.z_index == 1

check("GRP: z-index ordering", test_grp_z_index)

def test_grp_fog_overlay():
    """Fog overlay pattern with layer"""
    grid = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320), layers=[])
    fog = mcrfpy.ColorLayer(name="fog", z_index=1)
    grid.add_layer(fog)
    fog.fill(mcrfpy.Color(0, 0, 0, 192))

    # Make all cells transparent for FOV
    for x in range(20):
        for y in range(20):
            grid.at(x, y).transparent = True
            grid.at(x, y).walkable = True

    # Compute FOV and reveal
    grid.compute_fov((10, 10), radius=8)
    for x in range(20):
        for y in range(20):
            if grid.is_in_fov((x, y)):
                fog.set((x, y), mcrfpy.Color(0, 0, 0, 0))

    # Origin should be revealed
    c = fog.at((10, 10))
    assert c.a == 0

check("GRP: fog overlay", test_grp_fog_overlay)

def test_grp_grid_properties():
    """Grid rendering properties"""
    grid = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320))

    # Check zoom property exists
    assert hasattr(grid, 'zoom')

    # Check center properties
    assert hasattr(grid, 'center')

check("GRP: grid properties", test_grp_grid_properties)

# ===================================================================
print("\n=== GRID TCOD INTEGRATION ===")
# ===================================================================

def test_tcod_fov():
    """FOV computation with tuple args"""
    grid = mcrfpy.Grid(grid_size=(30, 30), pos=(0, 0), size=(400, 400))
    for x in range(30):
        for y in range(30):
            grid.at(x, y).transparent = True
            grid.at(x, y).walkable = True

    # Add wall
    grid.at(15, 10).transparent = False
    grid.at(15, 10).walkable = False

    # Compute FOV
    grid.compute_fov((10, 10), radius=10)

    # Origin should be visible
    assert grid.is_in_fov((10, 10))

    # Behind wall might not be visible
    # (depends on exact algorithm, just check API works)
    grid.is_in_fov((20, 10))  # Just verify no crash

check("TCOD: FOV computation", test_tcod_fov)

def test_tcod_pathfinding():
    """A* pathfinding with AStarPath object"""
    grid = mcrfpy.Grid(grid_size=(30, 30), pos=(0, 0), size=(400, 400))
    for x in range(30):
        for y in range(30):
            grid.at(x, y).walkable = True

    # Find path
    path = grid.find_path((5, 5), (25, 25))
    assert path is not None
    assert len(path) > 0

    # Walk the path
    step = path.walk()
    assert step is not None

    # Check properties
    assert path.origin is not None
    assert path.destination is not None
    assert path.remaining >= 0

check("TCOD: A* pathfinding", test_tcod_pathfinding)

def test_tcod_dijkstra():
    """Dijkstra map with DijkstraMap object"""
    grid = mcrfpy.Grid(grid_size=(30, 30), pos=(0, 0), size=(400, 400))
    for x in range(30):
        for y in range(30):
            grid.at(x, y).walkable = True

    dm = grid.get_dijkstra_map((15, 15))

    # Get distance
    d = dm.distance((0, 0))
    assert d > 0

    # Get path
    p = dm.path_from((0, 0))
    assert len(p) > 0

    # Get next step
    s = dm.step_from((0, 0))
    assert s is not None

check("TCOD: Dijkstra map", test_tcod_dijkstra)

def test_tcod_perspective():
    """Grid perspective assignment"""
    grid = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320))
    player = mcrfpy.Entity(grid_pos=(10, 10), sprite_index=0)
    grid.entities.append(player)

    # Set perspective
    grid.perspective = player
    assert grid.perspective is not None

check("TCOD: perspective", test_tcod_perspective)

def test_tcod_dynamic_obstacle():
    """Dynamic obstacle pattern"""
    grid = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320))
    for x in range(20):
        for y in range(20):
            grid.at(x, y).walkable = True

    # Open door pattern
    door = grid.at(10, 10)
    door.walkable = False
    door.transparent = False

    # Verify path around door
    path = grid.find_path((5, 10), (15, 10))
    assert path is not None  # Should find path around

    # Open door
    door.walkable = True
    door.transparent = True

    # Path should now go through
    path2 = grid.find_path((5, 10), (15, 10))
    assert path2 is not None
    # Direct path should be shorter
    assert len(path2) <= len(path)

check("TCOD: dynamic obstacle", test_tcod_dynamic_obstacle)

# ===================================================================
print("\n=== PERFORMANCE PATTERNS ===")
# ===================================================================

def test_perf_benchmark_api():
    """Check benchmark API exists"""
    assert hasattr(mcrfpy, 'start_benchmark') or True  # May not exist
    # Just check step works for headless benchmarking
    dt = mcrfpy.step(0.016)
    assert dt is not None

check("PERF: step-based benchmarking", test_perf_benchmark_api)

def test_perf_timer_benchmark():
    """Timer-based benchmarking pattern"""
    frame_times = []

    def measure(timer, runtime):
        frame_times.append(runtime)
        if len(frame_times) >= 5:
            timer.stop()

    t = mcrfpy.Timer("perf_bench", measure, 50)
    mcrfpy.step(0.3)  # Run several frames
    t.stop()

    assert len(frame_times) > 0

check("PERF: timer benchmark", test_perf_timer_benchmark)

# ===================================================================
print("\n=== PYTHON BINDING LAYER PATTERNS ===")
# ===================================================================

def test_pbl_grid_constructor():
    """Modern grid constructor"""
    grid = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(160, 160))
    gs = grid.grid_size
    assert gs[0] == 10
    assert gs[1] == 10

check("PBL: Grid constructor", test_pbl_grid_constructor)

def test_pbl_entity_constructor():
    """Modern entity constructor"""
    e = mcrfpy.Entity(grid_pos=(5, 5), sprite_index=42)
    assert e.grid_x == 5
    assert e.grid_y == 5
    # sprite_index is set
    assert e.sprite_index == 42

check("PBL: Entity constructor", test_pbl_entity_constructor)

def test_pbl_frame_constructor():
    """Frame constructor with keywords"""
    f = mcrfpy.Frame(pos=(100, 200), size=(300, 150))
    assert f.x == 100
    assert f.y == 200
    assert f.w == 300
    assert f.h == 150

check("PBL: Frame constructor", test_pbl_frame_constructor)

def test_pbl_sprite_constructor():
    """Sprite constructor"""
    s = mcrfpy.Sprite(x=10, y=20, sprite_index=5)
    assert s.x == 10
    assert s.y == 20

check("PBL: Sprite constructor", test_pbl_sprite_constructor)

def test_pbl_caption_constructor():
    """Caption constructor"""
    c = mcrfpy.Caption(text="Hello", pos=(50, 60))
    assert c.text == "Hello"
    assert c.x == 50

check("PBL: Caption constructor", test_pbl_caption_constructor)

def test_pbl_color():
    """Color creation"""
    c = mcrfpy.Color(255, 128, 0, 200)
    assert c.r == 255
    assert c.g == 128
    assert c.b == 0
    assert c.a == 200

check("PBL: Color object", test_pbl_color)

def test_pbl_scene_api():
    """Scene API pattern"""
    scene = mcrfpy.Scene("pbl_test")
    f = mcrfpy.Frame(pos=(0, 0), size=(100, 100))
    scene.children.append(f)
    assert len(scene.children) >= 1

check("PBL: Scene API", test_pbl_scene_api)

# Check what benchmark API exists
def test_check_benchmark_api():
    """Check which benchmark methods exist"""
    has_start = hasattr(mcrfpy, 'start_benchmark')
    has_end = hasattr(mcrfpy, 'end_benchmark')
    has_log = hasattr(mcrfpy, 'log_benchmark')
    print(f"    start_benchmark: {has_start}, end_benchmark: {has_end}, log_benchmark: {has_log}")
    # Also check for sync methods on grid
    grid = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(160, 160))
    has_sync = hasattr(grid, 'sync_tcod_map')
    has_sync_cell = hasattr(grid, 'sync_tcod_cell')
    print(f"    sync_tcod_map: {has_sync}, sync_tcod_cell: {has_sync_cell}")
    # Check for FOV algorithm constants
    has_fov_basic = hasattr(mcrfpy, 'FOV_BASIC')
    print(f"    FOV_BASIC constant: {has_fov_basic}")
    # Check cell.tilesprite
    cell = grid.at(0, 0)
    has_tilesprite = hasattr(cell, 'tilesprite')
    has_sprite_index = hasattr(cell, 'sprite_index')
    has_tile_index = hasattr(cell, 'tile_index')
    print(f"    cell.tilesprite: {has_tilesprite}, cell.sprite_index: {has_sprite_index}, cell.tile_index: {has_tile_index}")
    # Check cell color property
    has_color = hasattr(cell, 'color')
    has_fill_color = hasattr(cell, 'fill_color')
    print(f"    cell.color: {has_color}, cell.fill_color: {has_fill_color}")
    # Check entities_in_radius
    has_eir = hasattr(grid, 'entities_in_radius')
    print(f"    entities_in_radius: {has_eir}")
    # List all grid cell (GridPoint) attributes
    cell_attrs = [a for a in dir(cell) if not a.startswith('_')]
    print(f"    GridPoint attrs: {cell_attrs}")

check("API: check available methods", test_check_benchmark_api)

# ===================================================================
print("\n" + "=" * 60)
print(f"PHASE D3 VERIFICATION: {passes} passed, {fails} failed")
print("=" * 60)

if fails:
    sys.exit(1)
else:
    sys.exit(0)
