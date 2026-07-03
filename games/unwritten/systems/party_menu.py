"""UNWRITTEN - pause / party menu. Owner: Agent C.

Opened by Esc/Tab in the overworld, or directly to the swap view via
HOOKS["swap_menu"] (which returns to whatever ran it - dialogue may continue).

Tabs: PARTY (swap active-3 ordering), EQUIP (weapon/trinket from inventory),
ITEMS (use consumables outside battle), STATS (detail), KEY (key items;
blank_book always first). Footer shows gold and Story Points ("The Book: N
entries"). NYX cannot be item-healed: the canon line "The tonic passes through
her." shows as a Toast. Esc closes (or backs out of a picker).

data.items is Agent B's (parallel); imported LAZILY. Expected interface:
    data.items.ITEMS[id] = {"name","sprite","cost","kind"
        ("consumable"|"weapon"|"trinket"|"key"), "heal"(int), "sp"(int)}
    data.items.EQUIP[id] = {stat: delta}   # weapons + trinkets
"""
import mcrfpy

from core import palette
from core import assets
from core import ui
from core.inputstack import InputStack
from systems.state import GS, CHAR_TAGS
from systems import dialogue

_MENU = None
TABS = ["PARTY", "EQUIP", "ITEMS", "STATS", "KEY"]

KEY_ITEM_NAMES = {
    "blank_book": "The Blank Book - heavier every day.",
    "brass_key": "Brass Key",
    "gatekeepers_tooth": "Gatekeeper's Tooth",
    "the_wick": "The Wick",
}


def _items_tbl():
    from data import items
    tbl = getattr(items, "ITEMS", None)
    if tbl is None:
        raise RuntimeError("party menu needs data.items.ITEMS (see docstring)")
    return tbl


def _item_name(iid):
    try:
        return _items_tbl()[iid]["name"]
    except Exception:
        return iid


def _consumable_desc(d):
    """One-line effect summary for a consumable record (data.items schema uses
    effect/amount, not heal/sp keys)."""
    effect = d.get("effect")
    amount = d.get("amount", 0)
    if effect in ("heal", "cleanse_heal"):
        base = "heal %d" % int(amount)
        return base + " + cleanse" if effect == "cleanse_heal" else base
    if effect == "sp":
        return "+%d SP" % int(amount)
    if effect == "aoe_damage":
        return "%d AoE (battle)" % int(amount)
    if effect == "revive":
        return "revive (battle)"
    return ""


class _PartyMenu:
    def __init__(self, scene, stack, on_close, view="PARTY"):
        self.scene = scene
        self.on_close = on_close
        self.owns_stack = stack is None
        self.stack = stack if stack is not None else InputStack(scene)
        self.ch = scene.children
        self.tab = TABS.index(view) if view in TABS else 0
        self.sel = 0
        self.char_idx = 0
        self.swap_pick = None       # cid selected for swap on the PARTY tab
        self.picker = None          # active secondary MenuList
        self.nodes = []             # rebuildable drawables
        self.panel = ui.Panel(self.ch, (40, 40), (944, 688),
                              outline_color=palette.GOLD, z_index=4000)
        self._render()
        self.stack.push(self._handle, "party")

    # ----------------------------------------------------------------- render
    def _clear(self):
        for n in self.nodes:
            try:
                self.panel.children.remove(n)
            except Exception:
                pass
        self.nodes = []
        if self.picker is not None:
            self.picker.destroy()
            self.picker = None

    def _lab(self, text, pos, color=None, size=palette.BODY_SIZE, center=False):
        c = ui.Label(self.panel.children, text, pos, color=color, size=size,
                     center=center)
        self.nodes.append(c)
        return c

    def _render(self):
        self._clear()
        # tab bar
        for i, name in enumerate(TABS):
            x = 40 + i * 150
            self._lab(name, (x, 24),
                      color=palette.GOLD if i == self.tab else palette.DIM,
                      size=palette.NAME_SIZE)
        # divider
        div = mcrfpy.Frame(pos=(24, 56), size=(896, 2), fill_color=palette.OUTLINE)
        self.panel.children.append(div)
        self.nodes.append(div)
        # footer
        self._lab("%d cogs" % GS.gold, (32, 646), color=palette.GOLD,
                  size=palette.BODY_SIZE)
        self._lab("The Book: %d entries" % GS.points, (944 - 32 - 220, 646),
                  color=palette.GOLD, size=palette.BODY_SIZE)
        self._lab("Q/E tabs   arrows move   Enter select   Esc close",
                  (472, 668), color=palette.DIM, size=palette.SMALL_SIZE,
                  center=True)

        tab = TABS[self.tab]
        if tab == "PARTY":
            self._render_party()
        elif tab == "EQUIP":
            self._render_char_list(self._on_equip_char)
            self._render_char_detail()
        elif tab == "ITEMS":
            self._render_items()
        elif tab == "STATS":
            self._render_char_list(None)
            self._render_char_detail(full=True)
        elif tab == "KEY":
            self._render_key()

    def _roster_ids(self):
        # active party first (in order), then benched
        active = [c for c in GS.party if c in GS.roster]
        benched = [c for c in GS.roster if c not in active]
        return active + benched

    def _render_party(self):
        self._lab("active party is marked *. Enter picks, Enter again swaps.",
                  (32, 70), color=palette.DIM, size=palette.SMALL_SIZE)
        ids = self._roster_ids()
        y = 100
        for i, cid in enumerate(ids):
            cs = GS.roster[cid]
            mark = "*" if cid in GS.party else " "
            sel = ">" if i == self.sel else " "
            pick = " (picked)" if cid == self.swap_pick else ""
            color = palette.GOLD if i == self.sel else palette.PARCH
            row = self._lab("%s %s %-9s Lv%d%s" % (sel, mark, cid, cs.level, pick),
                            (40, y), color=color, size=palette.BODY_SIZE)
            # portrait chip
            chip = mcrfpy.Frame(pos=(300, y - 4), size=(30, 30),
                                fill_color=palette.INSET, outline=1,
                                outline_color=palette.OUTLINE)
            self.panel.children.append(chip)
            self.nodes.append(chip)
            spr = assets.PORTRAITS.get(cid, 0) or 0
            s = mcrfpy.Sprite(pos=(1, 1), texture=assets.TEX, sprite_index=spr)
            s.scale = 1.75
            chip.children.append(s)
            hb = ui.Bar(self.panel.children, (350, y - 2), (150, 14),
                        palette.BLOOD, cur=cs.hp, maxv=cs.max_hp)
            self.nodes.append(hb.bg)
            sb = ui.Bar(self.panel.children, (520, y - 2), (120, 14),
                        palette.TEAL, cur=cs.sp, maxv=cs.max_sp)
            self.nodes.append(sb.bg)
            tag = CHAR_TAGS.get(cid, "")
            self._lab(tag, (660, y), color=palette.DIM, size=palette.SMALL_SIZE)
            y += 40

    def _render_char_list(self, on_pick):
        ids = self._roster_ids()
        if self.char_idx >= len(ids):
            self.char_idx = 0
        y = 90
        for i, cid in enumerate(ids):
            cs = GS.roster[cid]
            sel = ">" if i == self.char_idx else " "
            color = palette.GOLD if i == self.char_idx else palette.PARCH
            self._lab("%s %-9s Lv%d" % (sel, cid, cs.level), (40, y),
                      color=color, size=palette.BODY_SIZE)
            y += 34

    def _render_char_detail(self, full=False):
        ids = self._roster_ids()
        if not ids:
            return
        cid = ids[min(self.char_idx, len(ids) - 1)]
        cs = GS.roster[cid]
        x = 400
        self._lab(cid, (x, 90), color=palette.GOLD, size=palette.NAME_SIZE)
        try:
            st = cs.stats()
        except Exception:
            st = {}
        rows = [("Level", cs.level), ("HP", "%d/%d" % (cs.hp, cs.max_hp)),
                ("SP", "%d/%d" % (cs.sp, cs.max_sp))]
        for k in ("ATK", "MAG", "DEF", "SPD"):
            rows.append((k, st.get(k, "-")))
        y = 126
        for k, v in rows:
            self._lab("%-6s %s" % (k, v), (x, y), color=palette.PARCH,
                      size=palette.BODY_SIZE)
            y += 28
        self._lab("Weapon:  %s" % (_item_name(cs.weapon) if cs.weapon else "-"),
                  (x, y + 8), color=palette.DIM, size=palette.SMALL_SIZE)
        self._lab("Trinket: %s" % (_item_name(cs.trinket) if cs.trinket else "-"),
                  (x, y + 30), color=palette.DIM, size=palette.SMALL_SIZE)
        if TABS[self.tab] == "EQUIP":
            self._lab("Enter: change equipment", (x, y + 64),
                      color=palette.GOLD, size=palette.SMALL_SIZE)

    def _render_items(self):
        tbl = _items_tbl()
        rows = []
        for iid, n in sorted(GS.inventory.items()):
            d = tbl.get(iid)
            if not d or d.get("kind") != "consumable":
                continue
            rows.append((iid, n, d))
        self._lab("use a consumable, then choose who receives it.", (32, 70),
                  color=palette.DIM, size=palette.SMALL_SIZE)
        y = 100
        if not rows:
            self._lab("(no consumables)", (40, y), color=palette.DIM)
            return
        for i, (iid, n, d) in enumerate(rows):
            sel = ">" if i == self.sel else " "
            color = palette.GOLD if i == self.sel else palette.PARCH
            eff = _consumable_desc(d)
            self._lab("%s %-14s x%d   %s" % (sel, d["name"], n, eff),
                      (40, y), color=color, size=palette.BODY_SIZE)
            y += 32
        self._item_rows = rows

    def _render_key(self):
        self._lab("key items", (32, 70), color=palette.DIM,
                  size=palette.SMALL_SIZE)
        keys = list(GS.key_items)
        ordered = (["blank_book"] if "blank_book" in keys else [])
        ordered += [k for k in keys if k != "blank_book"]
        if "blank_book" not in keys:
            ordered = ["blank_book"] + ordered   # always listed first
        y = 100
        for k in ordered:
            name = KEY_ITEM_NAMES.get(k, k)
            self._lab("- %s" % name, (40, y), color=palette.PARCH,
                      size=palette.BODY_SIZE)
            y += 30

    # ----------------------------------------------------------------- pickers
    def _on_equip_char(self):
        ids = self._roster_ids()
        cid = ids[self.char_idx]
        tbl = _items_tbl()
        opts = []
        for slot in ("weapon", "trinket"):
            for iid, n in sorted(GS.inventory.items()):
                d = tbl.get(iid)
                if d and d.get("kind") == slot:
                    opts.append(("%s: %s" % (slot, d["name"]), (slot, iid),
                                 True, ""))
        opts.append(("(remove weapon)", ("weapon", None), True, ""))
        opts.append(("(remove trinket)", ("trinket", None), True, ""))
        if not opts:
            return
        self.picker = ui.MenuList(self.panel.children, (400, 300), 320, opts,
                                  on_pick=lambda v: self._do_equip(cid, v),
                                  on_cancel=self._close_picker,
                                  title="Equip %s" % cid)

    def _do_equip(self, cid, val):
        slot, iid = val
        cs = GS.roster[cid]
        if slot == "weapon":
            cs.weapon = iid
        else:
            cs.trinket = iid
        self._close_picker()
        self._render()

    def _open_item_target(self, iid, d):
        opts = []
        for cid in self._roster_ids():
            opts.append((cid, cid, True, ""))
        self.picker = ui.MenuList(self.panel.children, (400, 260), 300, opts,
                                  on_pick=lambda v: self._use_item(iid, d, v),
                                  on_cancel=self._close_picker,
                                  title="Use %s on" % d["name"])

    def _use_item(self, iid, d, cid):
        cs = GS.roster[cid]
        effect = d.get("effect")
        amount = d.get("amount", 0)
        heals = effect in ("heal", "cleanse_heal")
        restores_sp = effect == "sp"
        # NYX cannot be restored by items (SYSTEMS section 3); canon line.
        if cid == "NYX" and (heals or restores_sp):
            ui.Toast(self.ch, "The tonic passes through her.", color=palette.DIM)
            self._close_picker()
            return
        if GS.inventory.get(iid, 0) <= 0:
            self._close_picker()
            return
        if heals:
            cs.hp = cs.hp + int(amount)
        elif restores_sp:
            cs.sp = cs.sp + int(amount)
        else:
            # revive / aoe_damage are battle-only; not usable from the menu
            ui.Toast(self.ch, "Cannot use %s here." % d["name"], color=palette.DIM)
            self._close_picker()
            return
        GS.take(iid, 1)
        ui.Toast(self.ch, "Used %s" % d["name"], color=palette.GRASS)
        self._close_picker()
        self._render()

    def _close_picker(self):
        if self.picker is not None:
            self.picker.destroy()
            self.picker = None

    # ----------------------------------------------------------------- swap
    def _party_pick(self):
        ids = self._roster_ids()
        cid = ids[self.sel]
        if self.swap_pick is None:
            self.swap_pick = cid
        else:
            self._do_swap(self.swap_pick, cid)
            self.swap_pick = None
        self._render()

    def _do_swap(self, a, b):
        if a == b:
            return
        pa = GS.party.index(a) if a in GS.party else None
        pb = GS.party.index(b) if b in GS.party else None
        if pa is not None and pb is not None:
            GS.party[pa], GS.party[pb] = GS.party[pb], GS.party[pa]
        elif pa is not None and pb is None:
            GS.party[pa] = b
        elif pa is None and pb is not None:
            GS.party[pb] = a
        # else both benched: no-op

    # ----------------------------------------------------------------- input
    def _list_len(self):
        tab = TABS[self.tab]
        if tab in ("PARTY",):
            return len(self._roster_ids())
        if tab in ("EQUIP", "STATS"):
            return len(self._roster_ids())
        if tab == "ITEMS":
            return len(getattr(self, "_item_rows", []))
        return 0

    def _handle(self, key, state):
        if state != mcrfpy.InputState.PRESSED:
            return True
        K = mcrfpy.Key
        if self.picker is not None:
            if key == K.ESCAPE:
                self._close_picker()
                return True
            self.picker.handle(key, state)
            return True
        if key == K.ESCAPE:
            self._close()
            return True
        if key in (K.Q, K.LEFT):
            self.tab = (self.tab - 1) % len(TABS)
            self.sel = 0
            self._render()
            return True
        if key in (K.E, K.RIGHT):
            self.tab = (self.tab + 1) % len(TABS)
            self.sel = 0
            self._render()
            return True
        n = self._list_len()
        tab = TABS[self.tab]
        cur = self.char_idx if tab in ("EQUIP", "STATS") else self.sel
        if key in (K.W, K.UP) and n:
            cur = (cur - 1) % n
        elif key in (K.S, K.DOWN) and n:
            cur = (cur + 1) % n
        elif key in (K.ENTER, K.SPACE):
            self._activate()
            return True
        else:
            return True
        if tab in ("EQUIP", "STATS"):
            self.char_idx = cur
        else:
            self.sel = cur
        self._render()
        return True

    def _activate(self):
        tab = TABS[self.tab]
        if tab == "PARTY":
            self._party_pick()
        elif tab == "EQUIP":
            self._on_equip_char()
        elif tab == "ITEMS":
            rows = getattr(self, "_item_rows", [])
            if rows:
                iid, n, d = rows[self.sel]
                self._open_item_target(iid, d)

    def _close(self):
        self.destroy()
        if self.on_close:
            self.on_close()

    def destroy(self):
        self._close_picker()
        self.stack.pop("party")
        self.panel.destroy()


def open_menu(scene=None, stack=None, on_close=None, view="PARTY"):
    global _MENU
    scene = scene if scene is not None else mcrfpy.current_scene
    _MENU = _PartyMenu(scene, stack, on_close, view=view)
    return _MENU


def _swap_hook():
    """HOOKS['swap_menu']: open directly to the swap (PARTY) view on the active
    overworld stack, so dialogue continuing beneath resumes when it closes."""
    stack = None
    try:
        from systems import overworld
        if overworld.WORLD is not None:
            stack = overworld.WORLD.stack
    except Exception:
        stack = None
    open_menu(mcrfpy.current_scene, stack, on_close=None, view="PARTY")


def register_hooks():
    dialogue.HOOKS["swap_menu"] = _swap_hook


register_hooks()
