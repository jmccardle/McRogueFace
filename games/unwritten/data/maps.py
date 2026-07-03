"""UNWRITTEN - area maps and placements. Authored by Fable; layouts are canon.

Legend (terrain chars -> walkability + ColorLayer color, see AREAS palette):
  '#' wall/building block (unwalkable)   '.' ground
  '~' water (unwalkable)                 ',' path
  't' canopy shadow (walkable, darker)   ' ' void (unwalkable, INK)

All coordinates are (x, y) cell positions. Props are decorative sprites placed
as entities (non-blocking unless 'block': True). NPCs/encounters reference
dialogue scene ids and enemy pack ids. Exits: standing on the cell triggers
transition (optional req flag; 'locked_text' scene plays if unmet).
"""

HOLLOWBROOK = [
    "########################",
    "#~~~~~~~~~~~~~~~~~~~~~~#",
    "#........,,,,..........#",
    "###########,############",
    "#....##....,,....##....#",
    "#.####.....,,....####..#",
    "#.#..#..,,,,,,,,.#..#..#",
    "#.#..,..,......,.,..#..#",
    "#.####..,......,.####..#",
    "#....,..,......,..,....#",
    "#....,..,,,,,,,,..,....#",
    "#....,......,......,...#",
    "#..,,,,,,,,,,,,,,,,,,..#",
    "#......................#",
    "#......................#",
    "########################",
]

GEARWOOD = [
    "##########################",
    "#tttt..........ttttttttt.#",
    "#tt....,,,,.......tttttt.#",
    "#t..####,..,,......ttttt.#",
    "#...#..#,....,,....ttt...#",
    "#...#..,........,....t...#",
    "#...####..tt.....,.......#",
    "#.....t...tt......,......#",
    "#..t......,,,......,.....#",
    "#..tt....,...,......,....#",
    "#...t...,.....,......,...#",
    "#......,.......,....###..#",
    "#.....,.........,...#.#..#",
    "#....,...........,,,,.#..#",
    "#tt..,.............###...#",
    "#ttt.,,,,,,..............#",
    "#ttttt.....,.....tttttt..#",
    "##########################",
]

UNDERCROFT = [
    "##########################",
    "#........#####...........#",
    "#........................#",
    "#........#####...........#",
    "#........#####...........#",
    "#........#####...........#",
    "#........##########.######",
    "###.####..#########.######",
    "###.####............######",
    "##................########",
    "##................########",
    "##.......#........########",
    "##.......#..............##",
    "##.......#..............##",
    "##.....######.##........##",
    "##.....######.##........##",
    "##.....####.#.##........##",
    "##.....####.#.#####.######",
    "########...,,,,,....######",
    "##########################",
]

STUDY = [
    "##################",
    "#................#",
    "#................#",
    "#......####......#",
    "#................#",
    "#................#",
    "#....#......#....#",
    "#................#",
    "#................#",
    "#................#",
    "#.......,........#",
    "##################",
]

AREAS = {
    "hollowbrook": {
        "map": HOLLOWBROOK,
        "banner": "HOLLOWBROOK",
        "banner_grey": "HOLLOWBROOK, REVERTED",
        "palette": {
            ".": (54, 44, 34), ",": (84, 66, 44), "~": (38, 66, 86),
            "#": (30, 32, 42), "t": (44, 38, 30),
        },
        # door cell: the famous North Door at (11,3); walkable only when flag set
        "door_cells": [{"pos": (11, 3), "flag": "door_open",
                        "locked_scene": "door_shut"}],
        "props": [
            {"pos": (11, 8), "sprite": 7, "id": "fountain"},   # dry fountain (8 when rewoken)
            {"pos": (13, 8), "sprite": None, "id": "plinth",   # empty plinth: no sprite,
             "scene": "plinth_look"},                          # a GOLD outline cell + interact
            {"pos": (4, 8),  "sprite": 46, "id": "shop_door", "scene": "enter_shop"},
            {"pos": (18, 7), "sprite": 45, "id": "mayor_door"},
            {"pos": (3, 9),  "sprite": 74, "id": "anvil"},
            {"pos": (2, 13), "sprite": 82, "id": "barrel1"},
            {"pos": (21, 13),"sprite": 63, "id": "crate1"},
            {"pos": (8, 11), "sprite": 72, "id": "vera_stall"},
        ],
        "npcs": [
            {"id": "QUILL",   "pos": (18, 9),  "sprite": 100,
             "scene": {1: "quill_first", 3: "rewake_quill"}},
            {"id": "GRISELDA","pos": (4, 9),   "sprite": 88,
             "scene": {1: "griselda_shop", 3: "rewake_griselda"}},
            {"id": "VERA",    "pos": (8, 10),  "sprite": 111,
             "scene": {1: "shop_dispute"}, "gone_flags": ["vera_joined_early", "vera_reconciled"]},
            {"id": "BRAMBLE", "pos": (11, 4),  "sprite": 96,
             "scene": {1: "bramble_door"}, "gone_flags": ["bramble_joined"]},
            {"id": "ODD",     "pos": (11, 2),  "sprite": 87,
             "scene": {1: "odd_ferry_1", 3: "rewake_odd"}},
            {"id": "NYX",     "pos": (13, 8),  "sprite": 121, "act_min": 3,
             "scene": {3: "nyx_plinth"}, "gone_flags": ["nyx_joined", "nyx_missed"]},
        ],
        "encounters": [],
        "exits": [],   # travel happens via Odd (ferry dialogue) and the North Door scene
        "spawns": {"start": (11, 12), "from_door": (11, 2), "from_ferry": (11, 2)},
        "camp": {"pos": (11, 9), "scene": "fountain_rest"},   # interact next to fountain
    },

    "gearwood": {
        "map": GEARWOOD,
        "banner": "THE GEARWOOD",
        "palette": {
            ".": (30, 46, 32), ",": (52, 62, 40), "~": (38, 66, 86),
            "#": (20, 30, 24), "t": (22, 34, 26),
        },
        "props": [
            {"pos": (5, 4),  "sprite": 43, "id": "shrine_brazier", "scene": "moth_shrine"},
            {"pos": (3, 4),  "sprite": 64, "id": "shrine_grave"},
            {"pos": (6, 5),  "sprite": 89, "id": "shrine_chest", "scene": "shrine_chest"},
            {"pos": (20, 12),"sprite": 33, "id": "stair_door", "scene": "gearwood_stair"},
            {"pos": (13, 8), "sprite": None, "id": "bell_spot", "scene": "gearwood_bell_1",
             "auto": True, "once": "bell_1_done"},   # auto-trigger walking within 1 cell
            {"pos": (2, 15), "sprite": 76, "id": "fence1"},
            {"pos": (3, 15), "sprite": 77, "id": "fence2"},
        ],
        "npcs": [
            {"id": "VERA", "pos": (19, 13), "sprite": 111, "act_min": 2,
             "scene": {2: "vera_reconcile"},
             "need_flags": ["vera_grudge"], "gone_flags": ["vera_reconciled"]},
        ],
        "encounters": [
            {"pos": (10, 3),  "pack": "gw_bats"},
            {"pos": (16, 6),  "pack": "gw_mixed"},
            {"pos": (8, 12),  "pack": "gw_slimes"},
            {"pos": (18, 15), "pack": "gw_mixed2"},
            {"pos": (7, 5),   "pack": "gw_scarabs", "leash": 0},  # shrine chest guards
        ],
        "exits": [{"pos": (13, 16), "to": "hollowbrook", "spawn": "from_ferry",
                   "scene": "odd_ferry_back"}],
        "spawns": {"from_ferry": (13, 15), "from_undercroft": (20, 13)},
        "camp": {"pos": (5, 5), "scene": "shrine_rest", "need_flags": ["moth_joined"]},
    },

    "undercroft": {
        "map": UNDERCROFT,
        "banner": "THE UNDERCROFT",
        "palette": {
            ".": (18, 20, 30), ",": (28, 30, 44), "~": (16, 24, 40),
            "#": (10, 11, 18), "t": (14, 16, 24),
        },
        "fov": True, "fov_radius": 7,
        "props": [
            {"pos": (13, 10), "sprite": 109, "id": "cantor_dormant",
             "scene": "cantor_wake", "gone_flags": ["cantor_joined"]},
            {"pos": (5, 15),  "sprite": 89, "id": "chest_a", "scene": "chest_a"},
            {"pos": (17, 4),  "sprite": 90, "id": "chest_b", "scene": "chest_b"},
            {"pos": (9, 8),   "sprite": 89, "id": "mimic_chest", "scene": "mimic_chest",
             "gone_flags": ["mimic_slain"]},
            {"pos": (13, 18), "sprite": 41, "id": "boss_door", "scene": "gatekeeper_pre",
             "gone_flags": ["gatekeeper_slain"]},
            {"pos": (3, 5),   "sprite": 65, "id": "grave_a"},
            {"pos": (23, 15), "sprite": 64, "id": "grave_b"},
            {"pos": (12, 9),  "sprite": None, "id": "nyx_sketch", "scene": "nyx_sketch"},
        ],
        "npcs": [],
        "encounters": [
            {"pos": (7, 3),   "pack": "uc_bones"},
            {"pos": (19, 8),  "pack": "uc_echoes"},
            {"pos": (5, 11),  "pack": "uc_mixed"},
            {"pos": (18, 13), "pack": "uc_bones2"},
            {"pos": (11, 16), "pack": "uc_chimes", "leash": 1},
        ],
        "exits": [{"pos": (3, 1), "to": "gearwood", "spawn": "from_undercroft"}],
        "spawns": {"enter": (3, 2)},
        "camp": None,
    },

    "study": {
        "map": STUDY,
        "banner": "THE MAKER'S STUDY",
        "palette": {
            ".": (214, 204, 178), ",": (196, 186, 158), "~": (170, 176, 186),
            "#": (28, 26, 24), "t": (188, 178, 152),
        },
        "ink_world": True,   # UI outlines use INK on parchment here
        "props": [   # desk props sit on the ink block on purpose (furniture)
            {"pos": (8, 3),  "sprite": 72, "id": "desk"},
            {"pos": (9, 3),  "sprite": 75, "id": "desk_books"},
            {"pos": (9, 4),  "sprite": None, "id": "custodian_spot",
             "scene": "custodian_pre", "auto": True, "once": "custodian_met"},
        ],
        "npcs": [],
        "encounters": [
            {"pos": (4, 8),  "pack": "st_echoes"},
            {"pos": (13, 8), "pack": "st_echoes2"},
        ],
        "exits": [],
        "spawns": {"enter": (9, 10)},
        "camp": None,
    },
}

# Battle backdrop band colors per area (top->bottom, 6 bands)
BATTLE_BACKDROPS = {
    "hollowbrook": [(30,32,42),(38,36,40),(46,40,36),(54,44,34),(64,52,38),(74,60,42)],
    "gearwood":    [(14,22,18),(18,30,22),(24,38,28),(30,46,32),(38,56,38),(46,64,42)],
    "undercroft":  [(8,9,14),(10,12,20),(14,16,26),(18,20,30),(24,26,38),(30,32,46)],
    "study":       [(230,222,200),(222,212,188),(214,204,178),(202,192,166),(66,60,52),(28,26,24)],
}
