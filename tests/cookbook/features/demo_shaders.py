#!/usr/bin/env python3
"""Shader Effects Demo - GLSL shader visual effects

Interactive controls:
    1-4: Focus on specific shader
    Space: Toggle shaders on/off
    R: Reset all shaders
    ESC: Exit demo

Shader uniforms available:
    - float time: Seconds since engine start
    - float delta_time: Seconds since last frame
    - vec2 resolution: Texture size in pixels
    - vec2 mouse: Mouse position in window coordinates
"""
import mcrfpy
import sys


class ShaderDemo:
    def __init__(self):
        self.scene = mcrfpy.Scene("shader_demo")
        self.ui = self.scene.children
        self.shaders_enabled = True
        self.shader_frames = []
        self.shaders = []
        self.setup()

    def setup(self):
        """Build the demo scene."""
        # Background
        bg = mcrfpy.Frame(
            pos=(0, 0),
            size=(1024, 768),
            fill_color=mcrfpy.Color(15, 15, 20)
        )
        self.ui.append(bg)

        # Title
        title = mcrfpy.Caption(
            text="Shader Effects Demo",
            pos=(512, 30),
            font_size=28,
            fill_color=mcrfpy.Color(255, 255, 255)
        )
        title.outline = 2
        title.outline_color = mcrfpy.Color(0, 0, 0)
        self.ui.append(title)

        # Create four shader demo quadrants
        self._create_pulse_shader(50, 100)
        self._create_vignette_shader(530, 100)
        self._create_wave_shader(50, 420)
        self._create_color_shift_shader(530, 420)

        # Instructions
        instr = mcrfpy.Caption(
            text="1-4: Focus shader | Space: Toggle on/off | R: Reset | ESC: Exit",
            pos=(50, 730),
            font_size=14,
            fill_color=mcrfpy.Color(120, 120, 120)
        )
        self.ui.append(instr)

        # Status
        self.status = mcrfpy.Caption(
            text="Shaders: Enabled",
            pos=(50, 700),
            font_size=16,
            fill_color=mcrfpy.Color(100, 200, 100)
        )
        self.ui.append(self.status)

    def _create_pulse_shader(self, x, y):
        """Create pulsing glow shader demo."""
        # Label
        label = mcrfpy.Caption(
            text="1. Pulse Glow",
            pos=(x + 200, y - 20),
            font_size=16,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(label)

        # Frame to apply shader to
        frame = mcrfpy.Frame(
            pos=(x, y),
            size=(420, 280),
            fill_color=mcrfpy.Color(80, 60, 120),
            outline_color=mcrfpy.Color(150, 100, 200),
            outline=2
        )

        # Add some content
        content = mcrfpy.Caption(
            text="Brightness pulses\nusing time uniform",
            pos=(210, 100),
            font_size=18,
            fill_color=mcrfpy.Color(255, 255, 255)
        )
        frame.children.append(content)

        # Create pulse shader
        pulse_shader = mcrfpy.Shader('''
            uniform sampler2D texture;
            uniform float time;

            void main() {
                vec2 uv = gl_TexCoord[0].xy;
                vec4 color = texture2D(texture, uv);

                // Pulse brightness
                float pulse = 0.7 + 0.3 * sin(time * 2.0);
                color.rgb *= pulse;

                gl_FragColor = color * gl_Color;
            }
        ''', dynamic=True)

        frame.shader = pulse_shader
        self.ui.append(frame)
        self.shader_frames.append(frame)
        self.shaders.append(pulse_shader)

    def _create_vignette_shader(self, x, y):
        """Create vignette (darkened edges) shader demo."""
        # Label
        label = mcrfpy.Caption(
            text="2. Vignette",
            pos=(x + 200, y - 20),
            font_size=16,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(label)

        # Frame
        frame = mcrfpy.Frame(
            pos=(x, y),
            size=(420, 280),
            fill_color=mcrfpy.Color(100, 80, 60),
            outline_color=mcrfpy.Color(200, 150, 100),
            outline=2
        )

        content = mcrfpy.Caption(
            text="Darkened edges\nclassic vignette effect",
            pos=(210, 100),
            font_size=18,
            fill_color=mcrfpy.Color(255, 255, 255)
        )
        frame.children.append(content)

        # Create vignette shader
        vignette_shader = mcrfpy.Shader('''
            uniform sampler2D texture;
            uniform vec2 resolution;

            void main() {
                vec2 uv = gl_TexCoord[0].xy;
                vec4 color = texture2D(texture, uv);

                // Calculate distance from center
                vec2 center = vec2(0.5, 0.5);
                float dist = distance(uv, center);

                // Vignette effect - darken edges
                float vignette = 1.0 - smoothstep(0.3, 0.8, dist);
                color.rgb *= vignette;

                gl_FragColor = color * gl_Color;
            }
        ''', dynamic=False)

        frame.shader = vignette_shader
        self.ui.append(frame)
        self.shader_frames.append(frame)
        self.shaders.append(vignette_shader)

    def _create_wave_shader(self, x, y):
        """Create wave distortion shader demo."""
        # Label
        label = mcrfpy.Caption(
            text="3. Wave Distortion",
            pos=(x + 200, y - 20),
            font_size=16,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(label)

        # Frame
        frame = mcrfpy.Frame(
            pos=(x, y),
            size=(420, 280),
            fill_color=mcrfpy.Color(60, 100, 120),
            outline_color=mcrfpy.Color(100, 180, 220),
            outline=2
        )

        content = mcrfpy.Caption(
            text="Sine wave\nUV distortion",
            pos=(210, 100),
            font_size=18,
            fill_color=mcrfpy.Color(255, 255, 255)
        )
        frame.children.append(content)

        # Create wave shader
        wave_shader = mcrfpy.Shader('''
            uniform sampler2D texture;
            uniform float time;

            void main() {
                vec2 uv = gl_TexCoord[0].xy;

                // Apply wave distortion
                float wave = sin(uv.y * 20.0 + time * 3.0) * 0.01;
                uv.x += wave;

                vec4 color = texture2D(texture, uv);
                gl_FragColor = color * gl_Color;
            }
        ''', dynamic=True)

        frame.shader = wave_shader
        self.ui.append(frame)
        self.shader_frames.append(frame)
        self.shaders.append(wave_shader)

    def _create_color_shift_shader(self, x, y):
        """Create chromatic aberration / color shift shader demo."""
        # Label
        label = mcrfpy.Caption(
            text="4. Color Shift",
            pos=(x + 200, y - 20),
            font_size=16,
            fill_color=mcrfpy.Color(150, 150, 150)
        )
        self.ui.append(label)

        # Frame
        frame = mcrfpy.Frame(
            pos=(x, y),
            size=(420, 280),
            fill_color=mcrfpy.Color(80, 80, 80),
            outline_color=mcrfpy.Color(150, 150, 150),
            outline=2
        )

        content = mcrfpy.Caption(
            text="Chromatic aberration\nRGB channel offset",
            pos=(210, 100),
            font_size=18,
            fill_color=mcrfpy.Color(255, 255, 255)
        )
        frame.children.append(content)

        # Create color shift shader
        colorshift_shader = mcrfpy.Shader('''
            uniform sampler2D texture;
            uniform float time;

            void main() {
                vec2 uv = gl_TexCoord[0].xy;

                // Offset for each channel
                float offset = 0.005 + 0.003 * sin(time);

                // Sample each channel with slight offset
                float r = texture2D(texture, uv + vec2(offset, 0.0)).r;
                float g = texture2D(texture, uv).g;
                float b = texture2D(texture, uv - vec2(offset, 0.0)).b;
                float a = texture2D(texture, uv).a;

                gl_FragColor = vec4(r, g, b, a) * gl_Color;
            }
        ''', dynamic=True)

        frame.shader = colorshift_shader
        self.ui.append(frame)
        self.shader_frames.append(frame)
        self.shaders.append(colorshift_shader)

    def toggle_shaders(self):
        """Toggle all shaders on/off."""
        self.shaders_enabled = not self.shaders_enabled

        for frame, shader in zip(self.shader_frames, self.shaders):
            if self.shaders_enabled:
                frame.shader = shader
                self.status.text = "Shaders: Enabled"
                self.status.fill_color = mcrfpy.Color(100, 200, 100)
            else:
                frame.shader = None
                self.status.text = "Shaders: Disabled"
                self.status.fill_color = mcrfpy.Color(200, 100, 100)

    def on_key(self, key, state):
        """Handle keyboard input."""
        if state != "start":
            return

        if key == "Escape":
            sys.exit(0)
        elif key == "Space":
            self.toggle_shaders()
        elif key == "R":
            # Re-enable all shaders
            self.shaders_enabled = False
            self.toggle_shaders()
        elif key in ("Num1", "Num2", "Num3", "Num4"):
            # Focus on specific shader (could zoom in)
            idx = int(key[-1]) - 1
            if idx < len(self.shader_frames):
                self.status.text = f"Focused: Shader {idx + 1}"

    def activate(self):
        """Activate the demo scene."""
        self.scene.on_key = self.on_key
        mcrfpy.current_scene = self.scene


def main():
    """Run the shader demo."""
    demo = ShaderDemo()
    demo.activate()

    # Headless mode: capture screenshot and exit
    try:
        if mcrfpy.headless_mode():
            from mcrfpy import automation
            mcrfpy.Timer("screenshot", lambda rt: (
                automation.screenshot("screenshots/features/shader_demo.png"),
                sys.exit(0)
            ), 200)
    except AttributeError:
        pass


if __name__ == "__main__":
    main()
