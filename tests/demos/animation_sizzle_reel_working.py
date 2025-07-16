#!/usr/bin/env python3
"""
McRogueFace Animation Sizzle Reel - Working Version
===================================================

Complete demonstration of all animation capabilities.
Fixed to work properly with the API.
"""

import mcrfpy
import sys
import math

# Configuration
DEMO_DURATION = 7.0  # Duration for each demo

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

# Track state
current_demo = 0
subtitle = None
demo_objects = []

def create_scene():
    """Create the demo scene with title"""
    mcrfpy.createScene("sizzle")
    mcrfpy.setScene("sizzle")
    
    ui = mcrfpy.sceneUI("sizzle")
    
    # Title
    title = mcrfpy.Caption("McRogueFace Animation Sizzle Reel", 340, 20)
    title.fill_color = mcrfpy.Color(255, 255, 0)
    title.outline = 2
    title.outline_color = mcrfpy.Color(0, 0, 0)
    ui.append(title)
    
    # Subtitle
    global subtitle
    subtitle = mcrfpy.Caption("Initializing...", 400, 60)
    subtitle.fill_color = mcrfpy.Color(200, 200, 200)
    ui.append(subtitle)

def clear_demo():
    """Clear demo objects"""
    global demo_objects
    ui = mcrfpy.sceneUI("sizzle")
    
    # Remove items starting from the end
    # Skip first 2 (title and subtitle)
    while len(ui) > 2:
        ui.remove(len(ui) - 1)
    
    demo_objects = []

def demo1_frame_basics():
    """Demo 1: Basic frame animations"""
    clear_demo()
    print("demo1")
    subtitle.text = "Demo 1: Frame Animations (Position, Size, Color)"
    
    ui = mcrfpy.sceneUI("sizzle")
    
    # Create frame
    frame = mcrfpy.Frame(100, 150, 200, 100)
    frame.fill_color = mcrfpy.Color(50, 50, 150)
    frame.outline = 3
    frame.outline_color = mcrfpy.Color(255, 255, 255)
    ui.append(frame)
    
    # Animate properties
    mcrfpy.Animation("x", 700.0, 2.5, "easeInOutBack").start(frame)
    mcrfpy.Animation("y", 350.0, 2.5, "easeInOutElastic").start(frame)
    mcrfpy.Animation("w", 350.0, 3.0, "easeInOutCubic").start(frame)
    mcrfpy.Animation("h", 180.0, 3.0, "easeInOutCubic").start(frame)
    mcrfpy.Animation("fill_color", (255, 100, 50, 200), 4.0, "easeInOutSine").start(frame)
    mcrfpy.Animation("outline_color", (0, 255, 255, 255), 4.0, "easeOutBounce").start(frame)
    mcrfpy.Animation("outline", 8.0, 4.0, "easeInOutQuad").start(frame)

def demo2_opacity_zindex():
    """Demo 2: Opacity and z-index animations"""
    clear_demo()
    print("demo2")
    subtitle.text = "Demo 2: Opacity & Z-Index Animations"
    
    ui = mcrfpy.sceneUI("sizzle")
    
    # Create overlapping frames
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
    
    for i in range(4):
        frame = mcrfpy.Frame(200 + i*80, 200 + i*40, 200, 150)
        frame.fill_color = mcrfpy.Color(colors[i][0], colors[i][1], colors[i][2], 200)
        frame.outline = 2
        frame.z_index = i
        ui.append(frame)
        
        # Animate opacity
        mcrfpy.Animation("opacity", 0.3, 2.0, "easeInOutSine").start(frame)
        
    # Schedule opacity return
    def return_opacity(rt):
        for i in range(4):
            mcrfpy.Animation("opacity", 1.0, 2.0, "easeInOutSine").start(ui[i])
    mcrfpy.setTimer(f"opacity_{i}", return_opacity, 2100)

def demo3_captions():
    """Demo 3: Caption animations"""
    clear_demo()
    print("demo3")
    subtitle.text = "Demo 3: Caption Animations"
    
    ui = mcrfpy.sceneUI("sizzle")
    
    # Moving caption
    c1 = mcrfpy.Caption("Bouncing Text!", 100, 200)
    c1.fill_color = mcrfpy.Color(255, 255, 255)
    c1.outline = 1
    ui.append(c1)
    mcrfpy.Animation("x", 800.0, 3.0, "easeOutBounce").start(c1)
    
    # Color cycling caption
    c2 = mcrfpy.Caption("Color Cycle", 400, 300)
    c2.outline = 2
    ui.append(c2)
    
    # Animate through colors
    def cycle_colors():
        anim = mcrfpy.Animation("fill_color", (255, 0, 0, 255), 0.5, "linear")
        anim.start(c2)
        
        def to_green(rt):
            mcrfpy.Animation("fill_color", (0, 255, 0, 255), 0.5, "linear").start(c2)
        def to_blue(rt):
            mcrfpy.Animation("fill_color", (0, 0, 255, 255), 0.5, "linear").start(c2)
        def to_white(rt):
            mcrfpy.Animation("fill_color", (255, 255, 255, 255), 0.5, "linear").start(c2)
            
        mcrfpy.setTimer("c_green", to_green, 600)
        mcrfpy.setTimer("c_blue", to_blue, 1200)
        mcrfpy.setTimer("c_white", to_white, 1800)
    
    cycle_colors()
    
    # Typewriter effect
    c3 = mcrfpy.Caption("", 100, 400)
    c3.fill_color = mcrfpy.Color(0, 255, 255)
    ui.append(c3)
    mcrfpy.Animation("text", "This text appears one character at a time...", 3.0, "linear").start(c3)

def demo4_easing_showcase():
    """Demo 4: Showcase easing functions"""
    clear_demo()
    print("demo4")
    subtitle.text = "Demo 4: 30 Easing Functions"
    
    ui = mcrfpy.sceneUI("sizzle")
    
    # Show first 15 easings
    for i in range(15):
        row = i // 5
        col = i % 5
        x = 80 + col * 180
        y = 150 + row * 120
        
        # Create frame
        f = mcrfpy.Frame(x, y, 20, 20)
        f.fill_color = mcrfpy.Color(100, 150, 255)
        f.outline = 1
        ui.append(f)
        
        # Label
        label = mcrfpy.Caption(EASING_FUNCTIONS[i][:10], x, y - 20)
        label.fill_color = mcrfpy.Color(200, 200, 200)
        ui.append(label)
        
        # Animate with this easing
        mcrfpy.Animation("x", float(x + 140), 3.0, EASING_FUNCTIONS[i]).start(f)

def demo5_performance():
    """Demo 5: Many simultaneous animations"""
    clear_demo()
    print("demo5")
    subtitle.text = "Demo 5: 50+ Simultaneous Animations"
    
    ui = mcrfpy.sceneUI("sizzle")
    
    # Create many animated objects
    for i in range(50):
        print(f"{i}...",end='',flush=True)
        x = 100 + (i % 10) * 90
        y = 120 + (i // 10) * 80
        
        f = mcrfpy.Frame(x, y, 25, 25)
        r = (i * 37) % 256
        g = (i * 73) % 256
        b = (i * 113) % 256
        f.fill_color = (r, g, b, 200) #mcrfpy.Color(r, g, b, 200)
        f.outline = 1
        ui.append(f)
        
        # Random animations
        target_x = 150 + (i % 8) * 100
        target_y = 150 + (i // 8) * 85
        duration = 2.0 + (i % 30) * 0.1
        easing = EASING_FUNCTIONS[i % len(EASING_FUNCTIONS)]
        
        mcrfpy.Animation("x", float(target_x), duration, easing).start(f)
        mcrfpy.Animation("y", float(target_y), duration, easing).start(f)
        mcrfpy.Animation("opacity", 0.3 + (i % 7) * 0.1, 2.5, "easeInOutSine").start(f)

def demo6_delta_mode():
    """Demo 6: Delta mode animations"""
    clear_demo()
    print("demo6")
    subtitle.text = "Demo 6: Delta Mode (Relative Movement)"
    
    ui = mcrfpy.sceneUI("sizzle")
    
    # Create frames that move relative to position
    positions = [(100, 300), (300, 300), (500, 300), (700, 300)]
    colors = [(255, 100, 100), (100, 255, 100), (100, 100, 255), (255, 255, 100)]
    
    for i, ((x, y), color) in enumerate(zip(positions, colors)):
        f = mcrfpy.Frame(x, y, 60, 60)
        f.fill_color = mcrfpy.Color(color[0], color[1], color[2])
        f.outline = 2
        ui.append(f)
        
        # Delta animations - move by amount, not to position
        dx = (i + 1) * 30
        dy = math.sin(i * 0.5) * 50
        
        mcrfpy.Animation("x", float(dx), 2.0, "easeInOutBack", delta=True).start(f)
        mcrfpy.Animation("y", float(dy), 2.0, "easeInOutElastic", delta=True).start(f)
    
    # Caption explaining delta mode
    info = mcrfpy.Caption("Delta mode: animations move BY amount, not TO position", 200, 450)
    info.fill_color = mcrfpy.Color(255, 255, 255)
    ui.append(info)

def run_next_demo(runtime):
    """Run the next demo in sequence"""
    global current_demo
    
    demos = [
        demo1_frame_basics,
        demo2_opacity_zindex,
        demo3_captions,
        demo4_easing_showcase,
        demo5_performance,
        demo6_delta_mode
    ]
    
    if current_demo < len(demos):
        # Clean up timers from previous demo
        for timer in ["opacity_0", "opacity_1", "opacity_2", "opacity_3", 
                      "c_green", "c_blue", "c_white"]:
            try:
                mcrfpy.delTimer(timer)
            except:
                pass
        
        # Run next demo
        print(f"Run next: {current_demo}")
        demos[current_demo]()
        current_demo += 1
        
        # Schedule next demo
        if current_demo < len(demos):
            #mcrfpy.setTimer("next_demo", run_next_demo, int(DEMO_DURATION * 1000))
            pass
        else:
            current_demo = 0
            # All done
            #subtitle.text = "Animation Showcase Complete!"
            #complete = mcrfpy.Caption("All animations demonstrated successfully!", 350, 350)
            #complete.fill_color = mcrfpy.Color(0, 255, 0)
            #complete.outline = 2
            #ui = mcrfpy.sceneUI("sizzle")
            #ui.append(complete)
            #
            ## Exit after delay
            #def exit_program(rt):
            #    print("\nSizzle reel completed successfully!")
            #    sys.exit(0)
            #mcrfpy.setTimer("exit", exit_program, 3000)

# Handle ESC key
def handle_keypress(scene_name, keycode):
    if keycode == 256:  # ESC
        print("\nExiting...")
        sys.exit(0)

# Initialize
print("Starting McRogueFace Animation Sizzle Reel...")
print("This demonstrates all animation capabilities.")
print("Press ESC to exit at any time.")

create_scene()
mcrfpy.keypressScene(handle_keypress)

# Start the show
mcrfpy.setTimer("start", run_next_demo, int(DEMO_DURATION * 1000))
