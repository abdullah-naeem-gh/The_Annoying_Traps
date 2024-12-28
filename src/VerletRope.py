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
        self.state = "stalking"  # states: stalking, striking, recovering
        self.patience = random.randint(30, 90)  # Random patience before striking
        self.patience_timer = 0
        self.strike_cooldown = 0
        self.missed_strikes = 0
        
        # Movement parameters
        self.strike_speed = 1.2
        self.recovery_speed = 0.15
        self.stalk_speed = 0.08
        
        # Physics parameters
        self.damping = 0.96
        self.spring_stiffness = 0.4
        self.gravity = pygame.Vector2(0, 0.15)
        
        # Targeting
        self.predicted_target = None
        self.last_mouse_pos = None
        self.target_velocity = pygame.Vector2(0, 0)

    def predict_target_position(self, mouse_pos):
        if self.last_mouse_pos is None:
            self.last_mouse_pos = pygame.Vector2(mouse_pos)
            return pygame.Vector2(mouse_pos)
        
        # Calculate mouse velocity
        current_mouse = pygame.Vector2(mouse_pos)
        self.target_velocity = (current_mouse - self.last_mouse_pos) * 0.8
        self.last_mouse_pos = current_mouse
        
        # Predict position based on current movement
        prediction = current_mouse + self.target_velocity * 10
        
        # Limit prediction to reachable distance
        direction = prediction - self.anchor_pos
        if direction.length() > self.total_length:
            direction.scale_to_length(self.total_length)
            prediction = self.anchor_pos + direction
            
        return prediction

    def update(self, mouse_pos, chain_end):
        if not self.is_active:
            if (chain_end - self.anchor_pos).length() <= self.total_length:
                self.is_active = True

        if self.is_active:
            current_head = self.points[0]
            mouse_vec = pygame.Vector2(mouse_pos)
            
            # Update target prediction
            self.predicted_target = self.predict_target_position(mouse_pos)
            
            if self.state == "stalking":
                # Increase patience while stalking
                self.patience_timer += 1
                
                # Calculate ideal striking position
                to_target = self.predicted_target - self.anchor_pos
                ideal_distance = self.total_length * 0.7  # Stay at 70% of max range while stalking
                
                if to_target.length() > 0:
                    to_target.scale_to_length(ideal_distance)
                stalk_pos = self.anchor_pos + to_target
                
                # Move head slowly toward stalking position
                stalk_direction = (stalk_pos - current_head)
                self.velocities[0] += stalk_direction * self.stalk_speed
                
                # Check if ready to strike
                dist_to_target = (mouse_vec - current_head).length()
                if self.patience_timer >= self.patience and dist_to_target < self.total_length:
                    self.state = "striking"
                    strike_dir = (self.predicted_target - current_head).normalize()
                    self.velocities[0] = strike_dir * 25  # Strong initial strike impulse
                    self.patience = random.randint(30, 90)  # Reset patience for next strike
                    self.patience_timer = 0
            
            elif self.state == "striking":
                # Direct velocity toward predicted target
                to_target = self.predicted_target - current_head
                if to_target.length() > 0:
                    strike_direction = to_target.normalize()
                    self.velocities[0] += strike_direction * self.strike_speed
                
                # Check if we hit or missed
                if to_target.length() < 20:  # Hit
                    self.state = "recovering"
                    self.strike_cooldown = random.randint(10, 20)
                    self.missed_strikes = 0
                elif (current_head - self.anchor_pos).length() >= self.total_length * 0.95:  # Missed
                    self.state = "recovering"
                    self.strike_cooldown = random.randint(20, 40)
                    self.missed_strikes += 1
            
            elif self.state == "recovering":
                # Calculate recovery position
                to_target = self.predicted_target - self.anchor_pos
                recovery_distance = self.total_length * (0.4 if self.missed_strikes > 2 else 0.6)
                
                if to_target.length() > 0:
                    to_target.scale_to_length(recovery_distance)
                recovery_pos = self.anchor_pos + to_target
                
                # Move toward recovery position
                recovery_direction = (recovery_pos - current_head)
                self.velocities[0] += recovery_direction * self.recovery_speed
                
                # Check if recovered
                self.strike_cooldown -= 1
                if self.strike_cooldown <= 0:
                    self.state = "stalking"
            
            # Apply physics
            for i in range(len(self.points) - 1):
                if i != len(self.points) - 1:  # Don't move anchor
                    self.velocities[i] += self.gravity
                    self.velocities[i] *= self.damping
                    self.points[i] += self.velocities[i]
            
            # Apply constraints
            for _ in range(3):
                for i in range(1, len(self.points)):
                    self.points[i] = self.constrain_distance(
                        self.points[i], 
                        self.points[i-1], 
                        self.segment_length
                    )
                
                self.points[-1] = self.anchor_pos
                
                for i in range(len(self.points) - 2, -1, -1):
                    self.points[i] = self.constrain_distance(
                        self.points[i],
                        self.points[i+1],
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

    def draw(self, screen, color=(255, 0, 0)):
        if self.is_active:
            # Draw rope segments
            for i in range(len(self.points) - 1):
                pygame.draw.line(screen, color, self.points[i], self.points[i + 1], 5)
            
            # Draw head
            head_color = {
                "stalking": (150, 0, 0),
                "striking": (255, 0, 0),
                "recovering": (100, 0, 0)
            }.get(self.state, (0, 0, 0))
            pygame.draw.circle(screen, head_color, (int(self.points[0].x), int(self.points[0].y)), 5)
        else:
            pygame.draw.circle(screen, color, (int(self.anchor_pos.x), int(self.anchor_pos.y)), 10)