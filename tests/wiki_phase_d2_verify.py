"""Verify code snippets from Phase D batch 2 wiki updates."""
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
print("=== AI AND PATHFINDING ===")
# ===================================================================

def test_aip_fov_basic():
    """Basic FOV setup"""
    grid = mcrfpy.Grid(grid_size=(50, 50), pos=(0, 0), size=(400, 400))
    for x in range(50):
        for y in range(50):
            grid.at(x, y).transparent = True
            grid.at(x, y).walkable = True
    # Set some walls
    grid.at(10, 10).transparent = False
    grid.at(10, 10).walkable = False
    # Compute FOV
    grid.compute_fov((25, 25), radius=10)
    assert grid.is_in_fov((25, 25))  # Origin visible
    assert not grid.is_in_fov((0, 0))  # Far away not visible

check("AIP: basic FOV", test_aip_fov_basic)

def test_aip_perspective():
    """Perspective system"""
    grid = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320))
    player = mcrfpy.Entity(grid_pos=(10, 10), sprite_index=0)
    grid.entities.append(player)
    grid.perspective = player
    assert grid.perspective is not None

check("AIP: perspective", test_aip_perspective)

def test_aip_fog_of_war():
    """Fog of war pattern"""
    grid = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320), layers=[])
    fog = mcrfpy.ColorLayer(name="fog", z_index=1)
    grid.add_layer(fog)
    fog.fill(mcrfpy.Color(0, 0, 0, 255))

    for x in range(20):
        for y in range(20):
            grid.at(x, y).transparent = True
            grid.at(x, y).walkable = True

    player = mcrfpy.Entity(grid_pos=(10, 10), sprite_index=0)
    grid.entities.append(player)

    # Compute FOV and reveal fog
    grid.compute_fov((10, 10), radius=8)
    for x in range(20):
        for y in range(20):
            if grid.is_in_fov((x, y)):
                fog.set((x, y), mcrfpy.Color(0, 0, 0, 0))

    # Check fog revealed at origin
    c = fog.at((10, 10))
    assert c.a == 0  # Revealed

check("AIP: fog of war", test_aip_fog_of_war)

def test_aip_astar():
    """A* pathfinding via grid"""
    grid = mcrfpy.Grid(grid_size=(30, 30), pos=(0, 0), size=(400, 400))
    for x in range(30):
        for y in range(30):
            grid.at(x, y).walkable = True

    path = grid.find_path((10, 10), (20, 20))
    assert path is not None
    assert len(path) > 0
    step = path.walk()
    assert step is not None
    assert path.remaining >= 0
    assert path.origin is not None
    assert path.destination is not None

check("AIP: A* pathfinding", test_aip_astar)

def test_aip_dijkstra():
    """Dijkstra map"""
    grid = mcrfpy.Grid(grid_size=(30, 30), pos=(0, 0), size=(400, 400))
    for x in range(30):
        for y in range(30):
            grid.at(x, y).walkable = True

    dm = grid.get_dijkstra_map((15, 15))
    d = dm.distance((0, 0))
    assert d > 0
    p = dm.path_from((0, 0))
    assert len(p) > 0
    s = dm.step_from((0, 0))
    assert s is not None

check("AIP: Dijkstra map", test_aip_dijkstra)

def test_aip_chase_pattern():
    """Enemy chase AI pattern"""
    grid = mcrfpy.Grid(grid_size=(30, 30), pos=(0, 0), size=(400, 400))
    for x in range(30):
        for y in range(30):
            grid.at(x, y).walkable = True

    player = mcrfpy.Entity(grid_pos=(15, 15), sprite_index=0, name="player")
    enemy = mcrfpy.Entity(grid_pos=(5, 5), sprite_index=1, name="enemy")
    grid.entities.append(player)
    grid.entities.append(enemy)

    # Chase: use dijkstra from player, step enemy toward player
    dm = grid.get_dijkstra_map((int(player.grid_x), int(player.grid_y)))
    next_step = dm.step_from((int(enemy.grid_x), int(enemy.grid_y)))
    assert next_step is not None
    # Move enemy
    enemy.grid_x = int(next_step.x)
    enemy.grid_y = int(next_step.y)

check("AIP: chase pattern", test_aip_chase_pattern)

def test_aip_wasd_fov():
    """WASD + FOV update pattern"""
    scene = mcrfpy.Scene("aip_wasd")
    grid = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320))
    for x in range(20):
        for y in range(20):
            grid.at(x, y).walkable = True
            grid.at(x, y).transparent = True
    scene.children.append(grid)

    player = mcrfpy.Entity(grid_pos=(10, 10), sprite_index=0)
    grid.entities.append(player)
    grid.perspective = player

    def on_player_move(dx, dy):
        new_x = int(player.grid_x + dx)
        new_y = int(player.grid_y + dy)
        point = grid.at(new_x, new_y)
        if point and point.walkable:
            player.grid_x = new_x
            player.grid_y = new_y
            grid.compute_fov((new_x, new_y), radius=10)

    on_player_move(1, 0)
    assert player.grid_x == 11

    move_map = {
        mcrfpy.Key.W: (0, -1),
        mcrfpy.Key.A: (-1, 0),
        mcrfpy.Key.S: (0, 1),
        mcrfpy.Key.D: (1, 0),
    }

    def handle_key(key, action):
        if action != mcrfpy.InputState.PRESSED:
            return
        if key in move_map:
            dx, dy = move_map[key]
            on_player_move(dx, dy)

    scene.on_key = handle_key

check("AIP: WASD + FOV pattern", test_aip_wasd_fov)

def test_aip_spatial_query():
    """Spatial query for AI aggro"""
    grid = mcrfpy.Grid(grid_size=(50, 50), pos=(0, 0), size=(400, 400))
    for x in range(50):
        for y in range(50):
            grid.at(x, y).walkable = True

    player = mcrfpy.Entity(grid_pos=(10, 10), sprite_index=0, name="p")
    enemy = mcrfpy.Entity(grid_pos=(12, 10), sprite_index=1, name="e")
    grid.entities.append(player)
    grid.entities.append(enemy)

    # Check aggro range
    nearby = grid.entities_in_radius((int(enemy.grid_x), int(enemy.grid_y)), 5.0)
    assert len(nearby) >= 2  # enemy and player both in range

check("AIP: spatial query for aggro", test_aip_spatial_query)

# ===================================================================
print("\n=== WRITING TESTS ===")
# ===================================================================

def test_wt_direct_execution():
    """Direct execution test template"""
    scene = mcrfpy.Scene("wt_test")
    frame = mcrfpy.Frame(pos=(100, 100), size=(200, 150))
    frame.fill_color = mcrfpy.Color(255, 0, 0)
    scene.children.append(frame)
    assert frame.x == 100
    assert frame.w == 200

check("WT: direct execution template", test_wt_direct_execution)

def test_wt_property_roundtrip():
    """Property round-trip test pattern"""
    obj = mcrfpy.Frame(pos=(0, 0), size=(100, 100))
    test_values = [0, 50, 100, 255, 127]
    for value in test_values:
        obj.x = value
        assert obj.x == value, f"Failed for {value}"

check("WT: property round-trip", test_wt_property_roundtrip)

def test_wt_exception_testing():
    """Exception testing pattern"""
    grid = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(160, 160))
    try:
        grid.at(-1, -1)
        assert False, "Should have raised"
    except Exception:
        pass  # Expected

check("WT: exception testing", test_wt_exception_testing)

def test_wt_grid_test_pattern():
    """Grid test pattern"""
    grid = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(160, 160))
    grid.at(5, 5).walkable = True
    assert grid.at(5, 5).walkable == True

check("WT: grid test pattern", test_wt_grid_test_pattern)

def test_wt_click_callback_setup():
    """Click callback test setup"""
    clicks_received = []
    scene = mcrfpy.Scene("wt_click")
    frame = mcrfpy.Frame(pos=(100, 100), size=(200, 150),
                          fill_color=mcrfpy.Color(0, 255, 0))
    def on_click(pos, button, action):
        clicks_received.append((pos, button, action))
    frame.on_click = on_click
    scene.children.append(frame)

check("WT: click callback setup", test_wt_click_callback_setup)

def test_wt_timer_pattern():
    """Timer creation pattern"""
    t = mcrfpy.Timer("wt_test_timer", lambda timer, runtime: None, 100)
    assert t is not None
    t.stop()

check("WT: timer creation", test_wt_timer_pattern)

# ===================================================================
print("\n=== HEADLESS MODE ===")
# ===================================================================

def test_hm_step():
    """Step function"""
    dt = mcrfpy.step(0.1)
    # In headless mode, returns the dt
    assert dt is not None

check("HM: step()", test_hm_step)

def test_hm_timer_with_step():
    """Timer fires with step"""
    fired = [False]
    def on_timer(timer, runtime):
        fired[0] = True
    t = mcrfpy.Timer("hm_test", on_timer, 500)
    mcrfpy.step(0.6)  # 600ms - timer should fire
    assert fired[0], "Timer should have fired"
    t.stop()

check("HM: timer with step", test_hm_timer_with_step)

def test_hm_animation_with_step():
    """Animation updates with step"""
    frame = mcrfpy.Frame(pos=(0, 0), size=(100, 100))
    frame.animate("x", 500.0, 2.0, mcrfpy.Easing.EASE_IN_OUT)
    mcrfpy.step(1.0)
    # Should be roughly halfway
    assert frame.x > 0  # At least started moving

check("HM: animation with step", test_hm_animation_with_step)

def test_hm_scene_setup():
    """Scene setup in headless"""
    scene = mcrfpy.Scene("hm_test")
    frame = mcrfpy.Frame(pos=(50, 50), size=(100, 100))
    scene.children.append(frame)
    mcrfpy.current_scene = scene
    assert frame.x == 50

check("HM: scene setup headless", test_hm_scene_setup)

# ===================================================================
print("\n=== UI COMPONENT HIERARCHY ===")
# ===================================================================

def test_uch_parent_child():
    """Parent-child coordinates"""
    frame = mcrfpy.Frame(pos=(100, 100), size=(200, 150))
    label = mcrfpy.Caption(text="Hello", pos=(10, 10))
    frame.children.append(label)
    assert label.x == 10  # Relative to parent

check("UCH: parent-child coords", test_uch_parent_child)

def test_uch_all_types():
    """All drawable types exist"""
    f = mcrfpy.Frame(pos=(0, 0), size=(100, 100))
    c = mcrfpy.Caption(text="test", pos=(0, 0))
    s = mcrfpy.Sprite(x=0, y=0, sprite_index=0)
    g = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(160, 160))
    e = mcrfpy.Entity(grid_pos=(0, 0), sprite_index=0)
    assert hasattr(mcrfpy, 'Arc')
    assert hasattr(mcrfpy, 'Circle')
    assert hasattr(mcrfpy, 'Line')

check("UCH: all drawable types", test_uch_all_types)

def test_uch_common_properties():
    """Common UIDrawable properties"""
    f = mcrfpy.Frame(pos=(50, 60), size=(100, 100))
    assert f.x == 50
    assert f.y == 60
    assert f.w == 100
    assert f.h == 100
    f.visible = False
    assert f.visible == False
    f.visible = True
    f.opacity = 0.5
    assert f.opacity == 0.5
    f.z_index = 42
    assert f.z_index == 42

check("UCH: common properties", test_uch_common_properties)

def test_uch_click_callbacks():
    """Callback signatures"""
    f = mcrfpy.Frame(pos=(0, 0), size=(100, 100))
    # on_click: (pos: Vector, button: MouseButton, action: InputState)
    f.on_click = lambda pos, button, action: None
    # on_enter/on_exit: (pos: Vector)
    f.on_enter = lambda pos: None
    f.on_exit = lambda pos: None
    # on_move: (pos: Vector)
    f.on_move = lambda pos: None

check("UCH: callback signatures", test_uch_click_callbacks)

def test_uch_collection():
    """UICollection operations"""
    scene = mcrfpy.Scene("uch_coll")
    f1 = mcrfpy.Frame(pos=(0, 0), size=(10, 10))
    f2 = mcrfpy.Caption(text="test", pos=(0, 0))
    f3 = mcrfpy.Sprite(x=0, y=0, sprite_index=0)
    scene.children.append(f1)
    scene.children.append(f2)
    scene.children.append(f3)
    assert len(scene.children) >= 3
    # Can iterate
    for item in scene.children:
        pass

check("UCH: UICollection", test_uch_collection)

def test_uch_entity_collection():
    """UIEntityCollection operations"""
    grid = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320))
    e1 = mcrfpy.Entity(grid_pos=(1, 1), sprite_index=0)
    e2 = mcrfpy.Entity(grid_pos=(2, 2), sprite_index=0)
    grid.entities.append(e1)
    grid.entities.append(e2)
    assert len(grid.entities) == 2
    grid.entities.remove(e1)
    assert len(grid.entities) == 1

check("UCH: EntityCollection", test_uch_entity_collection)

def test_uch_type_preservation():
    """Type preserved through collections"""
    scene = mcrfpy.Scene("uch_types")
    sprite = mcrfpy.Sprite(x=10, y=10, sprite_index=0)
    scene.children.append(sprite)
    retrieved = scene.children[0]
    assert type(retrieved).__name__ == "Sprite"

check("UCH: type preservation", test_uch_type_preservation)

# ===================================================================
print("\n" + "=" * 60)
print(f"PHASE D2 VERIFICATION: {passes} passed, {fails} failed")
print("=" * 60)

if fails:
    sys.exit(1)
else:
    sys.exit(0)
