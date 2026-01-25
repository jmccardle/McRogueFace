#!/usr/bin/env python3
"""
Shader POC Test - Issue #106

Tests 6 render variants:
1. Basic frame (no special flags)
2. clip_children=True
3. cache_subtree=True
4. Basic + shader_enabled
5. clip_children + shader_enabled
6. cache_subtree + shader_enabled

The shader applies a wave distortion + glow effect.
Shader-enabled frames should show visible animation.
"""
import mcrfpy
import sys

# Create test scene
scene = mcrfpy.Scene("shader_test")
mcrfpy.current_scene = scene
ui = scene.children

# Create a background
bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=(30, 30, 40, 255))
ui.append(bg)

# Helper to create a test frame with children
def create_test_frame(x, y, label, clip=False, cache=False, shader=False):
    """Create a frame with some child content for testing."""
    frame = mcrfpy.Frame(
        pos=(x, y),
        size=(200, 200),
        fill_color=(60, 80, 120, 255),
        outline_color=(200, 200, 255, 255),
        outline=2.0,
        clip_children=clip,
        cache_subtree=cache
    )

    # Add some child content
    title = mcrfpy.Caption(text=label, pos=(5, 5), font_size=12)
    title.fill_color = (255, 255, 200, 255)
    frame.children.append(title)

    # Add a sprite or shape inside
    inner = mcrfpy.Frame(
        pos=(20, 35),
        size=(110, 60),
        fill_color=(100, 150, 200, 255),
        outline_color=(255, 255, 255, 200),
        outline=1.0
    )
    frame.children.append(inner)

    # Add text inside inner frame
    inner_text = mcrfpy.Caption(text="Content", pos=(25, 20), font_size=14)
    inner_text.fill_color = (255, 255, 255, 255)
    inner.children.append(inner_text)

    # Enable shader if requested
    if shader:
        frame.shader_enabled = True

    return frame

# Row 1: Without shader
y1 = 50
title1 = mcrfpy.Caption(text="Without Shader:", pos=(20, y1 - 30), font_size=16)
title1.fill_color = (255, 255, 100, 255)
ui.append(title1)

# 1. Basic (no flags)
basic = create_test_frame(50, y1, "Basic", clip=False, cache=False, shader=False)
ui.append(basic)

# 2. clip_children
clipped = create_test_frame(300, y1, "clip_children", clip=True, cache=False, shader=False)
ui.append(clipped)

# 3. cache_subtree
cached = create_test_frame(550, y1, "cache_subtree", clip=False, cache=True, shader=False)
ui.append(cached)

# Row 2: With shader
y2 = 300
title2 = mcrfpy.Caption(text="With Shader (should animate):", pos=(20, y2 - 30), font_size=16)
title2.fill_color = (255, 255, 100, 255)
ui.append(title2)

# 4. Basic + shader
basic_shader = create_test_frame(50, y2, "Basic+Shader", clip=False, cache=False, shader=True)
ui.append(basic_shader)

# 5. clip_children + shader
clipped_shader = create_test_frame(300, y2, "clip+Shader", clip=True, cache=False, shader=True)
ui.append(clipped_shader)

# 6. cache_subtree + shader
cached_shader = create_test_frame(550, y2, "cache+Shader", clip=False, cache=True, shader=True)
ui.append(cached_shader)

# Add instructions
#instructions = mcrfpy.Caption(
#    text="Press Q or Escape to quit. Bottom row should show animated wave/glow effects.",
#    pos=(20, 400),
#    font_size=14
#)
#instructions.fill_color = (180, 180, 180, 255)
#ui.append(instructions)

# Debug info
#debug_info = mcrfpy.Caption(
#    text=f"Frames created: 6 variants (3 without shader, 3 with shader)",
#    pos=(20, 430),
#    font_size=12
#)
#debug_info.fill_color = (120, 120, 120, 255)
#ui.append(debug_info)

# Keyboard handler
def on_key(key, state):
    if state == "start" and key in ("Q", "Escape"):
        print("PASS: Shader POC test complete - exiting")
        sys.exit(0)

scene.on_key = on_key

print("Shader POC Test running...")
print("- Top row: No shader (static)")
print("- Bottom row: Shader enabled (should animate with wave/glow)")
print("Press Q or Escape to quit")
