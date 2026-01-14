"""Run all procgen demos and capture screenshots.
Execute this script from the build directory.
"""
import os
import sys
import subprocess

DEMOS = [
    "01_heightmap_hills.py",
    "02_heightmap_noise.py",
    "03_heightmap_operations.py",
    "04_heightmap_transforms.py",
    "05_heightmap_erosion.py",
    "06_heightmap_voronoi.py",
    "07_heightmap_bezier.py",
    "08_heightmap_thresholds.py",
    "10_bsp_dungeon.py",
    "11_bsp_traversal.py",
    "12_bsp_adjacency.py",
    "13_bsp_shrink.py",
    "14_bsp_manual_split.py",
    "20_noise_algorithms.py",
    "21_noise_parameters.py",
    "30_advanced_cave_dungeon.py",
    "31_advanced_island.py",
    "32_advanced_city.py",
    "33_advanced_caves.py",
    "34_advanced_volcanic.py",
]

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.abspath(os.path.join(script_dir, "../../../build"))

    if not os.path.exists(os.path.join(build_dir, "mcrogueface")):
        print(f"Error: mcrogueface not found in {build_dir}")
        print("Please run from the build directory or adjust paths.")
        return 1

    os.chdir(build_dir)

    success = 0
    failed = 0

    for demo in DEMOS:
        demo_path = os.path.join(script_dir, demo)
        if not os.path.exists(demo_path):
            print(f"SKIP: {demo} (not found)")
            continue

        print(f"Running: {demo}...", end=" ", flush=True)

        try:
            result = subprocess.run(
                ["./mcrogueface", "--headless", "--exec", demo_path],
                timeout=30,
                capture_output=True,
                text=True
            )

            # Check if screenshot was created
            png_name = f"procgen_{demo.replace('.py', '.png')}"
            if os.path.exists(png_name):
                print(f"OK -> {png_name}")
                success += 1
            else:
                print(f"FAIL (no screenshot)")
                if result.stderr:
                    print(f"  stderr: {result.stderr[:200]}")
                failed += 1

        except subprocess.TimeoutExpired:
            print("TIMEOUT")
            failed += 1
        except Exception as e:
            print(f"ERROR: {e}")
            failed += 1

    print(f"\nResults: {success} passed, {failed} failed")
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
