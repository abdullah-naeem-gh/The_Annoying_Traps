import pygame

class Camera:
    def __init__(self, window_size, world_size):
        self.window_size = pygame.Vector2(window_size)
        self.world_size = pygame.Vector2(world_size)
        self.offset = pygame.Vector2(0, 0)
        self.lerp_factor = 0.05  # Adjust as needed for smoothing
        self.threshold = 1.5  # Threshold below which movement will not be applied

    def update(self, target_pos):
        # Calculate the desired camera offset to center the target
        target_offset = pygame.Vector2(
            target_pos.x - self.window_size.x / 2,
            target_pos.y - self.window_size.y / 2,
        )

        # Clamp target offset to the boundaries of the world
        target_offset.x = max(0, min(target_offset.x, self.world_size.x - self.window_size.x))
        target_offset.y = max(0, min(target_offset.y, self.world_size.y - self.window_size.y))

        # Only apply movement if it's above the threshold
        if abs(target_offset.x - self.offset.x) > self.threshold:
            self.offset.x += (target_offset.x - self.offset.x) * self.lerp_factor

        if abs(target_offset.y - self.offset.y) > self.threshold:
            self.offset.y += (target_offset.y - self.offset.y) * self.lerp_factor

    def apply(self, entity):
        return entity - self.offset