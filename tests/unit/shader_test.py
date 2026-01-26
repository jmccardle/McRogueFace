#!/usr/bin/env python3
"""Unit tests for the Shader system (Issue #106)

Tests cover:
- Shader creation and compilation
- Static uniforms (float, vec2, vec3, vec4)
- PropertyBinding for dynamic uniform values
- CallableBinding for computed uniform values
- Shader assignment to various drawable types
- Dynamic flag propagation
"""

import mcrfpy
import sys


def test_shader_creation():
    """Test basic shader creation"""
    print("Testing shader creation...")

    # Valid shader
    shader = mcrfpy.Shader('''
        uniform sampler2D texture;
        void main() {
            gl_FragColor = texture2D(texture, gl_TexCoord[0].xy);
        }
    ''')
    assert shader is not None, "Shader should be created"
    assert shader.is_valid, "Shader should be valid"
    assert shader.dynamic == False, "Shader should not be dynamic by default"

    # Dynamic shader
    dynamic_shader = mcrfpy.Shader('''
        uniform sampler2D texture;
        uniform float time;
        void main() {
            gl_FragColor = texture2D(texture, gl_TexCoord[0].xy);
        }
    ''', dynamic=True)
    assert dynamic_shader.dynamic == True, "Shader should be dynamic when specified"

    print("  PASS: Basic shader creation works")


def test_shader_source():
    """Test that shader source is stored correctly"""
    print("Testing shader source storage...")

    source = '''uniform sampler2D texture;
void main() {
    gl_FragColor = texture2D(texture, gl_TexCoord[0].xy);
}'''
    shader = mcrfpy.Shader(source)
    assert source in shader.source, "Shader source should be stored"

    print("  PASS: Shader source is stored")


def test_static_uniforms():
    """Test static uniform values"""
    print("Testing static uniforms...")

    frame = mcrfpy.Frame(pos=(0, 0), size=(100, 100))

    # Test float uniform
    frame.uniforms['intensity'] = 0.5
    assert abs(frame.uniforms['intensity'] - 0.5) < 0.001, "Float uniform should match"

    # Test vec2 uniform
    frame.uniforms['offset'] = (10.0, 20.0)
    val = frame.uniforms['offset']
    assert len(val) == 2, "Vec2 should have 2 components"
    assert abs(val[0] - 10.0) < 0.001, "Vec2.x should match"
    assert abs(val[1] - 20.0) < 0.001, "Vec2.y should match"

    # Test vec3 uniform
    frame.uniforms['color_rgb'] = (1.0, 0.5, 0.0)
    val = frame.uniforms['color_rgb']
    assert len(val) == 3, "Vec3 should have 3 components"

    # Test vec4 uniform
    frame.uniforms['color'] = (1.0, 0.5, 0.0, 1.0)
    val = frame.uniforms['color']
    assert len(val) == 4, "Vec4 should have 4 components"

    print("  PASS: Static uniforms work")


def test_uniform_keys():
    """Test uniform collection keys/values/items"""
    print("Testing uniform collection methods...")

    frame = mcrfpy.Frame(pos=(0, 0), size=(100, 100))
    frame.uniforms['a'] = 1.0
    frame.uniforms['b'] = 2.0
    frame.uniforms['c'] = 3.0

    keys = frame.uniforms.keys()
    assert 'a' in keys, "Key 'a' should be present"
    assert 'b' in keys, "Key 'b' should be present"
    assert 'c' in keys, "Key 'c' should be present"
    assert len(keys) == 3, "Should have 3 keys"

    # Test 'in' operator
    assert 'a' in frame.uniforms, "'in' operator should work"
    assert 'nonexistent' not in frame.uniforms, "'not in' should work"

    # Test deletion
    del frame.uniforms['b']
    assert 'b' not in frame.uniforms, "Deleted key should be gone"
    assert len(frame.uniforms.keys()) == 2, "Should have 2 keys after deletion"

    print("  PASS: Uniform collection methods work")


def test_property_binding():
    """Test PropertyBinding for dynamic uniform values"""
    print("Testing PropertyBinding...")

    # Create source and target frames
    source_frame = mcrfpy.Frame(pos=(100, 200), size=(50, 50))
    target_frame = mcrfpy.Frame(pos=(0, 0), size=(100, 100))

    # Create binding to source frame's x position
    binding = mcrfpy.PropertyBinding(source_frame, 'x')
    assert binding is not None, "PropertyBinding should be created"
    assert binding.property == 'x', "Property name should be stored"
    assert abs(binding.value - 100.0) < 0.001, "Initial value should be 100"
    assert binding.is_valid == True, "Binding should be valid"

    # Assign binding to uniform
    target_frame.uniforms['source_x'] = binding

    # Check that value tracks changes
    source_frame.x = 300
    assert abs(binding.value - 300.0) < 0.001, "Binding should track changes"

    print("  PASS: PropertyBinding works")


def test_callable_binding():
    """Test CallableBinding for computed uniform values"""
    print("Testing CallableBinding...")

    counter = [0]  # Use list for closure

    def compute_value():
        counter[0] += 1
        return counter[0] * 0.1

    binding = mcrfpy.CallableBinding(compute_value)
    assert binding is not None, "CallableBinding should be created"
    assert binding.is_valid == True, "Binding should be valid"

    # Each access should call the function
    v1 = binding.value
    v2 = binding.value
    v3 = binding.value

    assert abs(v1 - 0.1) < 0.001, "First call should return 0.1"
    assert abs(v2 - 0.2) < 0.001, "Second call should return 0.2"
    assert abs(v3 - 0.3) < 0.001, "Third call should return 0.3"

    # Assign to uniform
    frame = mcrfpy.Frame(pos=(0, 0), size=(100, 100))
    frame.uniforms['computed'] = binding

    print("  PASS: CallableBinding works")


def test_shader_on_frame():
    """Test shader assignment to Frame"""
    print("Testing shader on Frame...")

    shader = mcrfpy.Shader('''
        uniform sampler2D texture;
        uniform float intensity;
        void main() {
            vec4 color = texture2D(texture, gl_TexCoord[0].xy);
            color.rgb *= intensity;
            gl_FragColor = color;
        }
    ''')

    frame = mcrfpy.Frame(pos=(0, 0), size=(100, 100))
    assert frame.shader is None, "Shader should be None initially"

    frame.shader = shader
    assert frame.shader is not None, "Shader should be assigned"

    frame.uniforms['intensity'] = 0.8
    assert abs(frame.uniforms['intensity'] - 0.8) < 0.001, "Uniform should be set"

    # Test shader removal
    frame.shader = None
    assert frame.shader is None, "Shader should be removable"

    print("  PASS: Shader on Frame works")


def test_shader_on_sprite():
    """Test shader assignment to Sprite"""
    print("Testing shader on Sprite...")

    shader = mcrfpy.Shader('''
        uniform sampler2D texture;
        void main() {
            gl_FragColor = texture2D(texture, gl_TexCoord[0].xy);
        }
    ''')

    sprite = mcrfpy.Sprite(pos=(0, 0))
    assert sprite.shader is None, "Shader should be None initially"

    sprite.shader = shader
    assert sprite.shader is not None, "Shader should be assigned"

    sprite.uniforms['test'] = 1.0
    assert abs(sprite.uniforms['test'] - 1.0) < 0.001, "Uniform should be set"

    print("  PASS: Shader on Sprite works")


def test_shader_on_caption():
    """Test shader assignment to Caption"""
    print("Testing shader on Caption...")

    shader = mcrfpy.Shader('''
        uniform sampler2D texture;
        void main() {
            gl_FragColor = texture2D(texture, gl_TexCoord[0].xy);
        }
    ''')

    caption = mcrfpy.Caption(text="Test", pos=(0, 0))
    assert caption.shader is None, "Shader should be None initially"

    caption.shader = shader
    assert caption.shader is not None, "Shader should be assigned"

    caption.uniforms['test'] = 1.0
    assert abs(caption.uniforms['test'] - 1.0) < 0.001, "Uniform should be set"

    print("  PASS: Shader on Caption works")


def test_shader_on_grid():
    """Test shader assignment to Grid"""
    print("Testing shader on Grid...")

    shader = mcrfpy.Shader('''
        uniform sampler2D texture;
        void main() {
            gl_FragColor = texture2D(texture, gl_TexCoord[0].xy);
        }
    ''')

    grid = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(200, 200))
    assert grid.shader is None, "Shader should be None initially"

    grid.shader = shader
    assert grid.shader is not None, "Shader should be assigned"

    grid.uniforms['test'] = 1.0
    assert abs(grid.uniforms['test'] - 1.0) < 0.001, "Uniform should be set"

    print("  PASS: Shader on Grid works")


def test_shader_on_entity():
    """Test shader assignment to Entity"""
    print("Testing shader on Entity...")

    shader = mcrfpy.Shader('''
        uniform sampler2D texture;
        void main() {
            gl_FragColor = texture2D(texture, gl_TexCoord[0].xy);
        }
    ''')

    entity = mcrfpy.Entity()
    assert entity.shader is None, "Shader should be None initially"

    entity.shader = shader
    assert entity.shader is not None, "Shader should be assigned"

    entity.uniforms['test'] = 1.0
    assert abs(entity.uniforms['test'] - 1.0) < 0.001, "Uniform should be set"

    print("  PASS: Shader on Entity works")


def test_shared_shader():
    """Test that multiple drawables can share the same shader"""
    print("Testing shared shader...")

    shader = mcrfpy.Shader('''
        uniform sampler2D texture;
        uniform float intensity;
        void main() {
            vec4 color = texture2D(texture, gl_TexCoord[0].xy);
            color.rgb *= intensity;
            gl_FragColor = color;
        }
    ''')

    frame1 = mcrfpy.Frame(pos=(0, 0), size=(100, 100))
    frame2 = mcrfpy.Frame(pos=(100, 0), size=(100, 100))

    # Assign same shader to both
    frame1.shader = shader
    frame2.shader = shader

    # But different uniform values
    frame1.uniforms['intensity'] = 0.5
    frame2.uniforms['intensity'] = 1.0

    assert abs(frame1.uniforms['intensity'] - 0.5) < 0.001, "Frame1 intensity should be 0.5"
    assert abs(frame2.uniforms['intensity'] - 1.0) < 0.001, "Frame2 intensity should be 1.0"

    print("  PASS: Shared shader with different uniforms works")


def test_shader_animation_properties():
    """Test that shader uniforms can be animated via the animation system"""
    print("Testing shader animation properties...")

    frame = mcrfpy.Frame(pos=(0, 0), size=(100, 100))

    # Set initial uniform value
    frame.uniforms['intensity'] = 0.0

    # Test animate() method with shader.X property syntax
    # This uses hasProperty/setProperty internally
    try:
        frame.animate('shader.intensity', 1.0, 0.5, mcrfpy.Easing.LINEAR)
        animation_works = True
    except Exception as e:
        animation_works = False
        print(f"    Animation error: {e}")

    assert animation_works, "Animating shader uniforms should work"

    # Test with different drawable types
    sprite = mcrfpy.Sprite(pos=(0, 0))
    sprite.uniforms['glow'] = 0.0
    try:
        sprite.animate('shader.glow', 2.0, 1.0, mcrfpy.Easing.EASE_IN)
        sprite_animation_works = True
    except Exception as e:
        sprite_animation_works = False
        print(f"    Sprite animation error: {e}")

    assert sprite_animation_works, "Animating Sprite shader uniforms should work"

    # Test Caption
    caption = mcrfpy.Caption(text="Test", pos=(0, 0))
    caption.uniforms['alpha'] = 1.0
    try:
        caption.animate('shader.alpha', 0.0, 0.5, mcrfpy.Easing.EASE_OUT)
        caption_animation_works = True
    except Exception as e:
        caption_animation_works = False
        print(f"    Caption animation error: {e}")

    assert caption_animation_works, "Animating Caption shader uniforms should work"

    # Test Grid
    grid = mcrfpy.Grid(grid_size=(5, 5), pos=(0, 0), size=(100, 100))
    grid.uniforms['zoom_effect'] = 1.0
    try:
        grid.animate('shader.zoom_effect', 2.0, 1.0, mcrfpy.Easing.LINEAR)
        grid_animation_works = True
    except Exception as e:
        grid_animation_works = False
        print(f"    Grid animation error: {e}")

    assert grid_animation_works, "Animating Grid shader uniforms should work"

    print("  PASS: Shader animation properties work")


def run_all_tests():
    """Run all shader tests"""
    print("=" * 50)
    print("Shader System Unit Tests")
    print("=" * 50)
    print()

    try:
        test_shader_creation()
        test_shader_source()
        test_static_uniforms()
        test_uniform_keys()
        test_property_binding()
        test_callable_binding()
        test_shader_on_frame()
        test_shader_on_sprite()
        test_shader_on_caption()
        test_shader_on_grid()
        test_shader_on_entity()
        test_shared_shader()
        test_shader_animation_properties()

        print()
        print("=" * 50)
        print("ALL TESTS PASSED")
        print("=" * 50)
        sys.exit(0)

    except AssertionError as e:
        print(f"  FAIL: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
