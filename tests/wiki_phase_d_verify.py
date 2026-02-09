"""Verify code snippets from Phase D wiki page updates."""
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
print("=== GRID INTERACTION PATTERNS ===")
# ===================================================================

def test_gip_setup():
    """Setup template from Grid Interaction Patterns"""
    scene = mcrfpy.Scene("gip_test")
    ui = scene.children

    texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    terrain = mcrfpy.TileLayer(name="terrain", z_index=-2, texture=texture)
    highlight = mcrfpy.ColorLayer(name="highlight", z_index=-1)
    overlay = mcrfpy.ColorLayer(name="overlay", z_index=1)

    grid = mcrfpy.Grid(
        grid_size=(20, 15),
        pos=(50, 50),
        size=(640, 480),
        layers=[terrain, highlight, overlay]
    )
    grid.fill_color = mcrfpy.Color(20, 20, 30)
    ui.append(grid)

    player = mcrfpy.Entity(grid_pos=(10, 7), sprite_index=0)
    grid.entities.append(player)
    mcrfpy.current_scene = scene

check("GIP: setup template", test_gip_setup)

def test_gip_cell_hover():
    """Cell hover highlighting pattern"""
    grid = mcrfpy.Grid(grid_size=(20, 15), pos=(0, 0), size=(320, 240), layers=[])
    highlight = mcrfpy.ColorLayer(name="highlight", z_index=-1)
    grid.add_layer(highlight)
    current_highlight = [None]

    def on_cell_enter(cell_pos):
        x, y = int(cell_pos.x), int(cell_pos.y)
        highlight.set((x, y), mcrfpy.Color(255, 255, 255, 40))
        current_highlight[0] = (x, y)

    def on_cell_exit(cell_pos):
        x, y = int(cell_pos.x), int(cell_pos.y)
        highlight.set((x, y), mcrfpy.Color(0, 0, 0, 0))
        current_highlight[0] = None

    grid.on_cell_enter = on_cell_enter
    grid.on_cell_exit = on_cell_exit

check("GIP: cell hover highlighting", test_gip_cell_hover)

def test_gip_cell_click():
    """Cell click actions pattern"""
    grid = mcrfpy.Grid(grid_size=(20, 15), pos=(0, 0), size=(320, 240))
    for x in range(20):
        for y in range(15):
            grid.at(x, y).walkable = True
    player = mcrfpy.Entity(grid_pos=(10, 7), sprite_index=0)
    grid.entities.append(player)

    def on_cell_click(cell_pos, button, action):
        x, y = int(cell_pos.x), int(cell_pos.y)
        point = grid.at(x, y)
        if button == mcrfpy.MouseButton.LEFT and action == mcrfpy.InputState.PRESSED:
            if point.walkable:
                player.grid_x = x
                player.grid_y = y
        elif button == mcrfpy.MouseButton.RIGHT and action == mcrfpy.InputState.PRESSED:
            pass  # inspect
        elif button == mcrfpy.MouseButton.MIDDLE and action == mcrfpy.InputState.PRESSED:
            point.walkable = not point.walkable

    grid.on_cell_click = on_cell_click

check("GIP: cell click actions", test_gip_cell_click)

def test_gip_wasd():
    """WASD movement pattern"""
    scene = mcrfpy.Scene("gip_wasd")
    grid = mcrfpy.Grid(grid_size=(20, 15), pos=(0, 0), size=(320, 240))
    for x in range(20):
        for y in range(15):
            grid.at(x, y).walkable = True
    player = mcrfpy.Entity(grid_pos=(10, 7), sprite_index=0)
    grid.entities.append(player)

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
            new_x = int(player.grid_x + dx)
            new_y = int(player.grid_y + dy)
            point = player.grid.at(new_x, new_y)
            if point and point.walkable:
                player.grid_x = new_x
                player.grid_y = new_y

    scene.on_key = handle_key

check("GIP: WASD movement", test_gip_wasd)

def test_gip_entity_selection():
    """Entity selection pattern"""
    grid = mcrfpy.Grid(grid_size=(20, 15), pos=(0, 0), size=(320, 240), layers=[])
    overlay = mcrfpy.ColorLayer(name="overlay", z_index=1)
    grid.add_layer(overlay)

    e1 = mcrfpy.Entity(grid_pos=(5, 5), sprite_index=0, name="sel_e1")
    e2 = mcrfpy.Entity(grid_pos=(10, 10), sprite_index=1, name="sel_e2")
    grid.entities.append(e1)
    grid.entities.append(e2)

    selected = [None]
    def select_entity(entity):
        if selected[0]:
            ex, ey = int(selected[0].grid_x), int(selected[0].grid_y)
            overlay.set((ex, ey), mcrfpy.Color(0, 0, 0, 0))
        selected[0] = entity
        if entity:
            overlay.set((int(entity.grid_x), int(entity.grid_y)), mcrfpy.Color(255, 200, 0, 80))

    def on_cell_click(cell_pos, button, action):
        if button == mcrfpy.MouseButton.LEFT and action == mcrfpy.InputState.PRESSED:
            x, y = int(cell_pos.x), int(cell_pos.y)
            for entity in grid.entities:
                if int(entity.grid_x) == x and int(entity.grid_y) == y:
                    select_entity(entity)
                    return
            select_entity(None)

    grid.on_cell_click = on_cell_click
    select_entity(e1)
    assert selected[0] == e1

check("GIP: entity selection", test_gip_entity_selection)

def test_gip_path_preview():
    """Path preview pattern"""
    grid = mcrfpy.Grid(grid_size=(20, 15), pos=(0, 0), size=(320, 240), layers=[])
    highlight = mcrfpy.ColorLayer(name="highlight", z_index=-1)
    grid.add_layer(highlight)
    for x in range(20):
        for y in range(15):
            grid.at(x, y).walkable = True
    player = mcrfpy.Entity(grid_pos=(5, 5), sprite_index=0)
    grid.entities.append(player)

    def show_path_to(target_x, target_y):
        path = grid.find_path(
            (int(player.grid_x), int(player.grid_y)),
            (target_x, target_y)
        )
        if path:
            while len(path) > 0:
                step = path.walk()
                if step:
                    highlight.set((int(step.x), int(step.y)),
                                  mcrfpy.Color(100, 200, 255, 60))

    show_path_to(15, 10)

check("GIP: path preview", test_gip_path_preview)

def test_gip_tile_inspector():
    """Tile inspector panel pattern"""
    scene = mcrfpy.Scene("gip_inspect")
    ui = scene.children
    grid = mcrfpy.Grid(grid_size=(20, 15), pos=(0, 0), size=(320, 240))
    ui.append(grid)

    inspector = mcrfpy.Frame(pos=(400, 50), size=(200, 150),
                              fill_color=mcrfpy.Color(30, 30, 40, 230))
    inspector.visible = False
    ui.append(inspector)

    title = mcrfpy.Caption(text="Cell Info", pos=(10, 8))
    inspector.children.append(title)

    info = mcrfpy.Caption(text="", pos=(10, 30))
    inspector.children.append(info)

    def on_cell_click(cell_pos, button, action):
        if button == mcrfpy.MouseButton.LEFT and action == mcrfpy.InputState.PRESSED:
            x, y = int(cell_pos.x), int(cell_pos.y)
            point = grid.at(x, y)
            title.text = f"Cell ({x}, {y})"
            info.text = f"Walkable: {point.walkable}"
            inspector.visible = True

    grid.on_cell_click = on_cell_click

check("GIP: tile inspector panel", test_gip_tile_inspector)

# ===================================================================
print("\n=== UI WIDGET PATTERNS ===")
# ===================================================================

def test_uwp_setup():
    """Setup template"""
    scene = mcrfpy.Scene("uwp_test")
    ui = scene.children

    root = mcrfpy.Frame(pos=(50, 50), size=(300, 400),
                         fill_color=mcrfpy.Color(30, 30, 40))
    root.outline_color = mcrfpy.Color(80, 80, 100)
    root.outline = 2
    ui.append(root)
    mcrfpy.current_scene = scene

check("UWP: setup template", test_uwp_setup)

def test_uwp_button():
    """Button pattern"""
    root = mcrfpy.Frame(pos=(0, 0), size=(300, 400))
    def make_button(parent, pos, text, on_click):
        btn = mcrfpy.Frame(pos=pos, size=(120, 32),
                            fill_color=mcrfpy.Color(60, 60, 80))
        btn.outline_color = mcrfpy.Color(100, 100, 140)
        btn.outline = 1
        label = mcrfpy.Caption(text=text, pos=(10, 6))
        label.fill_color = mcrfpy.Color(220, 220, 220)
        btn.children.append(label)
        btn.on_enter = lambda pos: setattr(btn, 'fill_color', mcrfpy.Color(80, 80, 110))
        btn.on_exit = lambda pos: setattr(btn, 'fill_color', mcrfpy.Color(60, 60, 80))
        btn.on_click = lambda pos, button, action: on_click() if button == mcrfpy.MouseButton.LEFT and action == mcrfpy.InputState.PRESSED else None
        parent.children.append(btn)
        return btn

    b1 = make_button(root, (20, 20), "New Game", lambda: None)
    b2 = make_button(root, (20, 60), "Options", lambda: None)
    assert b1.w == 120

check("UWP: button pattern", test_uwp_button)

def test_uwp_toggle():
    """Toggle/checkbox pattern"""
    root = mcrfpy.Frame(pos=(0, 0), size=(300, 400))

    def make_toggle(parent, pos, label_text, initial=False, on_change=None):
        state = {"checked": initial}
        frame = mcrfpy.Frame(pos=pos, size=(160, 28),
                              fill_color=mcrfpy.Color(40, 40, 50))
        indicator = mcrfpy.Frame(pos=(6, 6), size=(16, 16))
        indicator.outline = 1
        indicator.outline_color = mcrfpy.Color(120, 120, 140)
        frame.children.append(indicator)

        label = mcrfpy.Caption(text=label_text, pos=(30, 5))
        label.fill_color = mcrfpy.Color(200, 200, 200)
        frame.children.append(label)

        def update_visual():
            if state["checked"]:
                indicator.fill_color = mcrfpy.Color(100, 180, 100)
            else:
                indicator.fill_color = mcrfpy.Color(50, 50, 60)

        def toggle(pos, button, action):
            if button == mcrfpy.MouseButton.LEFT and action == mcrfpy.InputState.PRESSED:
                state["checked"] = not state["checked"]
                update_visual()
                if on_change:
                    on_change(state["checked"])

        frame.on_click = toggle
        update_visual()
        parent.children.append(frame)
        return state

    t = make_toggle(root, (20, 20), "Music", initial=True)
    assert t["checked"] == True

check("UWP: toggle pattern", test_uwp_toggle)

def test_uwp_vertical_menu():
    """Vertical menu with keyboard nav"""
    scene = mcrfpy.Scene("uwp_menu")
    root = mcrfpy.Frame(pos=(0, 0), size=(300, 400))
    scene.children.append(root)

    class VerticalMenu:
        def __init__(self, parent, pos, options, on_select):
            self.options = options
            self.on_select = on_select
            self.selected = 0
            self.frame = mcrfpy.Frame(pos=pos, size=(180, len(options) * 28 + 8),
                                       fill_color=mcrfpy.Color(35, 35, 45))
            parent.children.append(self.frame)
            self.items = []
            for i, (label, value) in enumerate(options):
                item = mcrfpy.Caption(text=label, pos=(12, 4 + i * 28))
                item.fill_color = mcrfpy.Color(180, 180, 180)
                self.frame.children.append(item)
                self.items.append(item)
            self._update_highlight()

        def _update_highlight(self):
            for i, item in enumerate(self.items):
                if i == self.selected:
                    item.fill_color = mcrfpy.Color(255, 220, 100)
                else:
                    item.fill_color = mcrfpy.Color(180, 180, 180)

        def move_up(self):
            self.selected = (self.selected - 1) % len(self.options)
            self._update_highlight()

        def move_down(self):
            self.selected = (self.selected + 1) % len(self.options)
            self._update_highlight()

        def confirm(self):
            _, value = self.options[self.selected]
            self.on_select(value)

    result = [None]
    menu = VerticalMenu(root, (20, 20), [
        ("Continue", "continue"),
        ("New Game", "new"),
        ("Quit", "quit")
    ], on_select=lambda v: result.__setitem__(0, v))

    def handle_key(key, action):
        if action != mcrfpy.InputState.PRESSED:
            return
        if key == mcrfpy.Key.UP:
            menu.move_up()
        elif key == mcrfpy.Key.DOWN:
            menu.move_down()
        elif key == mcrfpy.Key.ENTER:
            menu.confirm()

    scene.on_key = handle_key
    menu.confirm()
    assert result[0] == "continue"

check("UWP: vertical menu", test_uwp_vertical_menu)

def test_uwp_modal():
    """Modal dialog pattern"""
    scene = mcrfpy.Scene("uwp_modal")
    ui = scene.children

    dismissed = [False]
    backdrop = mcrfpy.Frame(pos=(0, 0), size=(1024, 768),
                             fill_color=mcrfpy.Color(0, 0, 0, 160))
    backdrop.z_index = 900
    backdrop.on_click = lambda pos, btn, action: None  # Block clicks
    ui.append(backdrop)

    dialog = mcrfpy.Frame(pos=(312, 284), size=(400, 200),
                           fill_color=mcrfpy.Color(50, 50, 65))
    dialog.outline_color = mcrfpy.Color(120, 120, 150)
    dialog.outline = 2
    dialog.z_index = 901
    ui.append(dialog)

    msg = mcrfpy.Caption(text="Game saved!", pos=(20, 20))
    msg.fill_color = mcrfpy.Color(220, 220, 220)
    dialog.children.append(msg)

    ok_btn = mcrfpy.Frame(pos=(150, 140), size=(100, 36),
                           fill_color=mcrfpy.Color(70, 100, 70))
    ok_btn.outline = 1
    ok_btn.on_click = lambda pos, btn, action: dismissed.__setitem__(0, True)
    dialog.children.append(ok_btn)

    ok_label = mcrfpy.Caption(text="OK", pos=(35, 8))
    ok_label.fill_color = mcrfpy.Color(220, 255, 220)
    ok_btn.children.append(ok_label)

check("UWP: modal dialog", test_uwp_modal)

def test_uwp_hotbar():
    """Hotbar / quick slots pattern"""
    scene = mcrfpy.Scene("uwp_hotbar")
    root = mcrfpy.Frame(pos=(0, 0), size=(800, 600))
    scene.children.append(root)

    slot_count = 9
    slots = []
    hotbar_frame = mcrfpy.Frame(pos=(200, 500), size=(slot_count * 36 + 8, 44),
                                 fill_color=mcrfpy.Color(30, 30, 40, 200))
    root.children.append(hotbar_frame)

    for i in range(slot_count):
        slot = mcrfpy.Frame(pos=(4 + i * 36, 4), size=(32, 32),
                             fill_color=mcrfpy.Color(50, 50, 60))
        slot.outline = 1
        slot.outline_color = mcrfpy.Color(80, 80, 100)
        hotbar_frame.children.append(slot)
        num = mcrfpy.Caption(text=str((i + 1) % 10), pos=(2, 2))
        num.fill_color = mcrfpy.Color(100, 100, 120)
        slot.children.append(num)
        slots.append(slot)

    selected = [0]
    def select_slot(index):
        if 0 <= index < len(slots):
            slots[selected[0]].outline_color = mcrfpy.Color(80, 80, 100)
            slots[selected[0]].outline = 1
            selected[0] = index
            slots[index].outline_color = mcrfpy.Color(200, 180, 80)
            slots[index].outline = 2

    select_slot(0)

    def handle_key(key, action):
        if action != mcrfpy.InputState.PRESSED:
            return
        num_keys = {
            mcrfpy.Key.NUM_1: 0, mcrfpy.Key.NUM_2: 1, mcrfpy.Key.NUM_3: 2,
            mcrfpy.Key.NUM_4: 3, mcrfpy.Key.NUM_5: 4, mcrfpy.Key.NUM_6: 5,
            mcrfpy.Key.NUM_7: 6, mcrfpy.Key.NUM_8: 7, mcrfpy.Key.NUM_9: 8,
        }
        if key in num_keys:
            select_slot(num_keys[key])

    scene.on_key = handle_key
    assert slots[0].outline == 2

check("UWP: hotbar/quick slots", test_uwp_hotbar)

def test_uwp_draggable():
    """Draggable window pattern"""
    root = mcrfpy.Frame(pos=(0, 0), size=(800, 600))

    frame = mcrfpy.Frame(pos=(100, 100), size=(250, 300),
                          fill_color=mcrfpy.Color(45, 45, 55))
    frame.outline = 1
    frame.outline_color = mcrfpy.Color(100, 100, 120)
    root.children.append(frame)

    title_bar = mcrfpy.Frame(pos=(0, 0), size=(250, 24),
                              fill_color=mcrfpy.Color(60, 60, 80))
    frame.children.append(title_bar)

    title_label = mcrfpy.Caption(text="Inventory", pos=(8, 4))
    title_label.fill_color = mcrfpy.Color(200, 200, 220)
    title_bar.children.append(title_label)

    content = mcrfpy.Caption(text="Items here...", pos=(10, 38))
    frame.children.append(content)

check("UWP: draggable window", test_uwp_draggable)

# ===================================================================
print("\n=== RENDERING AND VISUALS ===")
# ===================================================================

def test_rv_basic_elements():
    """Creating basic UI elements"""
    scene = mcrfpy.Scene("rv_test")
    ui = scene.children

    frame = mcrfpy.Frame(pos=(100, 100), size=(200, 150),
                          fill_color=mcrfpy.Color(50, 50, 50))
    frame.outline_color = mcrfpy.Color(255, 255, 255)
    frame.outline = 2
    ui.append(frame)

    label = mcrfpy.Caption(text="Hello World!", pos=(10, 10))
    label.font_size = 24
    label.fill_color = mcrfpy.Color(255, 255, 255)
    ui.append(label)

    sprite = mcrfpy.Sprite(x=50, y=50, sprite_index=0)
    ui.append(sprite)

check("RV: basic UI elements", test_rv_basic_elements)

def test_rv_textures():
    """Texture loading and sprite sheets"""
    texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    sprite = mcrfpy.Sprite(x=100, y=100)
    sprite.texture = texture
    sprite.sprite_index = 5

check("RV: textures and sprite sheets", test_rv_textures)

def test_rv_z_order():
    """Z-order layering"""
    scene = mcrfpy.Scene("rv_z")
    ui = scene.children

    background = mcrfpy.Frame(pos=(0, 0), size=(800, 600),
                               fill_color=mcrfpy.Color(20, 20, 20))
    background.z_index = 0
    ui.append(background)

    grid = mcrfpy.Grid(grid_size=(20, 15), pos=(50, 50), size=(400, 300))
    grid.z_index = 10
    ui.append(grid)

    hud = mcrfpy.Frame(pos=(0, 0), size=(800, 50),
                        fill_color=mcrfpy.Color(30, 30, 30, 200))
    hud.z_index = 100
    ui.append(hud)

check("RV: z-order layering", test_rv_z_order)

def test_rv_colors():
    """Color creation and application"""
    red = mcrfpy.Color(255, 0, 0)
    semi_transparent = mcrfpy.Color(255, 255, 255, 128)

    frame = mcrfpy.Frame(pos=(0, 0), size=(100, 100))
    frame.fill_color = mcrfpy.Color(50, 50, 50)
    frame.outline_color = mcrfpy.Color(255, 255, 255)

    caption = mcrfpy.Caption(text="Test", pos=(0, 0))
    caption.fill_color = mcrfpy.Color(255, 255, 0)

    assert red.r == 255
    assert semi_transparent.a == 128

check("RV: colors", test_rv_colors)

def test_rv_animations():
    """Animation patterns"""
    frame = mcrfpy.Frame(pos=(0, 0), size=(100, 100))
    frame.animate("opacity", 1.0, 1.0, mcrfpy.Easing.EASE_IN_QUAD)
    frame.animate("fill_color", (255, 0, 0, 255), 0.5, mcrfpy.Easing.LINEAR)
    frame.animate("x", 200.0, 0.3, mcrfpy.Easing.EASE_OUT_CUBIC)

check("RV: animations", test_rv_animations)

def test_rv_visibility():
    """Visibility control"""
    sprite = mcrfpy.Sprite(x=0, y=0, sprite_index=0)
    sprite.visible = False
    sprite.visible = True
    sprite.opacity = 0.5
    assert sprite.opacity == 0.5

check("RV: visibility", test_rv_visibility)

def test_rv_hud():
    """HUD overlay pattern"""
    scene = mcrfpy.Scene("rv_hud")
    ui = scene.children

    hud = mcrfpy.Frame(pos=(0, 0), size=(800, 60),
                        fill_color=mcrfpy.Color(30, 30, 30, 200))
    hud.z_index = 100
    ui.append(hud)

    health_label = mcrfpy.Caption(text="HP: 100/100", pos=(10, 10))
    health_label.font_size = 18
    health_label.fill_color = mcrfpy.Color(255, 255, 255)
    hud.children.append(health_label)

    def update_hud(current_hp, max_hp):
        health_label.text = f"HP: {current_hp}/{max_hp}"
        if current_hp < max_hp * 0.3:
            health_label.fill_color = mcrfpy.Color(255, 0, 0)
        elif current_hp < max_hp * 0.6:
            health_label.fill_color = mcrfpy.Color(255, 255, 0)
        else:
            health_label.fill_color = mcrfpy.Color(0, 255, 0)

    update_hud(50, 100)
    assert health_label.text == "HP: 50/100"

check("RV: HUD overlay", test_rv_hud)

def test_rv_health_bar():
    """Health bar pattern"""
    bg = mcrfpy.Frame(pos=(10, 10), size=(100, 10),
                       fill_color=mcrfpy.Color(255, 0, 0))
    bg.z_index = 90

    fg = mcrfpy.Frame(pos=(10, 10), size=(100, 10),
                       fill_color=mcrfpy.Color(0, 255, 0))
    fg.z_index = 91

    ratio = 0.5
    target_width = int(100 * ratio)
    fg.animate("w", float(target_width), 0.2, mcrfpy.Easing.EASE_OUT_QUAD)

check("RV: health bar", test_rv_health_bar)

def test_rv_grid_rendering():
    """Grid rendering basics"""
    texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    terrain = mcrfpy.TileLayer(name="terrain", z_index=-1, texture=texture)
    grid = mcrfpy.Grid(grid_size=(20, 15), pos=(100, 100), size=(400, 300),
                        layers=[terrain])

    for x in range(20):
        for y in range(15):
            if x == 0 or x == 19 or y == 0 or y == 14:
                terrain.set((x, y), 1)
            else:
                terrain.set((x, y), 0)

check("RV: grid rendering", test_rv_grid_rendering)

def test_rv_camera():
    """Camera/viewport control"""
    grid = mcrfpy.Grid(grid_size=(50, 50), pos=(0, 0), size=(400, 400))
    grid.zoom = 2.0
    grid.center_camera((25, 25))
    grid.animate("zoom", 1.5, 1.0, mcrfpy.Easing.EASE_IN_OUT)

check("RV: camera control", test_rv_camera)

def test_rv_particle_pattern():
    """Particle-like effects pattern"""
    scene = mcrfpy.Scene("rv_particles")
    ui = scene.children
    import random

    def create_explosion(x, y):
        particles = []
        for i in range(5):
            p = mcrfpy.Frame(pos=(x, y), size=(4, 4),
                              fill_color=mcrfpy.Color(255, 200, 50))
            p.z_index = 50
            target_x = x + random.randint(-50, 50)
            target_y = y + random.randint(-50, 50)
            p.animate("x", float(target_x), 0.5, mcrfpy.Easing.EASE_OUT_QUAD)
            p.animate("y", float(target_y), 0.5, mcrfpy.Easing.EASE_OUT_QUAD)
            p.animate("opacity", 0.0, 0.5, mcrfpy.Easing.LINEAR)
            particles.append(p)
            ui.append(p)
        return particles

    particles = create_explosion(100, 100)
    assert len(particles) == 5

check("RV: particle effects", test_rv_particle_pattern)

# ===================================================================
print("\n" + "=" * 60)
print(f"PHASE D VERIFICATION: {passes} passed, {fails} failed")
print("=" * 60)

if fails:
    sys.exit(1)
else:
    sys.exit(0)
