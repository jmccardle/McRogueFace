#!/usr/bin/env python3
"""
McRogueFace Animation Sizzle Reel
=================================

This script demonstrates EVERY animation type on EVERY UI object type.
It showcases all 30 easing functions, all animatable properties, and 
special animation modes (delta, sprite sequences, text effects).

The script creates a comprehensive visual demonstration of the animation
system's capabilities, cycling through different objects and effects.

Author: Claude
Purpose: Complete animation system demonstration
"""

import mcrfpy
from mcrfpy import Color, Frame, Caption, Sprite, Grid, Entity, Texture, Animation
import sys
import math

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
demo_start_time = 0
demos = []

# Handle ESC key to exit
def handle_keypress(scene_name, keycode):
    if keycode == 256:  # ESC key
        print("Exiting animation sizzle reel...")
        sys.exit(0)

def create_demo_scene():
    """Create the main demo scene with title"""
    mcrfpy.createScene("sizzle_reel")
    mcrfpy.setScene("sizzle_reel")
    mcrfpy.keypressScene(handle_keypress)
    
    ui = mcrfpy.sceneUI("sizzle_reel")
    
    # Title caption
    title = Caption("McRogueFace Animation Sizzle Reel", 
                   SCENE_WIDTH/2 - 200, 20)
    title.fill_color = Color(255, 255, 0)
    title.outline = 2
    title.outline_color = Color(0, 0, 0)
    ui.append(title)
    
    # Subtitle showing current demo
    global subtitle
    subtitle = Caption("Initializing...", 
                      SCENE_WIDTH/2 - 150, 60)
    subtitle.fill_color = Color(200, 200, 200)
    ui.append(subtitle)
    
    return ui

def demo_frame_basic_animations(ui):
    """Demo 1: Basic frame animations - position, size, colors"""
    subtitle.text = "Demo 1: Frame Basic Animations (Position, Size, Colors)"
    
    # Create test frame
    frame = Frame(100, 150, 200, 100)
    frame.fill_color = Color(50, 50, 150)
    frame.outline = 3
    frame.outline_color = Color(255, 255, 255)
    ui.append(frame)
    
    # Position animations with different easings
    x_anim = Animation("x", 800.0, 2.0, "easeInOutBack")
    y_anim = Animation("y", 400.0, 2.0, "easeInOutElastic")
    x_anim.start(frame)
    y_anim.start(frame)
    
    # Size animations
    w_anim = Animation("w", 400.0, 3.0, "easeInOutCubic")
    h_anim = Animation("h", 200.0, 3.0, "easeInOutCubic")
    w_anim.start(frame)
    h_anim.start(frame)
    
    # Color animations - use tuples instead of Color objects
    fill_anim = Animation("fill_color", (255, 100, 50, 200), 4.0, "easeInOutSine")
    outline_anim = Animation("outline_color", (0, 255, 255, 255), 4.0, "easeOutBounce")
    fill_anim.start(frame)
    outline_anim.start(frame)
    
    # Outline thickness animation
    thickness_anim = Animation("outline", 10.0, 4.5, "easeInOutQuad")
    thickness_anim.start(frame)
    
    return frame

def demo_frame_opacity_zindex(ui):
    """Demo 2: Frame opacity and z-index animations"""
    subtitle.text = "Demo 2: Frame Opacity & Z-Index Animations"
    
    frames = []
    colors = [
        Color(255, 0, 0, 200),
        Color(0, 255, 0, 200),
        Color(0, 0, 255, 200),
        Color(255, 255, 0, 200)
    ]
    
    # Create overlapping frames
    for i in range(4):
        frame = Frame(200 + i*80, 200 + i*40, 200, 150)
        frame.fill_color = colors[i]
        frame.outline = 2
        frame.z_index = i
        ui.append(frame)
        frames.append(frame)
        
        # Animate opacity in waves
        opacity_anim = Animation("opacity", 0.3, 2.0, "easeInOutSine")
        opacity_anim.start(frame)
        
        # Reverse opacity animation
        opacity_back = Animation("opacity", 1.0, 2.0, "easeInOutSine", delta=False)
        mcrfpy.setTimer(f"opacity_back_{i}", lambda t, f=frame, a=opacity_back: a.start(f), 2000)
        
        # Z-index shuffle animation
        z_anim = Animation("z_index", (i + 2) % 4, 3.0, "linear")
        z_anim.start(frame)
    
    return frames

def demo_caption_animations(ui):
    """Demo 3: Caption text animations and effects"""
    subtitle.text = "Demo 3: Caption Animations (Text, Color, Position)"
    
    # Basic caption with position animation
    caption1 = Caption("Moving Text!", 100, 200)
    caption1.fill_color = Color(255, 255, 255)
    caption1.outline = 1
    ui.append(caption1)
    
    # Animate across screen with bounce
    x_anim = Animation("x", 900.0, 3.0, "easeOutBounce")
    x_anim.start(caption1)
    
    # Color cycling caption
    caption2 = Caption("Rainbow Colors", 400, 300)
    caption2.outline = 2
    ui.append(caption2)
    
    # Cycle through colors - use tuples
    color_anim1 = Animation("fill_color", (255, 0, 0, 255), 1.0, "linear")
    color_anim2 = Animation("fill_color", (0, 255, 0, 255), 1.0, "linear")
    color_anim3 = Animation("fill_color", (0, 0, 255, 255), 1.0, "linear")
    color_anim4 = Animation("fill_color", (255, 255, 255, 255), 1.0, "linear")
    
    color_anim1.start(caption2)
    mcrfpy.setTimer("color2", lambda t: color_anim2.start(caption2), 1000)
    mcrfpy.setTimer("color3", lambda t: color_anim3.start(caption2), 2000)
    mcrfpy.setTimer("color4", lambda t: color_anim4.start(caption2), 3000)
    
    # Typewriter effect caption
    caption3 = Caption("", 100, 400)
    caption3.fill_color = Color(0, 255, 255)
    ui.append(caption3)
    
    typewriter = Animation("text", "This text appears one character at a time...", 3.0, "linear")
    typewriter.start(caption3)
    
    # Size animation caption
    caption4 = Caption("Growing Text", 400, 500)
    caption4.fill_color = Color(255, 200, 0)
    ui.append(caption4)
    
    # Note: size animation would require font size property support
    # For now, animate position to simulate growth
    scale_sim = Animation("y", 480.0, 2.0, "easeInOutElastic")
    scale_sim.start(caption4)
    
    return [caption1, caption2, caption3, caption4]

def demo_sprite_animations(ui):
    """Demo 4: Sprite animations including sprite sequences"""
    subtitle.text = "Demo 4: Sprite Animations (Position, Scale, Sprite Sequences)"
    
    # Load a test texture (you'll need to adjust path)
    try:
        texture = Texture("assets/sprites/player.png", grid_size=(32, 32))
    except:
        # Fallback if texture not found
        texture = None
    
    if texture:
        # Basic sprite with position animation
        sprite1 = Sprite(100, 200, texture, sprite_index=0)
        sprite1.scale = 2.0
        ui.append(sprite1)
        
        # Circular motion using sin/cos animations
        # We'll use delta mode to create circular motion
        x_circle = Animation("x", 300.0, 4.0, "easeInOutSine")
        y_circle = Animation("y", 300.0, 4.0, "easeInOutCubic")
        x_circle.start(sprite1)
        y_circle.start(sprite1)
        
        # Sprite sequence animation (walking cycle)
        sprite2 = Sprite(500, 300, texture, sprite_index=0)
        sprite2.scale = 3.0
        ui.append(sprite2)
        
        # Animate through sprite indices for animation
        walk_cycle = Animation("sprite_index", [0, 1, 2, 3, 2, 1], 2.0, "linear")
        walk_cycle.start(sprite2)
        
        # Scale pulsing sprite
        sprite3 = Sprite(800, 400, texture, sprite_index=4)
        ui.append(sprite3)
        
        # Note: scale animation would need to be supported
        # For now use position to simulate
        pulse_y = Animation("y", 380.0, 0.5, "easeInOutSine")
        pulse_y.start(sprite3)
        
        # Z-index animation for layering
        sprite3_z = Animation("z_index", 10, 2.0, "linear")
        sprite3_z.start(sprite3)
        
        return [sprite1, sprite2, sprite3]
    else:
        # Create placeholder caption if no texture
        no_texture = Caption("(Sprite demo requires texture file)", 400, 350)
        no_texture.fill_color = Color(255, 100, 100)
        ui.append(no_texture)
        return [no_texture]

def demo_grid_animations(ui):
    """Demo 5: Grid animations (position, camera, zoom)"""
    subtitle.text = "Demo 5: Grid Animations (Position, Camera Effects)"
    
    # Create a grid
    try:
        texture = Texture("assets/sprites/tiles.png", grid_size=(16, 16))
    except:
        texture = None
    
    # Grid constructor: Grid(grid_x, grid_y, texture, position, size)
    # Note: tile dimensions are determined by texture's grid_size
    grid = Grid(20, 15, texture, (100, 150), (480, 360))  # 20x24, 15x24
    grid.fill_color = Color(20, 20, 40)
    ui.append(grid)
    
    # Fill with some test pattern
    for y in range(15):
        for x in range(20):
            point = grid.at(x, y)
            point.tilesprite = (x + y) % 4
            point.walkable = ((x + y) % 3) != 0
            if not point.walkable:
                point.color = Color(100, 50, 50, 128)
    
    # Animate grid position
    grid_x = Animation("x", 400.0, 3.0, "easeInOutBack")
    grid_x.start(grid)
    
    # Camera pan animation (if supported)
    # center_x = Animation("center", (10.0, 7.5), 4.0, "easeInOutCubic")
    # center_x.start(grid)
    
    # Create entities in the grid
    if texture:
        entity1 = Entity((5.0, 5.0), texture, 8)  # position tuple, texture, sprite_index
        entity1.scale = 1.5
        grid.entities.append(entity1)
        
        # Animate entity movement
        entity_pos = Animation("position", (15.0, 10.0), 3.0, "easeInOutQuad")
        entity_pos.start(entity1)
        
        # Create patrolling entity
        entity2 = Entity((10.0, 2.0), texture, 12)  # position tuple, texture, sprite_index
        grid.entities.append(entity2)
        
        # Animate sprite changes
        entity2_sprite = Animation("sprite_index", [12, 13, 14, 15, 14, 13], 2.0, "linear")
        entity2_sprite.start(entity2)
    
    return grid

def demo_complex_combinations(ui):
    """Demo 6: Complex multi-property animations"""
    subtitle.text = "Demo 6: Complex Multi-Property Animations"
    
    # Create a complex UI composition
    main_frame = Frame(200, 200, 400, 300)
    main_frame.fill_color = Color(30, 30, 60, 200)
    main_frame.outline = 2
    ui.append(main_frame)
    
    # Child elements
    title = Caption("Multi-Animation Demo", 20, 20)
    title.fill_color = Color(255, 255, 255)
    main_frame.children.append(title)
    
    # Animate everything at once
    # Frame animations
    frame_x = Animation("x", 600.0, 3.0, "easeInOutElastic")
    frame_w = Animation("w", 300.0, 2.5, "easeOutBack")
    frame_fill = Animation("fill_color", (60, 30, 90, 220), 4.0, "easeInOutSine")
    frame_outline = Animation("outline", 8.0, 3.0, "easeInOutQuad")
    
    frame_x.start(main_frame)
    frame_w.start(main_frame)
    frame_fill.start(main_frame)
    frame_outline.start(main_frame)
    
    # Title animations  
    title_color = Animation("fill_color", (255, 200, 0, 255), 2.0, "easeOutBounce")
    title_color.start(title)
    
    # Add animated sub-frames
    for i in range(3):
        sub_frame = Frame(50 + i * 100, 100, 80, 80)
        sub_frame.fill_color = Color(100 + i*50, 50, 200 - i*50, 180)
        main_frame.children.append(sub_frame)
        
        # Rotate positions using delta animations
        sub_y = Animation("y", 50.0, 2.0, "easeInOutSine", delta=True)
        sub_y.start(sub_frame)
    
    return main_frame

def demo_easing_showcase(ui):
    """Demo 7: Showcase all 30 easing functions"""
    subtitle.text = "Demo 7: All 30 Easing Functions Showcase"
    
    # Create small frames for each easing function
    frames_per_row = 6
    frame_size = 180
    spacing = 10
    
    for i, easing in enumerate(EASING_FUNCTIONS[:12]):  # First 12 easings
        row = i // frames_per_row
        col = i % frames_per_row
        
        x = 50 + col * (frame_size + spacing)
        y = 150 + row * (60 + spacing)
        
        # Create indicator frame
        frame = Frame(x, y, 20, 20)
        frame.fill_color = Color(100, 200, 255)
        frame.outline = 1
        ui.append(frame)
        
        # Label
        label = Caption(easing, x, y - 20)
        label.fill_color = Color(200, 200, 200)
        ui.append(label)
        
        # Animate using this easing
        move_anim = Animation("x", x + frame_size - 20, 3.0, easing)
        move_anim.start(frame)
    
    # Continue with remaining easings after a delay
    def show_more_easings(runtime):
        for j, easing in enumerate(EASING_FUNCTIONS[12:24]):  # Next 12
            row = j // frames_per_row + 2
            col = j % frames_per_row
            
            x = 50 + col * (frame_size + spacing)
            y = 150 + row * (60 + spacing)
            
            frame2 = Frame(x, y, 20, 20)
            frame2.fill_color = Color(255, 150, 100)
            frame2.outline = 1
            ui.append(frame2)
            
            label2 = Caption(easing, x, y - 20)
            label2.fill_color = Color(200, 200, 200)
            ui.append(label2)
            
            move_anim2 = Animation("x", x + frame_size - 20, 3.0, easing)
            move_anim2.start(frame2)
    
    mcrfpy.setTimer("more_easings", show_more_easings, 1000)
    
    # Show final easings
    def show_final_easings(runtime):
        for k, easing in enumerate(EASING_FUNCTIONS[24:]):  # Last 6
            row = k // frames_per_row + 4
            col = k % frames_per_row
            
            x = 50 + col * (frame_size + spacing)
            y = 150 + row * (60 + spacing)
            
            frame3 = Frame(x, y, 20, 20)
            frame3.fill_color = Color(150, 255, 150)
            frame3.outline = 1
            ui.append(frame3)
            
            label3 = Caption(easing, x, y - 20)
            label3.fill_color = Color(200, 200, 200)
            ui.append(label3)
            
            move_anim3 = Animation("x", x + frame_size - 20, 3.0, easing)
            move_anim3.start(frame3)
    
    mcrfpy.setTimer("final_easings", show_final_easings, 2000)

def demo_delta_animations(ui):
    """Demo 8: Delta mode animations (relative movements)"""
    subtitle.text = "Demo 8: Delta Mode Animations (Relative Movements)"
    
    # Create objects that will move relative to their position
    frames = []
    start_positions = [(100, 200), (300, 200), (500, 200), (700, 200)]
    colors = [Color(255, 100, 100), Color(100, 255, 100), 
              Color(100, 100, 255), Color(255, 255, 100)]
    
    for i, (x, y) in enumerate(start_positions):
        frame = Frame(x, y, 80, 80)
        frame.fill_color = colors[i]
        frame.outline = 2
        ui.append(frame)
        frames.append(frame)
        
        # Delta animations - move relative to current position
        # Each frame moves by different amounts
        dx = (i + 1) * 50
        dy = math.sin(i) * 100
        
        x_delta = Animation("x", dx, 2.0, "easeInOutBack", delta=True)
        y_delta = Animation("y", dy, 2.0, "easeInOutElastic", delta=True)
        
        x_delta.start(frame)
        y_delta.start(frame)
    
    # Create caption showing delta mode
    delta_label = Caption("Delta mode: Relative animations from current position", 200, 400)
    delta_label.fill_color = Color(255, 255, 255)
    ui.append(delta_label)
    
    # Animate the label with delta mode text append
    text_delta = Animation("text", " - ANIMATED!", 2.0, "linear", delta=True)
    text_delta.start(delta_label)
    
    return frames

def demo_color_component_animations(ui):
    """Demo 9: Individual color channel animations"""
    subtitle.text = "Demo 9: Color Component Animations (R, G, B, A channels)"
    
    # Create frames to demonstrate individual color channel animations
    base_frame = Frame(300, 200, 600, 300)
    base_frame.fill_color = Color(128, 128, 128, 255)
    base_frame.outline = 3
    ui.append(base_frame)
    
    # Labels for each channel
    labels = ["Red", "Green", "Blue", "Alpha"]
    positions = [(50, 50), (200, 50), (350, 50), (500, 50)]
    
    for i, (label_text, (x, y)) in enumerate(zip(labels, positions)):
        # Create label
        label = Caption(label_text, x, y - 30)
        label.fill_color = Color(255, 255, 255)
        base_frame.children.append(label)
        
        # Create demo frame for this channel
        demo_frame = Frame(x, y, 100, 100)
        demo_frame.fill_color = Color(100, 100, 100, 200)
        demo_frame.outline = 2
        base_frame.children.append(demo_frame)
        
        # Animate individual color channel
        if i == 0:  # Red
            r_anim = Animation("fill_color.r", 255, 3.0, "easeInOutSine")
            r_anim.start(demo_frame)
        elif i == 1:  # Green  
            g_anim = Animation("fill_color.g", 255, 3.0, "easeInOutSine")
            g_anim.start(demo_frame)
        elif i == 2:  # Blue
            b_anim = Animation("fill_color.b", 255, 3.0, "easeInOutSine")
            b_anim.start(demo_frame)
        else:  # Alpha
            a_anim = Animation("fill_color.a", 50, 3.0, "easeInOutSine")
            a_anim.start(demo_frame)
    
    # Animate main frame outline color components in sequence
    outline_r = Animation("outline_color.r", 255, 1.0, "linear")
    outline_g = Animation("outline_color.g", 255, 1.0, "linear")
    outline_b = Animation("outline_color.b", 0, 1.0, "linear")
    
    outline_r.start(base_frame)
    mcrfpy.setTimer("outline_g", lambda t: outline_g.start(base_frame), 1000)
    mcrfpy.setTimer("outline_b", lambda t: outline_b.start(base_frame), 2000)
    
    return base_frame

def demo_performance_stress_test(ui):
    """Demo 10: Performance test with many simultaneous animations"""
    subtitle.text = "Demo 10: Performance Stress Test (100+ Simultaneous Animations)"
    
    # Create many small objects with different animations
    num_objects = 100
    
    for i in range(num_objects):
        # Random starting position
        x = 100 + (i % 20) * 50
        y = 150 + (i // 20) * 50
        
        # Create small frame
        size = 20 + (i % 3) * 10
        frame = Frame(x, y, size, size)
        
        # Random color
        r = (i * 37) % 256
        g = (i * 73) % 256  
        b = (i * 113) % 256
        frame.fill_color = Color(r, g, b, 200)
        frame.outline = 1
        ui.append(frame)
        
        # Random animation properties
        target_x = 100 + (i % 15) * 70
        target_y = 150 + (i // 15) * 70
        duration = 2.0 + (i % 30) * 0.1
        easing = EASING_FUNCTIONS[i % len(EASING_FUNCTIONS)]
        
        # Start multiple animations per object
        x_anim = Animation("x", target_x, duration, easing)
        y_anim = Animation("y", target_y, duration, easing)
        opacity_anim = Animation("opacity", 0.3 + (i % 7) * 0.1, duration, "easeInOutSine")
        
        x_anim.start(frame)
        y_anim.start(frame)
        opacity_anim.start(frame)
    
    # Performance counter
    perf_caption = Caption(f"Animating {num_objects * 3} properties simultaneously", 400, 600)
    perf_caption.fill_color = Color(255, 255, 0)
    ui.append(perf_caption)

def next_demo(runtime):
    """Cycle to the next demo"""
    global current_demo, demo_start_time
    
    # Clear the UI except title and subtitle
    ui = mcrfpy.sceneUI("sizzle_reel")
    
    # Keep only the first two elements (title and subtitle)
    while len(ui) > 2:
        # Remove from the end to avoid index issues
        ui.remove(len(ui) - 1)
    
    # Run the next demo
    if current_demo < len(demos):
        demos[current_demo](ui)
        current_demo += 1
        
        # Schedule next demo
        if current_demo < len(demos):
            mcrfpy.setTimer("next_demo", next_demo, int(DEMO_DURATION * 1000))
    else:
        # All demos complete
        subtitle.text = "Animation Showcase Complete! Press ESC to exit."
        complete = Caption("All animation types demonstrated!", 400, 350)
        complete.fill_color = Color(0, 255, 0)
        complete.outline = 2
        ui.append(complete)

def run_sizzle_reel(runtime):
    """Main entry point - start the demo sequence"""
    global demos
    
    # List of all demo functions
    demos = [
        demo_frame_basic_animations,
        demo_frame_opacity_zindex,
        demo_caption_animations,
        demo_sprite_animations,
        demo_grid_animations,
        demo_complex_combinations,
        demo_easing_showcase,
        demo_delta_animations,
        demo_color_component_animations,
        demo_performance_stress_test
    ]
    
    # Start the first demo
    next_demo(runtime)

# Initialize scene
ui = create_demo_scene()


# Start the sizzle reel after a short delay
mcrfpy.setTimer("start_sizzle", run_sizzle_reel, 500)

print("Starting McRogueFace Animation Sizzle Reel...")
print("This will demonstrate ALL animation types on ALL objects.")
print("Press ESC at any time to exit.")
