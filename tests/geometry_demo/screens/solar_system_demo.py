"""Animated solar system demonstration."""
import mcrfpy
import math
from .base import (GeometryDemoScreen, OrbitalBody, create_solar_system,
                   create_planet, create_moon, point_on_circle,
                   SCREEN_WIDTH, SCREEN_HEIGHT)


class SolarSystemDemo(GeometryDemoScreen):
    """Demonstrate animated orbital mechanics with timer-based updates."""

    name = "Solar System Animation"
    description = "Planets orbiting with discrete time steps"

    def setup(self):
        self.add_title("Animated Solar System")
        self.add_description("Planets snap to grid positions as time advances (1 tick = 1 turn)")

        margin = 30
        top_area = 80
        bottom_panel = 60

        # Screen layout - centered, with room for Earth's moon orbit
        frame_width = SCREEN_WIDTH - 2 * margin
        frame_height = SCREEN_HEIGHT - top_area - bottom_panel - margin

        # Center of display area, shifted down a bit to give room for moon orbit at top
        self.center_x = margin + frame_width // 2
        self.center_y = top_area + frame_height // 2 + 30  # Shifted down
        self.scale = 2.0  # Pixels per grid unit (larger for 1024x768)

        # Background
        bg = mcrfpy.Frame(pos=(margin, top_area), size=(frame_width, frame_height))
        bg.fill_color = mcrfpy.Color(5, 5, 15)
        bg.outline = 1
        bg.outline_color = mcrfpy.Color(40, 40, 80)
        self.ui.append(bg)

        # Store frame boundaries for info panel
        self.frame_bottom = top_area + frame_height

        # Create the solar system using geometry module
        self.star = create_solar_system(
            grid_width=200, grid_height=200,
            star_radius=15, star_orbit_radius=25
        )

        # Create planets with different orbital speeds
        self.planet1 = create_planet(
            name="Mercury",
            star=self.star,
            orbital_radius=60,
            surface_radius=5,
            orbit_ring_radius=12,
            angular_velocity=12,  # Fast orbit
            initial_angle=0
        )

        self.planet2 = create_planet(
            name="Venus",
            star=self.star,
            orbital_radius=100,
            surface_radius=8,
            orbit_ring_radius=16,
            angular_velocity=7,  # Medium orbit
            initial_angle=120
        )

        self.planet3 = create_planet(
            name="Earth",
            star=self.star,
            orbital_radius=150,
            surface_radius=10,
            orbit_ring_radius=20,
            angular_velocity=4,  # Slow orbit
            initial_angle=240
        )

        # Moon orbiting Earth
        self.moon = create_moon(
            name="Luna",
            planet=self.planet3,
            orbital_radius=30,
            surface_radius=3,
            orbit_ring_radius=8,
            angular_velocity=15,  # Faster than Earth
            initial_angle=45
        )

        self.planets = [self.planet1, self.planet2, self.planet3]
        self.moons = [self.moon]

        # Current time step
        self.current_time = 0

        # Store UI elements for updating
        self.planet_circles = {}
        self.orbit_rings = {}
        self.moon_circles = {}

        # Draw static elements (star, orbit paths)
        self._draw_static_elements()

        # Draw initial planet positions
        self._draw_planets()

        # Info panel below the main frame
        panel_y = self.frame_bottom + 10
        panel = mcrfpy.Frame(pos=(30, panel_y), size=(SCREEN_WIDTH - 60, 45))
        panel.fill_color = mcrfpy.Color(20, 20, 35)
        panel.outline = 1
        panel.outline_color = mcrfpy.Color(60, 60, 100)
        self.ui.append(panel)

        # Time display
        self.time_label = mcrfpy.Caption(text="Turn: 0", pos=(40, panel_y + 12))
        self.time_label.fill_color = mcrfpy.Color(255, 255, 255)
        self.ui.append(self.time_label)

        # Instructions
        self.add_label("Time advances automatically every second", 200, panel_y + 12, (150, 150, 150))

        # Start the animation timer
        self.add_timer("solar_tick", self._tick, 1000)  # 1 second per turn

    def _to_screen(self, grid_pos):
        """Convert grid position to screen coordinates."""
        gx, gy = grid_pos
        # Center on screen, with star at center
        star_pos = self.star.base_position
        dx = (gx - star_pos[0]) * self.scale
        dy = (gy - star_pos[1]) * self.scale
        return (self.center_x + dx, self.center_y + dy)

    def _draw_static_elements(self):
        """Draw elements that don't move (star, orbital paths)."""
        star_screen = self._to_screen(self.star.base_position)

        # Star
        star_circle = mcrfpy.Circle(
            center=star_screen,
            radius=self.star.surface_radius * self.scale,
            fill_color=mcrfpy.Color(255, 220, 100),
            outline_color=mcrfpy.Color(255, 180, 50),
            outline=3
        )
        self.ui.append(star_circle)

        # Star glow effect
        for i in range(3):
            glow = mcrfpy.Circle(
                center=star_screen,
                radius=(self.star.surface_radius + 5 + i * 8) * self.scale,
                fill_color=mcrfpy.Color(0, 0, 0, 0),
                outline_color=mcrfpy.Color(255, 200, 50, 50 - i * 15),
                outline=2
            )
            self.ui.append(glow)

        # Orbital paths (static ellipses showing where planets travel)
        for planet in self.planets:
            path = mcrfpy.Circle(
                center=star_screen,
                radius=planet.orbital_radius * self.scale,
                fill_color=mcrfpy.Color(0, 0, 0, 0),
                outline_color=mcrfpy.Color(40, 40, 60),
                outline=1
            )
            self.ui.append(path)

        # Star label
        self.add_label("Star", star_screen[0] - 15, star_screen[1] + self.star.surface_radius * self.scale + 5,
                       (255, 220, 100))

    def _draw_planets(self):
        """Draw planets at their current positions."""
        for planet in self.planets:
            self._draw_planet(planet)

        for moon in self.moons:
            self._draw_moon(moon)

    def _draw_planet(self, planet):
        """Draw a single planet."""
        # Get grid position at current time
        grid_pos = planet.grid_position_at_time(self.current_time)
        screen_pos = self._to_screen(grid_pos)

        # Color based on planet
        colors = {
            "Mercury": (180, 180, 180),
            "Venus": (255, 200, 150),
            "Earth": (100, 150, 255),
        }
        color = colors.get(planet.name, (150, 150, 150))

        # Planet surface
        planet_circle = mcrfpy.Circle(
            center=screen_pos,
            radius=planet.surface_radius * self.scale,
            fill_color=mcrfpy.Color(*color),
            outline_color=mcrfpy.Color(255, 255, 255, 100),
            outline=1
        )
        self.ui.append(planet_circle)
        self.planet_circles[planet.name] = planet_circle

        # Orbit ring around planet
        orbit_ring = mcrfpy.Circle(
            center=screen_pos,
            radius=planet.orbit_ring_radius * self.scale,
            fill_color=mcrfpy.Color(0, 0, 0, 0),
            outline_color=mcrfpy.Color(50, 150, 50, 100),
            outline=1
        )
        self.ui.append(orbit_ring)
        self.orbit_rings[planet.name] = orbit_ring

        # Planet label
        label = mcrfpy.Caption(
            text=planet.name,
            pos=(screen_pos[0] - 20, screen_pos[1] - planet.surface_radius * self.scale - 15)
        )
        label.fill_color = mcrfpy.Color(*color)
        self.ui.append(label)
        # Store label for updating
        if not hasattr(self, 'planet_labels'):
            self.planet_labels = {}
        self.planet_labels[planet.name] = label

    def _draw_moon(self, moon):
        """Draw a moon."""
        grid_pos = moon.grid_position_at_time(self.current_time)
        screen_pos = self._to_screen(grid_pos)

        moon_circle = mcrfpy.Circle(
            center=screen_pos,
            radius=moon.surface_radius * self.scale,
            fill_color=mcrfpy.Color(200, 200, 200),
            outline_color=mcrfpy.Color(255, 255, 255, 100),
            outline=1
        )
        self.ui.append(moon_circle)
        self.moon_circles[moon.name] = moon_circle

        # Moon's orbit path around Earth
        parent_pos = self._to_screen(moon.parent.grid_position_at_time(self.current_time))
        moon_path = mcrfpy.Circle(
            center=parent_pos,
            radius=moon.orbital_radius * self.scale,
            fill_color=mcrfpy.Color(0, 0, 0, 0),
            outline_color=mcrfpy.Color(60, 60, 80),
            outline=1
        )
        self.ui.append(moon_path)
        self.orbit_rings[moon.name + "_path"] = moon_path

    def _tick(self, runtime):
        """Advance time by one turn and update planet positions."""
        self.current_time += 1

        # Update time display
        self.time_label.text = f"Turn: {self.current_time}"

        # Update planet positions
        for planet in self.planets:
            grid_pos = planet.grid_position_at_time(self.current_time)
            screen_pos = self._to_screen(grid_pos)

            # Update circle position
            if planet.name in self.planet_circles:
                self.planet_circles[planet.name].center = screen_pos
                self.orbit_rings[planet.name].center = screen_pos

            # Update label position
            if hasattr(self, 'planet_labels') and planet.name in self.planet_labels:
                self.planet_labels[planet.name].pos = (
                    screen_pos[0] - 20,
                    screen_pos[1] - planet.surface_radius * self.scale - 15
                )

        # Update moon positions
        for moon in self.moons:
            grid_pos = moon.grid_position_at_time(self.current_time)
            screen_pos = self._to_screen(grid_pos)

            if moon.name in self.moon_circles:
                self.moon_circles[moon.name].center = screen_pos

            # Update moon's orbital path center
            parent_pos = self._to_screen(moon.parent.grid_position_at_time(self.current_time))
            path_key = moon.name + "_path"
            if path_key in self.orbit_rings:
                self.orbit_rings[path_key].center = parent_pos
