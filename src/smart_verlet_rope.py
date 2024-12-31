import pygame
import math
import random
import json
import os

class QTableManager:
    _instance = None
    _q_table = None
    _filename = "rope_learning.json"
    
    @classmethod
    def get_instance(cls, prefix="rope"):
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._filename = f"{prefix}_learning.json"
            cls._instance.load_q_table()
        return cls._instance
    
    def load_q_table(self):
        if self._q_table is None:
            if os.path.exists(self._filename):
                try:
                    with open(self._filename, 'r') as f:
                        self._q_table = json.load(f)
                except:
                    self._q_table = self._create_default_q_table()
            else:
                self._q_table = self._create_default_q_table()
    
    def _create_default_q_table(self):
        return {
            "Distant": {"stalk": 1.0, "ambush": -2.0, "attack": -5.0},
            "Nearby": {"stalk": 5.0, "ambush": 8.0, "attack": 0.0},
            "Close": {"stalk": -2.0, "ambush": 10.0, "attack": 15.0},
            "TooFar": {"stalk": 2.0, "ambush": -5.0, "attack": -10.0}
        }
    
    def update_q_value(self, state, action, value):
        if state not in self._q_table:
            self._q_table[state] = self._create_default_q_table()[state]
        if action not in self._q_table[state]:
            self._q_table[state][action] = 0.0
            
        self._q_table[state][action] = value
        if random.random() < 0.05:
            self.save_q_table()
    
    def save_q_table(self):
        with open(self._filename, 'w') as f:
            json.dump(self._q_table, f)
    
    def get_q_value(self, state, action):
        return self._q_table.get(state, {}).get(action, 0.0)
    
    def get_max_q_value(self, state):
        if state not in self._q_table:
            return 0.0
        return max(self._q_table[state].values())
    
    def get_best_action(self, state):
        if state not in self._q_table:
            return "stalk"
        return max(self._q_table[state].items(), key=lambda x: x[1])[0]

class SmartVerletRope:
    visual_cache = {}
    cache_counter = 0

    def __init__(self, anchor_pos, points, segment_length):
        self.rope_id = SmartVerletRope.cache_counter
        SmartVerletRope.cache_counter += 1
        
        # Initialize learning parameters
        self.learning_rate = 0.1
        self.discount_factor = 0.95
        self.exploration_rate = 0.15
        self.min_exploration_rate = 0.05
        self.exploration_decay = 0.995
        
        self.q_manager = QTableManager.get_instance("verlet_rope")
        self.current_state = "Distant"
        self.current_action = "stalk"
        self.previous_distance = float('inf')
        self.successful_hits = 0
        self.total_attempts = 0
        
        self.reset_state(anchor_pos, points, segment_length)
        
        if self.rope_id not in SmartVerletRope.visual_cache:
            self.initialize_visuals(points, segment_length)
        
        self.is_visible = True

    def reset_state(self, anchor_pos, points, segment_length):
        self.points = [pygame.Vector2(anchor_pos) for _ in range(points)]
        self.velocities = [pygame.Vector2(0, 0) for _ in range(points)]
        self.segment_length = segment_length
        self.total_length = segment_length * points
        self.anchor_pos = pygame.Vector2(anchor_pos)
        self.is_active = False
        
        self.state = "stalking"
        self.patience = random.randint(30, 90)
        self.patience_timer = 0
        self.strike_cooldown = 0
        self.consecutive_misses = 0
        
        self.strike_speed = 1.2
        self.recovery_speed = 0.15
        self.stalk_speed = 0.08
        self.damping = 0.96
        self.spring_stiffness = 0.2
        self.gravity = pygame.Vector2(0, 0.15)
        
        self.time = 0

    def get_state(self, distance_to_target):
        if distance_to_target > self.total_length * 1.5:
            return "TooFar"
        elif distance_to_target > self.total_length:
            return "Distant"
        elif distance_to_target > self.total_length * 0.5:
            return "Nearby"
        return "Close"

    def choose_action(self, state):
        if random.random() < self.exploration_rate:
            action = random.choice(["stalk", "ambush", "attack"])
            self.exploration_rate = max(self.min_exploration_rate, 
                                     self.exploration_rate * self.exploration_decay)
            return action
        return self.q_manager.get_best_action(state)

    def _calculate_reward(self, hit_success, distance):
        base_reward = 0
        
        if hit_success:
            base_reward += 100
            self.successful_hits += 1
        
        if distance < self.previous_distance:
            base_reward += 1
        else:
            base_reward -= 1
            
        if self.state == "striking" and not hit_success:
            self.consecutive_misses += 1
            base_reward -= self.consecutive_misses * 2
            
        return base_reward

    def _update_q_values(self, action, reward, new_state):
        old_value = self.q_manager.get_q_value(self.current_state, action)
        next_max = self.q_manager.get_max_q_value(new_state)
        
        new_value = (1 - self.learning_rate) * old_value + \
                   self.learning_rate * (reward + self.discount_factor * next_max)
        
        self.q_manager.update_q_value(self.current_state, action, new_value)

    def update(self, mouse_pos, chain_end):
        if not self.is_visible:
            return

        if not self.is_active:
            if (chain_end - self.anchor_pos).length() <= self.total_length:
                self.is_active = True

        if self.is_active:
            current_head = self.points[0]
            distance_to_target = (pygame.Vector2(mouse_pos) - current_head).length()
            
            new_state = self.get_state(distance_to_target)
            if self.is_visible:  # Only learn when visible
                action = self.choose_action(new_state)
                hit_success = False

                if action == "stalk":
                    self._execute_stalk_action(mouse_pos)
                elif action == "ambush":
                    self._execute_ambush_action(mouse_pos)
                else:  # attack
                    hit_success = self._execute_attack_action(mouse_pos)
                    
                reward = self._calculate_reward(hit_success, distance_to_target)
                self._update_q_values(action, reward, new_state)
                
                self.previous_distance = distance_to_target
                self.current_state = new_state

            self._update_physics()

    def _execute_stalk_action(self, target_pos):
        self.state = "stalking"
        direction_to_target = pygame.Vector2(target_pos) - self.anchor_pos
        ideal_distance = self.total_length * 0.7
        if direction_to_target.length() > 0:
            direction_to_target.scale_to_length(ideal_distance)
        stalk_pos = self.anchor_pos + direction_to_target
        self.velocities[0] += (stalk_pos - self.points[0]) * self.stalk_speed

    def _execute_ambush_action(self, target_pos):
        self.state = "ambushing"
        direction = pygame.Vector2(target_pos) - self.points[0]
        if direction.length() > 0:
            direction.scale_to_length(self.total_length * 0.4)
            ambush_pos = pygame.Vector2(target_pos) - direction
            self.velocities[0] += (ambush_pos - self.points[0]) * self.stalk_speed * 1.5

    def _execute_attack_action(self, target_pos):
        self.state = "striking"
        self.total_attempts += 1
        direction = pygame.Vector2(target_pos) - self.points[0]
        if direction.length() > 0:
            strike_direction = direction.normalize()
            self.velocities[0] += strike_direction * self.strike_speed * 2
        
        return direction.length() < 20

    def _update_physics(self):
        if self.state != "striking":
            self.apply_idle_motion()

        for i in range(len(self.points) - 1):
            if i != len(self.points) - 1:
                self.velocities[i] *= self.damping
            self.points[i] += self.velocities[i]

        for _ in range(3):
            for i in range(1, len(self.points)):
                self.points[i] = self.constrain_distance(self.points[i], self.points[i - 1])
            self.points[-1] = self.anchor_pos
            for i in range(len(self.points) - 2, -1, -1):
                self.points[i] = self.constrain_distance(self.points[i], self.points[i + 1])

    def constrain_distance(self, point, anchor):
        direction = point - anchor
        dist = direction.length()
        if dist > self.segment_length:
            normalized = direction / dist
            return anchor + normalized * self.segment_length
        return point

    def is_in_view(self, camera, window_size):
        for point in self.points:
            screen_pos = camera.apply(point)
            if (0 <= screen_pos.x <= window_size[0] and 
                0 <= screen_pos.y <= window_size[1]):
                return True
        
        if not self.is_active:
            screen_pos = camera.apply(self.anchor_pos)
            if (0 <= screen_pos.x <= window_size[0] and 
                0 <= screen_pos.y <= window_size[1]):
                return True
        
        return False

    def check_collision_with_chain(self, chain):
        for joint in chain.joints:
            for point in self.points:
                if (point - pygame.Vector2(joint)).length() < 5:
                    return True
        return False

    # [Previous visual methods remain unchanged]
    def initialize_visuals(self, points, segment_length):
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
        SmartVerletRope.visual_cache[self.rope_id] = visual_params

    @property
    def visuals(self):
        return SmartVerletRope.visual_cache[self.rope_id]

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

    @classmethod
    def clear_cache(cls):
        cls.visual_cache.clear()
        cls.cache_counter = 0

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