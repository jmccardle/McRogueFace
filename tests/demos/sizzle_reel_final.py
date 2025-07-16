#!/usr/bin/env python3
"""
McRogueFace Animation Sizzle Reel - Final Version
=================================================

Complete demonstration of all animation capabilities.
This version works properly with the game loop and avoids API issues.

WARNING: This demo causes a segmentation fault due to a bug in the
AnimationManager. When UI elements with active animations are removed
from the scene, the AnimationManager crashes when trying to update them.

Use sizzle_reel_final_fixed.py instead, which works around this issue
by hiding objects off-screen instead of removing them.
"""

import mcrfpy

# Configuration
DEMO_DURATION = 6.0  # Duration for each demo

# All available easing functions
EASING_FUNCTIONS = [
    "linear", "easeIn", "easeOut", "easeInOut",
    "easeInQuad", "easeOutQuad", "easeInOutQuad",
    "easeInCubic", "easeOutCubic", "easeInOutCubic",
    "easeInQuart", "easeOutQuart", "easeInOutQuart",
    "easeInSine", "easeOutSine", "easeInOutSine",
    "easeInExpo", "easeOutExpo", "easeInOutExpo",
    "easeInCirc", "easeOutCirc", "easeInOutCirc",
    "easeInElastic", "easeOutElastic", "easeInOutElastic",
    "easeInBack", "easeOutBack", "easeInOutBack",
    "easeInBounce", "easeOutBounce", "easeInOutBounce"
]

# Track demo state
current_demo = 0
subtitle = None

def create_scene():
    """Create the demo scene"""
    mcrfpy.createScene("demo")
    mcrfpy.setScene("demo")
    
    ui = mcrfpy.sceneUI("demo")
    
    # Title
    title = mcrfpy.Caption("Animation Sizzle Reel", 500, 20)
    title.fill_color = mcrfpy.Color(255, 255, 0)
    title.outline = 2
    title.font_size = 28
    ui.append(title)
    
    # Subtitle
    global subtitle
    subtitle = mcrfpy.Caption("Starting...", 450, 60)
    subtitle.fill_color = mcrfpy.Color(200, 200, 200)
    ui.append(subtitle)
    
    return ui

def demo1_frame_animations():
    """Frame position, size, and color animations"""
    ui = mcrfpy.sceneUI("demo")
    subtitle.text = "Demo 1: Frame Animations"
    
    # Create frame
    f = mcrfpy.Frame(100, 150, 200, 100)
    f.fill_color = mcrfpy.Color(50, 50, 150)
    f.outline = 3
    f.outline_color = mcrfpy.Color(255, 255, 255)
    ui.append(f)
    
    # Animate properties
    mcrfpy.Animation("x", 600.0, 2.0, "easeInOutBack").start(f)
    mcrfpy.Animation("y", 300.0, 2.0, "easeInOutElastic").start(f)
    mcrfpy.Animation("w", 300.0, 2.5, "easeInOutCubic").start(f)
    mcrfpy.Animation("h", 150.0, 2.5, "easeInOutCubic").start(f)
    mcrfpy.Animation("fill_color", (255, 100, 50, 200), 3.0, "easeInOutSine").start(f)
    mcrfpy.Animation("outline", 8.0, 3.0, "easeInOutQuad").start(f)

def demo2_caption_animations():
    """Caption movement and text effects"""
    ui = mcrfpy.sceneUI("demo")
    subtitle.text = "Demo 2: Caption Animations"
    
    # Moving caption
    c1 = mcrfpy.Caption("Bouncing Text!", 100, 200)
    c1.fill_color = mcrfpy.Color(255, 255, 255)
    c1.font_size = 28
    ui.append(c1)
    mcrfpy.Animation("x", 800.0, 3.0, "easeOutBounce").start(c1)
    
    # Color cycling
    c2 = mcrfpy.Caption("Color Cycle", 400, 300)
    c2.outline = 2
    c2.font_size = 28
    ui.append(c2)
    mcrfpy.Animation("fill_color", (255, 0, 0, 255), 1.0, "linear").start(c2)
    
    # Typewriter effect
    c3 = mcrfpy.Caption("", 100, 400)
    c3.fill_color = mcrfpy.Color(0, 255, 255)
    c3.font_size = 28
    ui.append(c3)
    mcrfpy.Animation("text", "Typewriter effect animation...", 3.0, "linear").start(c3)

def demo3_easing_showcase():
    """Show all 30 easing functions"""
    ui = mcrfpy.sceneUI("demo")
    subtitle.text = "Demo 3: All 30 Easing Functions"
    
    # Create a small frame for each easing
    for i, easing in enumerate(EASING_FUNCTIONS[:15]):  # First 15
        row = i // 5
        col = i % 5
        x = 100 + col * 200
        y = 150 + row * 100
        
        # Frame
        f = mcrfpy.Frame(x, y, 20, 20)
        f.fill_color = mcrfpy.Color(100, 150, 255)
        ui.append(f)
        
        # Label
        label = mcrfpy.Caption(easing[:10], x, y - 20)
        label.fill_color = mcrfpy.Color(200, 200, 200)
        ui.append(label)
        
        # Animate with this easing
        mcrfpy.Animation("x", float(x + 150), 3.0, easing).start(f)

def demo4_performance():
    """Many simultaneous animations"""
    ui = mcrfpy.sceneUI("demo")
    subtitle.text = "Demo 4: 50+ Simultaneous Animations"
    
    for i in range(50):
        x = 100 + (i % 10) * 100
        y = 150 + (i // 10) * 100
        
        f = mcrfpy.Frame(x, y, 30, 30)
        f.fill_color = mcrfpy.Color((i*37)%256, (i*73)%256, (i*113)%256)
        ui.append(f)
        
        # Animate to random position
        target_x = 150 + (i % 8) * 110
        target_y = 200 + (i // 8) * 90
        easing = EASING_FUNCTIONS[i % len(EASING_FUNCTIONS)]
        
        mcrfpy.Animation("x", float(target_x), 2.5, easing).start(f)
        mcrfpy.Animation("y", float(target_y), 2.5, easing).start(f)
        mcrfpy.Animation("opacity", 0.3 + (i%7)*0.1, 2.0, "easeInOutSine").start(f)

def clear_demo_objects():
    """Clear scene except title and subtitle"""
    ui = mcrfpy.sceneUI("demo")
    # Keep removing items after the first 2 (title and subtitle)
    while len(ui) > 2:
        # Remove the last item
        ui.remove(len(ui)-1)

def next_demo(runtime):
    """Run the next demo"""
    global current_demo
    
    clear_demo_objects()
    
    demos = [
        demo1_frame_animations,
        demo2_caption_animations,
        demo3_easing_showcase,
        demo4_performance
    ]
    
    if current_demo < len(demos):
        demos[current_demo]()
        current_demo += 1
        
        if current_demo < len(demos):
            #mcrfpy.setTimer("next", next_demo, int(DEMO_DURATION * 1000))
            pass
        else:
            subtitle.text = "Demo Complete!"

# Initialize
print("Starting Animation Sizzle Reel...")
create_scene()
mcrfpy.setTimer("start", next_demo, int(DEMO_DURATION * 1000))
next_demo(0)
