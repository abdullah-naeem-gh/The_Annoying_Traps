import pygame
import math
import random

class BlueTentacle:
    def __init__(self, anchor_pos, points=5, segment_length=20):
        self.points = [pygame.Vector2(anchor_pos) for _ in range(points)]
        self.velocities = [pygame.Vector2(0, 0) for _ in range(points)]
        self.segment_length = segment_length
        self.total_length = segment_length * points
        self.anchor_pos = pygame.Vector2(anchor_pos)
        self.has_coin = False
        self.is_active = False

        # Behaviors and parameters
        self.state = "stalking"
        self.patience = random.randint(30, 90)
        self.patience_timer = 0
        self.strike_cooldown = 0
        self.time = 0
        self.wiggle_amplitudes = [random.uniform(0.2, 0.5) for _ in range(points)]
        self.wiggle_frequencies = [random.uniform(0.05, 0.1) for _ in range(points)]
        self.wiggle_phases = [random.uniform(0, math.pi * 2) for _ in range(points)]
        self.strike_speed = 1.2
        self.recovery_speed = 0.5
        self.stalk_speed = 0.08
        self.damping = 0.96
        self.spring_stiffness = 0.1
        self.gravity = pygame.Vector2(0, 0.15)

    def apply_idle_motion(self):
        self.time += 0.016  # Assume 60 FPS
        for i in range(len(self.points) - 1):
            base_pos = self.points[i + 1]
            angle = (self.time * self.wiggle_frequencies[i] + self.wiggle_phases[i])
            perpendicular = pygame.Vector2(-math.sin(angle), math.cos(angle))
            amplitude = self.wiggle_amplitudes[i] * (1 - i / len(self.points))
            wiggle_offset = perpendicular * amplitude * self.segment_length
            target_pos = base_pos + wiggle_offset
            self.velocities[i] += (target_pos - self.points[i]) * 0.1
            if random.random() < 0.05:
                random_force = pygame.Vector2(random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5))
                self.velocities[i] += random_force

    def update(self, chain, coin):
        current_head = self.points[0]
        coin_pos = coin.position

        if not self.is_active:
            if (pygame.Vector2(chain.joints[0]) - self.anchor_pos).length() <= self.total_length * 1.5:
                self.is_active = True

        if self.is_active:
            if not self.has_coin:
                direction_to_coin = coin_pos - self.anchor_pos
                if self.state == "stalking":
                    self.patience_timer += 1
                    # Calculate stalking position with wiggle
                    ideal_distance = self.total_length * 0.7
                    if direction_to_coin.length() > 0:
                        direction_to_coin.scale_to_length(ideal_distance)
                    stalk_pos = self.anchor_pos + direction_to_coin
                    # Add wiggle to stalking position
                    wiggle = math.sin(self.time * 2) * 5
                    perp = pygame.Vector2(-direction_to_coin.y, direction_to_coin.x)
                    if perp.length() > 0:
                        perp.scale_to_length(wiggle)
                    stalk_pos += perp
                    # Move toward stalk position
                    self.velocities[0] += (stalk_pos - current_head) * self.stalk_speed
                    # Check for strike
                    if (coin.collected and
                        self.patience_timer >= self.patience and
                        (coin_pos - current_head).length() < self.total_length):
                        self.state = "striking"
                        strike_dir = (coin_pos - current_head).normalize()
                        self.velocities[0] = strike_dir * 25
                        self.patience = random.randint(30, 90)
                        self.patience_timer = 0
                elif self.state == "striking":
                    to_coin = coin_pos - current_head
                    if to_coin.length() > 0:
                        strike_direction = to_coin.normalize()
                        self.velocities[0] += strike_direction * self.strike_speed
                    # Check if we reached the coin
                    if to_coin.length() < 20:
                        self.has_coin = True
                        self.state = "recovering"
                        coin.collected = False
                        self.strike_cooldown = random.randint(40, 60)
                    elif (current_head - self.anchor_pos).length() >= self.total_length * 0.95:
                        self.state = "recovering"
                        self.strike_cooldown = random.randint(20, 40)
                    
            if self.state != "striking":
                self.apply_idle_motion()
                
            if self.state == "recovering":
                self.strike_cooldown -= 1
                if self.strike_cooldown <= 0:
                    self.state = "stalking"
            # Update coin position if we have it
            if self.has_coin:
                coin.position = self.points[0]

        # Apply physics
        for i in range(len(self.points) - 1):
            if i != len(self.points) - 1:
                self.velocities[i] *= self.damping
            self.points[i] += self.velocities[i]

        # Apply constraints
        for _ in range(3):
            for i in range(1, len(self.points)):
                self.points[i] = self.constrain_distance(self.points[i], self.points[i - 1], self.segment_length)
            self.points[-1] = self.anchor_pos
            for i in range(len(self.points) - 2, -1, -1):
                self.points[i] = self.constrain_distance(self.points[i], self.points[i + 1], self.segment_length)

    def constrain_distance(self, point, anchor, distance):
        direction = point - anchor
        dist = direction.length()
        if dist > distance:
            normalized = direction / dist
            return anchor + normalized * distance
        return point

    def draw(self, screen, camera):
        if self.is_active:
            color = (0, 0, 255)  # Base blue color
            for i in range(len(self.points) - 1):
                start_pos = camera.apply(self.points[i])
                end_pos = camera.apply(self.points[i + 1])
                pygame.draw.line(screen, color, start_pos, end_pos, 5)
            head_color = {
                "stalking": (0, 0, 150),
                "striking": (0, 0, 255),
                "recovering": (0, 0, 100)
            }.get(self.state, (0, 0, 100))
            pygame.draw.circle(screen, head_color, camera.apply(self.points[0]), 5)
            if self.has_coin:
                pygame.draw.circle(screen, (255, 165, 0), camera.apply(self.points[0]), 8)
        else:
            pygame.draw.circle(screen, (0, 0, 255), camera.apply(self.anchor_pos), 10)