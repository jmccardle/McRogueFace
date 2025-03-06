tiles = {}
deltas = [
        (-1, -1), ( 0, -1), (+1, -1),
        (-1,  0), ( 0,  0), (+1,  0),
        (-1, +1), ( 0, +1), (+1, +1)
        ]

class TileInfo:
    GROUND, WALL, DONTCARE = True, False, None
    chars = {
            "X": WALL, 
            "_": GROUND,
            "?": DONTCARE
            }
    symbols = {v: k for k, v in chars.items()}

    def __init__(self, values:dict):
        self._values = values
        self.rules = []
        self.chance = 1.0

    @staticmethod
    def from_grid(grid, xy:tuple):
        values = {}
        for d in deltas:
            tx, ty = d[0] + xy[0], d[1] + xy[1]
            try:
                values[d] = grid.at((tx, ty)).walkable
            except ValueError:
                values[d] = True
        return TileInfo(values)

    @staticmethod
    def from_string(s):
        values = {}
        for d, c in zip(deltas, s):
            values[d] = TileInfo.chars[c]
        return TileInfo(values)

    def __hash__(self):
        """for use as a dictionary key"""
        return hash(tuple(self._values.items()))

    def match(self, other:"TileInfo"):
        for d, rule in self._values.items():
            if rule is TileInfo.DONTCARE: continue
            if other._values[d] is TileInfo.DONTCARE: continue
            if rule != other._values[d]: return False
        return True

    def show(self):
        nine = ['', '', '\n'] * 3
        for k, end in zip(deltas, nine):
            c = TileInfo.symbols[self._values[k]]
            print(c, end=end)

    def __repr__(self):
        return f"<TileInfo {self._values}>"

cardinal_directions = {
    "N": ( 0, -1),
    "S": ( 0, +1),
    "E": (-1,  0),
    "W": (+1,  0)
}

def special_rule_verify(rule, grid, xy, unverified_tiles, pass_unverified=False):
    cardinal, allowed_tile = rule
    dxy = cardinal_directions[cardinal.upper()]
    tx, ty = xy[0] + dxy[0], xy[1] + dxy[1]
    #print(f"Special rule: {cardinal} {allowed_tile} {type(allowed_tile)} -> ({tx}, {ty}) [{grid.at((tx, ty)).tilesprite}]{'*' if (tx, ty) in unverified_tiles else ''}")
    if (tx, ty) in unverified_tiles and cardinal in "nsew": return pass_unverified
    try:
        return grid.at((tx, ty)).tilesprite == allowed_tile
    except ValueError:
        return False

import random
tile_of_last_resort = 431

def find_possible_tiles(grid, x, y, unverified_tiles=None, pass_unverified=False):
    ti = TileInfo.from_grid(grid, (x, y))
    if unverified_tiles is None: unverified_tiles = []
    matches = [(k, v) for k, v in tiles.items() if k.match(ti)]
    if not matches:
        return []
    possible = []
    if not any([tileinfo.rules for tileinfo, _ in matches]):
        # make weighted choice, as the tile does not depend on verification
        wts = [k.chance for k, v in matches]
        tileinfo, tile = random.choices(matches, weights=wts)[0]
        return [tile]

    for tileinfo, tile in matches:
        if not tileinfo.rules:
            possible.append(tile)
            continue
        for r in tileinfo.rules: #for r in ...: if ... continue == more readable than an "any" 1-liner
            p = special_rule_verify(r, grid, (x,y),
                                    unverified_tiles=unverified_tiles,
                                    pass_unverified = pass_unverified
                                    )
            if p: 
                possible.append(tile)
                continue
    return list(set(list(possible)))

def wfc_first_pass(grid):
    w, h = grid.grid_size
    possibilities = {}
    for x in range(0, w):
        for y in range(0, h):
            matches = find_possible_tiles(grid, x, y, pass_unverified=True)
            if len(matches) == 0:
                grid.at((x, y)).tilesprite = tile_of_last_resort
                possibilities[(x,y)] = matches
            elif len(matches) == 1:
                grid.at((x, y)).tilesprite = matches[0]
            else:
                possibilities[(x,y)] = matches
    return possibilities

def wfc_pass(grid, possibilities=None):
    w, h = grid.grid_size
    if possibilities is None:
        #print("first pass results:")
        possibilities = wfc_first_pass(grid)
        counts = {}
        for v in possibilities.values():
            if len(v) in counts: counts[len(v)] += 1
            else: counts[len(v)] = 1
        print(counts)
        return possibilities
    elif len(possibilities) == 0:
        print("We're done!")
        return
    old_possibilities = possibilities
    possibilities = {}
    for (x, y) in old_possibilities.keys():
        matches = find_possible_tiles(grid, x, y, unverified_tiles=old_possibilities.keys(), pass_unverified = True)
        if len(matches) == 0:
            print((x,y), matches)
            grid.at((x, y)).tilesprite = tile_of_last_resort
            possibilities[(x,y)] = matches
        elif len(matches) == 1:
            grid.at((x, y)).tilesprite = matches[0]
        else:
            grid.at((x, y)).tilesprite = -1
            grid.at((x, y)).color = (32 * len(matches), 32 * len(matches), 32 * len(matches))
            possibilities[(x,y)] = matches

    if len(possibilities) == len(old_possibilities):
        #print("No more tiles could be solved without collapse")
        counts = {}
        for v in possibilities.values():
            if len(v) in counts: counts[len(v)] += 1
            else: counts[len(v)] = 1
        #print(counts)
        if 0 in counts: del counts[0]
        if len(counts) == 0:
            print("Contrats! You broke it! (insufficient tile defs to solve remaining tiles)")
            return []
        target = min(list(counts.keys()))
        while possibilities:
            for (x, y) in possibilities.keys():
                if len(possibilities[(x, y)]) != target:
                    continue
                ti = TileInfo.from_grid(grid, (x, y))
                matches = [(k, v) for k, v in tiles.items() if k.match(ti)]
                verifiable_matches = find_possible_tiles(grid, x, y, unverified_tiles=possibilities.keys())
                if not verifiable_matches: continue
                #print(f"collapsing {(x, y)} ({target} choices)")
                matches = [(k, v) for k, v in matches if v in verifiable_matches]
                wts = [k.chance for k, v in matches]
                tileinfo, tile = random.choices(matches, weights=wts)[0]
                grid.at((x, y)).tilesprite = tile
                del possibilities[(x, y)]
                break
            else:
                selected = random.choice(list(possibilities.keys()))
                #print(f"No tiles have verifable solutions: QUANTUM -> {selected}")
                # sprinkle some quantumness on it
                ti = TileInfo.from_grid(grid, (x, y))
                matches = [(k, v) for k, v in tiles.items() if k.match(ti)]
                wts = [k.chance for k, v in matches]
                if not wts:
                    print(f"This one: {(x,y)} {matches}\n{wts}")
                    del possibilities[(x, y)]
                    return possibilities
                tileinfo, tile = random.choices(matches, weights=wts)[0]
                grid.at((x, y)).tilesprite = tile
                del possibilities[(x, y)]
                
    return possibilities

#with open("scripts/tile_def.txt", "r") as f:
with open("scripts/simple_tiles.txt", "r") as f:
    for block in f.read().split('\n\n'):
        info, constraints = block.split('\n', 1)
        if '#' in info:
            info, comment = info.split('#', 1)
        rules = []
        if '@' in info:
            info, *block_rules = info.split('@')
            #print(block_rules)
            for r in block_rules:
                rules.append((r[0], int(r[1:])))
            #cardinal_dir = block_rules[0]
            #partner
        if ':' not in info:
            tile_id = int(info)
            chance = 1.0
        else:
            tile_id, chance = info.split(':')
            tile_id = int(tile_id)
            chance = float(chance.strip())
        constraints = constraints.replace('\n', '')
        k = TileInfo.from_string(constraints)
        k.rules = rules
        k.chance = chance
        tiles[k] = tile_id


