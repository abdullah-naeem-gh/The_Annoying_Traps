import pygame

class Coin:
    def __init__(self, position, radius=8, follow_distance=20):
        self.position = pygame.Vector2(position)
        self.radius = radius
        self.collected = False
        self.follow_distance = follow_distance  # Closer follow distance

    def update(self, chain):
        if not self.collected:
            # Check if any of the joints in the chain are within proximity
            for joint in chain.joints:
                if self.position.distance_to(pygame.Vector2(joint)) < self.radius * 2:
                    self.collected = True
                    break
        else:
            # Follow the first joint (front) of the chain
            anchor = pygame.Vector2(chain.joints[0])  # Use the first joint
            direction = (self.position - anchor).normalize()
            self.position = anchor + direction * self.follow_distance

    def draw(self, screen, camera):
        color = (255, 165, 0)  # Yellow color for the coin
        pygame.draw.circle(screen, color, camera.apply(self.position), self.radius)