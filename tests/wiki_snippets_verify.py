"""Verify all code snippets from updated wiki pages run correctly."""
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
print("=== INPUT AND EVENTS WIKI ===")
# ===================================================================

def test_keyboard_handler():
    scene = mcrfpy.Scene("ie_test1")
    def handle_key(key, action):
        if key == mcrfpy.Key.ESCAPE and action == mcrfpy.InputState.PRESSED:
            pass
        elif key == mcrfpy.Key.W and action == mcrfpy.InputState.PRESSED:
            pass
    scene.on_key = handle_key
    mcrfpy.current_scene = scene

check("IE: keyboard handler with enums", test_keyboard_handler)

def test_key_enum_members():
    # Key.A has int value 0, so use hasattr or 'is not None' instead of truthiness
    assert hasattr(mcrfpy.Key, 'A')
    assert hasattr(mcrfpy.Key, 'Z')
    assert hasattr(mcrfpy.Key, 'NUM_0')
    assert hasattr(mcrfpy.Key, 'UP')
    assert hasattr(mcrfpy.Key, 'SPACE')
    assert hasattr(mcrfpy.Key, 'ENTER')
    assert hasattr(mcrfpy.Key, 'ESCAPE')
    assert hasattr(mcrfpy.Key, 'F1')
    assert hasattr(mcrfpy.Key, 'LEFT_SHIFT')

check("IE: Key enum members", test_key_enum_members)

def test_inputstate_legacy():
    assert mcrfpy.InputState.PRESSED == "start"
    assert mcrfpy.InputState.RELEASED == "end"

check("IE: InputState legacy string compat", test_inputstate_legacy)

def test_click_handler():
    frame = mcrfpy.Frame(pos=(100, 100), size=(200, 50))
    def on_frame_click(pos, button, action):
        if button == mcrfpy.MouseButton.LEFT and action == mcrfpy.InputState.PRESSED:
            pass
    frame.on_click = on_frame_click
    frame.on_enter = lambda pos: None
    frame.on_exit = lambda pos: None
    frame.on_move = lambda pos: None

check("IE: click/hover handlers", test_click_handler)

def test_mousebutton_members():
    assert mcrfpy.MouseButton.LEFT is not None
    assert mcrfpy.MouseButton.RIGHT is not None
    assert mcrfpy.MouseButton.MIDDLE is not None

check("IE: MouseButton enum members", test_mousebutton_members)

def test_grid_cell_events():
    grid = mcrfpy.Grid(grid_size=(20, 15), pos=(50, 50), size=(400, 300))
    def on_cell_click(cell_pos, button, action):
        if button == mcrfpy.MouseButton.LEFT and action == mcrfpy.InputState.PRESSED:
            x, y = int(cell_pos.x), int(cell_pos.y)
            point = grid.at(x, y)
    grid.on_cell_click = on_cell_click
    grid.on_cell_enter = lambda cell_pos: None
    grid.on_cell_exit = lambda cell_pos: None

check("IE: grid cell events", test_grid_cell_events)

def test_wasd_pattern():
    scene = mcrfpy.Scene("wasd_test")
    def handle_key(key, action):
        if action != mcrfpy.InputState.PRESSED:
            return
        moves = {
            mcrfpy.Key.W: (0, -1),
            mcrfpy.Key.A: (-1, 0),
            mcrfpy.Key.S: (0, 1),
            mcrfpy.Key.D: (1, 0),
        }
        if key in moves:
            dx, dy = moves[key]
    scene.on_key = handle_key

check("IE: WASD pattern", test_wasd_pattern)

def test_button_widget():
    def make_button(text, x, y, callback):
        btn = mcrfpy.Frame(pos=(x, y), size=(120, 40),
                           fill_color=mcrfpy.Color(60, 60, 80))
        label = mcrfpy.Caption(text=text, x=10, y=8)
        btn.children.append(label)
        def on_click(pos, button, action):
            if button == mcrfpy.MouseButton.LEFT and action == mcrfpy.InputState.PRESSED:
                callback()
        btn.on_click = on_click
        btn.on_enter = lambda pos: setattr(btn, 'fill_color', mcrfpy.Color(80, 80, 110))
        btn.on_exit = lambda pos: setattr(btn, 'fill_color', mcrfpy.Color(60, 60, 80))
        return btn
    btn = make_button("Test", 10, 10, lambda: None)
    assert btn.w == 120

check("IE: button widget pattern", test_button_widget)

def test_scene_switching():
    game_scene = mcrfpy.Scene("sw_game")
    menu_scene = mcrfpy.Scene("sw_menu")
    def game_keys(key, action):
        if key == mcrfpy.Key.ESCAPE and action == mcrfpy.InputState.PRESSED:
            menu_scene.activate()
    def menu_keys(key, action):
        if key == mcrfpy.Key.ESCAPE and action == mcrfpy.InputState.PRESSED:
            game_scene.activate()
    game_scene.on_key = game_keys
    menu_scene.on_key = menu_keys

check("IE: scene switching pattern", test_scene_switching)

# ===================================================================
print("\n=== ANIMATION SYSTEM WIKI ===")
# ===================================================================

def test_animate_basic():
    frame = mcrfpy.Frame(pos=(100, 100), size=(200, 150))
    frame.animate("x", 500.0, 2.0, mcrfpy.Easing.EASE_IN_OUT)
    frame.animate("opacity", 0.5, 1.0, mcrfpy.Easing.EASE_OUT_QUAD)

check("AS: basic .animate()", test_animate_basic)

def test_animate_callback():
    frame = mcrfpy.Frame(pos=(100, 100), size=(200, 150))
    def on_complete(target, prop, value):
        pass
    frame.animate("x", 500.0, 2.0, mcrfpy.Easing.EASE_IN_OUT, callback=on_complete)

check("AS: .animate() with callback", test_animate_callback)

def test_animate_chaining():
    frame = mcrfpy.Frame(pos=(0, 0), size=(100, 100))
    def step2(target, prop, value):
        target.animate("y", 300.0, 1.0, mcrfpy.Easing.EASE_OUT_BOUNCE)
    def step1(target, prop, value):
        target.animate("x", 500.0, 1.0, mcrfpy.Easing.EASE_IN_OUT, callback=step2)
    frame.animate("opacity", 1.0, 0.5, mcrfpy.Easing.EASE_IN, callback=step1)

check("AS: animation chaining", test_animate_chaining)

def test_animate_frame_props():
    f = mcrfpy.Frame(x=0, y=0, w=100, h=100)
    for prop in ['x', 'y', 'w', 'h', 'outline', 'opacity', 'fill_color', 'outline_color']:
        f.animate(prop, 1.0, 0.01, mcrfpy.Easing.LINEAR)

check("AS: all Frame animatable properties", test_animate_frame_props)

def test_animate_caption_props():
    c = mcrfpy.Caption(text="test", x=0, y=0)
    for prop in ['x', 'y', 'opacity', 'outline', 'fill_color', 'outline_color']:
        c.animate(prop, 1.0, 0.01, mcrfpy.Easing.LINEAR)

check("AS: all Caption animatable properties", test_animate_caption_props)

def test_animate_sprite_props():
    s = mcrfpy.Sprite(x=0, y=0, sprite_index=0)
    for prop in ['x', 'y', 'scale', 'sprite_index', 'opacity']:
        s.animate(prop, 1.0, 0.01, mcrfpy.Easing.LINEAR)

check("AS: all Sprite animatable properties", test_animate_sprite_props)

def test_animate_grid_props():
    g = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(160, 160))
    for prop in ['x', 'y', 'w', 'h', 'center_x', 'center_y', 'zoom']:
        g.animate(prop, 1.0, 0.01, mcrfpy.Easing.LINEAR)

check("AS: all Grid animatable properties", test_animate_grid_props)

def test_animate_entity_props():
    g = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320))
    e = mcrfpy.Entity(grid_pos=(5, 5), sprite_index=0)
    g.entities.append(e)
    for prop in ['x', 'y', 'draw_x', 'draw_y', 'sprite_index', 'sprite_scale']:
        e.animate(prop, 5.0, 0.01, mcrfpy.Easing.LINEAR)

check("AS: all Entity animatable properties", test_animate_entity_props)

def test_color_animation():
    f = mcrfpy.Frame(x=0, y=0, w=100, h=100)
    f.animate("fill_color", (255, 0, 0, 255), 1.0, mcrfpy.Easing.EASE_IN)
    f.animate("outline_color", (255, 255, 255, 0), 0.5, mcrfpy.Easing.LINEAR)

check("AS: color animations", test_color_animation)

def test_animation_object():
    anim = mcrfpy.Animation("x", 500.0, 2.0, mcrfpy.Easing.LINEAR)
    f = mcrfpy.Frame(x=0, y=0, w=100, h=100)
    anim.start(f)

check("AS: Animation object (advanced)", test_animation_object)

def test_easing_members():
    easings = ['LINEAR', 'EASE_IN', 'EASE_OUT', 'EASE_IN_OUT',
               'EASE_IN_QUAD', 'EASE_OUT_QUAD', 'EASE_IN_OUT_QUAD',
               'EASE_IN_CUBIC', 'EASE_OUT_CUBIC', 'EASE_IN_OUT_CUBIC',
               'EASE_OUT_BOUNCE', 'EASE_IN_ELASTIC']
    for name in easings:
        assert hasattr(mcrfpy.Easing, name), f"Missing Easing.{name}"

check("AS: Easing enum members", test_easing_members)

# ===================================================================
print("\n=== GRID SYSTEM WIKI ===")
# ===================================================================

def test_grid_basic_creation():
    grid = mcrfpy.Grid(grid_size=(50, 50), pos=(100, 100), size=(400, 400))
    assert grid.grid_w == 50
    assert grid.grid_h == 50

check("GS: basic grid creation", test_grid_basic_creation)

def test_grid_with_layers():
    terrain = mcrfpy.TileLayer(name="terrain", z_index=-1)
    fog = mcrfpy.ColorLayer(name="fog", z_index=1)
    grid = mcrfpy.Grid(grid_size=(50, 50), pos=(100, 100), size=(400, 400),
                       layers=[terrain, fog])
    assert len(grid.layers) == 2

check("GS: grid with layers=[]", test_grid_with_layers)

def test_grid_empty_layers():
    grid = mcrfpy.Grid(grid_size=(50, 50), pos=(100, 100), size=(400, 400), layers=[])
    assert len(grid.layers) == 0

check("GS: grid with layers=[] empty", test_grid_empty_layers)

def test_grid_add_to_scene():
    scene = mcrfpy.Scene("gs_test")
    grid = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(160, 160))
    scene.children.append(grid)
    assert len(scene.children) > 0

check("GS: add grid to scene", test_grid_add_to_scene)

def test_tilelayer_ops():
    grid = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320), layers=[])
    terrain = mcrfpy.TileLayer(name="terrain", z_index=-1)
    grid.add_layer(terrain)
    terrain.set((5, 3), 42)
    assert terrain.at((5, 3)) == 42
    terrain.fill(0)
    assert terrain.at((5, 3)) == 0
    terrain.set((5, 3), -1)
    assert terrain.at((5, 3)) == -1

check("GS: TileLayer set/at/fill", test_tilelayer_ops)

def test_colorlayer_ops():
    grid = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320), layers=[])
    fog = mcrfpy.ColorLayer(name="fog", z_index=1)
    grid.add_layer(fog)
    fog.set((5, 3), mcrfpy.Color(0, 0, 0, 200))
    c = fog.at((5, 3))
    assert c.a == 200
    fog.fill(mcrfpy.Color(0, 0, 0, 255))
    c2 = fog.at((0, 0))
    assert c2.a == 255

check("GS: ColorLayer set/at/fill", test_colorlayer_ops)

def test_layer_management():
    grid = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(160, 160), layers=[])
    tl = mcrfpy.TileLayer(name="terrain", z_index=-1)
    grid.add_layer(tl)
    assert len(grid.layers) == 1
    found = grid.layer("terrain")
    assert found is not None
    grid.remove_layer(tl)
    assert len(grid.layers) == 0

check("GS: layer management (add/layer/remove)", test_layer_management)

def test_gridpoint():
    grid = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(160, 160))
    point = grid.at(5, 5)
    point.walkable = True
    point.transparent = True
    assert point.walkable == True
    assert point.transparent == True

check("GS: GridPoint access", test_gridpoint)

def test_fov():
    grid = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320))
    for x in range(20):
        for y in range(20):
            grid.at(x, y).transparent = True
    grid.at(5, 5).transparent = False
    grid.compute_fov((10, 10), radius=8)
    assert grid.is_in_fov((10, 10)) == True
    assert grid.is_in_fov((0, 0)) == False

check("GS: FOV compute and query", test_fov)

def test_pathfinding():
    grid = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320))
    for x in range(20):
        for y in range(20):
            grid.at(x, y).walkable = True
    grid.at(5, 5).walkable = False
    path = grid.find_path((0, 0), (10, 10))
    assert path is not None
    assert len(path) > 0
    assert path.origin is not None
    assert path.destination is not None
    step = path.walk()
    assert step is not None
    # len() returns remaining steps, same as .remaining
    # After walk(), both decrease by 1
    initial_len = len(path) + 1  # path had one more step before walk()
    assert path.remaining == initial_len - 1

check("GS: A* pathfinding", test_pathfinding)

def test_dijkstra():
    grid = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320))
    for x in range(20):
        for y in range(20):
            grid.at(x, y).walkable = True
    dm = grid.get_dijkstra_map((5, 5))
    d = dm.distance((10, 10))
    assert d > 0
    p = dm.path_from((10, 10))
    assert len(p) > 0
    s = dm.step_from((10, 10))
    assert s is not None

check("GS: Dijkstra map", test_dijkstra)

def test_entity_on_grid():
    grid = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320))
    player = mcrfpy.Entity(grid_pos=(10, 10), sprite_index=0, name="player")
    grid.entities.append(player)
    assert player.grid is not None
    nearby = grid.entities_in_radius((10, 10), 5.0)
    assert len(nearby) > 0
    player.die()

check("GS: entity management on grid", test_entity_on_grid)

def test_camera_control():
    grid = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320))
    grid.center = (80, 80)
    grid.center_x = 100
    grid.center_y = 100
    grid.center_camera((10, 10))
    grid.zoom = 1.5
    grid.animate("center_x", 50.0, 0.5, mcrfpy.Easing.EASE_IN_OUT)
    grid.animate("zoom", 2.0, 0.3, mcrfpy.Easing.EASE_OUT_QUAD)

check("GS: camera control", test_camera_control)

def test_grid_mouse_events():
    grid = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320))
    def on_grid_click(pos, button, action):
        if button == mcrfpy.MouseButton.LEFT and action == mcrfpy.InputState.PRESSED:
            pass
    grid.on_click = on_grid_click
    grid.on_enter = lambda pos: None
    grid.on_exit = lambda pos: None
    def on_cell_click(cell_pos, button, action):
        if button == mcrfpy.MouseButton.LEFT and action == mcrfpy.InputState.PRESSED:
            x, y = int(cell_pos.x), int(cell_pos.y)
    grid.on_cell_click = on_cell_click
    grid.on_cell_enter = lambda cell_pos: None
    grid.on_cell_exit = lambda cell_pos: None

check("GS: mouse events", test_grid_mouse_events)

def test_perspective():
    grid = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320))
    player = mcrfpy.Entity(grid_pos=(10, 10), sprite_index=0)
    grid.entities.append(player)
    grid.perspective = player
    assert grid.perspective is not None
    grid.perspective = None

check("GS: perspective system", test_perspective)

# ===================================================================
print("\n=== ENTITY MANAGEMENT WIKI ===")
# ===================================================================

def test_entity_creation():
    entity = mcrfpy.Entity(grid_pos=(10, 10), sprite_index=0)
    player = mcrfpy.Entity(grid_pos=(5, 5), sprite_index=0, name="player2")
    e = mcrfpy.Entity()
    assert e.grid_x == 0

check("EM: entity creation forms", test_entity_creation)

def test_entity_grid_relationship():
    grid = mcrfpy.Grid(grid_size=(50, 50), pos=(0, 0), size=(400, 400))
    player = mcrfpy.Entity(grid_pos=(10, 10), sprite_index=0, name="em_player")
    assert player.grid is None
    grid.entities.append(player)
    assert player.grid is not None
    assert player in grid.entities
    grid.entities.remove(player)
    assert player.grid is None

check("EM: entity-grid relationship", test_entity_grid_relationship)

def test_entity_movement():
    grid = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320))
    player = mcrfpy.Entity(grid_pos=(5, 5), sprite_index=0)
    grid.entities.append(player)
    player.grid_x = 15
    player.grid_y = 20
    player.animate("x", 15.0, 0.3, mcrfpy.Easing.EASE_OUT_QUAD)
    player.animate("y", 20.0, 0.3, mcrfpy.Easing.EASE_OUT_QUAD)

check("EM: entity movement (direct + animated)", test_entity_movement)

def test_entity_animate_with_callback():
    grid = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320))
    player = mcrfpy.Entity(grid_pos=(5, 5), sprite_index=0)
    grid.entities.append(player)
    def on_move_complete(target, prop, value):
        pass
    player.animate("x", 15.0, 0.3, mcrfpy.Easing.EASE_OUT_QUAD, callback=on_move_complete)

check("EM: entity animate with callback", test_entity_animate_with_callback)

def test_spatial_queries():
    grid = mcrfpy.Grid(grid_size=(50, 50), pos=(0, 0), size=(400, 400))
    for i in range(5):
        e = mcrfpy.Entity(grid_pos=(10 + i, 10), sprite_index=0, name=f"e{i}")
        grid.entities.append(e)
    nearby = grid.entities_in_radius((10, 10), 5.0)
    assert len(nearby) > 0

check("EM: spatial queries", test_spatial_queries)

def test_entity_collection():
    grid = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320))
    e1 = mcrfpy.Entity(grid_pos=(1, 1), sprite_index=0)
    e2 = mcrfpy.Entity(grid_pos=(2, 2), sprite_index=0)
    e3 = mcrfpy.Entity(grid_pos=(3, 3), sprite_index=0)
    grid.entities.append(e1)
    grid.entities.extend([e2, e3])
    assert len(grid.entities) == 3
    grid.entities.remove(e2)
    assert len(grid.entities) == 2

check("EM: EntityCollection operations", test_entity_collection)

def test_entity_die():
    grid = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320))
    e = mcrfpy.Entity(grid_pos=(5, 5), sprite_index=0)
    grid.entities.append(e)
    e.die()
    assert e.grid is None

check("EM: Entity.die()", test_entity_die)

def test_fog_of_war():
    grid = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320), layers=[])
    fog = mcrfpy.ColorLayer(name="fog", z_index=1)
    grid.add_layer(fog)
    fog.fill(mcrfpy.Color(0, 0, 0, 255))
    for x in range(20):
        for y in range(20):
            grid.at(x, y).transparent = True
    grid.compute_fov((10, 10), radius=8)
    for x in range(20):
        for y in range(20):
            if grid.is_in_fov((x, y)):
                fog.set((x, y), mcrfpy.Color(0, 0, 0, 0))

check("EM: fog of war pattern", test_fog_of_war)

def test_player_class_pattern():
    class Player:
        def __init__(self, grid, start_pos):
            self.entity = mcrfpy.Entity(
                grid_pos=start_pos, sprite_index=0, name="pclass"
            )
            grid.entities.append(self.entity)
        def move(self, dx, dy):
            new_x = int(self.entity.grid_x + dx)
            new_y = int(self.entity.grid_y + dy)
            point = self.entity.grid.at(new_x, new_y)
            if point and point.walkable:
                self.entity.animate("x", float(new_x), 0.15, mcrfpy.Easing.EASE_OUT_QUAD)
                self.entity.animate("y", float(new_y), 0.15, mcrfpy.Easing.EASE_OUT_QUAD)
                self.entity.grid_x = new_x
                self.entity.grid_y = new_y
                return True
            return False

    grid = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320))
    for x in range(20):
        for y in range(20):
            grid.at(x, y).walkable = True
    p = Player(grid, (10, 10))
    assert p.move(1, 0) == True

check("EM: Player class pattern", test_player_class_pattern)

def test_enemy_ai_pattern():
    class Enemy:
        def __init__(self, grid, pos, aggro_range=10):
            self.entity = mcrfpy.Entity(
                grid_pos=pos, sprite_index=1, name="enemy_ai"
            )
            self.aggro_range = aggro_range
            grid.entities.append(self.entity)
        def update(self):
            grid = self.entity.grid
            nearby = grid.entities_in_radius(
                (self.entity.grid_x, self.entity.grid_y),
                self.aggro_range
            )
            return nearby

    grid = mcrfpy.Grid(grid_size=(50, 50), pos=(0, 0), size=(400, 400))
    for x in range(50):
        for y in range(50):
            grid.at(x, y).walkable = True
    player = mcrfpy.Entity(grid_pos=(12, 10), sprite_index=0, name="player_for_ai")
    grid.entities.append(player)
    enemy = Enemy(grid, (10, 10))
    nearby = enemy.update()
    assert len(nearby) > 0

check("EM: Enemy AI pattern", test_enemy_ai_pattern)

def test_item_pickup_pattern():
    class Item:
        def __init__(self, grid, pos, item_type):
            self.entity = mcrfpy.Entity(
                grid_pos=pos, sprite_index=10 + item_type, name=f"item_{item_type}"
            )
            self.item_type = item_type
            grid.entities.append(self.entity)
        def pickup(self, collector_inventory):
            collector_inventory.append(self.item_type)
            self.entity.die()

    grid = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320))
    item = Item(grid, (5, 5), 3)
    assert len(grid.entities) == 1
    inv = []
    item.pickup(inv)
    assert inv == [3]
    assert len(grid.entities) == 0

check("EM: Item pickup pattern", test_item_pickup_pattern)

def test_pathfinding_pattern():
    grid = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(320, 320))
    for x in range(20):
        for y in range(20):
            grid.at(x, y).walkable = True
    entity = mcrfpy.Entity(grid_pos=(0, 0), sprite_index=0)
    grid.entities.append(entity)
    path = grid.find_path(
        (int(entity.grid_x), int(entity.grid_y)),
        (10, 10)
    )
    if path and len(path) > 0:
        next_step = path.walk()
        entity.grid_x = next_step.x
        entity.grid_y = next_step.y
    dm = grid.get_dijkstra_map((15, 15))
    d = dm.distance((entity.grid_x, entity.grid_y))
    assert d > 0
    ns = dm.step_from((int(entity.grid_x), int(entity.grid_y)))
    assert ns is not None

check("EM: pathfinding pattern", test_pathfinding_pattern)

# ===================================================================
print("\n" + "=" * 60)
print(f"WIKI SNIPPET VERIFICATION: {passes} passed, {fails} failed")
print("=" * 60)

if fails:
    sys.exit(1)
else:
    sys.exit(0)
