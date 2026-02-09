"""Verify current API patterns for wiki documentation accuracy."""
import mcrfpy
import sys

errors = []
passes = []

def check(name, fn):
    try:
        fn()
        passes.append(name)
    except Exception as e:
        errors.append(f"{name}: {e}")

# === Scene API ===
def test_scene_creation():
    s = mcrfpy.Scene("wiki_test")
    assert s.name == "wiki_test"
    assert hasattr(s, 'children')
    assert hasattr(s, 'on_key')

check("Scene creation", test_scene_creation)

def test_scene_activate():
    s = mcrfpy.Scene("wiki_test2")
    s.activate()
    # Also test current_scene assignment
    s2 = mcrfpy.Scene("wiki_test3")
    mcrfpy.current_scene = s2

check("Scene activate / current_scene", test_scene_activate)

def test_scene_on_key():
    s = mcrfpy.Scene("key_test")
    def handler(key, action):
        pass
    s.on_key = handler

check("Scene on_key setter", test_scene_on_key)

# === Enum types ===
def test_key_enum():
    assert hasattr(mcrfpy, 'Key')
    assert hasattr(mcrfpy.Key, 'W')
    assert hasattr(mcrfpy.Key, 'ESCAPE')
    assert hasattr(mcrfpy.Key, 'SPACE')
    assert hasattr(mcrfpy.Key, 'UP')

check("Key enum", test_key_enum)

def test_mousebutton_enum():
    assert hasattr(mcrfpy, 'MouseButton')
    assert hasattr(mcrfpy.MouseButton, 'LEFT')
    assert hasattr(mcrfpy.MouseButton, 'RIGHT')
    assert hasattr(mcrfpy.MouseButton, 'MIDDLE')

check("MouseButton enum", test_mousebutton_enum)

def test_inputstate_enum():
    assert hasattr(mcrfpy, 'InputState')
    assert hasattr(mcrfpy.InputState, 'PRESSED')
    assert hasattr(mcrfpy.InputState, 'RELEASED')

check("InputState enum", test_inputstate_enum)

def test_easing_enum():
    assert hasattr(mcrfpy, 'Easing')
    assert hasattr(mcrfpy.Easing, 'LINEAR')
    assert hasattr(mcrfpy.Easing, 'EASE_IN')
    assert hasattr(mcrfpy.Easing, 'EASE_OUT')
    assert hasattr(mcrfpy.Easing, 'EASE_IN_OUT')
    assert hasattr(mcrfpy.Easing, 'EASE_IN_OUT_CUBIC')
    assert hasattr(mcrfpy.Easing, 'EASE_OUT_BOUNCE')

check("Easing enum", test_easing_enum)

# === Frame construction ===
def test_frame_keyword():
    f = mcrfpy.Frame(x=10, y=20, w=100, h=50)
    assert f.x == 10
    assert f.y == 20
    assert f.w == 100
    assert f.h == 50

check("Frame keyword args", test_frame_keyword)

def test_frame_pos_size():
    # Check if pos= and size= work as tuple kwargs
    try:
        f = mcrfpy.Frame(pos=(10, 20), size=(100, 50))
        passes.append("Frame pos/size tuple kwargs")
    except TypeError:
        # May not support pos= directly
        errors.append("Frame pos/size tuple kwargs: not supported")

test_frame_pos_size()

# === Grid construction ===
def test_grid_creation():
    g = mcrfpy.Grid(grid_size=(20, 15), pos=(0, 0), size=(320, 240))
    assert g.grid_w == 20
    assert g.grid_h == 15

check("Grid keyword creation", test_grid_creation)

# === Grid Layer API ===
def test_grid_layer_standalone():
    """Test current layer creation pattern"""
    g = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(160, 160))
    # Try standalone TileLayer creation
    has_tilelayer = hasattr(mcrfpy, 'TileLayer')
    has_colorlayer = hasattr(mcrfpy, 'ColorLayer')
    if has_tilelayer:
        try:
            tl = mcrfpy.TileLayer()
            passes.append("TileLayer standalone creation")
        except Exception as e:
            errors.append(f"TileLayer standalone creation: {e}")
    else:
        errors.append("TileLayer type not found in mcrfpy module")

    if has_colorlayer:
        try:
            cl = mcrfpy.ColorLayer()
            passes.append("ColorLayer standalone creation")
        except Exception as e:
            errors.append(f"ColorLayer standalone creation: {e}")
    else:
        errors.append("ColorLayer type not found in mcrfpy module")

test_grid_layer_standalone()

def test_grid_add_layer_old():
    """Test old-style grid.add_layer("tile", ...)"""
    g = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(160, 160))
    try:
        layer = g.add_layer("color", z_index=-1)
        passes.append("grid.add_layer('color', z_index=...) old-style")
    except Exception as e:
        errors.append(f"grid.add_layer('color', z_index=...) old-style: {e}")

test_grid_add_layer_old()

def test_grid_add_layer_new():
    """Test new-style grid.add_layer(layer_object)"""
    g = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(160, 160))
    if hasattr(mcrfpy, 'ColorLayer'):
        try:
            cl = mcrfpy.ColorLayer()
            g.add_layer(cl)
            passes.append("grid.add_layer(ColorLayer()) new-style")
        except Exception as e:
            errors.append(f"grid.add_layer(ColorLayer()) new-style: {e}")

test_grid_add_layer_new()

# === Grid cell access ===
def test_grid_at():
    g = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(160, 160))
    pt = g.at(5, 5)
    assert hasattr(pt, 'walkable')
    assert hasattr(pt, 'transparent')

check("Grid.at() cell access", test_grid_at)

# === Grid camera ===
def test_grid_center():
    g = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(160, 160))
    # Test center property
    g.center = (80, 80)
    # Test center_camera method
    if hasattr(g, 'center_camera'):
        g.center_camera((5, 5))
        passes.append("Grid.center_camera() method")
    else:
        errors.append("Grid.center_camera() not found")

check("Grid.center property", test_grid_center)

# === Grid callbacks ===
def test_grid_callbacks():
    g = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(160, 160))
    # click callback: (pos, button, action)
    g.on_click = lambda pos, btn, action: None
    # hover callbacks: (pos) only
    g.on_enter = lambda pos: None
    g.on_exit = lambda pos: None
    # cell callbacks
    g.on_cell_click = lambda cell_pos, btn, action: None
    g.on_cell_enter = lambda cell_pos: None
    g.on_cell_exit = lambda cell_pos: None

check("Grid callback setters", test_grid_callbacks)

# === Frame callbacks ===
def test_frame_callbacks():
    f = mcrfpy.Frame(x=0, y=0, w=100, h=100)
    f.on_click = lambda pos, btn, action: None
    f.on_enter = lambda pos: None
    f.on_exit = lambda pos: None
    f.on_move = lambda pos: None

check("Frame callback setters", test_frame_callbacks)

# === Entity ===
def test_entity_creation():
    e = mcrfpy.Entity(grid_x=5, grid_y=10, sprite_index=0)
    assert e.grid_x == 5
    assert e.grid_y == 10

check("Entity keyword creation", test_entity_creation)

def test_entity_pos_kwarg():
    try:
        e = mcrfpy.Entity(pos=(5, 10), sprite_index=0)
        passes.append("Entity pos= tuple kwarg")
    except TypeError:
        errors.append("Entity pos= tuple kwarg: not supported")

test_entity_pos_kwarg()

def test_entity_grid_relationship():
    g = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320))
    e = mcrfpy.Entity(grid_x=5, grid_y=5, sprite_index=0)
    g.entities.append(e)
    assert e.grid is not None

check("Entity-Grid relationship", test_entity_grid_relationship)

def test_entity_die():
    g = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320))
    e = mcrfpy.Entity(grid_x=5, grid_y=5, sprite_index=0)
    g.entities.append(e)
    e.die()

check("Entity.die()", test_entity_die)

# === Timer ===
def test_timer_object():
    t = mcrfpy.Timer("wiki_test_timer", lambda dt: None, 1000)
    assert hasattr(t, 'pause')
    assert hasattr(t, 'resume')
    assert hasattr(t, 'cancel')
    t.cancel()

check("Timer object creation", test_timer_object)

# === Animation - .animate() method ===
def test_animate_method():
    f = mcrfpy.Frame(x=0, y=0, w=100, h=100)
    f.animate("x", 200.0, 1.0, mcrfpy.Easing.EASE_IN_OUT)

check("frame.animate() method", test_animate_method)

def test_animate_with_callback():
    f = mcrfpy.Frame(x=0, y=0, w=100, h=100)
    def cb(target, prop, value):
        pass
    f.animate("x", 200.0, 1.0, mcrfpy.Easing.LINEAR, callback=cb)

check("frame.animate() with callback", test_animate_with_callback)

def test_animate_entity():
    g = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320))
    e = mcrfpy.Entity(grid_x=5, grid_y=5, sprite_index=0)
    g.entities.append(e)
    e.animate("grid_x", 10.0, 0.5, mcrfpy.Easing.EASE_OUT_QUAD)

check("entity.animate() method", test_animate_entity)

# === Animation - old-style (verify it still works or is removed) ===
def test_animation_object():
    try:
        a = mcrfpy.Animation("x", 200.0, 1.0, mcrfpy.Easing.LINEAR)
        passes.append("Animation() object creation")
        # Try .start()
        f = mcrfpy.Frame(x=0, y=0, w=100, h=100)
        a.start(f)
        passes.append("Animation.start() method")
    except Exception as e:
        errors.append(f"Animation() object: {e}")

test_animation_object()

# === Grid spatial queries ===
def test_entities_in_radius():
    g = mcrfpy.Grid(grid_size=(50, 50), pos=(0, 0), size=(400, 400))
    for i in range(5):
        e = mcrfpy.Entity(grid_x=10+i, grid_y=10, sprite_index=0)
        g.entities.append(e)

    nearby = g.entities_in_radius((10, 10), 5.0)
    assert len(nearby) > 0

check("Grid.entities_in_radius()", test_entities_in_radius)

# === FOV ===
def test_fov():
    assert hasattr(mcrfpy, 'FOV')
    assert hasattr(mcrfpy.FOV, 'SHADOW')
    assert hasattr(mcrfpy.FOV, 'BASIC')

check("FOV enum", test_fov)

def test_grid_fov():
    g = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320))
    # Make cells transparent
    for x in range(20):
        for y in range(20):
            pt = g.at(x, y)
            pt.walkable = True
            pt.transparent = True
    g.compute_fov((10, 10), radius=8)
    assert g.is_in_fov((10, 10))

check("Grid FOV compute/query", test_grid_fov)

# === Pathfinding ===
def test_pathfinding():
    g = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320))
    for x in range(20):
        for y in range(20):
            g.at(x, y).walkable = True
    path = g.find_path((0, 0), (5, 5))
    assert path is not None

check("Grid.find_path()", test_pathfinding)

# === Caption ===
def test_caption():
    c = mcrfpy.Caption(text="Hello", x=50, y=50)
    assert c.text == "Hello"

check("Caption creation", test_caption)

# === Sprite ===
def test_sprite():
    s = mcrfpy.Sprite(x=0, y=0, sprite_index=0)
    assert s.x == 0

check("Sprite creation", test_sprite)

# === Geometry primitives ===
def test_line():
    if hasattr(mcrfpy, 'Line'):
        l = mcrfpy.Line(start=(0,0), end=(100,100))
        passes.append("Line creation")
    else:
        errors.append("Line type not in mcrfpy")

test_line()

def test_circle():
    if hasattr(mcrfpy, 'Circle'):
        c = mcrfpy.Circle(radius=50)
        passes.append("Circle creation")
    else:
        errors.append("Circle type not in mcrfpy")

test_circle()

def test_arc():
    if hasattr(mcrfpy, 'Arc'):
        a = mcrfpy.Arc(radius=50, start_angle=0, end_angle=90)
        passes.append("Arc creation")
    else:
        errors.append("Arc type not in mcrfpy")

test_arc()

# === Grid perspective ===
def test_grid_perspective():
    g = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320))
    e = mcrfpy.Entity(grid_x=10, grid_y=10, sprite_index=0)
    g.entities.append(e)
    g.perspective = e
    assert g.perspective is not None

check("Grid.perspective", test_grid_perspective)

# === Color ===
def test_color():
    c = mcrfpy.Color(255, 0, 0)
    assert c.r == 255

check("Color creation", test_color)

# === Window ===
def test_window():
    if hasattr(mcrfpy, 'Window'):
        w = mcrfpy.Window.get()
        passes.append("Window.get()")
    else:
        errors.append("Window type not in mcrfpy")

test_window()

# === Check for deprecated functions still present ===
def test_deprecated_functions():
    """Check which deprecated functions still exist"""
    if hasattr(mcrfpy, 'keypressScene'):
        passes.append("keypressScene still exists (deprecated)")
    if hasattr(mcrfpy, 'setTimer'):
        passes.append("setTimer still exists (deprecated)")
    if hasattr(mcrfpy, 'delTimer'):
        passes.append("delTimer still exists (deprecated)")
    if hasattr(mcrfpy, 'createScene'):
        passes.append("createScene still exists (deprecated)")
    if hasattr(mcrfpy, 'sceneUI'):
        passes.append("sceneUI still exists (deprecated)")
    if hasattr(mcrfpy, 'setScene'):
        passes.append("setScene still exists (deprecated)")

test_deprecated_functions()

# === Check for layer API: layers property ===
def test_grid_layers_property():
    g = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(160, 160))
    layers = g.layers
    assert layers is not None

check("Grid.layers property", test_grid_layers_property)

# === Check entities_in_radius parameter format ===
def test_eir_tuple_vs_args():
    g = mcrfpy.Grid(grid_size=(50, 50), pos=(0, 0), size=(400, 400))
    e = mcrfpy.Entity(grid_x=10, grid_y=10, sprite_index=0)
    g.entities.append(e)

    # Try tuple form
    try:
        r = g.entities_in_radius((10, 10), 5.0)
        passes.append("entities_in_radius((x,y), r) tuple form")
    except:
        errors.append("entities_in_radius((x,y), r) tuple form failed")

    # Try separate args form
    try:
        r = g.entities_in_radius(10, 10, 5.0)
        passes.append("entities_in_radius(x, y, r) separate args")
    except:
        errors.append("entities_in_radius(x, y, r) separate args failed")

test_eir_tuple_vs_args()

# === DijkstraMap ===
def test_dijkstra():
    g = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320))
    for x in range(20):
        for y in range(20):
            g.at(x, y).walkable = True

    if hasattr(g, 'get_dijkstra_map'):
        dm = g.get_dijkstra_map((5, 5))
        passes.append("Grid.get_dijkstra_map()")
    else:
        errors.append("Grid.get_dijkstra_map() not found")

test_dijkstra()

# === Check animate properties list ===
def test_animate_properties():
    f = mcrfpy.Frame(x=0, y=0, w=100, h=100)
    working_props = []
    failing_props = []
    test_props = ['x', 'y', 'w', 'h', 'opacity', 'outline',
                  'fill_color', 'outline_color', 'z_index']
    for prop in test_props:
        try:
            f.animate(prop, 1.0, 0.01, mcrfpy.Easing.LINEAR)
            working_props.append(prop)
        except Exception as e:
            failing_props.append(f"{prop}: {e}")

    passes.append(f"Animatable Frame properties: {', '.join(working_props)}")
    if failing_props:
        errors.append(f"Non-animatable Frame properties: {'; '.join(failing_props)}")

test_animate_properties()

# === Print results ===
print("=" * 60)
print(f"WIKI API VERIFICATION: {len(passes)} passed, {len(errors)} failed")
print("=" * 60)
print("\nPASSED:")
for p in passes:
    print(f"  [OK] {p}")
print("\nFAILED:")
for e in errors:
    print(f"  [FAIL] {e}")
print()

if errors:
    sys.exit(1)
else:
    sys.exit(0)
