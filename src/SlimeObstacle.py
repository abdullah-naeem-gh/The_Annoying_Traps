import pygame
import math
from pygame import gfxdraw

class SlimeObstacle:
    def __init__(self, position, radius, points):
        self.position = pygame.Vector2(position)
        self.radius = radius
        self.points = points
        self.area = math.pi * radius * radius
        self.circumference = 2 * math.pi * radius
        self.segment_length = (self.circumference / points) * 0.95
        self.current_points = []
        self.old_points = []
        for i in range(points):
            angle = math.radians(360 / points * i)
            point = pygame.Vector2(
                position[0] + radius * math.cos(angle),
                position[1] + radius * math.sin(angle)
            )
            self.current_points.append(point)
            self.old_points.append(point.copy())
        self.time = 0
        self.pulse_strength = 3.0
        self.wobble_speed = 2.0

    def update(self, delta_time):
        self.time += delta_time * self.wobble_speed
        for i in range(self.points):
            self.old_points[i] = self.current_points[i].copy()
            angle = 360 / self.points * i
            wobble = math.sin(self.time + math.radians(angle)) * self.pulse_strength
            direction = (self.current_points[i] - self.position).normalize()
            self.current_points[i] += direction * wobble

        for _ in range(20):
            for i in range(self.points):
                next_i = (i + 1) % self.points
                current = self.current_points[i]
                next_point = self.current_points[next_i]
                to_next = next_point - current
                current_distance = to_next.length()
                if current_distance > 0:
                    correction = (current_distance - self.segment_length) / current_distance
                    offset = to_next * correction * 0.5
                    self.current_points[i] += offset
                    self.current_points[next_i] -= offset
                to_center = self.position - self.current_points[i]
                distance = to_center.length()
                if distance > self.radius:
                    self.current_points[i] += to_center * 0.1

    def draw(self, screen, camera):
        if len(self.current_points) < 3:
            return

        surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)

        points = [camera.apply(p) for p in self.current_points]
        gfxdraw.filled_polygon(surface, [(int(p.x), int(p.y)) for p in points], (0, 0, 0, 180))
        gfxdraw.aapolygon(surface, [(int(p.x), int(p.y)) for p in points], (0, 0, 0, 255))

        highlight_points = [(p.x - 5, p.y - 5) for p in self.current_points[:len(self.current_points)//3]]
        if len(highlight_points) > 2:
            gfxdraw.aapolygon(surface, [(int(p[0]), int(p[1])) for p in highlight_points], (255, 255, 255, 100))

        screen.blit(surface, (0, 0))

    def check_collision(self, chain):
        for joint in chain.joints:
            joint_pos = pygame.Vector2(joint)
            for i in range(len(self.current_points)):
                p1 = self.current_points[i]
                p2 = self.current_points[(i + 1) % len(self.current_points)]
                if self.point_to_line_distance(joint_pos, p1, p2) < 15:
                    return True
        return False

    def point_to_line_distance(self, point, line_start, line_end):
        line_vec = line_end - line_start
        point_vec = point - line_start
        line_length = line_vec.length()
        if line_length == 0:
            return point_vec.length()
        t = max(0, min(1, point_vec.dot(line_vec) / (line_length * line_length)))
        projection = line_start + line_vec * t
        return (point - projection).length()