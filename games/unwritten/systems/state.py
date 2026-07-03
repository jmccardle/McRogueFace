"""UNWRITTEN - GameState singleton. Owner: Agent A.

The single source of mutable game state (ARCHITECTURE section 5: no global
mutable state lives outside this module). Numeric tables (base stats, growth,
equipment bonuses) live in data.characters / data.items, which Agent B owns and
may not have written yet - so they are imported LAZILY inside methods. A missing
table at runtime raises (fail early); there is no fallback here.

Expected data interfaces (documented for Agent B):
  data.characters.BASE[char_id]   -> {"HP","SP","ATK","MAG","DEF","SPD": int}
  data.characters.GROWTH[char_id] -> list of up to 7 per-level growth dicts
                                     (applied for levels 2..8; extra levels reuse
                                      the last entry)
  data.items.EQUIP[item_id]       -> {stat: delta, ...} for weapons/trinkets
"""

STAT_KEYS = ("HP", "SP", "ATK", "MAG", "DEF", "SPD")

# Dialogue tag per character (BIBLE section 2). Canonical, owned here so the
# dialogue runner can evaluate ("tag", X) reqs without importing data.characters.
CHAR_TAGS = {
    "PIP": "NIMBLE",
    "BRAMBLE": "OATH",
    "MOTH": "LITURGY",
    "VERA": "ALCHEMY",
    "CANTOR": "RESONANCE",
    "NYX": "SHADOW",
}


def xp_for_level(level):
    """Cumulative XP required to BE at `level`. Matches SYSTEMS section 1
    (20/60/120/200/300/420/560 for levels 2..8)."""
    return 10 * level * (level - 1)


def level_for_xp(xp):
    """Highest level (1..8) whose cumulative threshold is <= xp."""
    lvl = 1
    while lvl < 8 and xp >= xp_for_level(lvl + 1):
        lvl += 1
    return lvl


class CharState:
    """One character's live state. Stats are computed lazily from the data
    tables so importing state without data.characters present does not crash."""

    def __init__(self, char_id, level=1):
        self.char_id = char_id
        self.level = max(1, int(level))
        self.xp = xp_for_level(self.level)
        self.weapon = None
        self.trinket = None
        self._hp = None
        self._sp = None

    # ---- derived stats -----------------------------------------------------
    def _base_growth(self):
        from data import characters
        if self.char_id not in characters.BASE:
            raise KeyError("no base stats for %r in data.characters.BASE"
                           % (self.char_id,))
        return characters.BASE[self.char_id], characters.GROWTH[self.char_id]

    def _equip_bonus(self):
        bonus = {}
        if not self.weapon and not self.trinket:
            return bonus
        from data import items
        for eid in (self.weapon, self.trinket):
            if not eid:
                continue
            if eid not in items.EQUIP:
                raise KeyError("unknown equipment id %r in data.items.EQUIP"
                               % (eid,))
            for k, v in items.EQUIP[eid].items():
                bonus[k] = bonus.get(k, 0) + v
        return bonus

    def stats(self):
        base, growth = self._base_growth()
        out = {k: base.get(k, 0) for k in STAT_KEYS}
        for i in range(self.level - 1):
            g = growth[i] if i < len(growth) else growth[-1]
            for k, v in g.items():
                out[k] = out.get(k, 0) + v
        for k, v in self._equip_bonus().items():
            out[k] = out.get(k, 0) + v
        return out

    @property
    def max_hp(self):
        return self.stats()["HP"]

    @property
    def max_sp(self):
        return self.stats()["SP"]

    @property
    def hp(self):
        if self._hp is None:
            self._hp = self.max_hp
        return self._hp

    @hp.setter
    def hp(self, v):
        self._hp = max(0, min(int(v), self.max_hp))

    @property
    def sp(self):
        if self._sp is None:
            self._sp = self.max_sp
        return self._sp

    @sp.setter
    def sp(self, v):
        self._sp = max(0, min(int(v), self.max_sp))

    @property
    def alive(self):
        return self.hp > 0

    def full_heal(self):
        self._hp = self.max_hp
        self._sp = self.max_sp

    def add_xp(self, amount):
        """Add XP; return list of new level numbers reached (may be empty)."""
        self.xp += int(amount)
        target = level_for_xp(self.xp)
        gained = []
        while self.level < target:
            self.level += 1
            gained.append(self.level)
            # top up current pools to the new maxima
            self._hp = self.max_hp
            self._sp = self.max_sp
        return gained


class GameState:
    """Singleton game state. Access via state.GS."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.party = []                 # active char ids, order, max 3
        self.roster = {}                # char_id -> CharState
        self.flags = set()
        self.points = 0
        self.gold = 0
        self.inventory = {}             # item_id -> count
        self.key_items = []
        self.act = 1
        self.hum_hook = None            # set by dialogue runner: pulses the Book

    # ---- flags / points ----------------------------------------------------
    def has(self, flag):
        return flag in self.flags

    def add_flag(self, flag):
        self.flags.add(flag)

    def remove_flag(self, flag):
        self.flags.discard(flag)

    def add_points(self, n):
        self.points += int(n)
        if self.hum_hook:
            self.hum_hook()

    # ---- party / roster ----------------------------------------------------
    def _avg_level(self):
        levels = [c.level for c in self.roster.values()]
        if not levels:
            return 1
        return max(1, sum(levels) // len(levels))

    def recruit(self, char_id, level):
        """Add a character to the roster (and to the active party if there is
        room, max 3). level 0 means 'party average level'."""
        if char_id not in self.roster:
            lvl = self._avg_level() if int(level) == 0 else int(level)
            self.roster[char_id] = CharState(char_id, lvl)
        if char_id not in self.party and len(self.party) < 3:
            self.party.append(char_id)
        return self.roster[char_id]

    def party_tags(self):
        """Dialogue tags of the ACTIVE party members."""
        return set(CHAR_TAGS[c] for c in self.party if c in CHAR_TAGS)

    def in_party(self, char_id):
        return char_id in self.party

    def heal_party(self):
        for c in self.roster.values():
            c.full_heal()

    def xp_gain(self, amount):
        """Whole roster gains XP (benched included). Returns level-up events as
        a list of (char_id, new_level)."""
        events = []
        for cid, c in self.roster.items():
            for lvl in c.add_xp(amount):
                events.append((cid, lvl))
        return events

    # ---- economy / items ---------------------------------------------------
    def add_gold(self, n):
        self.gold = max(0, self.gold + int(n))

    def spend_gold(self, n):
        if self.gold >= int(n):
            self.gold -= int(n)
            return True
        return False

    def grant(self, item_id, n=1):
        self.inventory[item_id] = self.inventory.get(item_id, 0) + int(n)

    def take(self, item_id, n=1):
        """Remove n of an item; clamps at zero, drops the key when empty."""
        have = self.inventory.get(item_id, 0)
        left = max(0, have - int(n))
        if left:
            self.inventory[item_id] = left
        else:
            self.inventory.pop(item_id, None)

    def add_key_item(self, item_id):
        if item_id not in self.key_items:
            self.key_items.append(item_id)

    def remove_key_item(self, item_id):
        if item_id in self.key_items:
            self.key_items.remove(item_id)
        self.inventory.pop(item_id, None)


# module-level singleton
GS = GameState()
