"""UNWRITTEN - Griselda's shop. Owner: Agent C.

HOOKS["shop"]() opens a two-column buy/sell UI over the current scene.
Stock per act, x1.25 prices under griselda_grudge, buyback at half, Chalk limited
to ONE ever (flag chalk_bought). Gold is called cogs. Esc leaves.

data.items is Agent B's (parallel); imported LAZILY. Expected interface:
    data.items.ITEMS[item_id] = {
        "name": str, "sprite": int, "cost": int,
        "kind": "consumable"|"weapon"|"trinket"|"key",
        "shop": bool,          # sold by Griselda
        "act": int,            # earliest act it appears in stock (default 1)
    }
"""
import math

import mcrfpy

from core import palette
from core import ui
from core.inputstack import InputStack
from systems import dialogue
from systems.state import GS

_MENU = None


def _items():
    from data import items
    tbl = getattr(items, "ITEMS", None)
    if tbl is None:
        raise RuntimeError("shop needs data.items.ITEMS (see module docstring)")
    return tbl


def _price(item_id):
    base = int(_items()[item_id]["cost"])
    if GS.has("griselda_grudge"):
        return int(math.ceil(base * 1.25))
    return base


def _sell_price(item_id):
    return int(_items()[item_id]["cost"]) // 2


class _Shop:
    def __init__(self, scene, stack, on_close):
        self.scene = scene
        self.on_close = on_close
        self.owns_stack = stack is None
        self.stack = stack if stack is not None else InputStack(scene)
        self.ch = scene.children
        self.mode = "buy"       # "buy" | "sell"
        self.buy_menu = None
        self.sell_menu = None
        self.panel = None
        self.gold_cap = None
        self._build()
        self.stack.push(self._handle, "shop")

    # ----------------------------------------------------------------- build
    def _build(self):
        self.panel = ui.Panel(self.ch, (72, 60), (880, 640),
                              outline_color=palette.GOLD, z_index=4000)
        p = self.panel.children
        ui.Label(p, "GRISELDA'S", (32, 22), color=palette.GOLD,
                 size=palette.NAME_SIZE)
        ui.Label(p, "forty years of sharpening. buy something.", (32, 48),
                 color=palette.DIM, size=palette.SMALL_SIZE)
        self.gold_cap = ui.Label(p, "", (880 - 32, 22), color=palette.GOLD,
                                 size=palette.NAME_SIZE)
        self._refresh_gold()
        ui.Label(p, "BUY", (170, 84), color=palette.PARCH, size=palette.BODY_SIZE,
                 center=True)
        ui.Label(p, "SELL", (620, 84), color=palette.PARCH, size=palette.BODY_SIZE,
                 center=True)
        ui.Label(p, "Tab: switch column    Enter: confirm    Esc: leave",
                 (440, 612), color=palette.DIM, size=palette.SMALL_SIZE, center=True)
        self._rebuild_lists()

    def _refresh_gold(self):
        self.gold_cap.text = "%d cogs" % GS.gold
        self.gold_cap.x = 880 - 32 - self.gold_cap.size.x

    def _stock_ids(self):
        # data.items exposes stock per act via SHOP_STOCK (act -> [ids]); the
        # older per-item "shop"/"act" keys this shop was first coded against
        # never existed. Use the real table (Agent D integration).
        from data import items
        stock = getattr(items, "SHOP_STOCK", None)
        if stock is None:
            raise RuntimeError("shop needs data.items.SHOP_STOCK (act -> [ids])")
        tbl = _items()
        act = GS.act if GS.act in stock else max(stock)
        return [iid for iid in stock[act] if iid in tbl]

    def _rebuild_lists(self):
        p = self.panel.children
        if self.buy_menu is not None:
            self.buy_menu.destroy()
        if self.sell_menu is not None:
            self.sell_menu.destroy()

        buy_items = []
        for iid in self._stock_ids():
            d = _items()[iid]
            enabled, reason = True, ""
            price = _price(iid)
            if iid == "chalk" and GS.has("chalk_bought"):
                enabled, reason = False, "sold out"
            elif GS.gold < price:
                enabled, reason = False, "need %d" % price
            label = "%-14s %d" % (d["name"], price)
            buy_items.append((label, iid, enabled, reason))
        if not buy_items:
            buy_items = [("(nothing in stock)", None, False, "")]
        self.buy_menu = ui.MenuList(p, (40, 104), 360, buy_items,
                                    on_pick=self._buy, on_cancel=self._leave)

        sell_items = []
        for iid, n in sorted(GS.inventory.items()):
            if iid not in _items():
                continue
            d = _items()[iid]
            if d.get("kind") == "key":
                continue
            label = "%-12s x%d  %d" % (d["name"], n, _sell_price(iid))
            sell_items.append((label, iid, True, ""))
        if not sell_items:
            sell_items = [("(nothing to sell)", None, False, "")]
        self.sell_menu = ui.MenuList(p, (490, 104), 360, sell_items,
                                     on_pick=self._sell, on_cancel=self._leave)
        self._highlight()

    def _highlight(self):
        self.buy_menu.panel.frame.outline_color = (
            palette.GOLD if self.mode == "buy" else palette.OUTLINE)
        self.sell_menu.panel.frame.outline_color = (
            palette.GOLD if self.mode == "sell" else palette.OUTLINE)

    # ----------------------------------------------------------------- actions
    def _buy(self, iid):
        if iid is None:
            return
        price = _price(iid)
        if not GS.spend_gold(price):
            return
        GS.grant(iid, 1)
        if iid == "chalk":
            GS.add_flag("chalk_bought")
        ui.Toast(self.ch, "Bought %s" % _items()[iid]["name"], color=palette.GOLD)
        self._refresh_gold()
        self._rebuild_lists()

    def _sell(self, iid):
        if iid is None:
            return
        if GS.inventory.get(iid, 0) <= 0:
            return
        gain = _sell_price(iid)
        GS.take(iid, 1)
        GS.add_gold(gain)
        ui.Toast(self.ch, "Sold %s (+%d)" % (_items()[iid]["name"], gain),
                 color=palette.GRASS)
        self._refresh_gold()
        self._rebuild_lists()

    # ----------------------------------------------------------------- input
    def _handle(self, key, state):
        if state != mcrfpy.InputState.PRESSED:
            return True
        K = mcrfpy.Key
        if key == K.ESCAPE:
            self._leave()
            return True
        if key == K.TAB:
            self.mode = "sell" if self.mode == "buy" else "buy"
            self._highlight()
            return True
        active = self.buy_menu if self.mode == "buy" else self.sell_menu
        active.handle(key, state)
        return True

    def _leave(self):
        self.destroy()
        if self.on_close:
            self.on_close()

    def destroy(self):
        self.stack.pop("shop")
        if self.buy_menu is not None:
            self.buy_menu.destroy()
        if self.sell_menu is not None:
            self.sell_menu.destroy()
        if self.panel is not None:
            self.panel.destroy()


def open_shop(scene=None, stack=None, on_close=None):
    global _MENU
    scene = scene if scene is not None else mcrfpy.current_scene
    _MENU = _Shop(scene, stack, on_close)
    return _MENU


def _hook():
    # opened from dialogue on the overworld: reuse the overworld's input stack
    stack = None
    try:
        from systems import overworld
        if overworld.WORLD is not None:
            stack = overworld.WORLD.stack

            def _reopen():
                overworld.WORLD.frozen = False
                overworld.WORLD.refresh_hud()
            open_shop(mcrfpy.current_scene, stack, on_close=_reopen)
            overworld.WORLD.frozen = True
            return
    except Exception:
        pass
    open_shop(mcrfpy.current_scene, stack, on_close=None)


def register_hooks():
    dialogue.HOOKS["shop"] = _hook


register_hooks()
