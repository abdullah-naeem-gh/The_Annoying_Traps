import pygame
import math

class VerletRope:
    def __init__(self, anchor_pos, points, length):
        self.points = [pygame.Vector2(anchor_pos) for _ in range(points)]
        self.length = length
        self.anchor_pos = pygame.Vector2(anchor_pos)
        self.is_active = False
        self.retracting = False
        self.cycle_timer = 0
        self.cycle_period = 120  # Adjust for cycle timings
        self.max_angle = math.pi / 6
        self.thrust_speed = 0.2  # Speed of initial thrust
        self.retraction_speed = 0.9  # Speed of retraction
    
    def constrain_distance(self, point, anchor, distance):
        direction = point - anchor
        dist = direction.length()

        if dist > 0:
            normalized = direction / dist
            return anchor + normalized * distance
        return anchor

    def constrain_angle(self, current_point, previous_point, next_point, max_angle):
        prev_direction = previous_point - current_point
        next_direction = next_point - current_point

        prev_angle = math.atan2(prev_direction.y, prev_direction.x)
        next_angle = math.atan2(next_direction.y, next_direction.x)

        angle_diff = next_angle - prev_angle

        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi

        if abs(angle_diff) > max_angle:
            if angle_diff > 0:
                next_angle = prev_angle + max_angle
            else:
                next_angle = prev_angle - max_angle
            next_point = current_point + pygame.Vector2(math.cos(next_angle), math.sin(next_angle)) * self.length

        return next_point

    def update(self, mouse_pos, chain_end):
        if not self.is_active:
            if (chain_end - self.anchor_pos).length() <= self.length * len(self.points):
                self.is_active = True

        if self.is_active:
            self.cycle_timer = (self.cycle_timer + 1) % (self.cycle_period * 2)

            if self.cycle_timer < self.cycle_period:
                self.retracting = False
                # Adjust the initial thrust speed
                thrust_target = pygame.Vector2(mouse_pos)
                self.points[0] = self.points[0].lerp(thrust_target, self.thrust_speed)
            else:
                self.retracting = True
                # Slow and deliberate retraction speed
                retract_target = self.constrain_distance(
                    self.points[0], self.anchor_pos, self.length * len(self.points) * 0.8)
                self.points[0] = self.points[0].lerp(retract_target, self.retraction_speed)

            for i in range(1, len(self.points)):
                self.points[i] = self.constrain_distance(self.points[i], self.points[i - 1], self.length)

            self.points[-1] = self.anchor_pos
            for i in range(len(self.points) - 2, -1, -1):
                self.points[i] = self.constrain_distance(self.points[i], self.points[i + 1], self.length)
                if i > 0:
                    self.points[i] = self.constrain_angle(self.points[i], self.points[i - 1], self.points[i + 1], self.max_angle)

    def check_collision_with_chain(self, chain):
        for joint in chain.joints:
            for point in self.points:
                if (point - pygame.Vector2(joint)).length() < 5:
                    return True
        return False

    def draw(self, screen, color=(255, 0, 0)):
        if self.is_active:
            for i in range(len(self.points) - 1):
                pygame.draw.line(screen, color, self.points[i], self.points[i + 1], 5)
            pygame.draw.circle(screen, (0, 0, 0), (int(self.points[0].x), int(self.points[0].y)), 5)
        else:
            pygame.draw.circle(screen, color, (int(self.anchor_pos.x), int(self.anchor_pos.y)), 10)