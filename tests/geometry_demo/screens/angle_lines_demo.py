"""Angle calculation demonstration with Line elements."""
import mcrfpy
import math
from .base import (GeometryDemoScreen, angle_between, angle_difference,
                   normalize_angle, point_on_circle, distance)


class AngleLinesDemo(GeometryDemoScreen):
    """Demonstrate angle calculations between points using Line elements."""

    name = "Angle Calculations"
    description = "Visualizing angles between grid positions"

    def setup(self):
        self.add_title("Angle Calculations & Line Elements")
        self.add_description("Computing headings, deviations, and opposite angles for pathfinding")

        # Demo 1: Basic angle between two points
        self._demo_basic_angle()

        # Demo 2: Angle between three points (deviation)
        self._demo_angle_deviation()

        # Demo 3: Waypoint viability visualization
        self._demo_waypoint_viability()

        # Demo 4: Orbit exit heading
        self._demo_orbit_exit()

    def _demo_basic_angle(self):
        """Show angle from point A to point B."""
        bg = mcrfpy.Frame(pos=(30, 80), size=(350, 200))
        bg.fill_color = mcrfpy.Color(15, 15, 25)
        bg.outline = 1
        bg.outline_color = mcrfpy.Color(60, 60, 100)
        self.ui.append(bg)

        self.add_label("Basic Angle Calculation", 50, 85, (255, 200, 100))

        # Point A (origin)
        ax, ay = 100, 180
        # Point B (target)
        bx, by = 300, 120

        angle = angle_between((ax, ay), (bx, by))
        dist = distance((ax, ay), (bx, by))

        # Draw the line A to B (green)
        line_ab = mcrfpy.Line(
            start=(ax, ay), end=(bx, by),
            color=mcrfpy.Color(100, 255, 100),
            thickness=3
        )
        self.ui.append(line_ab)

        # Draw reference line (east from A) in gray
        line_ref = mcrfpy.Line(
            start=(ax, ay), end=(ax + 150, ay),
            color=mcrfpy.Color(100, 100, 100),
            thickness=1
        )
        self.ui.append(line_ref)

        # Draw arc showing the angle
        arc = mcrfpy.Arc(
            center=(ax, ay), radius=40,
            start_angle=0, end_angle=-angle,  # Negative because screen Y is inverted
            color=mcrfpy.Color(255, 255, 100),
            thickness=2
        )
        self.ui.append(arc)

        # Points
        point_a = mcrfpy.Circle(center=(ax, ay), radius=8,
                               fill_color=mcrfpy.Color(255, 100, 100))
        point_b = mcrfpy.Circle(center=(bx, by), radius=8,
                               fill_color=mcrfpy.Color(100, 255, 100))
        self.ui.append(point_a)
        self.ui.append(point_b)

        # Labels
        self.add_label("A", ax - 20, ay - 5, (255, 100, 100))
        self.add_label("B", bx + 10, by - 5, (100, 255, 100))
        self.add_label(f"Angle: {angle:.1f}°", 50, 250, (255, 255, 100))
        self.add_label(f"Distance: {dist:.1f}", 180, 250, (150, 150, 150))

    def _demo_angle_deviation(self):
        """Show angle deviation when considering a waypoint."""
        bg = mcrfpy.Frame(pos=(400, 80), size=(380, 200))
        bg.fill_color = mcrfpy.Color(15, 15, 25)
        bg.outline = 1
        bg.outline_color = mcrfpy.Color(60, 60, 100)
        self.ui.append(bg)

        self.add_label("Waypoint Deviation", 420, 85, (255, 200, 100))
        self.add_label("Is planet C a useful waypoint from A to B?", 420, 105, (150, 150, 150))

        # Ship at A, target at B, potential waypoint C
        ax, ay = 450, 230
        bx, by = 720, 180
        cx, cy = 550, 150

        # Calculate angles
        angle_to_target = angle_between((ax, ay), (bx, by))
        angle_to_waypoint = angle_between((ax, ay), (cx, cy))
        deviation = abs(angle_difference(angle_to_target, angle_to_waypoint))

        # Draw line A to B (direct path - green)
        line_ab = mcrfpy.Line(
            start=(ax, ay), end=(bx, by),
            color=mcrfpy.Color(100, 255, 100),
            thickness=2
        )
        self.ui.append(line_ab)

        # Draw line A to C (waypoint path - yellow if viable, red if not)
        viable = deviation <= 45
        waypoint_color = mcrfpy.Color(255, 255, 100) if viable else mcrfpy.Color(255, 100, 100)
        line_ac = mcrfpy.Line(
            start=(ax, ay), end=(cx, cy),
            color=waypoint_color,
            thickness=2
        )
        self.ui.append(line_ac)

        # Draw deviation arc
        arc = mcrfpy.Arc(
            center=(ax, ay), radius=50,
            start_angle=-angle_to_target, end_angle=-angle_to_waypoint,
            color=waypoint_color,
            thickness=2
        )
        self.ui.append(arc)

        # Points
        point_a = mcrfpy.Circle(center=(ax, ay), radius=8,
                               fill_color=mcrfpy.Color(255, 100, 100))
        point_b = mcrfpy.Circle(center=(bx, by), radius=8,
                               fill_color=mcrfpy.Color(100, 255, 100))
        point_c = mcrfpy.Circle(center=(cx, cy), radius=12,
                               fill_color=mcrfpy.Color(100, 100, 200),
                               outline_color=mcrfpy.Color(150, 150, 255),
                               outline=2)
        self.ui.append(point_a)
        self.ui.append(point_b)
        self.ui.append(point_c)

        # Labels
        self.add_label("A (ship)", ax - 10, ay + 10, (255, 100, 100))
        self.add_label("B (target)", bx - 20, by + 15, (100, 255, 100))
        self.add_label("C (planet)", cx + 15, cy - 5, (150, 150, 255))
        label_color = (255, 255, 100) if viable else (255, 100, 100)
        self.add_label(f"Deviation: {deviation:.1f}°", 550, 250, label_color)
        status = "VIABLE (<45°)" if viable else "NOT VIABLE (>45°)"
        self.add_label(status, 680, 250, label_color)

    def _demo_waypoint_viability(self):
        """Show multiple potential waypoints with viability indicators."""
        bg = mcrfpy.Frame(pos=(30, 300), size=(350, 280))
        bg.fill_color = mcrfpy.Color(15, 15, 25)
        bg.outline = 1
        bg.outline_color = mcrfpy.Color(60, 60, 100)
        self.ui.append(bg)

        self.add_label("Multiple Waypoint Analysis", 50, 305, (255, 200, 100))

        # Ship and target
        ax, ay = 80, 450
        bx, by = 320, 380

        angle_to_target = angle_between((ax, ay), (bx, by))

        # Draw direct path
        line_ab = mcrfpy.Line(
            start=(ax, ay), end=(bx, by),
            color=mcrfpy.Color(100, 255, 100, 128),
            thickness=2
        )
        self.ui.append(line_ab)

        # Potential waypoints at various angles
        waypoints = [
            (150, 360, "W1"),  # Ahead and left - viable
            (200, 500, "W2"),  # Below path - marginal
            (100, 540, "W3"),  # Behind - not viable
            (250, 340, "W4"),  # Almost on path - very viable
        ]

        threshold = 45
        for wx, wy, label in waypoints:
            angle_to_wp = angle_between((ax, ay), (wx, wy))
            deviation = abs(angle_difference(angle_to_target, angle_to_wp))
            viable = deviation <= threshold

            # Line to waypoint
            color_tuple = (100, 255, 100) if viable else (255, 100, 100)
            color = mcrfpy.Color(*color_tuple)
            line = mcrfpy.Line(
                start=(ax, ay), end=(wx, wy),
                color=color,
                thickness=1
            )
            self.ui.append(line)

            # Waypoint circle
            wp_circle = mcrfpy.Circle(
                center=(wx, wy), radius=15,
                fill_color=mcrfpy.Color(80, 80, 120),
                outline_color=color,
                outline=2
            )
            self.ui.append(wp_circle)

            self.add_label(f"{label}:{deviation:.0f}°", wx + 18, wy - 8, color_tuple)

        # Ship and target markers
        ship = mcrfpy.Circle(center=(ax, ay), radius=8,
                            fill_color=mcrfpy.Color(255, 200, 100))
        target = mcrfpy.Circle(center=(bx, by), radius=8,
                              fill_color=mcrfpy.Color(100, 255, 100))
        self.ui.append(ship)
        self.ui.append(target)

        self.add_label("Ship", ax - 5, ay + 12, (255, 200, 100))
        self.add_label("Target", bx - 15, by + 12, (100, 255, 100))
        self.add_label(f"Threshold: {threshold}°", 50, 555, (150, 150, 150))

    def _demo_orbit_exit(self):
        """Show optimal orbit exit heading toward target."""
        bg = mcrfpy.Frame(pos=(400, 300), size=(380, 280))
        bg.fill_color = mcrfpy.Color(15, 15, 25)
        bg.outline = 1
        bg.outline_color = mcrfpy.Color(60, 60, 100)
        self.ui.append(bg)

        self.add_label("Orbit Exit Heading", 420, 305, (255, 200, 100))
        self.add_label("Ship in orbit chooses optimal exit point", 420, 325, (150, 150, 150))

        # Planet center and orbit
        px, py = 520, 450
        orbit_radius = 60
        surface_radius = 25

        # Target position
        tx, ty = 720, 380

        # Calculate optimal exit angle
        exit_angle = angle_between((px, py), (tx, ty))
        exit_x = px + orbit_radius * math.cos(math.radians(exit_angle))
        exit_y = py - orbit_radius * math.sin(math.radians(exit_angle))  # Flip for screen coords

        # Draw planet surface
        planet = mcrfpy.Circle(
            center=(px, py), radius=surface_radius,
            fill_color=mcrfpy.Color(80, 120, 180),
            outline_color=mcrfpy.Color(100, 150, 220),
            outline=2
        )
        self.ui.append(planet)

        # Draw orbit ring
        orbit = mcrfpy.Circle(
            center=(px, py), radius=orbit_radius,
            fill_color=mcrfpy.Color(0, 0, 0, 0),
            outline_color=mcrfpy.Color(50, 150, 50),
            outline=2
        )
        self.ui.append(orbit)

        # Draw ship positions around orbit (current position)
        ship_angle = 200  # Current position
        ship_x = px + orbit_radius * math.cos(math.radians(ship_angle))
        ship_y = py - orbit_radius * math.sin(math.radians(ship_angle))

        ship = mcrfpy.Circle(
            center=(ship_x, ship_y), radius=8,
            fill_color=mcrfpy.Color(255, 200, 100)
        )
        self.ui.append(ship)

        # Draw path: ship moves along orbit (free) to exit point
        # Arc from ship position to exit position
        orbit_arc = mcrfpy.Arc(
            center=(px, py), radius=orbit_radius,
            start_angle=-ship_angle, end_angle=-exit_angle,
            color=mcrfpy.Color(255, 255, 100),
            thickness=3
        )
        self.ui.append(orbit_arc)

        # Draw exit point
        exit_point = mcrfpy.Circle(
            center=(exit_x, exit_y), radius=6,
            fill_color=mcrfpy.Color(100, 255, 100)
        )
        self.ui.append(exit_point)

        # Draw line from exit to target
        exit_line = mcrfpy.Line(
            start=(exit_x, exit_y), end=(tx, ty),
            color=mcrfpy.Color(100, 255, 100),
            thickness=2
        )
        self.ui.append(exit_line)

        # Target
        target = mcrfpy.Circle(
            center=(tx, ty), radius=10,
            fill_color=mcrfpy.Color(255, 100, 100)
        )
        self.ui.append(target)

        # Labels
        self.add_label("Planet", px - 20, py + surface_radius + 5, (100, 150, 220))
        self.add_label("Ship", ship_x - 25, ship_y - 15, (255, 200, 100))
        self.add_label("Exit", exit_x + 10, exit_y - 10, (100, 255, 100))
        self.add_label("Target", tx - 15, ty + 15, (255, 100, 100))
        self.add_label(f"Exit angle: {exit_angle:.1f}°", 420, 555, (150, 150, 150))
        self.add_label("Yellow arc = free orbital movement", 550, 555, (255, 255, 100))
