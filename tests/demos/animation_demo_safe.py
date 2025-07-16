#!/usr/bin/env python3
"""
McRogueFace Animation Demo - Safe Version
=========================================

A safer, simpler version that demonstrates animations without crashes.
"""

import mcrfpy
import sys

# Configuration
DEMO_DURATION = 4.0

# Track state
current_demo = 0
subtitle = None
demo_items = []

def create_scene():
    """Create the demo scene"""
    mcrfpy.createScene("demo")
    mcrfpy.setScene("demo")
    
    ui = mcrfpy.sceneUI("demo")
    
    # Title
    title = mcrfpy.Caption("Animation Demo", 500, 20)
    title.fill_color = mcrfpy.Color(255, 255, 0)
    title.outline = 2
    ui.append(title)
    
    # Subtitle
    global subtitle
    subtitle = mcrfpy.Caption("Starting...", 450, 60)
    subtitle.fill_color = mcrfpy.Color(200, 200, 200)
    ui.append(subtitle)

def clear_demo_items():
    """Clear demo items from scene"""
    global demo_items
    ui = mcrfpy.sceneUI("demo")
    
    # Remove demo items by tracking what we added
    for item in demo_items:
        try:
            # Find index of item
            for i in range(len(ui)):
                if i >= 2:  # Skip title and subtitle
                    ui.remove(i)
                    break
        except:
            pass
    
    demo_items = []

def demo1_basic():
    """Basic frame animations"""
    global demo_items
    clear_demo_items()
    
    ui = mcrfpy.sceneUI("demo")
    subtitle.text = "Demo 1: Basic Frame Animations"
    
    # Create frame
    f = mcrfpy.Frame(100, 150, 200, 100)
    f.fill_color = mcrfpy.Color(50, 50, 150)
    f.outline = 3
    ui.append(f)
    demo_items.append(f)
    
    # Simple animations
    mcrfpy.Animation("x", 600.0, 2.0, "easeInOut").start(f)
    mcrfpy.Animation("w", 300.0, 2.0, "easeInOut").start(f)
    mcrfpy.Animation("fill_color", (255, 100, 50, 200), 3.0, "linear").start(f)

def demo2_caption():
    """Caption animations"""
    global demo_items
    clear_demo_items()
    
    ui = mcrfpy.sceneUI("demo")
    subtitle.text = "Demo 2: Caption Animations"
    
    # Moving caption
    c1 = mcrfpy.Caption("Moving Text!", 100, 200)
    c1.fill_color = mcrfpy.Color(255, 255, 255)
    ui.append(c1)
    demo_items.append(c1)
    
    mcrfpy.Animation("x", 700.0, 3.0, "easeOutBounce").start(c1)
    
    # Typewriter
    c2 = mcrfpy.Caption("", 100, 300)
    c2.fill_color = mcrfpy.Color(0, 255, 255)
    ui.append(c2)
    demo_items.append(c2)
    
    mcrfpy.Animation("text", "Typewriter effect...", 3.0, "linear").start(c2)

def demo3_multiple():
    """Multiple animations"""
    global demo_items
    clear_demo_items()
    
    ui = mcrfpy.sceneUI("demo")
    subtitle.text = "Demo 3: Multiple Animations"
    
    # Create several frames
    for i in range(5):
        f = mcrfpy.Frame(100 + i * 120, 200, 80, 80)
        f.fill_color = mcrfpy.Color(50 + i * 40, 100, 200 - i * 30)
        ui.append(f)
        demo_items.append(f)
        
        # Animate each differently
        target_y = 350 + i * 20
        mcrfpy.Animation("y", float(target_y), 2.0, "easeInOut").start(f)
        mcrfpy.Animation("opacity", 0.5, 3.0, "easeInOut").start(f)

def run_next_demo(runtime):
    """Run the next demo"""
    global current_demo
    
    demos = [demo1_basic, demo2_caption, demo3_multiple]
    
    if current_demo < len(demos):
        demos[current_demo]()
        current_demo += 1
        
        if current_demo < len(demos):
            mcrfpy.setTimer("next", run_next_demo, int(DEMO_DURATION * 1000))
        else:
            subtitle.text = "Demo Complete!"
            # Exit after a delay
            def exit_program(rt):
                print("Demo finished successfully!")
                sys.exit(0)
            mcrfpy.setTimer("exit", exit_program, 2000)

# Initialize
print("Starting Safe Animation Demo...")
create_scene()

# Start demos
mcrfpy.setTimer("start", run_next_demo, 500)