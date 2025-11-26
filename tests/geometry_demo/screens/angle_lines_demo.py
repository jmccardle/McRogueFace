"""Angle calculation demonstration with Line elements."""
import mcrfpy
import math
from .base import (GeometryDemoScreen, screen_angle_between, angle_difference,
                   normalize_angle, distance, SCREEN_WIDTH, SCREEN_HEIGHT)


class AngleLinesDemo(GeometryDemoScreen):
    """Demonstrate angle calculations between points using Line elements."""

    name = "Angle Calculations"
    description = "Visualizing angles between grid positions"

    def setup(self):
        self.add_title("Angle Calculations & Line Elements")
        self.add_description("Computing headings, deviations, and opposite angles for pathfinding")

        margin = 30
        frame_gap = 20
        top_area = 80
        bottom_margin = 30

        # Calculate frame dimensions for 2x2 layout
        frame_width = (SCREEN_WIDTH - 2 * margin - frame_gap) // 2
        available_height = SCREEN_HEIGHT - top_area - bottom_margin - frame_gap
        frame_height = available_height // 2

        # Demo 1: Basic angle between two points (top-left)
        self._demo_basic_angle(margin, top_area, frame_width, frame_height)

        # Demo 2: Angle deviation (top-right)
        self._demo_angle_deviation(margin + frame_width + frame_gap, top_area,
                                   frame_width, frame_height)

        # Demo 3: Multiple waypoints (bottom-left)
        self._demo_waypoint_viability(margin, top_area + frame_height + frame_gap,
                                      frame_width, frame_height)

        # Demo 4: Orbit exit heading (bottom-right)
        self._demo_orbit_exit(margin + frame_width + frame_gap, top_area + frame_height + frame_gap,
                              frame_width, frame_height)

    def _demo_basic_angle(self, fx, fy, fw, fh):
        """Show angle from point A to point B."""
        bg = mcrfpy.Frame(pos=(fx, fy), size=(fw, fh))
        bg.fill_color = mcrfpy.Color(15, 15, 25)
        bg.outline = 1
        bg.outline_color = mcrfpy.Color(60, 60, 100)
        self.ui.append(bg)

        self.add_label("Basic Angle Calculation", fx + 10, fy + 5, (255, 200, 100))

        # Point A (origin) - lower left area of frame
        ax, ay = fx + 80, fy + fh - 80
        # Point B (target) - upper right area of frame
        bx, by = fx + fw - 100, fy + 100

        # Calculate angle using screen coordinates
        angle = screen_angle_between((ax, ay), (bx, by))
        dist = distance((ax, ay), (bx, by))

        # Draw the line A to B (green)
        line_ab = mcrfpy.Line(
            start=(ax, ay), end=(bx, by),
            color=mcrfpy.Color(100, 255, 100),
            thickness=3
        )
        self.ui.append(line_ab)

        # Draw reference line (east from A) in gray
        ref_length = 120
        line_ref = mcrfpy.Line(
            start=(ax, ay), end=(ax + ref_length, ay),
            color=mcrfpy.Color(100, 100, 100),
            thickness=1
        )
        self.ui.append(line_ref)

        # Draw arc showing the angle (from reference to target line)
        # Arc goes from 0 degrees (east) to the calculated angle
        arc = mcrfpy.Arc(
            center=(ax, ay), radius=50,
            start_angle=0, end_angle=angle,
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
        self.add_label("A", ax - 20, ay + 5, (255, 100, 100))
        self.add_label("B", bx + 12, by - 5, (100, 255, 100))
        self.add_label(f"Angle: {angle:.1f} deg", fx + 10, fy + fh - 45, (255, 255, 100))
        self.add_label(f"Distance: {dist:.1f}", fx + 10, fy + fh - 25, (150, 150, 150))

    def _demo_angle_deviation(self, fx, fy, fw, fh):
        """Show angle deviation when considering a waypoint."""
        bg = mcrfpy.Frame(pos=(fx, fy), size=(fw, fh))
        bg.fill_color = mcrfpy.Color(15, 15, 25)
        bg.outline = 1
        bg.outline_color = mcrfpy.Color(60, 60, 100)
        self.ui.append(bg)

        self.add_label("Waypoint Deviation", fx + 10, fy + 5, (255, 200, 100))
        self.add_label("Is planet C useful from A to B?", fx + 10, fy + 25, (150, 150, 150))

        # Ship at A, target at B, potential waypoint C
        ax, ay = fx + 60, fy + fh - 100
        bx, by = fx + fw - 60, fy + fh - 60
        cx, cy = fx + fw // 2, fy + 100

        # Calculate angles using screen coordinates
        angle_to_target = screen_angle_between((ax, ay), (bx, by))
        angle_to_waypoint = screen_angle_between((ax, ay), (cx, cy))
        deviation = abs(angle_difference(angle_to_target, angle_to_waypoint))

        # Draw line A to B (direct path - green)
        line_ab = mcrfpy.Line(
            start=(ax, ay), end=(bx, by),
            color=mcrfpy.Color(100, 255, 100),
            thickness=2
        )
        self.ui.append(line_ab)

        # Draw line A to C (waypoint path)
        viable = deviation <= 45
        waypoint_color = (255, 255, 100) if viable else (255, 100, 100)
        line_ac = mcrfpy.Line(
            start=(ax, ay), end=(cx, cy),
            color=mcrfpy.Color(*waypoint_color),
            thickness=2
        )
        self.ui.append(line_ac)

        # Draw arc showing the deviation angle between the two directions
        # Arc should go from angle_to_target to angle_to_waypoint
        start_ang = min(angle_to_target, angle_to_waypoint)
        end_ang = max(angle_to_target, angle_to_waypoint)
        # If the arc would be > 180, we need to go the other way
        if end_ang - start_ang > 180:
            start_ang, end_ang = end_ang, start_ang + 360

        arc = mcrfpy.Arc(
            center=(ax, ay), radius=50,
            start_angle=start_ang, end_angle=end_ang,
            color=mcrfpy.Color(*waypoint_color),
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

        # Labels - positioned to avoid overlap
        self.add_label("A (ship)", ax - 15, ay + 15, (255, 100, 100))
        self.add_label("B (target)", bx - 30, by + 15, (100, 255, 100))
        self.add_label("C (planet)", cx + 15, cy - 10, (150, 150, 255))

        # Status at bottom
        self.add_label(f"Deviation: {deviation:.1f} deg", fx + 10, fy + fh - 45, waypoint_color)
        status = "VIABLE (<45 deg)" if viable else "NOT VIABLE (>45 deg)"
        self.add_label(status, fx + 200, fy + fh - 45, waypoint_color)

    def _demo_waypoint_viability(self, fx, fy, fw, fh):
        """Show multiple potential waypoints with viability indicators."""
        bg = mcrfpy.Frame(pos=(fx, fy), size=(fw, fh))
        bg.fill_color = mcrfpy.Color(15, 15, 25)
        bg.outline = 1
        bg.outline_color = mcrfpy.Color(60, 60, 100)
        self.ui.append(bg)

        self.add_label("Multiple Waypoint Analysis", fx + 10, fy + 5, (255, 200, 100))

        # Ship and target positions
        ax, ay = fx + 60, fy + fh - 80
        bx, by = fx + fw - 80, fy + fh // 2

        angle_to_target = screen_angle_between((ax, ay), (bx, by))

        # Draw direct path
        line_ab = mcrfpy.Line(
            start=(ax, ay), end=(bx, by),
            color=mcrfpy.Color(100, 255, 100, 128),
            thickness=2
        )
        self.ui.append(line_ab)

        # Potential waypoints at various positions
        waypoints = [
            (fx + 180, fy + 80, "W1"),   # Upper area
            (fx + 280, fy + fh - 60, "W2"),  # Right of path
            (fx + 80, fy + fh - 150, "W3"),  # Left/behind
            (fx + fw - 150, fy + fh // 2 - 30, "W4"),  # Near target
        ]

        threshold = 45
        for wx, wy, label in waypoints:
            angle_to_wp = screen_angle_between((ax, ay), (wx, wy))
            deviation = abs(angle_difference(angle_to_target, angle_to_wp))
            viable = deviation <= threshold

            # Line to waypoint
            color_tuple = (100, 255, 100) if viable else (255, 100, 100)
            line = mcrfpy.Line(
                start=(ax, ay), end=(wx, wy),
                color=mcrfpy.Color(*color_tuple),
                thickness=1
            )
            self.ui.append(line)

            # Waypoint circle
            wp_circle = mcrfpy.Circle(
                center=(wx, wy), radius=15,
                fill_color=mcrfpy.Color(80, 80, 120),
                outline_color=mcrfpy.Color(*color_tuple),
                outline=2
            )
            self.ui.append(wp_circle)

            self.add_label(f"{label}:{deviation:.0f}", wx + 18, wy - 8, color_tuple)

        # Ship and target markers
        ship = mcrfpy.Circle(center=(ax, ay), radius=8,
                            fill_color=mcrfpy.Color(255, 200, 100))
        target = mcrfpy.Circle(center=(bx, by), radius=8,
                              fill_color=mcrfpy.Color(100, 255, 100))
        self.ui.append(ship)
        self.ui.append(target)

        self.add_label("Ship", ax - 10, ay + 12, (255, 200, 100))
        self.add_label("Target", bx - 20, by + 12, (100, 255, 100))
        self.add_label(f"Threshold: {threshold} deg", fx + 10, fy + fh - 25, (150, 150, 150))

    def _demo_orbit_exit(self, fx, fy, fw, fh):
        """Show optimal orbit exit heading toward target."""
        bg = mcrfpy.Frame(pos=(fx, fy), size=(fw, fh))
        bg.fill_color = mcrfpy.Color(15, 15, 25)
        bg.outline = 1
        bg.outline_color = mcrfpy.Color(60, 60, 100)
        self.ui.append(bg)

        self.add_label("Orbit Exit Heading", fx + 10, fy + 5, (255, 200, 100))
        self.add_label("Ship repositions FREE in orbit", fx + 10, fy + 25, (150, 150, 150))

        # Planet center and orbit
        px, py = fx + fw // 3, fy + fh // 2
        orbit_radius = 70
        surface_radius = 30

        # Target position
        tx, ty = fx + fw - 80, fy + 100

        # Calculate optimal exit angle (toward target in screen coords)
        exit_angle = screen_angle_between((px, py), (tx, ty))
        exit_x = px + orbit_radius * math.cos(math.radians(exit_angle))
        exit_y = py - orbit_radius * math.sin(math.radians(exit_angle))  # Negate for screen Y

        # Ship's current position on orbit (arbitrary starting position)
        ship_angle = exit_angle + 120  # 120 degrees away from exit
        ship_x = px + orbit_radius * math.cos(math.radians(ship_angle))
        ship_y = py - orbit_radius * math.sin(math.radians(ship_angle))

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

        # Draw arc showing orbital movement from ship to exit (FREE movement)
        # Arc goes from ship_angle to exit_angle
        start_ang = min(ship_angle, exit_angle)
        end_ang = max(ship_angle, exit_angle)
        orbit_arc = mcrfpy.Arc(
            center=(px, py), radius=orbit_radius,
            start_angle=start_ang, end_angle=end_ang,
            color=mcrfpy.Color(255, 255, 100),
            thickness=4
        )
        self.ui.append(orbit_arc)

        # Draw ship
        ship = mcrfpy.Circle(
            center=(ship_x, ship_y), radius=8,
            fill_color=mcrfpy.Color(255, 200, 100)
        )
        self.ui.append(ship)

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

        # Labels - positioned to avoid overlap
        self.add_label("Planet", px - 20, py + surface_radius + 5, (100, 150, 220))
        self.add_label("Ship", ship_x - 30, ship_y - 15, (255, 200, 100))
        self.add_label("Exit", exit_x + 10, exit_y - 15, (100, 255, 100))
        self.add_label("Target", tx - 20, ty + 15, (255, 100, 100))

        # Info at bottom
        self.add_label(f"Exit angle: {exit_angle:.1f} deg", fx + 10, fy + fh - 45, (150, 150, 150))
        self.add_label("Yellow = FREE orbital move", fx + 200, fy + fh - 45, (255, 255, 100))
