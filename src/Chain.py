import pygame
import math

class Chain:
    def __init__(self, start_pos, points, length, max_angle):
        self.joints = [(start_pos[0] + i * length, start_pos[1]) for i in range(points)]
        self.angles = [0] * points
        self.length = length
        self.max_angle = max_angle

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

    def draw(self, screen, camera, color=(0, 0, 0)):
        for i in range(len(self.joints) - 1):
            start_pos = camera.apply(pygame.Vector2(self.joints[i]))
            end_pos = camera.apply(pygame.Vector2(self.joints[i + 1]))
            pygame.draw.line(screen, color, start_pos, end_pos, 3)
        for joint in self.joints:
            pygame.draw.circle(screen, color, camera.apply(pygame.Vector2(joint)), 5)