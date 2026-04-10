"""fuzz_anim_timer_scene - Wave 2 / W6 target for #283.

Targets lifecycle-sensitive bugs:
- #269 PythonObjectCache::lookup() no mutex (race on cache)
- #270 GridLayer::parent_grid dangling pointer
- #275 UIEntity missing tp_dealloc (leak/dangle)
- #277 GridChunk::parent_grid dangling pointer

Common thread: objects that hold references across scene/grid lifetimes
and misbehave when the lifetime ends unexpectedly. The target hammers
Animation, Timer, and Scene-graph mutation, focusing on callback paths
that fire AFTER a parent/target has been removed from the tree. Scene
swap mid-callback and closure captures that outlive their target are
the two main attack patterns.

Contract: fuzz_one_input(data: bytes) -> None. The C++ harness
(tests/fuzz/fuzz_common.cpp) calls safe_reset() before each iteration
and catches any Python exception that escapes. We still wrap the ops
loop to keep the libFuzzer output quiet.
"""

import mcrfpy

from fuzz_common import ByteStream, EXPECTED_EXCEPTIONS


# --- Easing pool: pre-resolve enum members so dispatch is O(1) ----------
_EASING_NAMES = (
    "LINEAR", "EASE_IN", "EASE_OUT", "EASE_IN_OUT",
    "EASE_IN_QUAD", "EASE_OUT_QUAD", "EASE_IN_OUT_QUAD",
    "EASE_IN_CUBIC", "EASE_OUT_CUBIC", "EASE_IN_OUT_CUBIC",
    "EASE_IN_SINE", "EASE_OUT_SINE", "EASE_IN_OUT_SINE",
    "EASE_IN_BACK", "EASE_OUT_BACK", "EASE_IN_OUT_BACK",
    "EASE_IN_BOUNCE", "EASE_OUT_BOUNCE", "EASE_IN_OUT_BOUNCE",
    "EASE_IN_ELASTIC", "EASE_OUT_ELASTIC",
    "PING_PONG", "PING_PONG_SMOOTH",
)

_EASINGS = []
try:
    _EasingEnum = getattr(mcrfpy, "Easing", None)
    if _EasingEnum is not None:
        for _n in _EASING_NAMES:
            _v = getattr(_EasingEnum, _n, None)
            if _v is not None:
                _EASINGS.append(_v)
except Exception:
    pass


# Properties that are numeric on most UIDrawable subtypes - safe to animate
# to a float target without tripping type validation.
_NUMERIC_PROPS = ("x", "y", "w", "h", "opacity", "sprite_index")


# --- Callback factories ---------------------------------------------------
#
# These are the DANGEROUS closures. Each captures references to scene-graph
# objects and fires at an unpredictable later time (timer interval elapsed,
# animation duration reached, scene swapped). If the engine has a stale
# pointer anywhere in that chain, ASan fires here.

def _noop_anim(target, prop, value):
    pass


def _noop_timer(timer, runtime):
    pass


class _AnimCallbackTouchesDrawables:
    """Animation completion callback that pokes at a list of drawables.

    The drawables list is captured at animate() time; by the time the
    callback fires, some of those drawables may have been removed from
    their parent, reparented, or dropped from every python ref. Touching
    .parent, .x, etc. probes whether the engine kept live pointers.
    """
    __slots__ = ("_drawables",)

    def __init__(self, drawables):
        self._drawables = list(drawables)

    def __call__(self, target, prop, value):
        for d in self._drawables:
            try:
                # Force a property access; accessor round-trips through
                # the PythonObjectCache (#269) and the C++ parent backref.
                _ = d.x
                _ = d.parent
            except Exception:
                pass


class _AnimCallbackCascades:
    """Animation callback that starts NEW animations on the same target.

    Exercises cascading animation creation from inside an animation
    completion handler - tests whether the animation system is
    reentrant-safe when it fires callbacks.
    """
    __slots__ = ("_depth",)

    def __init__(self, depth=2):
        self._depth = depth

    def __call__(self, target, prop, value):
        if self._depth <= 0:
            return
        try:
            target.animate("x", 0.0, 0.05, _EASINGS[0] if _EASINGS else None,
                           callback=_AnimCallbackCascades(self._depth - 1))
        except Exception:
            pass


class _TimerSwapsScene:
    """Timer callback that swaps mcrfpy.current_scene to another scene.

    This is the #269 (PythonObjectCache race) stress: while a timer fires,
    the scene it was created under may be torn down and another scene
    installed. Any C++ code that holds a parent_scene pointer should
    cope, or we crash.
    """
    __slots__ = ("_scenes",)

    def __init__(self, scenes):
        self._scenes = list(scenes)

    def __call__(self, timer, runtime):
        try:
            if self._scenes:
                mcrfpy.current_scene = self._scenes[-1]
        except Exception:
            pass


class _TimerMutatesTimers:
    """Timer callback that creates AND destroys timers mid-fire.

    The timer queue is being walked by the engine when this fires; adding
    and removing entries probes iterator-invalidation safety.
    """
    __slots__ = ("_timers", "_scenes_ref")

    def __init__(self, timers, scenes_ref):
        self._timers = timers
        self._scenes_ref = scenes_ref

    def __call__(self, timer, runtime):
        try:
            # Destroy self if possible
            try:
                timer.stop()
            except Exception:
                pass
            # Create a replacement timer
            if len(self._timers) < 8:
                new_t = mcrfpy.Timer("reentrant", _noop_timer, 50)
                self._timers.append(new_t)
        except Exception:
            pass


class _TimerStartsAnimation:
    """Timer callback that kicks off new animations on captured drawables.

    Tests the path where a drawable's python wrapper might still be live
    but its C++ backing has been relocated or its parent has been swapped.
    """
    __slots__ = ("_drawables",)

    def __init__(self, drawables):
        self._drawables = list(drawables)

    def __call__(self, timer, runtime):
        for d in self._drawables[:3]:
            try:
                easing = _EASINGS[0] if _EASINGS else None
                d.animate("x", 10.0, 0.1, easing)
            except Exception:
                pass


# --- Helpers --------------------------------------------------------------

def _make_scene(stream, scenes):
    if len(scenes) >= 3:
        return
    name = stream.ascii_str(8) or "fuzz_s"
    s = mcrfpy.Scene(name)
    scenes.append(s)


def _activate_scene(stream, scenes):
    if not scenes:
        return
    s = stream.pick_one(scenes)
    if s is not None:
        mcrfpy.current_scene = s


def _make_frame(stream, frames, drawables):
    if len(frames) >= 16:
        return
    x = float(stream.int_in_range(-50, 500))
    y = float(stream.int_in_range(-50, 500))
    w = float(stream.int_in_range(1, 400))
    h = float(stream.int_in_range(1, 400))
    f = mcrfpy.Frame(pos=(x, y), size=(w, h))
    frames.append(f)
    drawables.append(f)


def _make_caption(stream, drawables):
    text = stream.ascii_str(12)
    x = float(stream.int_in_range(-50, 500))
    y = float(stream.int_in_range(-50, 500))
    c = mcrfpy.Caption(text=text, pos=(x, y))
    drawables.append(c)
    return c


def _make_sprite(stream, drawables):
    x = float(stream.int_in_range(-50, 500))
    y = float(stream.int_in_range(-50, 500))
    idx = stream.int_in_range(0, 255)
    tex = getattr(mcrfpy, "default_texture", None)
    if tex is None:
        s = mcrfpy.Sprite(pos=(x, y))
    else:
        s = mcrfpy.Sprite(pos=(x, y), texture=tex, sprite_index=idx)
    drawables.append(s)
    return s


def _attach_to_scene(stream, scenes, drawables):
    if not scenes or not drawables:
        return
    s = stream.pick_one(scenes)
    d = stream.pick_one(drawables)
    if s is None or d is None:
        return
    try:
        s.children.append(d)
    except Exception:
        pass


def _nest_into_frame(stream, frames, drawables):
    if not frames or not drawables:
        return
    parent = stream.pick_one(frames)
    child = stream.pick_one(drawables)
    if parent is None or child is None or parent is child:
        return
    try:
        parent.children.append(child)
    except Exception:
        pass


def _reparent(stream, frames, scenes, drawables):
    """Remove a drawable from wherever it lives and append it to a new parent.

    Exercises #270/#277: the engine must keep parent backrefs in sync
    when a drawable moves between containers.
    """
    if not drawables:
        return
    child = stream.pick_one(drawables)
    if child is None:
        return
    # Try all parent containers; the one that contains child, remove it.
    removed = False
    for f in frames:
        try:
            f.children.remove(child)
            removed = True
            break
        except Exception:
            pass
    if not removed:
        for s in scenes:
            try:
                s.children.remove(child)
                removed = True
                break
            except Exception:
                pass
    # Now append to a new random parent (Frame or Scene).
    if frames and stream.bool():
        target = stream.pick_one(frames)
    elif scenes:
        target = stream.pick_one(scenes)
    else:
        target = None
    if target is None or target is child:
        return
    try:
        target.children.append(child)
    except Exception:
        pass


def _animate_plain(stream, drawables):
    if not drawables:
        return
    d = stream.pick_one(drawables)
    if d is None:
        return
    prop = stream.pick_one(_NUMERIC_PROPS)
    target = stream.float_in_range(-200.0, 500.0)
    duration = stream.float_in_range(0.01, 2.0)
    easing = stream.pick_one(_EASINGS) if _EASINGS else None
    try:
        if easing is None:
            d.animate(prop, target, duration)
        else:
            d.animate(prop, target, duration, easing)
    except Exception:
        pass


def _animate_with_closure(stream, drawables):
    """Create an animation whose completion callback captures other
    drawables by strong ref. When the callback fires, some captured
    drawables may be gone from the tree.
    """
    if not drawables:
        return
    d = stream.pick_one(drawables)
    if d is None:
        return
    prop = stream.pick_one(_NUMERIC_PROPS)
    target = stream.float_in_range(-100.0, 300.0)
    duration = stream.float_in_range(0.01, 0.5)
    easing = stream.pick_one(_EASINGS) if _EASINGS else None
    n_captured = stream.int_in_range(1, min(4, len(drawables)))
    captured = [stream.pick_one(drawables) for _ in range(n_captured)]
    captured = [c for c in captured if c is not None]
    cb = _AnimCallbackTouchesDrawables(captured)
    try:
        if easing is None:
            d.animate(prop, target, duration, callback=cb)
        else:
            d.animate(prop, target, duration, easing, callback=cb)
    except Exception:
        pass


def _animate_cascading(stream, drawables):
    if not drawables:
        return
    d = stream.pick_one(drawables)
    if d is None:
        return
    depth = stream.int_in_range(1, 3)
    cb = _AnimCallbackCascades(depth)
    easing = _EASINGS[0] if _EASINGS else None
    try:
        if easing is None:
            d.animate("y", 50.0, 0.05, callback=cb)
        else:
            d.animate("y", 50.0, 0.05, easing, callback=cb)
    except Exception:
        pass


def _make_timer_plain(stream, timers):
    if len(timers) >= 8:
        return
    name = stream.ascii_str(6) or "t"
    interval = stream.int_in_range(1, 500)
    t = mcrfpy.Timer(name, _noop_timer, interval)
    timers.append(t)


def _make_timer_swap(stream, timers, scenes):
    if len(timers) >= 8 or len(scenes) < 2:
        return
    name = stream.ascii_str(6) or "sw"
    interval = stream.int_in_range(1, 200)
    cb = _TimerSwapsScene(scenes)
    t = mcrfpy.Timer(name, cb, interval)
    timers.append(t)


def _make_timer_mutate(stream, timers, scenes):
    if len(timers) >= 8:
        return
    name = stream.ascii_str(6) or "mu"
    interval = stream.int_in_range(1, 200)
    cb = _TimerMutatesTimers(timers, scenes)
    t = mcrfpy.Timer(name, cb, interval)
    timers.append(t)


def _make_timer_anim(stream, timers, drawables):
    if len(timers) >= 8 or not drawables:
        return
    name = stream.ascii_str(6) or "ta"
    interval = stream.int_in_range(1, 200)
    cb = _TimerStartsAnimation(drawables)
    t = mcrfpy.Timer(name, cb, interval)
    timers.append(t)


def _timer_transition(stream, timers):
    if not timers:
        return
    t = stream.pick_one(timers)
    if t is None:
        return
    op = stream.u8() % 5
    try:
        if op == 0:
            t.stop()
        elif op == 1:
            t.pause()
        elif op == 2:
            t.resume()
        elif op == 3:
            t.restart()
        else:
            # Poke properties - may throw
            _ = t.active
            _ = t.paused
            _ = t.stopped
            _ = t.remaining
    except Exception:
        pass


def _step_time(stream):
    dt = stream.float_in_range(0.0, 0.5)
    try:
        mcrfpy.step(dt)
    except Exception:
        pass


def _drop_refs(frames, timers, drawables):
    """Clear local python references to drawables/frames/timers.

    After this, only the C++ side (scene graph, timer queue) still knows
    about these objects. A subsequent step() that fires pending callbacks
    will hit any dangling pointers.
    """
    frames.clear()
    timers.clear()
    drawables.clear()


# --- Main dispatch --------------------------------------------------------

_NUM_OPS = 16


def fuzz_one_input(data):
    stream = ByteStream(data)
    scenes = []
    frames = []
    timers = []
    drawables = []

    try:
        # Seed one scene and make it active so subsequent ops have a
        # valid current_scene to mutate.
        try:
            first = mcrfpy.Scene("fuzz_atc")
            scenes.append(first)
            mcrfpy.current_scene = first
        except EXPECTED_EXCEPTIONS:
            pass

        n_ops = stream.int_in_range(1, 48)
        for _ in range(n_ops):
            if stream.remaining < 1:
                break
            op = stream.u8() % _NUM_OPS
            try:
                if op == 0:
                    _make_scene(stream, scenes)
                elif op == 1:
                    _activate_scene(stream, scenes)
                elif op == 2:
                    _make_frame(stream, frames, drawables)
                elif op == 3:
                    _make_caption(stream, drawables)
                elif op == 4:
                    _make_sprite(stream, drawables)
                elif op == 5:
                    _attach_to_scene(stream, scenes, drawables)
                elif op == 6:
                    _nest_into_frame(stream, frames, drawables)
                elif op == 7:
                    _reparent(stream, frames, scenes, drawables)
                elif op == 8:
                    _animate_plain(stream, drawables)
                elif op == 9:
                    _animate_with_closure(stream, drawables)
                elif op == 10:
                    _animate_cascading(stream, drawables)
                elif op == 11:
                    _make_timer_plain(stream, timers)
                elif op == 12:
                    _make_timer_swap(stream, timers, scenes)
                elif op == 13:
                    _make_timer_mutate(stream, timers, scenes)
                elif op == 14:
                    _make_timer_anim(stream, timers, drawables)
                elif op == 15:
                    _timer_transition(stream, timers)
            except EXPECTED_EXCEPTIONS:
                pass

            # Periodically advance time so timers/animations fire BEFORE
            # the scene is torn down. A single step() fires at most one
            # timer event; multiple steps guarantee forward progress.
            if (op & 3) == 0:
                _step_time(stream)

        # Final-phase: drop all local refs, then step again. Any callback
        # that still fires after this must operate on objects whose only
        # keep-alive was the C++ scene graph / timer queue. If any of
        # #269/#270/#275/#277 reproduces, it's most likely here.
        _drop_refs(frames, timers, drawables)
        for _ in range(3):
            _step_time(stream)

    except EXPECTED_EXCEPTIONS:
        pass
