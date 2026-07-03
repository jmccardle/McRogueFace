"""UNWRITTEN - the explorable world. Owner: Agent C.

Builds Grid-based area scenes from data.maps.AREAS: ColorLayer terrain, a player
Entity with WASD/arrow movement, props/NPCs/encounters, exits, doors, camps, a
persistent HUD, FOV for the Undercroft, and the Act-3 grey-town beat.

Public surface (ARCHITECTURE section 3):
    enter_area(area_id, spawn="start")   build/reuse "ow_<area>" scene
    refresh_area()                        re-theme after flag changes (grey town)

Registers at import:
    dialogue.HOOKS["goto_area"] = lambda area, spawn="start": _goto(area, spawn)

Integration contract for Agent B (battle) / Agent D:
    dialogue.HOOKS["battle"](pack_id, on_victory=None) must accept an optional
    on_victory keyword. The overworld passes a callback that removes the bumped
    encounter entity and remembers the kill via GS flag
    f"enc_<area>_<x>_<y>_done" so it stays gone on re-entry.
    data.enemies (Agent B, parallel) is imported LAZILY; it must expose either
    pack_first_sprite(pack)->int OR PACKS[pack] (list) + ENEMIES[id]["sprite"].
"""
import mcrfpy

from core import palette
from core import assets
from core import ui
from core import tween
from core.inputstack import InputStack
from systems import dialogue
from systems.state import GS

# ---------------------------------------------------------------- module state
WORLD = None                 # the live _World, or None
GREY_TEX = None              # desaturated texture for pre-rewake NPCs (lazy)
TEST_ENEMY_FALLBACK = None   # set to a sprite index by tests when data.enemies absent

# rewakeable NPCs -> their story flag (Act-3 grey beat)
REWAKE_FLAG = {"QUILL": "rewoke_quill", "GRISELDA": "rewoke_griselda",
               "ODD": "rewoke_odd"}

_MOVE_MS = 140               # hold-to-repeat interval
_STEP_DUR = 0.12             # slide animation per step
_WANDER_MS = 900

_DIRS = {
    mcrfpy.Key.W: (0, -1), mcrfpy.Key.UP: (0, -1),
    mcrfpy.Key.S: (0, 1),  mcrfpy.Key.DOWN: (0, 1),
    mcrfpy.Key.A: (-1, 0), mcrfpy.Key.LEFT: (-1, 0),
    mcrfpy.Key.D: (1, 0),  mcrfpy.Key.RIGHT: (1, 0),
}


def _grey_tex():
    global GREY_TEX
    if GREY_TEX is None:
        GREY_TEX = assets.TEX.hsl_shift(0, -100, -15)
    return GREY_TEX


def _clamp8(v):
    return 0 if v < 0 else (255 if v > 255 else int(v))


def _cell_offset(x, y):
    """Deterministic small per-cell variation for '.' ground (+-4)."""
    h = (x * 73856093) ^ (y * 19349663)
    return ((h & 0xff) % 9) - 4       # -4..4


# =====================================================================  _World
class _World:
    def __init__(self, area_id, spawn):
        if area_id not in _areas():
            raise KeyError("unknown area id %r (data.maps.AREAS)" % (area_id,))
        self.area_id = area_id
        self.area = _areas()[area_id]
        self.rows = self.area["map"]
        self.h = len(self.rows)
        self.w = max(len(r) for r in self.rows)
        spawns = self.area["spawns"]
        if spawn not in spawns:
            raise KeyError("unknown spawn %r for area %r (have %r)"
                           % (spawn, area_id, list(spawns)))
        self.spawn_cell = spawns[spawn]

        self.scene = None
        self.grid = None
        self.stack = None
        self.player = None
        self.terrain = None
        self.fov = None
        self.zoom = 1.0

        self.prop_entities = {}      # id -> Entity
        self.door_entities = {}      # (x,y) -> Entity
        self.npc_entities = {}       # id -> (Entity, npc_dict)
        self.enc_entities = []       # list of (Entity, enc_dict)
        self.markers = []            # scene-level gold marker Frames
        self.hud = []                # scene-level HUD drawables

        self.held = []               # currently held direction vectors (recency)
        self.frozen = False          # True while a dialogue/menu is modal above
        self._move_timer = None
        self._wander_timer = None
        self._rng = 1234567

    # -------------------------------------------------------------- geometry
    def _ch(self, x, y):
        if 0 <= y < self.h and 0 <= x < len(self.rows[y]):
            return self.rows[y][x]
        return " "

    def _blocking_char(self, ch):
        return ch in ("#", "~", " ")

    def _door_at(self, x, y):
        for d in self.area.get("door_cells", []):
            if tuple(d["pos"]) == (x, y):
                return d
        return None

    def walkable(self, x, y):
        ch = self._ch(x, y)
        d = self._door_at(x, y)
        if d is not None:
            return GS.has(d["flag"])
        return not self._blocking_char(ch)

    def cell_screen(self, x, y):
        """Top-left screen pixel of cell. The map is anchored at grid.pos with
        cells drawn at 16px * zoom, so scene-level overlays (markers) that must
        stay glued to a cell scale with zoom too."""
        return (self._gx + x * 16 * self.zoom, self._gy + y * 16 * self.zoom)

    # -------------------------------------------------------------- build
    def build(self):
        self.scene = mcrfpy.Scene("ow_" + self.area_id)
        mcrfpy.current_scene = self.scene
        GS.current_area = self.area_id

        bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=palette.INK)
        self.scene.children.append(bg)

        # BIBLE section 6 look: chunky 32px cells. grid.zoom scales the 16px
        # atlas to 32px and (per Fable, verified) works in the headless render
        # used for QA screenshots. We size the on-screen viewport to exactly the
        # zoomed map and centre it; with size == map*zoom the engine's default
        # camera (center = w/(2*zoom)) top-left-aligns tile (0,0), so a cell
        # (x,y) lands at grid.pos + (x*16*zoom, y*16*zoom). All four maps fit
        # 1024x768 at zoom 2 (hollowbrook 768x512, gearwood 832x576,
        # undercroft 832x608, study 576x384).
        self.zoom = 2.0
        map_w = self.w * 16
        map_h = self.h * 16
        disp_w = int(map_w * self.zoom)
        disp_h = int(map_h * self.zoom)
        gx = round((1024 - disp_w) / 2)
        gy = round(max(40, (768 - disp_h) / 2))

        # framing border behind the play area
        border = mcrfpy.Frame(pos=(gx - 6, gy - 6), size=(disp_w + 12, disp_h + 12),
                              fill_color=palette.PANEL, outline=2,
                              outline_color=palette.OUTLINE)
        self.scene.children.append(border)

        self.grid = mcrfpy.Grid(grid_size=(self.w, self.h),
                                pos=(gx, gy), size=(disp_w, disp_h),
                                zoom=self.zoom)
        self.grid.fill_color = palette.INK
        self.grid.z_index = 10
        self.scene.children.append(self.grid)
        self._gx, self._gy = gx, gy
        self._follow = False

        # terrain layer (below entities)
        self.terrain = mcrfpy.ColorLayer(name="terrain", z_index=-2)
        self.grid.add_layer(self.terrain)

        # walkability + transparency per cell
        for y in range(self.h):
            for x in range(self.w):
                ch = self._ch(x, y)
                pt = self.grid.at(x, y)
                pt.walkable = self.walkable(x, y)
                pt.transparent = ch not in ("#", " ")

        self._apply_terrain()

        # player entity
        self._make_player()

        # optional FOV overlay (Undercroft): dim/hide terrain outside sight
        if self.area.get("fov"):
            self.grid.fov_radius = int(self.area.get("fov_radius", 7))
            self.fov = mcrfpy.ColorLayer(name="fov", z_index=-1)
            self.grid.add_layer(self.fov)
            self.fov.fill(palette.C(palette.INK_T, 255))
            self.fov.apply_perspective(
                entity=self.player,
                visible=mcrfpy.Color(60, 52, 36, 26),     # faint warm torchlight
                discovered=palette.C(palette.INK_T, 170),  # explored: dim
                unknown=palette.C(palette.INK_T, 255))     # unseen: black
            self.grid.perspective = self.player

        self._build_doors()
        self._build_props()
        self._build_npcs()
        self._build_encounters()

        if self.fov is not None:
            self._refresh_fov()

        self._start_timers()

        self.stack = InputStack(self.scene)
        self.stack.push(self._on_key, "move")

        self.refresh_hud()

    def _make_player(self):
        if self.player is None:
            self.player = mcrfpy.Entity(grid_pos=self.spawn_cell,
                                        texture=assets.TEX, sprite_index=85)
            self.grid.entities.append(self.player)
        return self.player

    # -------------------------------------------------------------- terrain
    def _grey_factor(self):
        if (GS.act == 3 and self.area_id == "hollowbrook"
                and not GS.has("town_rewoken")):
            n = sum(1 for f in REWAKE_FLAG.values() if GS.has(f))
            return max(0.0, 0.7 - 0.23 * n)
        return None

    def _apply_terrain(self):
        factor = self._grey_factor()
        for y in range(self.h):
            row = self.rows[y]
            for x in range(len(row)):
                ch = row[x]
                base = self.area["palette"].get(ch, palette.INK_T)
                if ch == ".":
                    o = _cell_offset(x, y)
                    base = (_clamp8(base[0] + o), _clamp8(base[1] + o),
                            _clamp8(base[2] + o))
                if factor is not None:
                    base = palette.lerp_t(base, palette.GREY_T, factor)
                self.terrain.set((x, y), palette.C(base))

    # -------------------------------------------------------------- doors
    def _build_doors(self):
        for d in self.area.get("door_cells", []):
            x, y = d["pos"]
            spr = 47 if GS.has(d["flag"]) else 45
            e = mcrfpy.Entity(grid_pos=(x, y), texture=assets.TEX,
                              sprite_index=spr)
            self.grid.entities.append(e)
            self.door_entities[(x, y)] = e

    def _refresh_doors(self):
        for d in self.area.get("door_cells", []):
            x, y = d["pos"]
            e = self.door_entities.get((x, y))
            if e is not None:
                e.sprite_index = 47 if GS.has(d["flag"]) else 45
            self.grid.at(x, y).walkable = self.walkable(x, y)

    # -------------------------------------------------------------- props
    def _prop_present(self, prop):
        for f in prop.get("gone_flags", []):
            if GS.has(f):
                return False
        return True

    def _build_props(self):
        for prop in self.area.get("props", []):
            if not self._prop_present(prop):
                continue
            x, y = prop["pos"]
            spr = prop.get("sprite")
            if spr is None:
                self._add_marker(x, y)
                continue
            e = mcrfpy.Entity(grid_pos=(x, y), texture=assets.TEX,
                              sprite_index=spr)
            self.grid.entities.append(e)
            self.prop_entities[prop["id"]] = e
        self._refresh_fountain()

    def _add_marker(self, x, y):
        s = 16 * self.zoom
        px, py = self.cell_screen(x, y)
        f = mcrfpy.Frame(pos=(px + 1, py + 1), size=(s - 2, s - 2),
                         fill_color=palette.C(palette.GOLD_T, 0),
                         outline=2, outline_color=palette.GOLD)
        f.z_index = 90
        self.scene.children.append(f)
        self.markers.append((f, x, y))
        # gentle pulse so the empty spot reads as interactive
        f.animate("opacity", 0.4, 0.9, mcrfpy.Easing.EASE_IN_OUT, loop=True)

    def _refresh_fountain(self):
        e = self.prop_entities.get("fountain")
        if e is not None:
            e.sprite_index = 8 if GS.has("town_rewoken") else 7

    def _prop_scene_at(self, x, y):
        for prop in self.area.get("props", []):
            if tuple(prop["pos"]) == (x, y) and prop.get("scene") \
                    and self._prop_present(prop):
                return prop
        return None

    # -------------------------------------------------------------- npcs
    def _npc_present(self, npc):
        if GS.act < npc.get("act_min", 1):
            return False
        for f in npc.get("need_flags", []):
            if not GS.has(f):
                return False
        for f in npc.get("gone_flags", []):
            if GS.has(f):
                return False
        return True

    def _npc_scene_id(self, npc):
        nid = npc["id"]
        if GS.act == 3 and nid == "ODD":
            return "rewake_odd" if not GS.has("rewoke_odd") else "odd_ferry_study"
        scenes = npc["scene"]
        if GS.act in scenes:
            return scenes[GS.act]
        keys = sorted(k for k in scenes if k <= GS.act)
        if not keys:
            raise KeyError("NPC %r has no dialogue scene for act %d"
                           % (nid, GS.act))
        return scenes[keys[-1]]

    def _npc_texture(self, npc):
        flag = REWAKE_FLAG.get(npc["id"])
        if flag is not None and self._grey_factor() is not None \
                and not GS.has(flag):
            return _grey_tex()
        return assets.TEX

    def _build_npcs(self):
        idx = 0
        for npc in self.area.get("npcs", []):
            if not self._npc_present(npc):
                continue
            x, y = npc["pos"]
            e = mcrfpy.Entity(grid_pos=(x, y), texture=self._npc_texture(npc),
                              sprite_index=npc["sprite"])
            self.grid.entities.append(e)
            self.npc_entities[npc["id"]] = (e, npc)
            # idle bob (staggered), oscillates draw_y by ~0.06
            e.animate("draw_y", float(y) - 0.06, 0.75 + 0.05 * (idx % 6),
                      mcrfpy.Easing.EASE_IN_OUT, loop=True)
            idx += 1

    def _npc_at(self, x, y):
        for nid, (e, npc) in self.npc_entities.items():
            if int(e.grid_x) == x and int(e.grid_y) == y:
                return npc
        return None

    # -------------------------------------------------------------- encounters
    def _enc_done_key(self, enc):
        x, y = enc["pos"]
        return "enc_%s_%d_%d_done" % (self.area_id, x, y)

    def _build_encounters(self):
        for enc in self.area.get("encounters", []):
            if GS.has(self._enc_done_key(enc)):
                continue
            x, y = enc["pos"]
            spr = _pack_first_sprite(enc["pack"])
            e = mcrfpy.Entity(grid_pos=(x, y), texture=assets.TEX,
                              sprite_index=spr)
            self.grid.entities.append(e)
            enc = dict(enc)
            enc["home"] = (x, y)
            self.enc_entities.append((e, enc))

    def _enc_at(self, x, y):
        for e, enc in self.enc_entities:
            if int(e.grid_x) == x and int(e.grid_y) == y:
                return (e, enc)
        return None

    def _rand(self, n):
        self._rng = (self._rng * 1103515245 + 12345) & 0x7fffffff
        return self._rng % n

    def _is_current(self):
        """True only while this world's scene is the one on screen. Guards the
        held-key move + encounter-wander timers so they never fire under a
        battle/menu/dialogue scene that has taken over current_scene."""
        return mcrfpy.current_scene is self.scene

    def _wander(self, timer, runtime):
        if self.frozen or not self._is_current():
            return
        for e, enc in self.enc_entities:
            leash = enc.get("leash", 2)
            if leash == 0:
                continue
            hx, hy = enc["home"]
            dx, dy = [(0, -1), (0, 1), (-1, 0), (1, 0), (0, 0)][self._rand(5)]
            nx, ny = int(e.grid_x) + dx, int(e.grid_y) + dy
            if abs(nx - hx) > leash or abs(ny - hy) > leash:
                continue
            if not self.walkable(nx, ny):
                continue
            if self._occupied(nx, ny, ignore=e):
                continue
            e.grid_pos = (nx, ny)
            e.animate("draw_x", float(nx), 0.25, mcrfpy.Easing.EASE_OUT)
            e.animate("draw_y", float(ny), 0.25, mcrfpy.Easing.EASE_OUT)

    def _occupied(self, x, y, ignore=None):
        if self.player is not None and int(self.player.grid_x) == x \
                and int(self.player.grid_y) == y:
            return True
        for e, _n in self.enc_entities:
            if e is ignore:
                continue
            if int(e.grid_x) == x and int(e.grid_y) == y:
                return True
        if self._npc_at(x, y) is not None:
            return True
        return False

    # -------------------------------------------------------------- timers
    def _start_timers(self):
        self._move_timer = mcrfpy.Timer("ow_move", self._repeat_move, _MOVE_MS)
        if any(enc.get("leash", 2) != 0
               for _e, enc in self.enc_entities):
            self._wander_timer = mcrfpy.Timer("ow_wander", self._wander,
                                              _WANDER_MS)

    def _repeat_move(self, timer, runtime):
        if self.frozen or not self.held or not self._is_current():
            return
        dx, dy = self.held[-1]
        self.try_step(dx, dy)

    # -------------------------------------------------------------- input
    def _on_key(self, key, state):
        K = mcrfpy.Key
        if self.frozen:
            return False
        if state == mcrfpy.InputState.PRESSED:
            if key in _DIRS:
                d = _DIRS[key]
                if d in self.held:
                    self.held.remove(d)
                self.held.append(d)
                self.try_step(d[0], d[1])
                return True
            if key in (K.E, K.ENTER, K.SPACE):
                self._interact_here()
                return True
            if key in (K.ESCAPE, K.TAB):
                self._open_party_menu()
                return True
            return False
        else:  # RELEASED
            if key in _DIRS and _DIRS[key] in self.held:
                self.held.remove(_DIRS[key])
                return True
            return False

    # -------------------------------------------------------------- movement
    def try_step(self, dx, dy):
        if self.frozen:
            return
        px, py = int(self.player.grid_x), int(self.player.grid_y)
        tx, ty = px + dx, py + dy

        npc = self._npc_at(tx, ty)
        if npc is not None:
            self.talk(npc)
            return
        hit = self._enc_at(tx, ty)
        if hit is not None:
            self.fight(hit)
            return
        d = self._door_at(tx, ty)
        if d is not None and not GS.has(d["flag"]):
            self.run_dialogue(d["locked_scene"])
            return
        prop = self._prop_scene_at(tx, ty)
        if prop is not None and not self.walkable(tx, ty):
            self.trigger_prop(prop)
            return
        if not self.walkable(tx, ty):
            self._nudge(dx, dy)
            return

        self.player.grid_pos = (tx, ty)
        self.player.animate("draw_x", float(tx), _STEP_DUR, mcrfpy.Easing.EASE_OUT)
        self.player.animate("draw_y", float(ty), _STEP_DUR, mcrfpy.Easing.EASE_OUT)
        self.after_move(tx, ty)

    def _nudge(self, dx, dy):
        px, py = int(self.player.grid_x), int(self.player.grid_y)
        if dx:
            self.player.animate("draw_x", px + 0.22 * dx, 0.06,
                                mcrfpy.Easing.EASE_OUT,
                                callback=lambda *_a: self.player.animate(
                                    "draw_x", float(px), 0.08))
        elif dy:
            self.player.animate("draw_y", py + 0.22 * dy, 0.06,
                                mcrfpy.Easing.EASE_OUT,
                                callback=lambda *_a: self.player.animate(
                                    "draw_y", float(py), 0.08))

    def _refresh_fov(self):
        """Update the FOV overlay and hide entities the player cannot see."""
        self.player.update_visibility()
        px, py = int(self.player.grid_x), int(self.player.grid_y)
        r = int(self.grid.fov_radius)
        self.grid.compute_fov((px, py), r)
        groups = [e for e, _n in self.enc_entities]
        groups += [e for e, _n in self.npc_entities.values()]
        groups += list(self.prop_entities.values())
        groups += list(self.door_entities.values())
        for e in groups:
            e.visible = self.grid.is_in_fov(int(e.grid_x), int(e.grid_y))
        for f, mx, my in self.markers:
            f.visible = self.grid.is_in_fov(mx, my)
        self.player.visible = True

    def after_move(self, x, y):
        if self.fov is not None:
            self._refresh_fov()
        # step-onto prop scene
        prop = self._prop_scene_at(x, y)
        if prop is not None:
            self.trigger_prop(prop)
            return
        # auto props (proximity, within 1 cell)
        for p in self.area.get("props", []):
            if not p.get("auto") or not self._prop_present(p):
                continue
            once = p.get("once")
            if once and GS.has(once):
                continue
            ax, ay = p["pos"]
            if abs(ax - x) <= 1 and abs(ay - y) <= 1:
                self.trigger_prop(p)
                return
        # exits
        for ex in self.area.get("exits", []):
            if tuple(ex["pos"]) == (x, y):
                self._take_exit(ex)
                return

    def _interact_here(self):
        x, y = int(self.player.grid_x), int(self.player.grid_y)
        camp = self.area.get("camp")
        if camp and tuple(camp["pos"]) == (x, y):
            for f in camp.get("need_flags", []):
                if not GS.has(f):
                    return
            self.run_dialogue(camp["scene"])
            return
        prop = self._prop_scene_at(x, y)
        if prop is not None:
            self.trigger_prop(prop)

    # -------------------------------------------------------------- triggers
    def talk(self, npc):
        self.run_dialogue(self._npc_scene_id(npc))

    def trigger_prop(self, prop):
        self.run_dialogue(prop["scene"])

    def _take_exit(self, ex):
        if ex.get("scene"):
            self.run_dialogue(ex["scene"])
        else:
            _goto(ex["to"], ex.get("spawn", "start"))

    def fight(self, hit):
        e, enc = hit
        hook = dialogue.HOOKS.get("battle")
        if hook is None:
            raise RuntimeError(
                "encounter bump needs dialogue.HOOKS['battle'](pack, "
                "on_victory=) - Agent B must register it")
        done_key = self._enc_done_key(enc)
        # freeze the overworld for the whole battle; on_victory/on_defeat unfreeze
        self.frozen = True
        self.held = []

        def on_victory(*_a):
            try:
                e.die()
            except Exception:
                pass
            if (e, enc) in self.enc_entities:
                self.enc_entities.remove((e, enc))
            GS.add_flag(done_key)
            self._post_dialogue(None)

        def on_defeat(*_a):
            self.frozen = False

        hook(enc["pack"], on_victory=on_victory, on_defeat=on_defeat)

    def run_dialogue(self, scene_id, after=None):
        self.frozen = True
        self.held = []
        dialogue.run_scene(scene_id,
                           on_done=lambda: self._post_dialogue(after),
                           stack=self.stack)

    def _post_dialogue(self, after):
        self.frozen = False
        self.refresh_theme()
        self.refresh_hud()
        if after:
            after()

    def _open_party_menu(self):
        try:
            from systems import party_menu
        except Exception as ex:
            raise RuntimeError("party menu unavailable: %s" % (ex,))
        self.frozen = True
        self.held = []

        def _closed():
            self.frozen = False
            self.refresh_hud()
        party_menu.open_menu(self.scene, self.stack, on_close=_closed)

    # -------------------------------------------------------------- refresh
    def refresh_theme(self):
        """Re-apply terrain wash, NPC textures, doors, fountain: the grey beat.
        Color literally returns to town as rewoke_* flags are set."""
        was_rewoken = GS.has("town_rewoken")
        if (GS.act == 3 and self.area_id == "hollowbrook"
                and not was_rewoken
                and all(GS.has(f) for f in REWAKE_FLAG.values())):
            GS.add_flag("town_rewoken")
            ui.TitleBanner(self.scene.children, self.area.get("banner"))

        self._apply_terrain()
        for nid, (e, npc) in self.npc_entities.items():
            e.texture = self._npc_texture(npc)
        self._refresh_doors()
        self._refresh_fountain()

    def refresh_hud(self):
        for d in self.hud:
            try:
                self.scene.children.remove(d)
            except Exception:
                pass
        self.hud = []
        grey = self._grey_factor() is not None
        name = self.area.get("banner_grey") if grey else self.area.get("banner")

        loc = ui.Label(self.scene.children, name or self.area_id.upper(),
                       (18, 14), color=palette.DIM, size=palette.SMALL_SIZE)
        loc.z_index = 5000
        self.hud.append(loc)

        cogs = ui.Label(self.scene.children, "%d cogs" % GS.gold, (0, 14),
                        color=palette.GOLD, size=palette.SMALL_SIZE)
        cogs.x = 1024 - 18 - cogs.size.x
        cogs.z_index = 5000
        self.hud.append(cogs)

        # up to 3 party mini-cards, bottom-left
        base_y = 700
        for i, cid in enumerate(GS.party[:3]):
            cs = GS.roster.get(cid)
            if cs is None:
                continue
            cx = 16 + i * 132
            card = mcrfpy.Frame(pos=(cx, base_y), size=(124, 54),
                                fill_color=palette.PANEL, outline=2,
                                outline_color=palette.OUTLINE)
            card.z_index = 5000
            self.scene.children.append(card)
            self.hud.append(card)
            chip = mcrfpy.Frame(pos=(6, 6), size=(40, 40),
                                fill_color=palette.INSET, outline=1,
                                outline_color=palette.OUTLINE)
            card.children.append(chip)
            spr = assets.PORTRAITS.get(cid, 0) or 0
            s = mcrfpy.Sprite(pos=(4, 4), texture=assets.TEX, sprite_index=spr)
            s.scale = 2.0
            chip.children.append(s)
            ui.Label(card.children, cid, (54, 6), color=palette.PARCH,
                     size=palette.SMALL_SIZE)
            try:
                hp, mhp = cs.hp, cs.max_hp
            except Exception:
                hp, mhp = 1, 1
            hb = ui.Bar(card.children, (54, 28), (62, 16), palette.BLOOD,
                        cur=hp, maxv=mhp, show_text=False)

    # -------------------------------------------------------------- arrival
    def arrival_scene(self):
        """Dialogue to auto-run once the area is built and the player arrives.
        Wires the authored-but-otherwise-unreferenced Bell appearance #3
        (script_act3 'hollowbrook_grey') to the grey-town arrival."""
        if (self.area_id == "hollowbrook" and GS.act == 3
                and not GS.has("bell_3_done")
                and not GS.has("town_rewoken")):
            return "hollowbrook_grey"
        return None

    # -------------------------------------------------------------- banner
    def show_banner(self):
        grey = (GS.act == 3 and self.area_id == "hollowbrook"
                and not GS.has("town_rewoken"))
        text = self.area.get("banner_grey") if grey and self.area.get(
            "banner_grey") else self.area.get("banner")
        if text:
            ui.TitleBanner(self.scene.children, text)

    # -------------------------------------------------------------- teardown
    def teardown(self):
        for t in (self._move_timer, self._wander_timer):
            if t is not None:
                try:
                    t.stop()
                except Exception:
                    pass
        self._move_timer = None
        self._wander_timer = None
        self.held = []


# =====================================================================  helpers
def _areas():
    from data import maps
    return maps.AREAS


def _pack_first_sprite(pack):
    """Sprite index of a pack's first enemy. data.enemies is Agent B's (parallel);
    imported lazily. Tests without it set TEST_ENEMY_FALLBACK."""
    enemies = None
    try:
        from data import enemies as _en
        enemies = _en
    except Exception:
        enemies = None
    if enemies is not None:
        fn = getattr(enemies, "pack_first_sprite", None)
        if callable(fn):
            return int(fn(pack))
        packs = getattr(enemies, "PACKS", None)
        stats = getattr(enemies, "ENEMIES", None) or getattr(enemies, "STATS", None)
        if packs is not None and pack in packs:
            members = packs[pack]
            if isinstance(members, dict):
                members = members.get("enemies") or members.get("members") or []
            m0 = members[0] if members else None
            if isinstance(m0, dict):
                if "sprite" in m0:
                    return int(m0["sprite"])
                m0 = m0.get("id") or m0.get("enemy") or m0.get("name")
            if stats is not None and m0 in stats and "sprite" in stats[m0]:
                return int(stats[m0]["sprite"])
    if TEST_ENEMY_FALLBACK is not None:
        return int(TEST_ENEMY_FALLBACK)
    raise KeyError(
        "cannot resolve first-enemy sprite for pack %r: data.enemies must expose "
        "pack_first_sprite(pack) or PACKS[pack] + ENEMIES[id]['sprite']" % (pack,))


# =====================================================================  public
def enter_area(area_id, spawn="start"):
    """Build (or rebuild) the scene for an area and make it current."""
    global WORLD
    if WORLD is not None:
        WORLD.teardown()
    WORLD = _World(area_id, spawn)
    WORLD.build()
    WORLD.show_banner()
    arr = WORLD.arrival_scene()
    if arr is not None:
        WORLD.run_dialogue(arr)
    return WORLD


def refresh_area():
    """Re-apply palette/NPCs/doors after flag changes (Act-3 grey beat)."""
    if WORLD is None:
        raise RuntimeError("refresh_area() called with no active world")
    WORLD.refresh_theme()
    WORLD.refresh_hud()


def _goto(area, spawn="start"):
    scn = mcrfpy.current_scene
    if (WORLD is not None and scn is not None
            and getattr(scn, "name", "").startswith("ow_")):
        tween.fade_scene(scn, on_done=lambda: enter_area(area, spawn))
    else:
        enter_area(area, spawn)


def register_hooks():
    dialogue.HOOKS["goto_area"] = lambda area, spawn="start": _goto(area, spawn)


register_hooks()
