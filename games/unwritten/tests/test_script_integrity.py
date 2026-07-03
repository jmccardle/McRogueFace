"""UNWRITTEN - script integrity walker. Owner: Agent A.

Walks every scene in data/script_act1|2|3 plus data/epilogue.PAGES and asserts:
  - every 'next' and choice target node exists within its scene
  - every req and effect tuple is a form the dialogue runner supports
  - every speaker id has a portrait entry (core.assets.PORTRAITS)
  - every action string parses
  - collects the battle pack ids referenced (for Agent B)

Protects the authored content: run after ANY change to the scripts.

Run:
  cd build && ./mcrogueface --headless --exec ../games/unwritten/tests/test_script_integrity.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import assets
from data import script_act1, script_act2, script_act3, epilogue

REQ_KINDS = {"flag", "flag_not", "tag", "party", "points", "item"}
EFFECT_KINDS = {"flag", "points", "gold", "item", "act", "key_item_remove"}
ACTION_NAMES = {"end", "shop", "heal_party", "swap_menu", "recruit",
                "battle", "goto_area", "epilogue", "act"}

errors = []
battle_packs = set()
counts = {"scenes": 0, "nodes": 0, "choices": 0, "effects": 0, "reqs": 0,
          "actions": 0}


def err(where, msg):
    errors.append("%s: %s" % (where, msg))


def check_req(where, req):
    if req is None:
        return
    counts["reqs"] += 1
    if not isinstance(req, tuple) or len(req) < 1:
        err(where, "malformed req %r" % (req,))
        return
    kind = req[0]
    if kind not in REQ_KINDS:
        err(where, "unknown req kind %r" % (kind,))
        return
    if kind == "points":
        if len(req) != 2 or not isinstance(req[1], int):
            err(where, "points req needs int arg: %r" % (req,))
    else:
        if len(req) != 2 or not isinstance(req[1], str):
            err(where, "%s req needs str arg: %r" % (kind, req))


def check_effects(where, effects):
    if effects is None:
        return
    if not isinstance(effects, (list, tuple)):
        err(where, "effects must be a list: %r" % (effects,))
        return
    for e in effects:
        counts["effects"] += 1
        if not isinstance(e, tuple) or len(e) < 1:
            err(where, "malformed effect %r" % (e,))
            continue
        kind = e[0]
        if kind not in EFFECT_KINDS:
            err(where, "unknown effect kind %r" % (kind,))
            continue
        if kind in ("flag", "key_item_remove"):
            if len(e) != 2 or not isinstance(e[1], str):
                err(where, "%s effect needs str arg: %r" % (kind, e))
        elif kind in ("points", "gold", "act"):
            if len(e) != 2 or not isinstance(e[1], int):
                err(where, "%s effect needs int arg: %r" % (kind, e))
        elif kind == "item":
            if len(e) != 3 or not isinstance(e[1], str) or not isinstance(e[2], int):
                err(where, "item effect needs (id:str, n:int): %r" % (e,))


def check_action(where, action):
    counts["actions"] += 1
    if not isinstance(action, str):
        err(where, "action must be a str: %r" % (action,))
        return
    parts = action.split(":")
    name = parts[0]
    if name not in ACTION_NAMES:
        err(where, "unknown action %r" % (action,))
        return
    if name in ("end", "shop", "heal_party", "swap_menu", "epilogue"):
        if len(parts) != 1:
            err(where, "action %r takes no args" % (action,))
    elif name == "recruit":
        if len(parts) != 3:
            err(where, "recruit needs CHARID:LEVEL: %r" % (action,))
        else:
            if parts[1] not in assets.PORTRAITS:
                err(where, "recruit unknown char %r" % (parts[1],))
            try:
                int(parts[2])
            except ValueError:
                err(where, "recruit level not int: %r" % (action,))
    elif name == "battle":
        if len(parts) != 2:
            err(where, "battle needs pack id: %r" % (action,))
        else:
            battle_packs.add(parts[1])
    elif name == "goto_area":
        if len(parts) != 3:
            err(where, "goto_area needs area:spawn: %r" % (action,))
    elif name == "act":
        if len(parts) != 2 or not parts[1].isdigit():
            err(where, "act needs int: %r" % (action,))


def walk_scenes(modname, scenes):
    for scene_id, scene in scenes.items():
        counts["scenes"] += 1
        where0 = "%s/%s" % (modname, scene_id)
        nodes = scene.get("nodes", {})
        start = scene.get("start")
        if start not in nodes:
            err(where0, "start node %r missing" % (start,))
        for node_id, node in nodes.items():
            counts["nodes"] += 1
            where = "%s/%s" % (where0, node_id)

            speaker = node.get("speaker", "NARRATOR")
            if speaker not in assets.PORTRAITS:
                err(where, "speaker %r has no portrait entry" % (speaker,))

            check_effects(where, node.get("effects"))

            action = node.get("action")
            if action is not None:
                check_action(where, action)

            has_choices = "choices" in node
            has_next = "next" in node
            if has_choices:
                for i, c in enumerate(node["choices"]):
                    counts["choices"] += 1
                    cw = "%s/choice[%d]" % (where, i)
                    check_req(cw, c.get("req"))
                    check_effects(cw, c.get("effects"))
                    tgt = c.get("next")
                    if tgt is None:
                        err(cw, "choice has no 'next'")
                    elif tgt not in nodes:
                        err(cw, "choice target %r missing" % (tgt,))
            if has_next:
                tgt = node["next"]
                if tgt not in nodes:
                    err(where, "next target %r missing" % (tgt,))

            # a node must resolve somehow: choices, next, or a terminal action
            if not has_choices and not has_next and action is None:
                err(where, "dead-end node (no choices, no next, no action)")


def walk_epilogue():
    valid = 0
    for i, entry in enumerate(epilogue.PAGES):
        where = "epilogue/PAGES[%d]" % (i,)
        if not isinstance(entry, tuple) or len(entry) != 2:
            err(where, "page must be (condition, text): %r" % (entry,))
            continue
        cond, text = entry
        if cond is not None:
            if not isinstance(cond, tuple) or cond[0] not in ("flag", "flag_not", "points"):
                err(where, "unsupported page condition %r" % (cond,))
        if not isinstance(text, str) or not text.strip():
            err(where, "page text must be a non-empty str")
        valid += 1
    return valid


def main():
    walk_scenes("act1", script_act1.SCENES)
    walk_scenes("act2", script_act2.SCENES)
    walk_scenes("act3", script_act3.SCENES)
    pages = walk_epilogue()

    # cross-check: no duplicate scene ids across files
    all_ids = (list(script_act1.SCENES) + list(script_act2.SCENES) +
               list(script_act3.SCENES))
    dupes = set(x for x in all_ids if all_ids.count(x) > 1)
    if dupes:
        err("global", "duplicate scene ids across script files: %s" % sorted(dupes))

    # battle packs referenced by the overworld maps (for Agent B's full list)
    map_packs = set()
    try:
        from data import maps
        for area in maps.AREAS.values():
            for enc in area.get("encounters", []):
                map_packs.add(enc["pack"])
    except Exception as e:
        print("note: could not read data/maps.py encounters (%s)" % (e,), flush=True)

    print("--- UNWRITTEN script integrity ---", flush=True)
    print("scenes=%(scenes)d nodes=%(nodes)d choices=%(choices)d "
          "effects=%(effects)d reqs=%(reqs)d actions=%(actions)d"
          % counts, flush=True)
    print("epilogue pages=%d" % pages, flush=True)
    print("battle packs referenced in SCRIPTS: %s"
          % (sorted(battle_packs) if battle_packs else "(none)"), flush=True)
    print("battle packs referenced in MAPS:    %s"
          % (sorted(map_packs) if map_packs else "(none)"), flush=True)
    print("ALL battle packs (for Agent B):     %s"
          % sorted(battle_packs | map_packs), flush=True)

    if errors:
        print("FAIL test_script_integrity (%d problems):" % len(errors), flush=True)
        for e in errors:
            print("  " + e, flush=True)
        sys.exit(1)

    print("PASS test_script_integrity", flush=True)
    sys.exit(0)


if __name__ == "__main__":
    main()
