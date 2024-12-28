import pygame
import math
import random

class VerletRope:
    def __init__(self, anchor_pos, points, segment_length):
        self.points = [pygame.Vector2(anchor_pos) for _ in range(points)]
        self.velocities = [pygame.Vector2(0, 0) for _ in range(points)]
        self.segment_length = segment_length
        self.total_length = segment_length * points
        self.anchor_pos = pygame.Vector2(anchor_pos)
        self.is_active = False
        # Behavior states
        self.state = "stalking"
        self.patience = random.randint(30, 90)
        self.patience_timer = 0
        self.strike_cooldown = 0
        self.missed_strikes = 0
        # Idle animation parameters
        self.time = 0
        self.wiggle_amplitudes = [random.uniform(0.2, 0.5) for _ in range(points)]
        self.wiggle_frequencies = [random.uniform(0.05, 0.1) for _ in range(points)]
        self.wiggle_phases = [random.uniform(0, math.pi * 2) for _ in range(points)]
        # Movement parameters
        self.strike_speed = 1.2
        self.recovery_speed = 0.15
        self.stalk_speed = 0.08
        # Physics parameters
        self.damping = 0.96
        self.spring_stiffness = 0.2
        self.gravity = pygame.Vector2(0, 0.15)

    def apply_idle_motion(self):
        self.time += 0.016  # Assuming 60 FPS
        for i in range(len(self.points) - 1):  # Don't move anchor
            # Calculate base position relative to previous point
            base_pos = self.points[i + 1]
            # Calculate wiggle offset
            angle = (self.time * self.wiggle_frequencies[i] + self.wiggle_phases[i])
            perpendicular = pygame.Vector2(-math.sin(angle), math.cos(angle))
            # Amplitude decreases along the rope
            amplitude = self.wiggle_amplitudes[i] * (1 - i / len(self.points))
            # Apply wiggle motion
            wiggle_offset = perpendicular * amplitude * self.segment_length
            target_pos = base_pos + wiggle_offset
            # Smoothly move toward target position
            self.velocities[i] += (target_pos - self.points[i]) * 0.1
            # Add some random variation
            if random.random() < 0.05:
                random_force = pygame.Vector2(
                    random.uniform(-0.5, 0.5),
                    random.uniform(-0.5, 0.5)
                )
                self.velocities[i] += random_force

    def update(self, mouse_pos, chain_end):
        if not self.is_active:
            if (chain_end - self.anchor_pos).length() <= self.total_length:
                self.is_active = True
        if self.is_active:
            # Apply idle wiggle motion when not striking
            if self.state != "striking":
                self.apply_idle_motion()
            current_head = self.points[0]
            mouse_vec = pygame.Vector2(mouse_pos)
            direction_to_mouse = mouse_vec - self.anchor_pos
            if self.state == "stalking":
                self.patience_timer += 1
                # Calculate stalking position with wiggle
                ideal_distance = self.total_length * 0.7
                if direction_to_mouse.length() > 0:
                    direction_to_mouse.scale_to_length(ideal_distance)
                stalk_pos = self.anchor_pos + direction_to_mouse
                # Add wiggle to stalking position
                wiggle = math.sin(self.time * 2) * 5
                perp = pygame.Vector2(-direction_to_mouse.y, direction_to_mouse.x)
                if perp.length() > 0:
                    perp.scale_to_length(wiggle)
                stalk_pos += perp
                # Move toward stalk position
                self.velocities[0] += (stalk_pos - current_head) * self.stalk_speed
                # Check for strike
                dist_to_target = (mouse_vec - current_head).length()
                if self.patience_timer >= self.patience and dist_to_target < self.total_length:
                    self.state = "striking"
                    strike_dir = (mouse_vec - current_head).normalize()
                    self.velocities[0] = strike_dir * 25
                    self.patience = random.randint(30, 90)
                    self.patience_timer = 0
            elif self.state == "striking":
                to_target = mouse_vec - current_head
                if to_target.length() > 0:
                    strike_direction = to_target.normalize()
                    self.velocities[0] += strike_direction * self.strike_speed
                if to_target.length() < 20 or (current_head - self.anchor_pos).length() >= self.total_length * 0.95:
                    self.state = "recovering"
                    self.strike_cooldown = random.randint(20, 40)
            elif self.state == "recovering":
                # Return to wiggly rest position
                self.strike_cooldown -= 1
                if self.strike_cooldown <= 0:
                    self.state = "stalking"

            # Apply physics
            for i in range(len(self.points) - 1):
                if i != len(self.points) - 1:
                    self.velocities[i] *= self.damping
                self.points[i] += self.velocities[i]

            # Apply constraints
            for _ in range(3):
                for i in range(1, len(self.points)):
                    self.points[i] = self.constrain_distance(
                        self.points[i],
                        self.points[i - 1],
                        self.segment_length
                    )
                self.points[-1] = self.anchor_pos
                for i in range(len(self.points) - 2, -1, -1):
                    self.points[i] = self.constrain_distance(
                        self.points[i],
                        self.points[i + 1],
                        self.segment_length
                    )

    def constrain_distance(self, point, anchor, distance):
        direction = point - anchor
        dist = direction.length()
        if dist > distance:
            normalized = direction / dist
            return anchor + normalized * distance
        return point

    def check_collision_with_chain(self, chain):
        for joint in chain.joints:
            for point in self.points:
                if (point - pygame.Vector2(joint)).length() < 5:
                    return True
        return False

    def draw(self, screen, camera, color=(255, 0, 0)):
        if self.is_active:
            for i in range(len(self.points) - 1):
                start_pos = camera.apply(self.points[i])
                end_pos = camera.apply(self.points[i + 1])
                pygame.draw.line(screen, color, start_pos, end_pos, 5)
            head_color = {
                "stalking": (150, 0, 0),
                "striking": (255, 0, 0),
                "recovering": (100, 0, 0)
            }.get(self.state, (0, 0, 0))
            pygame.draw.circle(screen, head_color, camera.apply(self.points[0]), 5)
        else:
            pygame.draw.circle(screen, color, camera.apply(self.anchor_pos), 10)