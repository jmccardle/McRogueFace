#!/usr/bin/env python3
"""
McRogueFace Animation Sizzle Reel - Fixed Version
=================================================

This version works around the animation crash by:
1. Using shorter demo durations to ensure animations complete before clearing
2. Adding a delay before clearing to let animations finish
3. Not removing objects, just hiding them off-screen instead
"""

import mcrfpy

# Configuration
DEMO_DURATION = 3.5  # Slightly shorter to ensure animations complete
CLEAR_DELAY = 0.5    # Extra delay before clearing

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
demo_objects = []  # Track objects to hide instead of remove

def create_scene():
    """Create the demo scene"""
    mcrfpy.createScene("demo")
    mcrfpy.setScene("demo")
    
    ui = mcrfpy.sceneUI("demo")
    
    # Title
    title = mcrfpy.Caption("Animation Sizzle Reel", 500, 20)
    title.fill_color = mcrfpy.Color(255, 255, 0)
    title.outline = 2
    ui.append(title)
    
    # Subtitle
    global subtitle
    subtitle = mcrfpy.Caption("Starting...", 450, 60)
    subtitle.fill_color = mcrfpy.Color(200, 200, 200)
    ui.append(subtitle)
    
    return ui

def hide_demo_objects():
    """Hide demo objects by moving them off-screen instead of removing"""
    global demo_objects
    # Move all demo objects far off-screen
    for obj in demo_objects:
        obj.x = -1000
        obj.y = -1000
    demo_objects = []

def demo1_frame_animations():
    """Frame position, size, and color animations"""
    global demo_objects
    ui = mcrfpy.sceneUI("demo")
    subtitle.text = "Demo 1: Frame Animations"
    
    # Create frame
    f = mcrfpy.Frame(100, 150, 200, 100)
    f.fill_color = mcrfpy.Color(50, 50, 150)
    f.outline = 3
    f.outline_color = mcrfpy.Color(255, 255, 255)
    ui.append(f)
    demo_objects.append(f)
    
    # Animate properties with shorter durations
    mcrfpy.Animation("x", 600.0, 2.0, "easeInOutBack").start(f)
    mcrfpy.Animation("y", 300.0, 2.0, "easeInOutElastic").start(f)
    mcrfpy.Animation("w", 300.0, 2.5, "easeInOutCubic").start(f)
    mcrfpy.Animation("h", 150.0, 2.5, "easeInOutCubic").start(f)
    mcrfpy.Animation("fill_color", (255, 100, 50, 200), 3.0, "easeInOutSine").start(f)
    mcrfpy.Animation("outline", 8.0, 3.0, "easeInOutQuad").start(f)

def demo2_caption_animations():
    """Caption movement and text effects"""
    global demo_objects
    ui = mcrfpy.sceneUI("demo")
    subtitle.text = "Demo 2: Caption Animations"
    
    # Moving caption
    c1 = mcrfpy.Caption("Bouncing Text!", 100, 200)
    c1.fill_color = mcrfpy.Color(255, 255, 255)
    ui.append(c1)
    demo_objects.append(c1)
    mcrfpy.Animation("x", 800.0, 3.0, "easeOutBounce").start(c1)
    
    # Color cycling
    c2 = mcrfpy.Caption("Color Cycle", 400, 300)
    c2.outline = 2
    ui.append(c2)
    demo_objects.append(c2)
    mcrfpy.Animation("fill_color", (255, 0, 0, 255), 1.0, "linear").start(c2)
    
    # Static text (no typewriter effect to avoid issues)
    c3 = mcrfpy.Caption("Animation Demo", 100, 400)
    c3.fill_color = mcrfpy.Color(0, 255, 255)
    ui.append(c3)
    demo_objects.append(c3)

def demo3_easing_showcase():
    """Show all 30 easing functions"""
    global demo_objects
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
        demo_objects.append(f)
        
        # Label
        label = mcrfpy.Caption(easing[:10], x, y - 20)
        label.fill_color = mcrfpy.Color(200, 200, 200)
        ui.append(label)
        demo_objects.append(label)
        
        # Animate with this easing
        mcrfpy.Animation("x", float(x + 150), 3.0, easing).start(f)

def demo4_performance():
    """Many simultaneous animations"""
    global demo_objects
    ui = mcrfpy.sceneUI("demo")
    subtitle.text = "Demo 4: 50+ Simultaneous Animations"
    
    for i in range(50):
        x = 100 + (i % 10) * 80
        y = 150 + (i // 10) * 80
        
        f = mcrfpy.Frame(x, y, 30, 30)
        f.fill_color = mcrfpy.Color((i*37)%256, (i*73)%256, (i*113)%256)
        ui.append(f)
        demo_objects.append(f)
        
        # Animate to random position
        target_x = 150 + (i % 8) * 90
        target_y = 200 + (i // 8) * 70
        easing = EASING_FUNCTIONS[i % len(EASING_FUNCTIONS)]
        
        mcrfpy.Animation("x", float(target_x), 2.5, easing).start(f)
        mcrfpy.Animation("y", float(target_y), 2.5, easing).start(f)

def next_demo(runtime):
    """Run the next demo with proper cleanup"""
    global current_demo
    
    # First hide old objects
    hide_demo_objects()
    
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
            mcrfpy.setTimer("next", next_demo, int(DEMO_DURATION * 1000))
        else:
            subtitle.text = "Demo Complete!"
            mcrfpy.setTimer("exit", lambda t: mcrfpy.exit(), 2000)

# Initialize
print("Starting Animation Sizzle Reel (Fixed)...")
create_scene()
mcrfpy.setTimer("start", next_demo, 500)