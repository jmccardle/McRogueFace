"""Benchmark: TerminalLayer (#550) parse throughput and frame cost.

Reports:
  parse       MB/s of TerminalLayer.write() over a synthetic TUI stream (full-screen redraws with
              cursor moves, 256-colour and truecolor SGR, box drawing, plus colourised scrolling
              output), written in 64 KiB chunks. Parsing only: the cells are synced at render.
  scroll      per frame: one new line at the bottom (the whole screen scrolls, so every row is
              dirty), then a render. grid_render_time covers the sync from libghostty's render
              state, the chunk repaints and the blit.
  one cell    per frame: one character changed, then a render (one chunk repainted).
  idle        per frame: nothing written. The view re-blits its cached raster, so the layer does
              no work at all (grid_min 0, no chunk repaints).
  idle pan    per frame: nothing written, camera panned 1 px, so the view re-rasterises from the
              clean chunk textures: the layer's cost with nothing to sync.
  fill_rect   one full-screen fill_rect() through the terminal (one CUP + REP per row), and the
              render that follows.

grid_* is get_metrics()["grid_render_time"] (ms, min and median); there is no glFinish(), so on a
GPU driver it is mostly CPU submit time. A step() does not render headless; a screenshot does.

Usage:
  cd build && xvfb-run -a -s "-noreset" ./mcrogueface --headless --exec ../tests/benchmarks/terminal_layer_bench.py
"""
import os
import statistics
import sys
import tempfile
import time

import mcrfpy
from mcrfpy import automation

FRAMES = 40
WARMUP = 4
SHOT = os.path.join(tempfile.mkdtemp(prefix="mcrf_termbench_"), "f.png")
FONT = mcrfpy.Font("assets/JetbrainsMono.ttf")
TEX = mcrfpy.Texture.from_font(FONT, 8, codepoints=[(0x20, 0x7E), (0x2500, 0x259F)])
CW, CH = TEX.sprite_width, TEX.sprite_height


def tui_stream(cols, rows, frames):
    """A redraw-heavy TUI session (top/htop-like frames) interleaved with colourised log output."""
    parts = []
    for f in range(frames):
        parts.append("\x1b[?2026h\x1b[H")
        parts.append("\x1b[1;37;44m" + f" frame {f} ".ljust(cols)[:cols] + "\x1b[0m")
        for r in range(2, rows):
            parts.append(f"\x1b[{r};1H\x1b[38;5;{(r * 7 + f) % 256}m│\x1b[0m")
            parts.append(f"\x1b[38;2;{(r * 13) % 256};{(f * 5) % 256};200m pid {r * 101 + f:>6} ")
            bar = "█" * ((r + f) % max(1, cols // 3))
            parts.append(f"\x1b[32m{bar}\x1b[0m\x1b[K")
        parts.append("\x1b[?2026l")
        if f % 4 == 3:
            parts.append(f"\x1b[{rows};1H")
            for k in range(rows // 2):
                parts.append(f"\r\n\x1b[1;34mlog\x1b[0m {f}:{k} \x1b[33mwarning\x1b[0m something happened at {f * k}")
    return "".join(parts).encode()


def scene_for(term, cols, rows):
    scene = mcrfpy.Scene(f"tb_{cols}x{rows}_{time.perf_counter_ns()}")
    g = mcrfpy.Grid(grid_size=(cols, rows), pos=(0, 0), size=(cols * CW, rows * CH), texture=TEX, layers=[term])
    g.center = (cols * CW / 2, rows * CH / 2)
    scene.children.append(g)
    mcrfpy.current_scene = scene
    return g


def frame():
    mcrfpy.step(0.016)
    automation.screenshot(SHOT)
    return mcrfpy.get_metrics()


def run(fn, frames=FRAMES):
    times, chunks = [], []
    for i in range(WARMUP + frames):
        fn(i)
        m = frame()
        if i >= WARMUP:
            times.append(m["grid_render_time"])
            chunks.append(m["grid_chunks_repainted"])
    return min(times), statistics.median(times), statistics.median(chunks)


print(f"libghostty-vt TerminalLayer benchmark, atlas cell {CW}x{CH}")
for cols, rows in ((80, 24), (200, 60)):
    term = mcrfpy.TerminalLayer(texture=TEX, grid_size=(cols, rows))
    term.blink_interval = None
    grid = scene_for(term, cols, rows)
    data = tui_stream(cols, rows, 400)
    chunk = 64 * 1024
    t0 = time.perf_counter()
    for k in range(0, len(data), chunk):
        term.write(data[k:k + chunk])
    dt = time.perf_counter() - t0
    print(f"{cols}x{rows} parse: {len(data) / 1e6:.2f} MB in {dt * 1000:.1f} ms = {len(data) / dt / 1e6:.1f} MB/s")
    frame()

    n = [0]

    def scroll(i):
        n[0] += 1
        term.write(f"\r\n\x1b[3{n[0] % 8}mline {n[0]} \x1b[0m".encode() + b"x" * (cols // 2))

    gmin, gmed, ch = run(scroll)
    print(f"{cols}x{rows} full-screen scroll: grid_min {gmin:.3f} ms, grid_med {gmed:.3f} ms, chunks/frame {ch}")

    def one_cell(i):
        term.write(f"\x1b[{rows // 2};{cols // 2}H{'AB'[i % 2]}".encode())

    gmin, gmed, ch = run(one_cell)
    print(f"{cols}x{rows} one cell:           grid_min {gmin:.3f} ms, grid_med {gmed:.3f} ms, chunks/frame {ch}")

    gmin, gmed, ch = run(lambda i: None)
    print(f"{cols}x{rows} idle:               grid_min {gmin:.3f} ms, grid_med {gmed:.3f} ms, chunks/frame {ch}")

    def pan(i):
        grid.center = (cols * CW / 2 + (i % 2), rows * CH / 2)

    gmin, gmed, ch = run(pan)
    print(f"{cols}x{rows} idle pan:           grid_min {gmin:.3f} ms, grid_med {gmed:.3f} ms, chunks/frame {ch}")

    fills = []
    for i in range(10):
        t0 = time.perf_counter()
        term.fill_rect((0, 0), (cols, rows), TEX.index("#.:"[i % 3]))
        fills.append((time.perf_counter() - t0) * 1000)
    m = frame()
    print(f"{cols}x{rows} fill_rect full screen: median {statistics.median(fills):.3f} ms (min {min(fills):.3f}); "
          f"next render {m['grid_render_time']:.3f} ms")
sys.exit(0)
