#smart_blue_tentacle.py

import pygame
import math
import random
import json
import os

class QTableManager:
    _instance = None
    _q_table = None
    _filename = "tentacle_learning.json"
    
    @classmethod
    def get_instance(cls, prefix="tentacle"):
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
    
    def save_q_table(self):
        with open(self._filename, 'w') as f:
            json.dump(self._q_table, f)
    
    def _create_default_q_table(self):
        return {
            "Far": {"stalk": 1.0, "strike": -5.0, "retreat": 0.0},
            "Medium": {"stalk": 5.0, "strike": 0.0, "retreat": -2.0},
            "Close": {"stalk": 0.0, "strike": 8.0, "retreat": 2.0},
            "VeryClose": {"stalk": -5.0, "strike": 10.0, "retreat": 5.0},
            "Danger": {"stalk": -10.0, "strike": -8.0, "retreat": 10.0}
        }
    
    def update_q_value(self, state, action, value):
        if state not in self._q_table:
            self._q_table[state] = self._create_default_q_table()[state]
        if action not in self._q_table[state]:
            self._q_table[state][action] = 0.0
            
        self._q_table[state][action] = value
        if random.random() < 0.05:  # 5% chance to save
            self.save_q_table()
    
    def get_q_value(self, state, action):
        return self._q_table.get(state, {}).get(action, 0.0)
    
    def get_max_q_value(self, state):
        if state not in self._q_table:
            return 0.0
        return max(self._q_table[state].values())
    
    def get_best_action(self, state):
        if state not in self._q_table:
            return "retreat"
        return max(self._q_table[state].items(), key=lambda x: x[1])[0]

class SmartBlueTentacle:
    def __init__(self, anchor_pos, points=5, segment_length=20):
        self.points = [pygame.Vector2(anchor_pos) for _ in range(points)]
        self.velocities = [pygame.Vector2(0, 0) for _ in range(points)]
        self.segment_length = segment_length
        self.total_length = segment_length * points
        self.anchor_pos = pygame.Vector2(anchor_pos)
        self.has_coin = False
        self.is_active = False
        self.is_visible = True
        
        # Learning parameters
        self.learning_rate = 0.1
        self.discount_factor = 0.95
        self.exploration_rate = 0.15
        self.min_exploration_rate = 0.05
        self.exploration_decay = 0.995
        
        self.current_state = "Far"
        self.previous_distance = float('inf')
        self.state = "stalking"
        self.patience = random.randint(30, 90)
        self.patience_timer = 0
        self.strike_cooldown = 0
        self.consecutive_misses = 0
        self.success_streak = 0
        
        # Movement parameters
        self.time = 0
        self.wiggle_amplitudes = [random.uniform(0.2, 0.5) for _ in range(points)]
        self.wiggle_frequencies = [random.uniform(0.05, 0.1) for _ in range(points)]
        self.wiggle_phases = [random.uniform(0, math.pi * 2) for _ in range(points)]
        self.base_strike_speed = 1.2
        self.strike_speed = self.base_strike_speed
        self.recovery_speed = 0.5
        self.stalk_speed = 0.08
        self.damping = 0.96
        self.spring_stiffness = 0.1
        self.gravity = pygame.Vector2(0, 0.15)
        
        self.q_manager = QTableManager.get_instance("blue_tentacle")
        
        # Performance tracking
        self.total_attempts = 0
        self.successful_catches = 0

    def get_state(self, distance_to_target, chain_distance=float('inf')):
        if chain_distance < 100:  # Danger state when chain is too close
            return "Danger"
        if distance_to_target > 300:
            return "Far"
        elif distance_to_target > 200:
            return "Medium"
        elif distance_to_target > 100:
            return "Close"
        return "VeryClose"

    def choose_action(self, state):
        if random.random() < self.exploration_rate:
            action = random.choice(list(self.q_manager._q_table[state].keys()))
            self.exploration_rate = max(self.min_exploration_rate, 
                                     self.exploration_rate * self.exploration_decay)
            return action
        return self.q_manager.get_best_action(state)

    def _calculate_reward(self, distance, coin, chain_distance):
        base_reward = 0
        
        # Coin-related rewards
        if self.has_coin:
            base_reward += 100
            self.successful_catches += 1
            self.success_streak += 1
            self.strike_speed = self.base_strike_speed * (1 + min(self.success_streak * 0.1, 0.5))
        elif distance < self.previous_distance:
            base_reward += 1
        else:
            base_reward -= 1
            
        # Distance-based penalties
        if chain_distance < 100:
            base_reward -= 50  # Heavy penalty for being too close to chain
            
        # Consecutive misses penalties
        if self.state == "striking" and distance > 20:
            self.consecutive_misses += 1
            base_reward -= self.consecutive_misses * 2
        else:
            self.consecutive_misses = max(0, self.consecutive_misses - 1)
            
        return base_reward

    def apply_idle_motion(self):
        self.time += 0.016
        for i in range(len(self.points)):
            if i == len(self.points) - 1:
                continue
                
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
        if not self.is_visible and not self.has_coin:
            return
            
        if not self.is_active:
            if (pygame.Vector2(chain.joints[0]) - self.anchor_pos).length() <= self.total_length * 1.5:
                self.is_active = True
                
        if self.is_active and not self.has_coin:
            current_head = self.points[0]
            distance_to_coin = (coin.position - current_head).length()
            distance_to_chain = (pygame.Vector2(chain.joints[0]) - current_head).length()
            
            self.current_state = self.get_state(distance_to_coin, distance_to_chain)
            action = self.choose_action(self.current_state)
            
            if action == "stalk":
                self._execute_stalk_action(coin, current_head)
            elif action == "strike":
                self._execute_strike_action(coin, current_head)
            else:  # retreat
                self._execute_retreat_action(current_head)

            reward = self._calculate_reward(distance_to_coin, coin, distance_to_chain)
            self._update_q_values(action, reward, distance_to_coin, distance_to_chain)

            if self.state != "striking":
                self.apply_idle_motion()

        self._update_physics()
        
        if self.has_coin:
            coin.position = self.points[0]

    def _execute_stalk_action(self, coin, current_head):
        self.state = "stalking"
        direction_to_coin = coin.position - self.anchor_pos
        ideal_distance = self.total_length * 0.7
        if direction_to_coin.length() > 0:
            direction_to_coin.scale_to_length(ideal_distance)
        stalk_pos = self.anchor_pos + direction_to_coin
        self.velocities[0] += (stalk_pos - current_head) * self.stalk_speed

    def _execute_strike_action(self, coin, current_head):
        self.state = "striking"
        self.total_attempts += 1
        to_coin = coin.position - current_head
        if to_coin.length() > 0:
            strike_direction = to_coin.normalize()
            self.velocities[0] += strike_direction * self.strike_speed
        if to_coin.length() < 20:
            self.has_coin = True
            coin.collected = False
            self.consecutive_misses = 0

    def _execute_retreat_action(self, current_head):
        self.state = "recovering"
        to_anchor = self.anchor_pos - current_head
        if to_anchor.length() > 0:
            retreat_direction = to_anchor.normalize()
            self.velocities[0] += retreat_direction * self.recovery_speed

    def _update_q_values(self, action, reward, distance, chain_distance):
        next_state = self.get_state(distance, chain_distance)
        old_value = self.q_manager.get_q_value(self.current_state, action)
        next_max = self.q_manager.get_max_q_value(next_state)
        
        new_value = (1 - self.learning_rate) * old_value + \
                   self.learning_rate * (reward + self.discount_factor * next_max)
        
        self.q_manager.update_q_value(self.current_state, action, new_value)
        self.previous_distance = distance

    def _update_physics(self):
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