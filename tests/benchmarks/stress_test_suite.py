#!/usr/bin/env python3
"""
Stress Test Suite for McRogueFace Performance Analysis

Establishes baseline performance data before implementing texture caching (#144).
Uses a single repeating timer pattern to avoid callback chain issues.

Usage:
  ./mcrogueface --headless --exec tests/benchmarks/stress_test_suite.py
"""
import mcrfpy
import sys
import os
import json
from datetime import datetime

# Configuration
TEST_DURATION_MS = 2000
TIMER_INTERVAL_MS = 50
OUTPUT_DIR = "../tests/benchmarks/baseline"
IS_HEADLESS = True  # Assume headless for automated testing

class StressTestRunner:
    def __init__(self):
        self.tests = []
        self.current_test = -1
        self.results = {}
        self.frames_counted = 0
        self.mode = "headless" if IS_HEADLESS else "windowed"

    def add_test(self, name, setup_fn, description=""):
        self.tests.append({'name': name, 'setup': setup_fn, 'description': description})

    def tick(self, timer, runtime):
        """Single timer callback that manages all test flow"""
        self.frames_counted += 1

        # Check if current test should end
        if self.current_test >= 0 and self.frames_counted * TIMER_INTERVAL_MS >= TEST_DURATION_MS:
            self.end_current_test()
            self.start_next_test()
        elif self.current_test < 0:
            self.start_next_test()

    def start_next_test(self):
        self.current_test += 1

        if self.current_test >= len(self.tests):
            self.finish_suite()
            return

        test = self.tests[self.current_test]
        print(f"\n[{self.current_test + 1}/{len(self.tests)}] {test['name']}")
        print(f"  {test['description']}")

        # Setup scene
        scene_name = f"stress_{self.current_test}"
        _scene = mcrfpy.Scene(scene_name)

        # Start benchmark
        mcrfpy.start_benchmark()
        mcrfpy.log_benchmark(f"TEST: {test['name']}")

        # Run setup
        try:
            test['setup'](scene_name)
        except Exception as e:
            print(f"  SETUP ERROR: {e}")

        mcrfpy.current_scene = scene_name
        self.frames_counted = 0

    def end_current_test(self):
        if self.current_test < 0:
            return

        test = self.tests[self.current_test]
        try:
            filename = mcrfpy.end_benchmark()

            with open(filename, 'r') as f:
                data = json.load(f)

            frames = data['frames'][30:]  # Skip warmup
            if frames:
                avg_work = sum(f['work_time_ms'] for f in frames) / len(frames)
                avg_frame = sum(f['frame_time_ms'] for f in frames) / len(frames)
                max_work = max(f['work_time_ms'] for f in frames)

                self.results[test['name']] = {
                    'avg_work_ms': avg_work,
                    'max_work_ms': max_work,
                    'frame_count': len(frames),
                }
                print(f"  Work: {avg_work:.2f}ms avg, {max_work:.2f}ms max ({len(frames)} frames)")

            os.makedirs(OUTPUT_DIR, exist_ok=True)
            new_name = f"{OUTPUT_DIR}/{self.mode}_{test['name']}.json"
            os.rename(filename, new_name)

        except Exception as e:
            print(f"  ERROR: {e}")
            self.results[test['name']] = {'error': str(e)}

    def finish_suite(self):
        self.tick_timer.stop()

        print("\n" + "="*50)
        print("STRESS TEST COMPLETE")
        print("="*50)

        for name, r in self.results.items():
            if 'error' in r:
                print(f"  {name}: ERROR")
            else:
                print(f"  {name}: {r['avg_work_ms']:.2f}ms avg")

        # Save summary
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(f"{OUTPUT_DIR}/{self.mode}_summary.json", 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'mode': self.mode,
                'results': self.results
            }, f, indent=2)

        print(f"\nResults saved to {OUTPUT_DIR}/")
        sys.exit(0)

    def start(self):
        print("="*50)
        print("McRogueFace Stress Test Suite")
        print("="*50)
        print(f"Tests: {len(self.tests)}, Duration: {TEST_DURATION_MS}ms each")

        init = mcrfpy.Scene("init")
        ui = init.children
        ui.append(mcrfpy.Frame(pos=(0,0), size=(10,10)))  # Required for timer to fire
        init.activate()
        self.tick_timer = mcrfpy.Timer("tick", self.tick, TIMER_INTERVAL_MS)


# =============================================================================
# TEST SETUP FUNCTIONS
# =============================================================================

def test_many_frames(scene_name):
    """1000 Frame elements"""
    ui = _scene.children  # TODO: Replace _scene with correct Scene object
    for i in range(1000):
        frame = mcrfpy.Frame(
            pos=((i % 32) * 32, (i // 32) * 24),
            size=(30, 22),
            fill_color=mcrfpy.Color((i*7)%256, (i*13)%256, (i*17)%256)
        )
        ui.append(frame)
    mcrfpy.log_benchmark("1000 frames created")

def test_many_sprites(scene_name):
    """500 Sprite elements"""
    ui = _scene.children  # TODO: Replace _scene with correct Scene object
    texture = mcrfpy.Texture("assets/kenney_ice.png", 16, 16)
    for i in range(500):
        sprite = mcrfpy.Sprite(
            pos=((i % 20) * 48 + 10, (i // 20) * 28 + 10),
            texture=texture,
            sprite_index=i % 128
        )
        sprite.scale_x = 2.0
        sprite.scale_y = 2.0
        ui.append(sprite)
    mcrfpy.log_benchmark("500 sprites created")

def test_many_captions(scene_name):
    """500 Caption elements"""
    ui = _scene.children  # TODO: Replace _scene with correct Scene object
    for i in range(500):
        caption = mcrfpy.Caption(
            text=f"Text #{i}",
            pos=((i % 20) * 50 + 5, (i // 20) * 28 + 5)
        )
        ui.append(caption)
    mcrfpy.log_benchmark("500 captions created")

def test_deep_nesting(scene_name):
    """15-level nested frames"""
    ui = _scene.children  # TODO: Replace _scene with correct Scene object
    current = ui
    for level in range(15):
        frame = mcrfpy.Frame(
            pos=(20, 20),
            size=(1024 - level * 60, 768 - level * 45),
            fill_color=mcrfpy.Color((level * 17) % 256, 100, (255 - level * 17) % 256, 200)
        )
        current.append(frame)
        # Add children at each level
        for j in range(3):
            child = mcrfpy.Frame(pos=(50 + j * 80, 50), size=(60, 30))
            frame.children.append(child)
        current = frame.children
    mcrfpy.log_benchmark("15-level nesting created")

def test_large_grid(scene_name):
    """100x100 grid with 500 entities"""
    ui = _scene.children  # TODO: Replace _scene with correct Scene object
    texture = mcrfpy.Texture("assets/kenney_ice.png", 16, 16)
    grid = mcrfpy.Grid(pos=(50, 50), size=(900, 650), grid_size=(100, 100), texture=texture)
    ui.append(grid)

    for y in range(100):
        for x in range(100):
            cell = grid.at(x, y)
            cell.tilesprite = (x + y) % 64

    for i in range(500):
        entity = mcrfpy.Entity(
            grid_pos=((i * 7) % 100, (i * 11) % 100),
            texture=texture,
            sprite_index=(i * 3) % 128,
            grid=grid
        )
    mcrfpy.log_benchmark("100x100 grid with 500 entities created")

def test_animation_stress(scene_name):
    """100 frames with 200 animations"""
    ui = _scene.children  # TODO: Replace _scene with correct Scene object
    for i in range(100):
        frame = mcrfpy.Frame(
            pos=((i % 10) * 100 + 10, (i // 10) * 70 + 10),
            size=(80, 50),
            fill_color=mcrfpy.Color(100, 150, 200)
        )
        ui.append(frame)

        # Two animations per frame
        anim_x = mcrfpy.Animation("x", float((i % 10) * 100 + 50), 1.5, "easeInOut")
        anim_x.start(frame)
        anim_o = mcrfpy.Animation("fill_color.a", 128 + (i % 128), 2.0, "linear")
        anim_o.start(frame)
    mcrfpy.log_benchmark("100 frames with 200 animations")

def test_static_scene(scene_name):
    """Static game scene (ideal for caching)"""
    ui = _scene.children  # TODO: Replace _scene with correct Scene object
    texture = mcrfpy.Texture("assets/kenney_ice.png", 16, 16)

    # Background
    bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 50))
    ui.append(bg)

    # UI panel
    panel = mcrfpy.Frame(pos=(10, 10), size=(200, 300), fill_color=mcrfpy.Color(50, 50, 70))
    ui.append(panel)
    for i in range(10):
        caption = mcrfpy.Caption(text=f"Status {i}", pos=(10, 10 + i * 25))
        panel.children.append(caption)

    # Grid
    grid = mcrfpy.Grid(pos=(220, 10), size=(790, 600), grid_size=(40, 30), texture=texture)
    ui.append(grid)
    for y in range(30):
        for x in range(40):
            grid.at(x, y).tilesprite = ((x + y) % 4) + 1

    for i in range(20):
        entity = mcrfpy.Entity(grid_pos=((i*2) % 40, (i*3) % 30),
                              texture=texture, sprite_index=64 + i % 16, grid=grid)
    mcrfpy.log_benchmark("Static game scene created")


def test_static_scene_cached(scene_name):
    """Static game scene with cache_subtree enabled (#144)"""
    ui = _scene.children  # TODO: Replace _scene with correct Scene object
    texture = mcrfpy.Texture("assets/kenney_ice.png", 16, 16)

    # Background with caching enabled
    bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 50), cache_subtree=True)
    ui.append(bg)

    # UI panel with caching enabled
    panel = mcrfpy.Frame(pos=(10, 10), size=(200, 300), fill_color=mcrfpy.Color(50, 50, 70), cache_subtree=True)
    ui.append(panel)
    for i in range(10):
        caption = mcrfpy.Caption(text=f"Status {i}", pos=(10, 10 + i * 25))
        panel.children.append(caption)

    # Grid (not cached - grids handle their own optimization)
    grid = mcrfpy.Grid(pos=(220, 10), size=(790, 600), grid_size=(40, 30), texture=texture)
    ui.append(grid)
    for y in range(30):
        for x in range(40):
            grid.at(x, y).tilesprite = ((x + y) % 4) + 1

    for i in range(20):
        entity = mcrfpy.Entity(grid_pos=((i*2) % 40, (i*3) % 30),
                              texture=texture, sprite_index=64 + i % 16, grid=grid)
    mcrfpy.log_benchmark("Static game scene with cache_subtree created")


def test_deep_nesting_cached(scene_name):
    """15-level nested frames with cache_subtree on outer frame (#144)"""
    ui = _scene.children  # TODO: Replace _scene with correct Scene object

    # Outer frame with caching - entire subtree cached
    outer = mcrfpy.Frame(
        pos=(0, 0),
        size=(1024, 768),
        fill_color=mcrfpy.Color(0, 100, 255, 200),
        cache_subtree=True  # Cache entire nested hierarchy
    )
    ui.append(outer)

    current = outer.children
    for level in range(15):
        frame = mcrfpy.Frame(
            pos=(20, 20),
            size=(1024 - level * 60, 768 - level * 45),
            fill_color=mcrfpy.Color((level * 17) % 256, 100, (255 - level * 17) % 256, 200)
        )
        current.append(frame)
        # Add children at each level
        for j in range(3):
            child = mcrfpy.Frame(pos=(50 + j * 80, 50), size=(60, 30))
            frame.children.append(child)
        current = frame.children
    mcrfpy.log_benchmark("15-level nesting with cache_subtree created")


# =============================================================================
# MAIN
# =============================================================================

runner = StressTestRunner()
runner.add_test("many_frames", test_many_frames, "1000 Frame elements")
runner.add_test("many_sprites", test_many_sprites, "500 Sprite elements")
runner.add_test("many_captions", test_many_captions, "500 Caption elements")
runner.add_test("deep_nesting", test_deep_nesting, "15-level nested hierarchy")
runner.add_test("deep_nesting_cached", test_deep_nesting_cached, "15-level nested (cache_subtree)")
runner.add_test("large_grid", test_large_grid, "100x100 grid, 500 entities")
runner.add_test("animation_stress", test_animation_stress, "100 frames, 200 animations")
runner.add_test("static_scene", test_static_scene, "Static game scene (no caching)")
runner.add_test("static_scene_cached", test_static_scene_cached, "Static game scene (cache_subtree)")
runner.start()
