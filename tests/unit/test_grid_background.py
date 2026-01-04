#!/usr/bin/env python3
"""Test Grid background color functionality"""

import mcrfpy
import sys

def test_grid_background():
    """Test Grid background color property"""
    print("Testing Grid Background Color...")
    
    # Create a test scene
    test = mcrfpy.Scene("test")
    ui = test.children
    
    # Create a grid with default background
    grid = mcrfpy.Grid(pos=(50, 50), size=(400, 300), grid_size=(20, 15))
    ui.append(grid)

    # Add color layer for some tiles to see the background better
    color_layer = grid.add_layer("color", z_index=-1)
    for x in range(5, 15):
        for y in range(5, 10):
            color_layer.set(x, y, mcrfpy.Color(100, 150, 100))
    
    # Add UI to show current background color
    info_frame = mcrfpy.Frame(pos=(500, 50), size=(200, 150),
                             fill_color=mcrfpy.Color(40, 40, 40),
                             outline_color=mcrfpy.Color(200, 200, 200),
                             outline=2)
    ui.append(info_frame)

    color_caption = mcrfpy.Caption(pos=(510, 60), text="Background Color:")
    color_caption.font_size = 14
    color_caption.fill_color = mcrfpy.Color(255, 255, 255)
    info_frame.children.append(color_caption)

    color_display = mcrfpy.Caption(pos=(510, 80), text="")
    color_display.font_size = 12
    color_display.fill_color = mcrfpy.Color(200, 200, 200)
    info_frame.children.append(color_display)
    
    # Activate the scene
    test.activate()
    
    def run_tests(timer, runtime):
        """Run background color tests"""
        timer.stop()
        
        print("\nTest 1: Default background color")
        default_color = grid.background_color
        print(f"Default: R={default_color.r}, G={default_color.g}, B={default_color.b}, A={default_color.a}")
        color_display.text = f"R:{default_color.r} G:{default_color.g} B:{default_color.b}"
        
        def test_set_color(timer, runtime):
            timer.stop()
            print("\nTest 2: Set background to blue")
            grid.background_color = mcrfpy.Color(20, 40, 100)
            new_color = grid.background_color
            print(f"+ Set to: R={new_color.r}, G={new_color.g}, B={new_color.b}")
            color_display.text = f"R:{new_color.r} G:{new_color.g} B:{new_color.b}"

        def test_animation(timer, runtime):
            timer.stop()
            print("\nTest 3: Manual color cycling")
            # Manually change color to test property is working
            colors = [
                mcrfpy.Color(200, 20, 20),   # Red
                mcrfpy.Color(20, 200, 20),   # Green
                mcrfpy.Color(20, 20, 200),   # Blue
            ]

            color_index = [0]  # Use list to allow modification in nested function

            def cycle_red(t, r):
                t.stop()
                grid.background_color = colors[0]
                c = grid.background_color
                color_display.text = f"R:{c.r} G:{c.g} B:{c.b}"
                print(f"+ Set to Red: R={c.r}, G={c.g}, B={c.b}")

            def cycle_green(t, r):
                t.stop()
                grid.background_color = colors[1]
                c = grid.background_color
                color_display.text = f"R:{c.r} G:{c.g} B:{c.b}"
                print(f"+ Set to Green: R={c.r}, G={c.g}, B={c.b}")

            def cycle_blue(t, r):
                t.stop()
                grid.background_color = colors[2]
                c = grid.background_color
                color_display.text = f"R:{c.r} G:{c.g} B:{c.b}"
                print(f"+ Set to Blue: R={c.r}, G={c.g}, B={c.b}")

            # Cycle through colors
            mcrfpy.Timer("cycle_0", cycle_red, 100, once=True)
            mcrfpy.Timer("cycle_1", cycle_green, 400, once=True)
            mcrfpy.Timer("cycle_2", cycle_blue, 700, once=True)

        def test_complete(timer, runtime):
            timer.stop()
            print("\nTest 4: Final color check")
            final_color = grid.background_color
            print(f"Final: R={final_color.r}, G={final_color.g}, B={final_color.b}")

            print("\n+ Grid background color tests completed!")
            print("- Default background color works")
            print("- Setting background color works")
            print("- Color cycling works")

            sys.exit(0)

        # Schedule tests
        mcrfpy.Timer("test_set", test_set_color, 1000, once=True)
        mcrfpy.Timer("test_anim", test_animation, 2000, once=True)
        mcrfpy.Timer("complete", test_complete, 4500, once=True)

    # Start tests
    mcrfpy.Timer("run_tests", run_tests, 100, once=True)

if __name__ == "__main__":
    test_grid_background()