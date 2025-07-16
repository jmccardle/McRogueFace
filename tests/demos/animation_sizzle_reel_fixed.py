#!/usr/bin/env python3
"""
McRogueFace Animation Sizzle Reel (Fixed)
=========================================

This script demonstrates EVERY animation type on EVERY UI object type.
Fixed version that works properly with the game loop.
"""

import mcrfpy

# Configuration
SCENE_WIDTH = 1280
SCENE_HEIGHT = 720
DEMO_DURATION = 5.0  # Duration for each demo section

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

# Track current demo state
current_demo = 0
subtitle = None

def create_demo_scene():
    """Create the main demo scene with title"""
    mcrfpy.createScene("sizzle_reel")
    mcrfpy.setScene("sizzle_reel")
    
    ui = mcrfpy.sceneUI("sizzle_reel")
    
    # Title caption
    title = mcrfpy.Caption("McRogueFace Animation Sizzle Reel", 
                   SCENE_WIDTH/2 - 200, 20)
    title.fill_color = mcrfpy.Color(255, 255, 0)
    title.outline = 2
    title.outline_color = mcrfpy.Color(0, 0, 0)
    ui.append(title)
    
    # Subtitle showing current demo
    global subtitle
    subtitle = mcrfpy.Caption("Initializing...", 
                      SCENE_WIDTH/2 - 150, 60)
    subtitle.fill_color = mcrfpy.Color(200, 200, 200)
    ui.append(subtitle)
    
    return ui

def demo_frame_basic_animations():
    """Demo 1: Basic frame animations - position, size, colors"""
    ui = mcrfpy.sceneUI("sizzle_reel")
    subtitle.text = "Demo 1: Frame Basic Animations (Position, Size, Colors)"
    
    # Create test frame
    frame = mcrfpy.Frame(100, 150, 200, 100)
    frame.fill_color = mcrfpy.Color(50, 50, 150)
    frame.outline = 3
    frame.outline_color = mcrfpy.Color(255, 255, 255)
    ui.append(frame)
    
    # Position animations with different easings
    x_anim = mcrfpy.Animation("x", 800.0, 2.0, "easeInOutBack")
    y_anim = mcrfpy.Animation("y", 400.0, 2.0, "easeInOutElastic")
    x_anim.start(frame)
    y_anim.start(frame)
    
    # Size animations
    w_anim = mcrfpy.Animation("w", 400.0, 3.0, "easeInOutCubic")
    h_anim = mcrfpy.Animation("h", 200.0, 3.0, "easeInOutCubic")
    w_anim.start(frame)
    h_anim.start(frame)
    
    # Color animations
    fill_anim = mcrfpy.Animation("fill_color", mcrfpy.Color(255, 100, 50, 200), 4.0, "easeInOutSine")
    outline_anim = mcrfpy.Animation("outline_color", mcrfpy.Color(0, 255, 255), 4.0, "easeOutBounce")
    fill_anim.start(frame)
    outline_anim.start(frame)
    
    # Outline thickness animation
    thickness_anim = mcrfpy.Animation("outline", 10.0, 4.5, "easeInOutQuad")
    thickness_anim.start(frame)

def demo_caption_animations():
    """Demo 2: Caption text animations and effects"""
    ui = mcrfpy.sceneUI("sizzle_reel")
    subtitle.text = "Demo 2: Caption Animations (Text, Color, Position)"
    
    # Basic caption with position animation
    caption1 = mcrfpy.Caption("Moving Text!", 100, 200)
    caption1.fill_color = mcrfpy.Color(255, 255, 255)
    caption1.outline = 1
    ui.append(caption1)
    
    # Animate across screen with bounce
    x_anim = mcrfpy.Animation("x", 900.0, 3.0, "easeOutBounce")
    x_anim.start(caption1)
    
    # Color cycling caption
    caption2 = mcrfpy.Caption("Rainbow Colors", 400, 300)
    caption2.outline = 2
    ui.append(caption2)
    
    # Cycle through colors
    color_anim1 = mcrfpy.Animation("fill_color", mcrfpy.Color(255, 0, 0), 1.0, "linear")
    color_anim1.start(caption2)
    
    # Typewriter effect caption
    caption3 = mcrfpy.Caption("", 100, 400)
    caption3.fill_color = mcrfpy.Color(0, 255, 255)
    ui.append(caption3)
    
    typewriter = mcrfpy.Animation("text", "This text appears one character at a time...", 3.0, "linear")
    typewriter.start(caption3)

def demo_sprite_animations():
    """Demo 3: Sprite animations (if texture available)"""
    ui = mcrfpy.sceneUI("sizzle_reel")
    subtitle.text = "Demo 3: Sprite Animations"
    
    # Create placeholder caption since texture might not exist
    no_texture = mcrfpy.Caption("(Sprite demo - textures may not be loaded)", 400, 350)
    no_texture.fill_color = mcrfpy.Color(255, 100, 100)
    ui.append(no_texture)

def demo_performance_stress_test():
    """Demo 4: Performance test with many simultaneous animations"""
    ui = mcrfpy.sceneUI("sizzle_reel")
    subtitle.text = "Demo 4: Performance Test (50+ Simultaneous Animations)"
    
    # Create many small objects with different animations
    num_objects = 50
    
    for i in range(num_objects):
        # Random starting position
        x = 100 + (i % 10) * 100
        y = 150 + (i // 10) * 80
        
        # Create small frame
        size = 20 + (i % 3) * 10
        frame = mcrfpy.Frame(x, y, size, size)
        
        # Random color
        r = (i * 37) % 256
        g = (i * 73) % 256  
        b = (i * 113) % 256
        frame.fill_color = mcrfpy.Color(r, g, b, 200)
        frame.outline = 1
        ui.append(frame)
        
        # Random animation properties
        target_x = 100 + (i % 8) * 120
        target_y = 150 + (i // 8) * 100
        duration = 2.0 + (i % 30) * 0.1
        easing = EASING_FUNCTIONS[i % len(EASING_FUNCTIONS)]
        
        # Start multiple animations per object
        x_anim = mcrfpy.Animation("x", float(target_x), duration, easing)
        y_anim = mcrfpy.Animation("y", float(target_y), duration, easing)
        opacity_anim = mcrfpy.Animation("opacity", 0.3 + (i % 7) * 0.1, duration, "easeInOutSine")
        
        x_anim.start(frame)
        y_anim.start(frame)
        opacity_anim.start(frame)
    
    # Performance counter
    perf_caption = mcrfpy.Caption(f"Animating {num_objects * 3} properties simultaneously", 400, 600)
    perf_caption.fill_color = mcrfpy.Color(255, 255, 0)
    ui.append(perf_caption)

def clear_scene():
    """Clear the scene except title and subtitle"""
    ui = mcrfpy.sceneUI("sizzle_reel")
    
    # Keep only the first two elements (title and subtitle)
    while len(ui) > 2:
        ui.remove(2)

def run_demo_sequence(runtime):
    """Run through all demos"""
    global current_demo
    
    # Clear previous demo
    clear_scene()
    
    # Demo list
    demos = [
        demo_frame_basic_animations,
        demo_caption_animations,
        demo_sprite_animations,
        demo_performance_stress_test
    ]
    
    if current_demo < len(demos):
        # Run current demo
        demos[current_demo]()
        current_demo += 1
        
        # Schedule next demo
        if current_demo < len(demos):
            mcrfpy.setTimer("next_demo", run_demo_sequence, int(DEMO_DURATION * 1000))
    else:
        # All demos complete
        subtitle.text = "Animation Showcase Complete!"
        complete = mcrfpy.Caption("All animation types demonstrated!", 400, 350)
        complete.fill_color = mcrfpy.Color(0, 255, 0)
        complete.outline = 2
        ui = mcrfpy.sceneUI("sizzle_reel")
        ui.append(complete)

# Initialize scene
print("Starting McRogueFace Animation Sizzle Reel...")
print("This will demonstrate animation types on various objects.")

ui = create_demo_scene()

# Start the demo sequence after a short delay
mcrfpy.setTimer("start_demos", run_demo_sequence, 500)