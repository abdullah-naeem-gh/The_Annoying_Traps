# alert.py
import math
import pygame
import numpy as np

class FuzzyAlert:
    def __init__(self):
        self.danger_level = 0
        self.max_alpha = 144
        
        # Threat-specific intensity multipliers
        self.threat_intensities = {
            'rope': 0.9,      # intensity for ropes
            'tentacle': 0.0   # intensity for tentacles
        }
        
        # Fuzzy sets for distance
        self.distance_sets = {
            'very_close': {'peak': 0, 'spread': 30},
            'close': {'peak': 60, 'spread': 30},
            'medium': {'peak': 120, 'spread': 30},
            'far': {'peak': 180, 'spread': 50}
        }
        
        # Fuzzy sets for velocity
        self.velocity_sets = {
            'slow': {'peak': 0, 'spread': 2},
            'medium': {'peak': 5, 'spread': 3},
            'fast': {'peak': 10, 'spread': 5}
        }
        
        # Rule weights for different combinations
        self.rules = {
            ('very_close', 'fast'): 1.0,
            ('very_close', 'medium'): 0.8,
            ('very_close', 'slow'): 0.6,
            ('close', 'fast'): 0.7,
            ('close', 'medium'): 0.5,
            ('close', 'slow'): 0.3,
            ('medium', 'fast'): 0.4,
            ('medium', 'medium'): 0.2,
            ('medium', 'slow'): 0.1,
            ('far', 'fast'): 0.1,
            ('far', 'medium'): 0.0,
            ('far', 'slow'): 0.0
        }
        
        self.overlay = None
        self.danger_color = (255, 0, 0)
        
    def membership_function(self, value, peak, spread):
        return max(0, 1 - abs(value - peak) / spread)
    
    def calculate_distance_memberships(self, distance):
        memberships = {}
        for set_name, params in self.distance_sets.items():
            memberships[set_name] = self.membership_function(
                distance, params['peak'], params['spread']
            )
        return memberships
    
    def calculate_velocity_memberships(self, velocity):
        memberships = {}
        for set_name, params in self.velocity_sets.items():
            memberships[set_name] = self.membership_function(
                velocity, params['peak'], params['spread']
            )
        return memberships
    
    def update_danger_level(self, threats):
        """
        Update danger level based on threats
        threats: list of tuples (distance, velocity, threat_type)
        """
        if not threats:
            self.danger_level = max(0, self.danger_level - 0.02)
            return
        
        danger_values = []
        
        for distance, velocity, threat_type in threats:
            # Get memberships
            distance_memberships = self.calculate_distance_memberships(distance)
            velocity_memberships = self.calculate_velocity_memberships(velocity)
            
            # Apply fuzzy rules
            rule_outputs = []
            for (dist_set, vel_set), weight in self.rules.items():
                activation = min(
                    distance_memberships[dist_set],
                    velocity_memberships[vel_set]
                )
                # Apply threat-specific intensity
                intensity = self.threat_intensities.get(threat_type, 1.0)
                rule_outputs.append(activation * weight * intensity)
            
            danger_values.append(max(rule_outputs))
        
        target_danger = max(danger_values)
        
        if target_danger > self.danger_level:
            self.danger_level = min(1.0, self.danger_level + 0.08)
        else:
            self.danger_level = max(0, self.danger_level - 0.04)
    
    def create_overlay(self, window_size):
        if self.overlay is None or self.overlay.get_size() != window_size:
            self.overlay = pygame.Surface(window_size, pygame.SRCALPHA)
        
        self.overlay.fill((0, 0, 0, 0))
        
        if self.danger_level > 0:
            alpha = int(self.max_alpha * self.danger_level)
            self.overlay.fill((self.danger_color[0], self.danger_color[1], 
                             self.danger_color[2], alpha))
    
    def draw(self, screen):
        if self.danger_level > 0:
            screen.blit(self.overlay, (0, 0))

def calculate_distance(point1, point2):
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def calculate_velocity(entity):
    if hasattr(entity, 'velocities') and entity.velocities:
        vel = entity.velocities[0]
        return math.sqrt(vel.x**2 + vel.y**2)
    return 0