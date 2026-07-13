"""Regression test for #368 - Frame(cache_subtree=True) froze its subtree's content.

`UIDrawable::markContentDirty()` guarded its walk up the parent chain with

    bool was_dirty = render_dirty;
    ...
    if (p && (!was_dirty || !p->render_dirty)) p->markContentDirty();

That guard is sound only if `render_dirty` is reliably cleared once a drawable has
been drawn. It was not: `clearDirty()` had exactly ONE call site in the entire
engine (UIGridView, added by #364). UIFrame/UICaption/UISprite/UILine/UICircle/UIArc
never cleared it, so `render_dirty` was a WRITE-ONCE LATCH -- true from the first
mutation until the object died.

With the flag permanently true, `was_dirty` was permanently true, the parent's
`render_dirty` was permanently true, and the guard was permanently false. Content
invalidation stopped propagating entirely, so a caching ancestor kept re-blitting a
stale composite: text never updated, colors never changed, sprites never changed.

Only MOVEMENT survived, because `x`/`y` route through `markCompositeDirty()` -- a
different function whose walk was already unconditional. That asymmetry is what made
the bug look intermittent rather than total, and it is why every case below mutates
CONTENT (color, text, sprite index) rather than position.

The fix makes markContentDirty's walk unconditional too, matching markCompositeDirty.
Correctness then does not depend on any drawable remembering to clear a flag.
"""
import mcrfpy
from mcrfpy import automation
import sys, os, tempfile

TMPDIR = tempfile.mkdtemp(prefix="mcrf368_")
_counter = 0
_results = []


def check(label, ok):
    _results.append((label, bool(ok)))
    print("  [%s] %s" % ("PASS" if ok else "FAIL", label))


def shot():
    global _counter
    path = os.path.join(TMPDIR, "s%d.png" % _counter)
    _counter += 1
    automation.screenshot(path)
    with open(path, "rb") as f:
        return f.read()


def case_recolor_under_cache():
    """Every recolor of a nested child must reach the caching ancestor.

    Not just the first: on master ZERO of these propagated, because render_dirty had
    already latched by the time the first one ran.
    """
    scene = mcrfpy.Scene("t368_recolor")
    scene.activate()

    cache = mcrfpy.Frame(pos=(10, 10), size=(300, 300), cache_subtree=True)
    scene.children.append(cache)
    inner = mcrfpy.Frame(pos=(0, 0), size=(280, 280))
    cache.children.append(inner)
    kid = mcrfpy.Frame(pos=(32, 32), size=(48, 48), fill_color=mcrfpy.Color(255, 0, 0))
    inner.children.append(kid)

    prev = shot()
    for i, rgb in enumerate([(0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)]):
        kid.fill_color = mcrfpy.Color(*rgb)
        cur = shot()
        check("1.%d: recolor -> %s repaints through the cache" % (i + 1, rgb), cur != prev)
        prev = cur


def case_caption_text_under_cache():
    """The most visible form of this bug: a label inside a cached panel never updates."""
    scene = mcrfpy.Scene("t368_text")
    scene.activate()

    cache = mcrfpy.Frame(pos=(10, 10), size=(300, 300), cache_subtree=True)
    scene.children.append(cache)
    inner = mcrfpy.Frame(pos=(0, 0), size=(280, 280))
    cache.children.append(inner)
    cap = mcrfpy.Caption(text="one", pos=(20, 20))
    inner.children.append(cap)

    prev = shot()
    for i, txt in enumerate(["two", "three", "four"]):
        cap.text = txt
        cur = shot()
        check("2.%d: caption text -> %r repaints through the cache" % (i + 1, txt), cur != prev)
        prev = cur


def case_deep_nesting():
    """The walk must reach the cache from arbitrary depth, not just one level down."""
    scene = mcrfpy.Scene("t368_deep")
    scene.activate()

    cache = mcrfpy.Frame(pos=(10, 10), size=(300, 300), cache_subtree=True)
    scene.children.append(cache)

    node = cache
    for d in range(4):
        nxt = mcrfpy.Frame(pos=(5, 5), size=(260 - d * 10, 260 - d * 10))
        node.children.append(nxt)
        node = nxt

    leaf = mcrfpy.Frame(pos=(10, 10), size=(40, 40), fill_color=mcrfpy.Color(255, 0, 0))
    node.children.append(leaf)

    prev = shot()
    for i, rgb in enumerate([(0, 255, 0), (0, 0, 255), (255, 255, 0)]):
        leaf.fill_color = mcrfpy.Color(*rgb)
        cur = shot()
        check("3.%d: depth-5 leaf recolor reaches the cache" % (i + 1), cur != prev)
        prev = cur


def case_idle_is_still_cheap():
    """The fix must not defeat the cache: an untouched frame stays byte-identical.

    If markContentDirty had been "fixed" by marking everything dirty every frame, the
    tests above would pass and the cache would be worthless. This is the counterweight.
    """
    scene = mcrfpy.Scene("t368_idle")
    scene.activate()

    cache = mcrfpy.Frame(pos=(10, 10), size=(300, 300), cache_subtree=True)
    scene.children.append(cache)
    kid = mcrfpy.Frame(pos=(32, 32), size=(48, 48), fill_color=mcrfpy.Color(255, 0, 0))
    cache.children.append(kid)

    a = shot()
    b = shot()
    c = shot()
    check("4a: idle frames under a cache are byte-identical", a == b == c)


def case_uncached_still_works():
    """Sanity: the ordinary (uncached) path must be unaffected."""
    scene = mcrfpy.Scene("t368_plain")
    scene.activate()

    holder = mcrfpy.Frame(pos=(10, 10), size=(300, 300))
    scene.children.append(holder)
    kid = mcrfpy.Frame(pos=(32, 32), size=(48, 48), fill_color=mcrfpy.Color(255, 0, 0))
    holder.children.append(kid)

    prev = shot()
    for i, rgb in enumerate([(0, 255, 0), (0, 0, 255)]):
        kid.fill_color = mcrfpy.Color(*rgb)
        cur = shot()
        check("5.%d: recolor repaints without a cache" % (i + 1), cur != prev)
        prev = cur


def run_tests():
    case_recolor_under_cache()
    case_caption_text_under_cache()
    case_deep_nesting()
    case_idle_is_still_cheap()
    case_uncached_still_works()
    return all(ok for _, ok in _results)


if __name__ == "__main__":
    try:
        ok = run_tests()
        print("PASS" if ok else "FAIL")
        sys.exit(0 if ok else 1)
    except Exception:
        import traceback
        traceback.print_exc()
        print("FAIL")
        sys.exit(1)
