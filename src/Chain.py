import pygame
import math

class Chain:
    def __init__(self, start_pos, points, length, max_angle):
        self.joints = [(start_pos[0] + i * length, start_pos[1]) for i in range(points)]
        self.angles = [0] * points
        self.length = length
        self.max_angle = max_angle
        # More points for smoother appearance
        self.circle_radii = [20 - i * (15 / points) for i in range(points)]
        # Store previous positions for smoothing
        self.prev_joints = self.joints.copy()
        
    def bezier_point(self, points, t):
        """Calculate point along a Bezier curve."""
        if len(points) == 1:
            return points[0]
        new_points = []
        for i in range(len(points) - 1):
            x = points[i][0] * (1 - t) + points[i + 1][0] * t
            y = points[i][1] * (1 - t) + points[i + 1][1] * t
            new_points.append((x, y))
        return self.bezier_point(new_points, t)

    def interpolate_points(self, points, num_segments=10):
        """Create smooth interpolation between points."""
        if len(points) < 3:
            return points
        
        smooth_points = []
        
        # Add first point
        smooth_points.append(points[0])
        
        # Process each segment
        for i in range(len(points) - 2):
            p0 = points[max(i - 1, 0)]
            p1 = points[i]
            p2 = points[i + 1]
            p3 = points[min(i + 2, len(points) - 1)]
            
            # Generate points along the curve
            for t in range(num_segments):
                t = t / num_segments
                # Catmull-Rom spline calculation
                t2 = t * t
                t3 = t2 * t
                
                x = ((-t3 + 2*t2 - t) * p0[0] +
                     (3*t3 - 5*t2 + 2) * p1[0] +
                     (-3*t3 + 4*t2 + t) * p2[0] +
                     (t3 - t2) * p3[0]) / 2
                
                y = ((-t3 + 2*t2 - t) * p0[1] +
                     (3*t3 - 5*t2 + 2) * p1[1] +
                     (-3*t3 + 4*t2 + t) * p2[1] +
                     (t3 - t2) * p3[1]) / 2
                
                smooth_points.append((x, y))
        
        # Add last point
        smooth_points.append(points[-1])
        return smooth_points

    def smooth_joints(self):
        """Apply smoothing to joint positions."""
        smoothing_factor = 0.3
        for i in range(len(self.joints)):
            self.joints[i] = (
                self.joints[i][0] * (1 - smoothing_factor) + self.prev_joints[i][0] * smoothing_factor,
                self.joints[i][1] * (1 - smoothing_factor) + self.prev_joints[i][1] * smoothing_factor
            )
        self.prev_joints = self.joints.copy()

    def get_body_points(self):
        """Get smoothed left and right points for drawing the eel's body."""
        left_points = []
        right_points = []
        
        # Create control points for the body curve
        for i in range(len(self.joints)):
            if i < len(self.joints) - 1:
                dx = self.joints[i+1][0] - self.joints[i][0]
                dy = self.joints[i+1][1] - self.joints[i][1]
                angle = math.atan2(dy, dx)
            else:
                angle = self.angles[i]
                
            radius = self.circle_radii[i]
            # Add some sinusoidal movement for more organic feel
            wave_offset = math.sin(pygame.time.get_ticks() * 0.01 + i * 0.5) * (radius * 0.2)
            
            left_x = self.joints[i][0] + (radius + wave_offset) * math.cos(angle + math.pi/2)
            left_y = self.joints[i][1] + (radius + wave_offset) * math.sin(angle + math.pi/2)
            right_x = self.joints[i][0] + (radius - wave_offset) * math.cos(angle - math.pi/2)
            right_y = self.joints[i][1] + (radius - wave_offset) * math.sin(angle - math.pi/2)
            
            left_points.append((left_x, left_y))
            right_points.append((right_x, right_y))
        
        # Apply interpolation for smoother curves
        left_points = self.interpolate_points(left_points, 15)
        right_points = self.interpolate_points(right_points, 15)
        
        return left_points, right_points

    def draw(self, screen, camera, color=(0, 150, 150)):
        # Apply smoothing to joint positions
        self.smooth_joints()
        
        # Get smoothed body points
        left_points, right_points = self.get_body_points()
        
        # Convert points to screen space
        left_points = [camera.apply(pygame.Vector2(p)) for p in left_points]
        right_points = [camera.apply(pygame.Vector2(p)) for p in right_points]
        
        # Draw the main body
        points = left_points + list(reversed(right_points))
        if len(points) > 2:
            # Draw body with gradient effect
            pygame.draw.polygon(screen, color, points)
            pygame.draw.polygon(screen, (0, 130, 130), points, 2)  # Darker outline
        
        # Draw smoother head
        head_pos = camera.apply(pygame.Vector2(self.joints[0]))
        head_radius = int(self.circle_radii[0])
        
        # Draw head with gradient effect
        pygame.draw.circle(screen, (0, 170, 170), head_pos, head_radius)
        pygame.draw.circle(screen, (0, 190, 190), head_pos, head_radius - 4)
        
        # Draw more detailed eye
        eye_offset = pygame.Vector2(head_radius * 0.5, -head_radius * 0.3)
        eye_pos = head_pos + eye_offset.rotate_rad(self.angles[0])
        pygame.draw.circle(screen, (255, 255, 255), eye_pos, head_radius * 0.25)
        pygame.draw.circle(screen, (0, 0, 0), eye_pos, head_radius * 0.15)
        # Add eye highlight
        highlight_pos = eye_pos + pygame.Vector2(-2, -2)
        pygame.draw.circle(screen, (255, 255, 255), highlight_pos, head_radius * 0.05)

    # [Previous methods remain unchanged: constrain_distance, constrain_angle, update]
    def constrain_distance(self, point, anchor):
        direction = (point[0] - anchor[0], point[1] - anchor[1])
        dist = math.sqrt(direction[0] ** 2 + direction[1] ** 2)
        if dist > 0:
            normalized = (direction[0] / dist, direction[1] / dist)
            return (anchor[0] + normalized[0] * self.length, anchor[1] + normalized[1] * self.length)
        return anchor

    def constrain_angle(self, current, previous, previous_angle):
        offset = (current[0] - previous[0], current[1] - previous[1])
        current_angle = math.atan2(offset[1], offset[0])
        angle_diff = current_angle - previous_angle
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi
        if angle_diff > self.max_angle:
            current_angle = previous_angle + self.max_angle
        elif angle_diff < -self.max_angle:
            current_angle = previous_angle - self.max_angle
        new_position = (
            previous[0] + math.cos(current_angle) * self.length,
            previous[1] + math.sin(current_angle) * self.length
        )
        return new_position, current_angle

    def update(self, mouse_pos):
        self.joints[0] = mouse_pos
        self.angles[0] = math.atan2(self.joints[1][1] - mouse_pos[1], self.joints[1][0] - mouse_pos[0])
        for i in range(1, len(self.joints)):
            next_position = self.constrain_distance(self.joints[i], self.joints[i-1])
            self.joints[i], self.angles[i] = self.constrain_angle(next_position, self.joints[i-1], self.angles[i-1])