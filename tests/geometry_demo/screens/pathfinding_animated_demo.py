"""Animated pathfinding through a moving solar system."""
import mcrfpy
import math
from .base import (GeometryDemoScreen, OrbitalBody, create_solar_system,
                   create_planet, point_on_circle, distance, angle_between,
                   normalize_angle, is_viable_waypoint, nearest_orbit_entry,
                   optimal_exit_heading, screen_angle_between,
                   SCREEN_WIDTH, SCREEN_HEIGHT)


class PathfindingAnimatedDemo(GeometryDemoScreen):
    """Demonstrate ship navigation through moving orbital bodies."""

    name = "Animated Pathfinding"
    description = "Ship navigates through moving planets"

    def setup(self):
        self.add_title("Pathfinding Through Moving Planets")
        self.add_description("Ship anticipates planetary motion to use orbital slingshots")

        margin = 30
        top_area = 80
        bottom_panel = 60

        # Screen layout - full width for 1024x768
        frame_width = SCREEN_WIDTH - 2 * margin
        frame_height = SCREEN_HEIGHT - top_area - bottom_panel - margin

        # Center of display area
        self.center_x = margin + frame_width // 2
        self.center_y = top_area + frame_height // 2
        self.scale = 2.5  # Larger scale for better visibility

        # Background
        bg = mcrfpy.Frame(pos=(margin, top_area), size=(frame_width, frame_height))
        bg.fill_color = mcrfpy.Color(5, 5, 15)
        bg.outline = 1
        bg.outline_color = mcrfpy.Color(40, 40, 80)
        self.ui.append(bg)

        # Store frame boundaries
        self.frame_bottom = top_area + frame_height

        # Create solar system
        self.star = create_solar_system(
            grid_width=200, grid_height=200,
            star_radius=10, star_orbit_radius=18
        )

        # Create a planet that the ship will use as waypoint
        self.planet = create_planet(
            name="Waypoint",
            star=self.star,
            orbital_radius=60,  # Smaller orbit to not clip edges
            surface_radius=8,
            orbit_ring_radius=15,
            angular_velocity=5,  # Moves 5 degrees per turn
            initial_angle=180    # Starts on left side
        )

        # Ship state
        self.ship_speed = 8  # Grid units per turn
        # Position ship further from sun to avoid line clipping through it
        self.ship_pos = [-80, 60]  # Start position (grid coords, relative to star) - lower left
        self.ship_target = [80, -60]  # Target position - upper right
        self.ship_state = "approach"  # approach, orbiting, exiting, traveling
        self.ship_orbit_angle = 0
        self.current_time = 0

        # Plan the path
        self.path_plan = []
        self.current_path_index = 0

        # Store UI elements
        self.planet_circle = None
        self.planet_orbit_ring = None
        self.ship_circle = None
        self.path_lines = []
        self.status_label = None

        # Draw static elements
        self._draw_static()

        # Draw initial state
        self._draw_dynamic()

        # Info panel
        self._draw_info_panel()

        # Start animation
        self.add_timer("pathfind_tick", self._tick, 1000)

    def _to_screen(self, grid_pos):
        """Convert grid position (relative to star) to screen coordinates."""
        gx, gy = grid_pos
        return (self.center_x + gx * self.scale, self.center_y - gy * self.scale)

    def _draw_static(self):
        """Draw static elements."""
        star_screen = self._to_screen((0, 0))

        # Star
        star = mcrfpy.Circle(
            center=star_screen,
            radius=self.star.surface_radius * self.scale,
            fill_color=mcrfpy.Color(255, 220, 100),
            outline_color=mcrfpy.Color(255, 180, 50),
            outline=2
        )
        self.ui.append(star)

        # Planet orbital path
        orbit_path = mcrfpy.Circle(
            center=star_screen,
            radius=self.planet.orbital_radius * self.scale,
            fill_color=mcrfpy.Color(0, 0, 0, 0),
            outline_color=mcrfpy.Color(40, 40, 60),
            outline=1
        )
        self.ui.append(orbit_path)

        # Target marker
        target_screen = self._to_screen(self.ship_target)
        target = mcrfpy.Circle(
            center=target_screen,
            radius=12,
            fill_color=mcrfpy.Color(255, 100, 100),
            outline_color=mcrfpy.Color(255, 200, 200),
            outline=2
        )
        self.ui.append(target)
        self.add_label("TARGET", target_screen[0] - 25, target_screen[1] + 15, (255, 100, 100))

        # Start marker
        start_screen = self._to_screen(self.ship_pos)
        self.add_label("START", start_screen[0] - 20, start_screen[1] + 15, (100, 255, 100))

    def _draw_dynamic(self):
        """Draw/update dynamic elements (planet, ship, path)."""
        # Get planet position at current time
        planet_grid = self._get_planet_pos(self.current_time)
        planet_screen = self._to_screen(planet_grid)

        # Planet
        if self.planet_circle:
            self.planet_circle.center = planet_screen
        else:
            self.planet_circle = mcrfpy.Circle(
                center=planet_screen,
                radius=self.planet.surface_radius * self.scale,
                fill_color=mcrfpy.Color(100, 150, 255),
                outline_color=mcrfpy.Color(150, 200, 255),
                outline=2
            )
            self.ui.append(self.planet_circle)

        # Planet orbit ring
        if self.planet_orbit_ring:
            self.planet_orbit_ring.center = planet_screen
        else:
            self.planet_orbit_ring = mcrfpy.Circle(
                center=planet_screen,
                radius=self.planet.orbit_ring_radius * self.scale,
                fill_color=mcrfpy.Color(0, 0, 0, 0),
                outline_color=mcrfpy.Color(50, 150, 50),
                outline=2
            )
            self.ui.append(self.planet_orbit_ring)

        # Ship
        ship_screen = self._to_screen(self.ship_pos)
        if self.ship_circle:
            self.ship_circle.center = ship_screen
        else:
            self.ship_circle = mcrfpy.Circle(
                center=ship_screen,
                radius=8,
                fill_color=mcrfpy.Color(255, 200, 100),
                outline_color=mcrfpy.Color(255, 255, 200),
                outline=2
            )
            self.ui.append(self.ship_circle)

        # Draw predicted path
        self._draw_predicted_path()

    def _get_planet_pos(self, t):
        """Get planet position in grid coords relative to star."""
        angle = self.planet.initial_angle + self.planet.angular_velocity * t
        x = self.planet.orbital_radius * math.cos(math.radians(angle))
        y = self.planet.orbital_radius * math.sin(math.radians(angle))
        return (x, y)

    def _draw_predicted_path(self):
        """Draw the predicted ship path."""
        # Clear old path lines
        # (In a real implementation, we'd remove old lines from UI)
        # For now, we'll just draw new ones each time

        ship_pos = tuple(self.ship_pos)
        target = tuple(self.ship_target)

        # Simple path prediction:
        # 1. Calculate when ship can intercept planet's orbit
        # 2. Show line to intercept point
        # 3. Show arc on orbit
        # 4. Show line to target

        if self.ship_state == "approach":
            # Find intercept time
            intercept_time, intercept_pos = self._find_intercept()
            if intercept_time:
                # Line from ship to intercept
                ship_screen = self._to_screen(ship_pos)
                intercept_screen = self._to_screen(intercept_pos)

                # Draw approach line
                approach_line = mcrfpy.Line(
                    start=ship_screen, end=intercept_screen,
                    color=mcrfpy.Color(100, 200, 255, 150),
                    thickness=2
                )
                self.ui.append(approach_line)

    def _find_intercept(self):
        """Find when ship can intercept planet's orbit."""
        # Simplified: check next 20 turns
        for dt in range(1, 20):
            future_t = self.current_time + dt
            planet_pos = self._get_planet_pos(future_t)

            # Distance ship could travel
            max_dist = self.ship_speed * dt

            # Distance from ship to planet's orbit ring
            dist_to_planet = distance(self.ship_pos, planet_pos)
            dist_to_orbit = abs(dist_to_planet - self.planet.orbit_ring_radius)

            if dist_to_orbit <= max_dist:
                # Calculate entry point
                angle_to_planet = angle_between(self.ship_pos, planet_pos)
                entry_x = planet_pos[0] + self.planet.orbit_ring_radius * math.cos(math.radians(angle_to_planet + 180))
                entry_y = planet_pos[1] + self.planet.orbit_ring_radius * math.sin(math.radians(angle_to_planet + 180))
                return (future_t, (entry_x, entry_y))

        return (None, None)

    def _draw_info_panel(self):
        """Draw information panel."""
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

        # Status display
        self.status_label = mcrfpy.Caption(text="Status: Approaching planet", pos=(180, panel_y + 12))
        self.status_label.fill_color = mcrfpy.Color(100, 200, 255)
        self.ui.append(self.status_label)

        # Distance display
        self.dist_label = mcrfpy.Caption(text="Distance to target: ---", pos=(550, panel_y + 12))
        self.dist_label.fill_color = mcrfpy.Color(150, 150, 150)
        self.ui.append(self.dist_label)

    def _tick(self, runtime):
        """Advance one turn."""
        self.current_time += 1
        self.time_label.text = f"Turn: {self.current_time}"

        # Update ship based on state
        if self.ship_state == "approach":
            self._update_approach()
        elif self.ship_state == "orbiting":
            self._update_orbiting()
        elif self.ship_state == "exiting":
            self._update_exiting()
        elif self.ship_state == "traveling":
            self._update_traveling()
        elif self.ship_state == "arrived":
            pass  # Done!

        # Update distance display
        dist = distance(self.ship_pos, self.ship_target)
        self.dist_label.text = f"Distance to target: {dist:.1f}"

        # Update visuals
        self._draw_dynamic()

    def _update_approach(self):
        """Move ship toward planet's predicted position."""
        # Find where planet will be when we can intercept
        intercept_time, intercept_pos = self._find_intercept()

        if intercept_pos:
            # Move toward intercept point
            dx = intercept_pos[0] - self.ship_pos[0]
            dy = intercept_pos[1] - self.ship_pos[1]
            dist = math.sqrt(dx*dx + dy*dy)

            if dist <= self.ship_speed:
                # Arrived at orbit - enter orbit
                self.ship_pos = list(intercept_pos)
                planet_pos = self._get_planet_pos(self.current_time)
                self.ship_orbit_angle = angle_between(planet_pos, self.ship_pos)
                self.ship_state = "orbiting"
                self.status_label.text = "Status: In orbit (repositioning FREE)"
                self.status_label.fill_color = mcrfpy.Color(255, 255, 100)
            else:
                # Move toward intercept
                self.ship_pos[0] += (dx / dist) * self.ship_speed
                self.ship_pos[1] += (dy / dist) * self.ship_speed
                self.status_label.text = f"Status: Approaching intercept (T+{intercept_time - self.current_time})"
        else:
            # Can't find intercept, go direct
            self.ship_state = "traveling"

    def _update_orbiting(self):
        """Reposition on orbit toward optimal exit."""
        planet_pos = self._get_planet_pos(self.current_time)

        # Calculate optimal exit angle (toward target)
        exit_angle = angle_between(planet_pos, self.ship_target)

        # Move along orbit toward exit angle (this is FREE movement)
        angle_diff = exit_angle - self.ship_orbit_angle
        if angle_diff > 180:
            angle_diff -= 360
        elif angle_diff < -180:
            angle_diff += 360

        # Move up to 45 degrees per turn along orbit (arbitrary limit for demo)
        move_angle = max(-45, min(45, angle_diff))
        self.ship_orbit_angle = normalize_angle(self.ship_orbit_angle + move_angle)

        # Update ship position to new orbital position
        self.ship_pos[0] = planet_pos[0] + self.planet.orbit_ring_radius * math.cos(math.radians(self.ship_orbit_angle))
        self.ship_pos[1] = planet_pos[1] + self.planet.orbit_ring_radius * math.sin(math.radians(self.ship_orbit_angle))

        # Check if we're at optimal exit
        if abs(angle_diff) < 10:
            self.ship_state = "exiting"
            self.status_label.text = "Status: Exiting orbit toward target"
            self.status_label.fill_color = mcrfpy.Color(100, 255, 100)

    def _update_exiting(self):
        """Exit orbit and head toward target."""
        # Just transition to traveling
        self.ship_state = "traveling"

    def _update_traveling(self):
        """Travel directly toward target."""
        dx = self.ship_target[0] - self.ship_pos[0]
        dy = self.ship_target[1] - self.ship_pos[1]
        dist = math.sqrt(dx*dx + dy*dy)

        if dist <= self.ship_speed:
            # Arrived!
            self.ship_pos = list(self.ship_target)
            self.ship_state = "arrived"
            self.status_label.text = "Status: ARRIVED!"
            self.status_label.fill_color = mcrfpy.Color(100, 255, 100)
        else:
            # Move toward target
            self.ship_pos[0] += (dx / dist) * self.ship_speed
            self.ship_pos[1] += (dy / dist) * self.ship_speed
            self.status_label.text = f"Status: Traveling to target ({dist:.0f} units)"
