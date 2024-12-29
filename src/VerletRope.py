import pygame
import math
import random

class VerletRope:
    # Class-level cache for visual parameters
    visual_cache = {}
    cache_counter = 0

    def __init__(self, anchor_pos, points, segment_length):
        # Generate a unique ID for this rope instance
        self.rope_id = VerletRope.cache_counter
        VerletRope.cache_counter += 1
        
        # Physics and behavior parameters (reset on retry)
        self.reset_state(anchor_pos, points, segment_length)
        
        # Only initialize visual parameters if not in cache
        if self.rope_id not in VerletRope.visual_cache:
            self.initialize_visuals(points, segment_length)
        
    def reset_state(self, anchor_pos, points, segment_length):
        """Reset physics and behavior state (called on retry)"""
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
        
        # Movement parameters
        self.strike_speed = 1.2
        self.recovery_speed = 0.15
        self.stalk_speed = 0.08
        
        # Physics parameters
        self.damping = 0.96
        self.spring_stiffness = 0.2
        self.gravity = pygame.Vector2(0, 0.15)
        
        # Animation time (reset but keep using cached visual parameters)
        self.time = 0

    def initialize_visuals(self, points, segment_length):
        """Initialize visual parameters (only called once)"""
        visual_params = {
            'thickness': [segment_length * 0.7 * (1 - i/points) for i in range(points)],
            'hair_lengths': [random.uniform(5, 15) for _ in range(points * 3)],
            'hair_angles': [random.uniform(0, math.pi * 2) for _ in range(points * 3)],
            'hair_waves': [random.uniform(0.05, 0.15) for _ in range(points * 3)],
            'texture_offsets': [(random.uniform(-2, 2), random.uniform(-2, 2)) 
                               for _ in range(points * 2)],
            'bulge_locations': [random.randint(0, points-1) for _ in range(3)],
            'bulge_sizes': [random.uniform(1.2, 1.5) for _ in range(3)],
            'wiggle_amplitudes': [random.uniform(0.2, 0.5) for _ in range(points)],
            'wiggle_frequencies': [random.uniform(0.05, 0.1) for _ in range(points)],
            'wiggle_phases': [random.uniform(0, math.pi * 2) for _ in range(points)],
            'base_color': (random.randint(20, 40), random.randint(80, 120), random.randint(20, 40)),
            'hair_color': (random.randint(30, 50), random.randint(90, 130), random.randint(30, 50)),
            'highlight_color': (random.randint(40, 60), random.randint(100, 140), random.randint(40, 60))
        }
        
        # Store in class cache
        VerletRope.visual_cache[self.rope_id] = visual_params

    @property
    def visuals(self):
        """Get visual parameters from cache"""
        return VerletRope.visual_cache[self.rope_id]

    def get_perpendicular(self, point1, point2, thickness):
        """Get perpendicular points for thickness."""
        direction = point2 - point1
        if direction.length() == 0:
            return None
        perp = pygame.Vector2(-direction.y, direction.x)
        perp.scale_to_length(thickness)
        return perp

    def draw_organic_segment(self, screen, camera, p1, p2, thickness1, thickness2):
        """Draw a single organic segment with texture."""
        if thickness1 <= 0 or thickness2 <= 0:
            return

        perp1 = self.get_perpendicular(p1, p2, thickness1)
        perp2 = self.get_perpendicular(p1, p2, thickness2)
        if perp1 is None or perp2 is None:
            return
        
        time_offset = self.time * 0.1
        points = [
            camera.apply(p1 + perp1),
            camera.apply(p2 + perp2),
            camera.apply(p2 - perp2),
            camera.apply(p1 - perp1)
        ]

        pygame.draw.polygon(screen, self.visuals['base_color'], points)

        for _ in range(3):
            offset = random.uniform(-2, 2)
            texture_points = [
                (
                    p[0] + math.sin(time_offset + i) * offset,
                    p[1] + math.cos(time_offset + i) * offset
                ) for i, p in enumerate(points)
            ]
            pygame.draw.polygon(screen, self.visuals['highlight_color'], texture_points, 1)

    def draw_hairs(self, screen, camera, point, angle, thickness):
        """Draw organic-looking hairs/tendrils."""
        num_hairs = 3
        for i in range(num_hairs):
            base_angle = angle + random.uniform(-math.pi/4, math.pi/4)
            hair_length = thickness * random.uniform(1.5, 2.5)
            wave = math.sin(self.time * self.visuals['hair_waves'][i] + i)
            
            points = []
            steps = 5
            for step in range(steps):
                t = step / (steps - 1)
                offset_angle = base_angle + wave * t * math.pi/4
                x = point.x + math.cos(offset_angle) * hair_length * t
                y = point.y + math.sin(offset_angle) * hair_length * t
                points.append(camera.apply(pygame.Vector2(x, y)))
            
            if len(points) >= 2:
                pygame.draw.lines(screen, self.visuals['hair_color'], False, points, max(1, int(thickness * 0.15)))

    def draw_bulge(self, screen, camera, center, radius):
        """Draw organic bulge/growth."""
        pos = camera.apply(center)
        pygame.draw.circle(screen, self.visuals['highlight_color'], pos, radius)
        
        for _ in range(3):
            offset = random.uniform(-2, 2)
            pygame.draw.circle(screen, self.visuals['base_color'],
                (pos[0] + offset, pos[1] + offset),
                radius * random.uniform(0.5, 0.8))

    def draw(self, screen, camera):
        if not self.is_active:
            pygame.draw.circle(screen, self.visuals['base_color'], 
                             camera.apply(self.anchor_pos), 10)
            return

        self.time += 0.016

        for i in range(len(self.points) - 1):
            p1, p2 = self.points[i], self.points[i + 1]
            
            thickness1 = self.visuals['thickness'][i] * (1 + math.sin(self.time + i) * 0.1)
            thickness2 = self.visuals['thickness'][i + 1] * (1 + math.sin(self.time + i + 1) * 0.1)
            
            if i in self.visuals['bulge_locations']:
                bulge_index = self.visuals['bulge_locations'].index(i)
                thickness1 *= self.visuals['bulge_sizes'][bulge_index]
                thickness2 *= self.visuals['bulge_sizes'][bulge_index]
            
            self.draw_organic_segment(screen, camera, p1, p2, thickness1, thickness2)
            
            if i % 2 == 0:
                angle = math.atan2(p2.y - p1.y, p2.x - p1.x)
                self.draw_hairs(screen, camera, p1, angle, thickness1)
            
            if i in self.visuals['bulge_locations']:
                bulge_pos = (p1 + p2) * 0.5
                self.draw_bulge(screen, camera, bulge_pos, thickness1 * 1.5)

        head_color = {
            "stalking": tuple(c * 0.8 for c in self.visuals['base_color']),
            "striking": tuple(c * 1.2 for c in self.visuals['base_color']),
            "recovering": tuple(c * 0.6 for c in self.visuals['base_color'])
        }.get(self.state, self.visuals['base_color'])
        
        head_pos = camera.apply(self.points[0])
        head_radius = self.visuals['thickness'][0] * 1.2
        pygame.draw.circle(screen, head_color, head_pos, head_radius)

    def apply_idle_motion(self):
        self.time += 0.016
        for i in range(len(self.points) - 1):
            base_pos = self.points[i + 1]
            angle = (self.time * self.visuals['wiggle_frequencies'][i] + self.visuals['wiggle_phases'][i])
            perpendicular = pygame.Vector2(-math.sin(angle), math.cos(angle))
            amplitude = self.visuals['wiggle_amplitudes'][i] * (1 - i / len(self.points))
            wiggle_offset = perpendicular * amplitude * self.segment_length
            target_pos = base_pos + wiggle_offset
            self.velocities[i] += (target_pos - self.points[i]) * 0.1
            if random.random() < 0.05:
                random_force = pygame.Vector2(random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5))
                self.velocities[i] += random_force

    def update(self, mouse_pos, chain_end):
        if not self.is_active:
            if (chain_end - self.anchor_pos).length() <= self.total_length:
                self.is_active = True

        if self.is_active:
            if self.state != "striking":
                self.apply_idle_motion()

            current_head = self.points[0]
            mouse_vec = pygame.Vector2(mouse_pos)
            direction_to_mouse = mouse_vec - self.anchor_pos

            if self.state == "stalking":
                self.patience_timer += 1
                ideal_distance = self.total_length * 0.7
                if direction_to_mouse.length() > 0:
                    direction_to_mouse.scale_to_length(ideal_distance)
                stalk_pos = self.anchor_pos + direction_to_mouse
                wiggle = math.sin(self.time * 2) * 5
                perp = pygame.Vector2(-direction_to_mouse.y, direction_to_mouse.x)
                if perp.length() > 0:
                    perp.scale_to_length(wiggle)
                stalk_pos += perp
                self.velocities[0] += (stalk_pos - current_head) * self.stalk_speed
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
                self.strike_cooldown -= 1
                if self.strike_cooldown <= 0:
                    self.state = "stalking"

            for i in range(len(self.points) - 1):
                if i != len(self.points) - 1:
                    self.velocities[i] *= self.damping
                self.points[i] += self.velocities[i]

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

    def check_collision_with_chain(self, chain):
        for joint in chain.joints:
            for point in self.points:
                if (point - pygame.Vector2(joint)).length() < 5:
                    return True
        return False

    @classmethod
    def clear_cache(cls):
        """Clear the visual cache if needed"""
        cls.visual_cache.clear()
        cls.cache_counter = 0