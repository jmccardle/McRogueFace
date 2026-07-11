"""Footprint measurement for #338 - UIDrawable per-instance memory.

#338 tracks trimming per-drawable memory (the base class is paid by every
Frame/Caption/Sprite/Grid). This is the "measure first" deliverable: it reports
the approximate per-drawable resident-memory cost (C++ object + Python wrapper +
allocator overhead) for a batch of drawables and guards against gross
regressions. It is intentionally a loose bound, not a precise sizeof -- the
invasive base-class relocations (render_sprite into the cache struct, callback
block) are deferred; only the lazy rotationTexture change landed.

Direct-execution style; Linux RSS via /proc/self/statm.
"""
import mcrfpy
import sys
import os

N = 5000


def rss_bytes():
    # statm fields are in pages; field[1] is resident set size.
    with open("/proc/self/statm") as f:
        pages = int(f.read().split()[1])
    return pages * os.sysconf("SC_PAGE_SIZE")


def measure(factory, label):
    base = rss_bytes()
    keep = [factory(i) for i in range(N)]
    after = rss_bytes()
    per = (after - base) / N
    print("  %-8s %d instances: ~%.0f bytes/instance (RSS delta %.1f MB)"
          % (label, N, per, (after - base) / 1e6))
    # Loose guard: catches a gross per-instance blowup, not small drift.
    assert per < 8192, "%s per-instance RSS %.0f exceeds 8KB guard" % (label, per)
    return keep


def main():
    scene = mcrfpy.Scene("t338")

    frames = measure(lambda i: mcrfpy.Frame(pos=(0, 0), size=(4, 4)), "Frame")
    caps = measure(lambda i: mcrfpy.Caption(pos=(0, 0), text="x"), "Caption")

    # Sanity: a rotating grid still renders correctly after rotationTexture was
    # made lazily allocated (#338). Just exercise the path; no crash == pass.
    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(6, 6), texture=tex)
    scene.children.append(grid)
    grid.camera_rotation = 30.0
    from mcrfpy import automation
    automation.screenshot("/tmp/issue338_rotated.png")  # forces render through the lazy path

    # keep references alive until here
    assert len(frames) == N and len(caps) == N

    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
