"""UNWRITTEN - dialogue runner. Owner: Agent A.

run_scene(scene_id, on_done=None, stack=None) loads a node dict from the merged
SCENES of data.script_act1/2/3, drives a core.ui.DialogueBox through the
InputStack, applies effects/actions to state.GS, and hands off scene-changing
actions (shop, swap_menu, battle, goto_area, epilogue) to the HOOKS registry
that Agent B/C register.

Supported constructs (every one actually used by the authored scripts):
  req:     None | ("tag",X) | ("flag",X) | ("flag_not",X) | ("party",X)
                 | ("points",N) | ("item",item_id)
  effects: ("flag",x) | ("points",n) | ("gold",n) | ("item",id,n) [n<0 removes]
                 | ("act",n) | ("key_item_remove",id)
  actions: end | shop | heal_party | swap_menu | recruit:CHARID:LEVEL
                 | battle:pack_id | goto_area:area:spawn | epilogue | act:N
"""
import mcrfpy
from core import ui
from core.inputstack import InputStack
from systems.state import GS

# --------------------------------------------------------------------- HOOKS
# Other agents register scene-changing handlers here, e.g.
#   systems.dialogue.HOOKS["battle"] = battle.start_from_dialogue
# Signatures:
#   HOOKS["shop"]()                        (Agent C)
#   HOOKS["swap_menu"]()                   (Agent C) - should be modal/returning
#   HOOKS["battle"](pack_id)               (Agent B)
#   HOOKS["goto_area"](area, spawn)        (Agent C)
#   HOOKS["epilogue"]()                    (Agent C)
HOOKS = {}

# The runner currently driving a dialogue, if any. Exposed as a test seam so a
# scripted playthrough can drive the REAL runner (apply effects, goto nodes,
# fire deferred actions) by index instead of injecting keypresses. None when no
# dialogue is open. See select_choice()/advance() below.
CURRENT = None


def _hook(name):
    if name not in HOOKS:
        raise KeyError(
            "dialogue action '%s' needs a handler: set "
            "systems.dialogue.HOOKS['%s'] (owning agent has not registered it)"
            % (name, name))
    return HOOKS[name]


# ----------------------------------------------------------------- scene lookup
def _all_scenes():
    scenes = {}
    from data import script_act1, script_act2, script_act3
    for mod in (script_act1, script_act2, script_act3):
        for k, v in mod.SCENES.items():
            if k in scenes:
                raise KeyError("duplicate dialogue scene id %r across script "
                               "files" % (k,))
            scenes[k] = v
    return scenes


# ---------------------------------------------------------------- req / effects
def req_met(req):
    if req is None:
        return True
    kind = req[0]
    if kind == "flag":
        return GS.has(req[1])
    if kind == "flag_not":
        return not GS.has(req[1])
    if kind == "tag":
        return req[1] in GS.party_tags()
    if kind == "party":
        return GS.in_party(req[1])
    if kind == "points":
        return GS.points >= req[1]
    if kind == "item":
        return GS.inventory.get(req[1], 0) > 0
    raise ValueError("unknown req form %r" % (req,))


def apply_effects(effects):
    for e in effects or []:
        kind = e[0]
        if kind == "flag":
            GS.add_flag(e[1])
        elif kind == "points":
            GS.add_points(e[1])          # triggers the Book hum via GS.hum_hook
        elif kind == "gold":
            GS.add_gold(e[1])
        elif kind == "item":
            n = e[2]
            if n >= 0:
                GS.grant(e[1], n)
            else:
                GS.take(e[1], -n)
        elif kind == "act":
            GS.act = int(e[1])
        elif kind == "key_item_remove":
            GS.remove_key_item(e[1])
        else:
            raise ValueError("unknown effect form %r" % (e,))


# actions that fire when the player ADVANCES past a text node (deferred)
_DEFERRED = ("end", "shop", "swap_menu", "battle", "goto_area", "epilogue")
# transfer actions hand the scene off entirely; the runner finishes afterward
_TRANSFER = ("shop", "battle", "goto_area", "epilogue")


def _do_recruit(action):
    _, char_id, level = action.split(":")
    GS.recruit(char_id, int(level))


class _Runner:
    def __init__(self, scene, scene_dict, on_done, stack):
        self.scene = scene
        self.sc = scene_dict
        self.on_done = on_done
        self.owns_stack = stack is None
        self.stack = stack if stack is not None else InputStack(scene)
        self.box = ui.DialogueBox(scene.children)
        self.node = None               # current node (test seam)
        GS.hum_hook = self.box.hum
        self.stack.push(self.box.handle, "dialogue")
        global CURRENT
        CURRENT = self

    # ---- lifecycle ---------------------------------------------------------
    def start(self):
        self.goto(self.sc["start"])

    def finish(self):
        global CURRENT
        if CURRENT is self:
            CURRENT = None
        self.node = None
        self.box.destroy()
        self.stack.pop("dialogue")
        GS.hum_hook = None
        if self.on_done:
            self.on_done()

    # ---- node flow ---------------------------------------------------------
    def goto(self, node_id):
        if node_id not in self.sc["nodes"]:
            raise KeyError("dialogue target node %r not found" % (node_id,))
        node = self.sc["nodes"][node_id]
        self.enter(node)

    def enter(self, node):
        # 1. enter-time effects
        apply_effects(node.get("effects"))
        # 2. enter-time (immediate) actions
        action = node.get("action")
        if action:
            name = action.split(":")[0]
            if name == "heal_party":
                GS.heal_party()
            elif name == "recruit":
                _do_recruit(action)
            elif name == "act":
                GS.act = int(action.split(":")[1])
        # 3. present
        self.present(node)

    def present(self, node):
        self.node = node
        speaker = node.get("speaker", "NARRATOR")
        text = node.get("text", "")
        choices = node.get("choices")
        if choices:
            display = [(c["label"], req_met(c.get("req"))) for c in choices]
            self.box.show_node(speaker, text, choices=display,
                               on_choice=lambda i, n=node: self.pick(n, i))
        else:
            self.box.show_node(speaker, text,
                               on_advance=lambda n=node: self.advance(n))

    def pick(self, node, index):
        choice = node["choices"][index]
        apply_effects(choice.get("effects"))
        nxt = choice.get("next")
        if nxt is None:
            raise KeyError("choice %r in a dialogue node has no 'next'"
                           % (choice.get("label"),))
        self.goto(nxt)

    def advance(self, node):
        action = node.get("action")
        if action:
            name = action.split(":")[0]
            if name in _DEFERRED:
                self._do_deferred(action, name, node)
                return
        nxt = node.get("next")
        if nxt is not None:
            self.goto(nxt)
        else:
            self.finish()

    def _do_deferred(self, action, name, node):
        if name == "end":
            self.finish()
            return
        if name == "battle":
            pack = action.split(":", 1)[1]
            _hook("battle")(pack)
            self.finish()
            return
        if name == "goto_area":
            _, area, spawn = action.split(":")
            _hook("goto_area")(area, spawn)
            self.finish()
            return
        if name == "epilogue":
            _hook("epilogue")()
            self.finish()
            return
        if name == "shop":
            _hook("shop")()
            self.finish()
            return
        if name == "swap_menu":
            # returning hook: run it, then continue if the node chains onward
            _hook("swap_menu")()
            nxt = node.get("next")
            if nxt is not None:
                self.goto(nxt)
            else:
                self.finish()
            return
        raise ValueError("unhandled deferred action %r" % (action,))


def run_scene(scene_id, on_done=None, stack=None):
    """Run a dialogue scene on mcrfpy.current_scene. If `stack` (an InputStack)
    is given, the dialogue pushes onto it (so overworld movement stays frozen
    beneath); otherwise a fresh InputStack is bound to the scene."""
    scene = mcrfpy.current_scene
    scenes = _all_scenes()
    if scene_id not in scenes:
        raise KeyError("unknown dialogue scene id %r" % (scene_id,))
    runner = _Runner(scene, scenes[scene_id], on_done, stack)
    runner.start()
    return runner


# --------------------------------------------------------------------- test seam
def current_choice_labels():
    """Labels of the current node's choices as (label, enabled) tuples, or None
    if the current node is not a choice node. For scripted playthroughs."""
    if CURRENT is None or CURRENT.node is None:
        return None
    choices = CURRENT.node.get("choices")
    if not choices:
        return None
    return [(c["label"], req_met(c.get("req"))) for c in choices]


def select_choice(index):
    """Pick choice `index` on the open dialogue node, driving the REAL runner
    (applies the choice's effects, follows its 'next'). Raises if no choice node
    is open or the choice is disabled by its req."""
    if CURRENT is None or CURRENT.node is None:
        raise RuntimeError("select_choice: no dialogue open")
    node = CURRENT.node
    choices = node.get("choices")
    if not choices:
        raise RuntimeError("select_choice: current node has no choices")
    if index < 0 or index >= len(choices):
        raise IndexError("select_choice: index %d out of range (%d choices)"
                         % (index, len(choices)))
    if not req_met(choices[index].get("req")):
        raise RuntimeError("select_choice: choice %d is disabled (%r)"
                           % (index, choices[index].get("label")))
    CURRENT.pick(node, index)


def advance():
    """Advance the open text node (as if the player pressed space), driving the
    REAL runner (fires deferred actions like battle/goto_area/shop/epilogue, or
    follows 'next', or finishes). Raises if a choice is pending."""
    if CURRENT is None or CURRENT.node is None:
        raise RuntimeError("advance: no dialogue open")
    node = CURRENT.node
    if node.get("choices"):
        raise RuntimeError("advance: current node is a choice node; use "
                           "select_choice(i)")
    CURRENT.advance(node)
