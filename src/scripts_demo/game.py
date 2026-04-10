"""McRogueFace Web Demo - A roguelike dungeon crawler showcasing engine features.

Features demonstrated:
- BSP dungeon generation with corridors
- Wang tile autotiling for pretty dungeons
- Entity system with player and enemies
- Field of view with fog of war
- Turn-based bump combat
- UI overlays (health bar, messages, depth counter)
- Animations and timers
"""
import mcrfpy
import random

# -- Assets ------------------------------------------------------------------
texture = mcrfpy.Texture("assets/kenney_TD_MR_IP.png", 16, 16)
font = mcrfpy.Font("assets/JetbrainsMono.ttf")

# Try to load Wang tileset for pretty autotiling
try:
    _tileset = mcrfpy.TileSetFile("assets/kenney_TD_MR_IP.tsx")
    _wang_set = _tileset.wang_set("dungeon")
    _Terrain = _wang_set.terrain_enum()
    HAS_WANG = True
except Exception:
    HAS_WANG = False

# -- Sprite indices from kenney_TD_MR_IP (12 cols x 55 rows, 16x16) ----------
# Rows are 0-indexed; sprite_index = row * 12 + col
FLOOR_TILE = 145       # open stone floor
WALL_TILE = 251        # solid wall
PLAYER_SPRITE = 84     # hero character
RAT_SPRITE = 123       # small rat enemy
CYCLOPS_SPRITE = 109   # big enemy
SKELETON_SPRITE = 110  # skeleton enemy
HEART_FULL = 210
HEART_HALF = 209
HEART_EMPTY = 208
POTION_SPRITE = 115    # red potion
STAIRS_SPRITE = 91     # stairs down
SKULL_SPRITE = 135     # death indicator
TREASURE_SPRITE = 127  # treasure chest

# -- Configuration ------------------------------------------------------------
MAP_W, MAP_H = 40, 30
ZOOM = 2.0
GRID_PX_W = 1024
GRID_PX_H = 700
FOV_RADIUS = 10
MAX_HP = 10
ENEMY_SIGHT = 8


# =============================================================================
# Wang tile autotiling
# =============================================================================
def paint_tiles(grid, w, h):
    """Apply Wang tile autotiling or fallback to simple tiles."""
    if HAS_WANG:
        dm = mcrfpy.DiscreteMap((w, h))
        for y in range(h):
            for x in range(w):
                if grid.at((x, y)).walkable:
                    dm.set(x, y, int(_Terrain.GROUND))
                else:
                    dm.set(x, y, int(_Terrain.WALL))
        tiles = _wang_set.resolve(dm)
        for y in range(h):
            for x in range(w):
                tid = tiles[y * w + x]
                if tid >= 0:
                    grid.at((x, y)).tilesprite = tid
                else:
                    grid.at((x, y)).tilesprite = (
                        FLOOR_TILE if grid.at((x, y)).walkable else WALL_TILE
                    )
    else:
        for y in range(h):
            for x in range(w):
                grid.at((x, y)).tilesprite = (
                    FLOOR_TILE if grid.at((x, y)).walkable else WALL_TILE
                )


# =============================================================================
# Dungeon generator (BSP)
# =============================================================================
class Dungeon:
    def __init__(self, grid, w, h):
        self.grid = grid
        self.w = w
        self.h = h
        self.rooms = []        # list of (cx, cy) room centers
        self.walkable = set()  # walkable cell coords

    def generate(self):
        # Reset all cells to walls
        for x in range(self.w):
            for y in range(self.h):
                self.grid.at((x, y)).walkable = False
                self.grid.at((x, y)).transparent = False

        # BSP split
        bsp = mcrfpy.BSP(pos=(1, 1), size=(self.w - 2, self.h - 2))
        bsp.split_recursive(depth=5, min_size=(4, 4), max_ratio=1.5)
        leaves = list(bsp.leaves())

        # Carve rooms (1-cell margin from leaf edges)
        for leaf in leaves:
            lx, ly = int(leaf.pos[0]), int(leaf.pos[1])
            lw, lh = int(leaf.size[0]), int(leaf.size[1])
            cx = lx + lw // 2
            cy = ly + lh // 2
            self.rooms.append((cx, cy))
            for rx in range(lx + 1, lx + lw - 1):
                for ry in range(ly + 1, ly + lh - 1):
                    if 0 <= rx < self.w and 0 <= ry < self.h:
                        self.grid.at((rx, ry)).walkable = True
                        self.grid.at((rx, ry)).transparent = True
                        self.walkable.add((rx, ry))

        # Carve corridors using BSP adjacency
        adj = bsp.adjacency
        connected = set()
        for i in range(len(adj)):
            for j in adj[i]:
                edge = (min(i, j), max(i, j))
                if edge in connected:
                    continue
                connected.add(edge)
                self._dig_corridor(self.rooms[i], self.rooms[j])

        # Apply tile graphics
        paint_tiles(self.grid, self.w, self.h)

    def _dig_corridor(self, start, end):
        x1, x2 = min(start[0], end[0]), max(start[0], end[0])
        y1, y2 = min(start[1], end[1]), max(start[1], end[1])
        # L-shaped corridor
        if random.random() < 0.5:
            tx, ty = x1, y2
        else:
            tx, ty = x2, y1
        for x in range(x1, x2 + 1):
            if 0 <= x < self.w and 0 <= ty < self.h:
                self.grid.at((x, ty)).walkable = True
                self.grid.at((x, ty)).transparent = True
                self.walkable.add((x, ty))
        for y in range(y1, y2 + 1):
            if 0 <= tx < self.w and 0 <= y < self.h:
                self.grid.at((tx, y)).walkable = True
                self.grid.at((tx, y)).transparent = True
                self.walkable.add((tx, y))

    def random_floor(self, exclude=None):
        """Find a random walkable cell not in the exclude set."""
        exclude = exclude or set()
        candidates = list(self.walkable - exclude)
        if not candidates:
            return None
        return random.choice(candidates)


# =============================================================================
# Game state
# =============================================================================
class Game:
    def __init__(self):
        self.scene = mcrfpy.Scene("game")
        self.ui = self.scene.children
        self.depth = 1
        self.player_hp = MAX_HP
        self.player_max_hp = MAX_HP
        self.player_atk = 2
        self.player_def = 0
        self.score = 0
        self.game_over = False
        self.enemies = []    # list of dicts: {entity, hp, atk, def, sprite, name}
        self.items = []      # list of dicts: {entity, kind}
        self.dungeon = None
        self.fog_layer = None
        self.grid = None
        self.player = None
        self.message_timer = None
        self.occupied = set()  # cells occupied by entities

        self._build_ui()
        self._new_level()

        self.scene.on_key = self.on_key
        self.scene.activate()

    # -- UI -------------------------------------------------------------------
    def _build_ui(self):
        # Main grid
        self.grid = mcrfpy.Grid(
            grid_size=(MAP_W, MAP_H),
            texture=texture,
            pos=(0, 0),
            size=(GRID_PX_W, GRID_PX_H),
        )
        self.grid.zoom = ZOOM
        self.grid.center = (MAP_W / 2.0 * 16, MAP_H / 2.0 * 16)
        self.ui.append(self.grid)

        # HUD bar at bottom
        self.hud = mcrfpy.Frame(
            pos=(0, GRID_PX_H), size=(1024, 68),
            fill_color=(20, 16, 28, 240)
        )
        self.ui.append(self.hud)

        # Health display
        self.health_label = mcrfpy.Caption(
            text="HP: 10/10", pos=(12, 6), font=font,
            fill_color=(220, 50, 50)
        )
        self.health_label.font_size = 20
        self.health_label.outline = 2
        self.health_label.outline_color = (0, 0, 0)
        self.hud.children.append(self.health_label)

        # Heart sprites
        self.hearts = []
        for i in range(5):
            h = mcrfpy.Sprite(
                x=12 + i * 36, y=32,
                texture=texture, sprite_index=HEART_FULL, scale=2.0
            )
            self.hearts.append(h)
            self.hud.children.append(h)

        # Depth label
        self.depth_label = mcrfpy.Caption(
            text="Depth: 1", pos=(220, 6), font=font,
            fill_color=(180, 180, 220)
        )
        self.depth_label.font_size = 20
        self.depth_label.outline = 2
        self.depth_label.outline_color = (0, 0, 0)
        self.hud.children.append(self.depth_label)

        # Score label
        self.score_label = mcrfpy.Caption(
            text="Score: 0", pos=(220, 32), font=font,
            fill_color=(220, 200, 80)
        )
        self.score_label.font_size = 18
        self.score_label.outline = 2
        self.score_label.outline_color = (0, 0, 0)
        self.hud.children.append(self.score_label)

        # Message area
        self.msg_label = mcrfpy.Caption(
            text="Arrow keys to move. Bump enemies to attack.",
            pos=(450, 6), font=font,
            fill_color=(160, 200, 160)
        )
        self.msg_label.font_size = 16
        self.msg_label.outline = 1
        self.msg_label.outline_color = (0, 0, 0)
        self.hud.children.append(self.msg_label)

        self.msg_label2 = mcrfpy.Caption(
            text="Find the stairs to descend deeper!",
            pos=(450, 30), font=font,
            fill_color=(140, 160, 180)
        )
        self.msg_label2.font_size = 14
        self.msg_label2.outline = 1
        self.msg_label2.outline_color = (0, 0, 0)
        self.hud.children.append(self.msg_label2)

    # -- Level generation -----------------------------------------------------
    def _new_level(self):
        # Clear old entities
        while len(self.grid.entities) > 0:
            self.grid.entities.pop(0)
        self.enemies.clear()
        self.items.clear()
        self.occupied.clear()

        # Generate dungeon
        self.dungeon = Dungeon(self.grid, MAP_W, MAP_H)
        self.dungeon.generate()

        # Place player in first room
        px, py = self.dungeon.rooms[0]
        if self.player is None:
            self.player = mcrfpy.Entity(
                grid_pos=(px, py), texture=texture,
                sprite_index=PLAYER_SPRITE
            )
        else:
            self.player.grid_pos = (px, py)
        self.grid.entities.append(self.player)
        self.occupied.add((px, py))

        # Place stairs in last room
        sx, sy = self.dungeon.rooms[-1]
        stairs = mcrfpy.Entity(
            grid_pos=(sx, sy), texture=texture,
            sprite_index=STAIRS_SPRITE
        )
        self.grid.entities.append(stairs)
        self.stairs_pos = (sx, sy)
        self.occupied.add((sx, sy))

        # Place enemies (more enemies on deeper levels)
        num_enemies = min(3 + self.depth * 2, 15)
        enemy_types = self._enemy_table()
        for _ in range(num_enemies):
            pos = self.dungeon.random_floor(exclude=self.occupied)
            if pos is None:
                break
            etype = random.choice(enemy_types)
            e = mcrfpy.Entity(
                grid_pos=pos, texture=texture,
                sprite_index=etype["sprite"]
            )
            self.grid.entities.append(e)
            self.enemies.append({
                "entity": e,
                "hp": etype["hp"],
                "max_hp": etype["hp"],
                "atk": etype["atk"],
                "def": etype["def"],
                "name": etype["name"],
                "sprite": etype["sprite"],
            })
            self.occupied.add(pos)

        # Place health potions
        num_potions = random.randint(1, 3)
        for _ in range(num_potions):
            pos = self.dungeon.random_floor(exclude=self.occupied)
            if pos is None:
                break
            item = mcrfpy.Entity(
                grid_pos=pos, texture=texture,
                sprite_index=POTION_SPRITE
            )
            self.grid.entities.append(item)
            self.items.append({"entity": item, "kind": "potion", "pos": pos})
            self.occupied.add(pos)

        # Place treasure
        num_treasure = random.randint(1, 2 + self.depth)
        for _ in range(num_treasure):
            pos = self.dungeon.random_floor(exclude=self.occupied)
            if pos is None:
                break
            item = mcrfpy.Entity(
                grid_pos=pos, texture=texture,
                sprite_index=TREASURE_SPRITE
            )
            self.grid.entities.append(item)
            self.items.append({"entity": item, "kind": "treasure", "pos": pos})
            self.occupied.add(pos)

        # Set up fog of war (remove old layer first to prevent accumulation)
        if self.fog_layer is not None:
            self.grid.remove_layer(self.fog_layer)
        self.fog_layer = mcrfpy.ColorLayer(name="fog", z_index=10)
        self.grid.add_layer(self.fog_layer)
        self.fog_layer.fill(mcrfpy.Color(0, 0, 0, 255))
        self.discovered = set()

        # Center camera on player
        self._center_camera()
        self._update_fov()
        self._update_hud()

        # Depth label
        self.depth_label.text = f"Depth: {self.depth}"

    def _enemy_table(self):
        """Return available enemy types scaled by depth."""
        table = [
            {"name": "Rat", "sprite": RAT_SPRITE,
             "hp": 2 + self.depth // 3, "atk": 1, "def": 0},
        ]
        if self.depth >= 2:
            table.append(
                {"name": "Skeleton", "sprite": SKELETON_SPRITE,
                 "hp": 3 + self.depth // 2, "atk": 2, "def": 1}
            )
        if self.depth >= 4:
            table.append(
                {"name": "Cyclops", "sprite": CYCLOPS_SPRITE,
                 "hp": 6 + self.depth, "atk": 3, "def": 2}
            )
        return table

    # -- Camera ---------------------------------------------------------------
    def _center_camera(self):
        px = int(self.player.grid_pos.x)
        py = int(self.player.grid_pos.y)
        self.grid.center = (px * 16 + 8, py * 16 + 8)

    # -- FOV ------------------------------------------------------------------
    def _update_fov(self):
        if self.fog_layer is None:
            return
        px = int(self.player.grid_pos.x)
        py = int(self.player.grid_pos.y)
        self.grid.compute_fov((px, py), radius=FOV_RADIUS)

        for x in range(MAP_W):
            for y in range(MAP_H):
                if self.grid.is_in_fov((x, y)):
                    self.discovered.add((x, y))
                    self.fog_layer.set((x, y), mcrfpy.Color(0, 0, 0, 0))
                elif (x, y) in self.discovered:
                    self.fog_layer.set((x, y), mcrfpy.Color(0, 0, 0, 140))
                # else: stays at 255 alpha (fully hidden)

    # -- HUD ------------------------------------------------------------------
    def _update_hud(self):
        self.health_label.text = f"HP: {self.player_hp}/{self.player_max_hp}"
        self.score_label.text = f"Score: {self.score}"
        # Update heart sprites
        for i, h in enumerate(self.hearts):
            full = self.player_hp - i * 2
            cap = self.player_max_hp - i * 2
            if cap < 1:
                h.sprite_index = 659  # invisible/blank
            elif full >= 2:
                h.sprite_index = HEART_FULL
            elif full == 1:
                h.sprite_index = HEART_HALF
            else:
                h.sprite_index = HEART_EMPTY

    def _show_message(self, line1, line2=""):
        self.msg_label.text = line1
        self.msg_label2.text = line2

    # -- Combat ---------------------------------------------------------------
    def _attack_enemy(self, enemy_data):
        dmg = max(1, self.player_atk - enemy_data["def"])
        enemy_data["hp"] -= dmg
        name = enemy_data["name"]
        if enemy_data["hp"] <= 0:
            self._show_message(
                f"You slay the {name}! (+{10 * self.depth} pts)",
                f"Hit for {dmg} damage - lethal!"
            )
            self.score += 10 * self.depth
            # Remove from grid
            for i in range(len(self.grid.entities)):
                if self.grid.entities[i] is enemy_data["entity"]:
                    self.grid.entities.pop(i)
                    break
            ex = int(enemy_data["entity"].grid_pos.x)
            ey = int(enemy_data["entity"].grid_pos.y)
            self.occupied.discard((ex, ey))
            self.enemies.remove(enemy_data)
        else:
            self._show_message(
                f"You hit the {name} for {dmg}!",
                f"{name} HP: {enemy_data['hp']}/{enemy_data['max_hp']}"
            )

    def _enemy_attacks_player(self, enemy_data):
        dmg = max(1, enemy_data["atk"] - self.player_def)
        self.player_hp -= dmg
        name = enemy_data["name"]
        if self.player_hp <= 0:
            self.player_hp = 0
            self._update_hud()
            self._game_over()
            return
        self._show_message(
            f"The {name} hits you for {dmg}!",
            f"HP: {self.player_hp}/{self.player_max_hp}"
        )

    def _game_over(self):
        self.game_over = True
        # Darken screen
        overlay = mcrfpy.Frame(
            pos=(0, 0), size=(1024, 768),
            fill_color=(0, 0, 0, 180)
        )
        self.ui.append(overlay)

        title = mcrfpy.Caption(
            text="YOU DIED", pos=(340, 250), font=font,
            fill_color=(200, 30, 30)
        )
        title.font_size = 60
        title.outline = 4
        title.outline_color = (0, 0, 0)
        overlay.children.append(title)

        info = mcrfpy.Caption(
            text=f"Reached depth {self.depth} with {self.score} points",
            pos=(280, 340), font=font,
            fill_color=(200, 200, 200)
        )
        info.font_size = 22
        info.outline = 2
        info.outline_color = (0, 0, 0)
        overlay.children.append(info)

        restart = mcrfpy.Caption(
            text="Press R to restart",
            pos=(370, 400), font=font,
            fill_color=(160, 200, 160)
        )
        restart.font_size = 20
        restart.outline = 2
        restart.outline_color = (0, 0, 0)
        overlay.children.append(restart)
        self.game_over_overlay = overlay

    def _restart(self):
        self.game_over = False
        self.player_hp = MAX_HP
        self.player_max_hp = MAX_HP
        self.player_atk = 2
        self.player_def = 0
        self.depth = 1
        self.score = 0
        self.player = None
        self.fog_layer = None  # Old grid is being discarded
        # Remove overlay
        if hasattr(self, 'game_over_overlay'):
            # Rebuild UI from scratch
            while len(self.ui) > 0:
                self.ui.pop(0)
            self._build_ui()
            self._new_level()
            self.scene.on_key = self.on_key

    # -- Items ----------------------------------------------------------------
    def _check_items(self, px, py):
        for item in self.items[:]:
            ix = int(item["entity"].grid_pos.x)
            iy = int(item["entity"].grid_pos.y)
            if ix == px and iy == py:
                if item["kind"] == "potion":
                    heal = random.randint(2, 4)
                    self.player_hp = min(self.player_max_hp, self.player_hp + heal)
                    self._show_message(
                        f"Healed {heal} HP!",
                        f"HP: {self.player_hp}/{self.player_max_hp}"
                    )
                elif item["kind"] == "treasure":
                    pts = random.randint(5, 15) * self.depth
                    self.score += pts
                    self._show_message(
                        f"Found treasure! (+{pts} pts)",
                        f"Total score: {self.score}"
                    )
                # Remove item entity
                for i in range(len(self.grid.entities)):
                    if self.grid.entities[i] is item["entity"]:
                        self.grid.entities.pop(i)
                        break
                self.occupied.discard((ix, iy))
                self.items.remove(item)

    # -- Enemy AI (simple: move toward player if visible) ---------------------
    def _enemy_turn(self):
        px = int(self.player.grid_pos.x)
        py = int(self.player.grid_pos.y)

        for edata in self.enemies[:]:
            ex = int(edata["entity"].grid_pos.x)
            ey = int(edata["entity"].grid_pos.y)

            # Only act if in FOV (player can see them)
            if not self.grid.is_in_fov((ex, ey)):
                continue

            # Manhattan distance
            dist = abs(ex - px) + abs(ey - py)
            if dist > ENEMY_SIGHT:
                continue

            # Adjacent? Attack!
            if dist == 1:
                self._enemy_attacks_player(edata)
                if self.game_over:
                    return
                continue

            # Move toward player (simple greedy)
            dx = 0
            dy = 0
            if abs(ex - px) > abs(ey - py):
                dx = 1 if px > ex else -1
            else:
                dy = 1 if py > ey else -1

            nx, ny = ex + dx, ey + dy

            # Check bounds and walkability
            if (0 <= nx < MAP_W and 0 <= ny < MAP_H
                    and self.grid.at((nx, ny)).walkable
                    and (nx, ny) not in self.occupied):
                self.occupied.discard((ex, ey))
                edata["entity"].grid_pos = (nx, ny)
                self.occupied.add((nx, ny))

    # -- Input ----------------------------------------------------------------
    def on_key(self, key, state):
        if state != mcrfpy.InputState.PRESSED:
            return

        if self.game_over:
            if key == mcrfpy.Key.R:
                self._restart()
            return

        dx, dy = 0, 0
        if key == mcrfpy.Key.UP or key == mcrfpy.Key.W:
            dy = -1
        elif key == mcrfpy.Key.DOWN or key == mcrfpy.Key.S:
            dy = 1
        elif key == mcrfpy.Key.LEFT or key == mcrfpy.Key.A:
            dx = -1
        elif key == mcrfpy.Key.RIGHT or key == mcrfpy.Key.D:
            dx = 1
        elif key == mcrfpy.Key.PERIOD:
            # Wait a turn
            self._enemy_turn()
            self._update_fov()
            self._update_hud()
            return
        else:
            return

        if dx == 0 and dy == 0:
            return

        px = int(self.player.grid_pos.x)
        py = int(self.player.grid_pos.y)
        nx, ny = px + dx, py + dy

        # Bounds check
        if nx < 0 or nx >= MAP_W or ny < 0 or ny >= MAP_H:
            return

        # Check for enemy at target
        for edata in self.enemies:
            ex = int(edata["entity"].grid_pos.x)
            ey = int(edata["entity"].grid_pos.y)
            if ex == nx and ey == ny:
                self._attack_enemy(edata)
                self._enemy_turn()
                self._update_fov()
                self._center_camera()
                self._update_hud()
                return

        # Check walkability
        if not self.grid.at((nx, ny)).walkable:
            return

        # Move player
        self.occupied.discard((px, py))
        self.player.grid_pos = (nx, ny)
        self.occupied.add((nx, ny))

        # Check stairs
        if (nx, ny) == self.stairs_pos:
            self.depth += 1
            self._show_message(
                f"Descending to depth {self.depth}...",
                "The dungeon grows more dangerous."
            )
            self._new_level()
            self._enemy_turn()
            self._update_fov()
            self._center_camera()
            self._update_hud()
            return

        # Check items
        self._check_items(nx, ny)

        # Enemy turn
        self._enemy_turn()
        if not self.game_over:
            self._update_fov()
            self._center_camera()
            self._update_hud()


# =============================================================================
# Title screen
# =============================================================================
class TitleScreen:
    def __init__(self):
        self.scene = mcrfpy.Scene("title")
        ui = self.scene.children

        # Dark background
        bg = mcrfpy.Frame(
            pos=(0, 0), size=(1024, 768),
            fill_color=(12, 10, 20)
        )
        ui.append(bg)

        # Title
        title = mcrfpy.Caption(
            text="McRogueFace", pos=(240, 140), font=font,
            fill_color=(220, 60, 60)
        )
        title.font_size = 72
        title.outline = 4
        title.outline_color = (0, 0, 0)
        bg.children.append(title)

        # Subtitle
        sub = mcrfpy.Caption(
            text="A Python-Powered Roguelike Engine",
            pos=(270, 240), font=font,
            fill_color=(160, 160, 200)
        )
        sub.font_size = 22
        sub.outline = 2
        sub.outline_color = (0, 0, 0)
        bg.children.append(sub)

        # Features list
        features = [
            "BSP dungeon generation",
            "Wang tile autotiling",
            "Field of view & fog of war",
            "Turn-based combat",
            "Entity system with Python scripting",
        ]
        for i, feat in enumerate(features):
            dot = mcrfpy.Caption(
                text=f"  {feat}",
                pos=(320, 320 + i * 32), font=font,
                fill_color=(140, 180, 140)
            )
            dot.font_size = 16
            dot.outline = 1
            dot.outline_color = (0, 0, 0)
            bg.children.append(dot)

        # Start prompt
        start = mcrfpy.Caption(
            text="Press ENTER or SPACE to begin",
            pos=(310, 540), font=font,
            fill_color=(200, 200, 100)
        )
        start.font_size = 20
        start.outline = 2
        start.outline_color = (0, 0, 0)
        bg.children.append(start)

        # Animate the start prompt
        self._blink_visible = True
        self._start_caption = start

        # Controls hint
        controls = mcrfpy.Caption(
            text="Controls: Arrow keys / WASD to move, . to wait, R to restart",
            pos=(200, 600), font=font,
            fill_color=(100, 100, 130)
        )
        controls.font_size = 14
        controls.outline = 1
        controls.outline_color = (0, 0, 0)
        bg.children.append(controls)

        # Version info
        ver = mcrfpy.Caption(
            text="Built with McRogueFace - C++ engine, Python gameplay",
            pos=(250, 700), font=font,
            fill_color=(60, 60, 80)
        )
        ver.font_size = 12
        bg.children.append(ver)

        self.scene.on_key = self.on_key
        self.scene.activate()

        # Blink timer for "Press ENTER"
        self.blink_timer = mcrfpy.Timer("blink", self._blink, 600)

    def _blink(self, timer, runtime):
        self._blink_visible = not self._blink_visible
        if self._blink_visible:
            self._start_caption.fill_color = mcrfpy.Color(200, 200, 100)
        else:
            self._start_caption.fill_color = mcrfpy.Color(200, 200, 100, 60)

    def on_key(self, key, state):
        if state != mcrfpy.InputState.PRESSED:
            return
        if key in (mcrfpy.Key.ENTER, mcrfpy.Key.SPACE):
            self.blink_timer.stop()
            Game()


# =============================================================================
# Entry point
# =============================================================================
title = TitleScreen()
