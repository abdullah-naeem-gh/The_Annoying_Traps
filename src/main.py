import pygame
from VerletRope import VerletRope
from Chain import Chain
import math

# Initialize Pygame
pygame.init()

# Set up display
window_size = (800, 600)
screen = pygame.display.set_mode(window_size)
pygame.display.set_caption("Chain and Rope Game")

# Colors
background_color = (255, 255, 255)

def display_game_over(screen):
    font = pygame.font.SysFont(None, 55)  # Default font-size can be changed
    text = font.render('Game Over! Press SPACE to Restart', True, (255, 0, 0))
    text_rect = text.get_rect(center=(window_size[0] / 2, window_size[1] / 2))
    screen.blit(text, text_rect)

def main():
    running = True
    clock = pygame.time.Clock()
    game_over = False

    # Initialize chain and rope
    chain_start_pos = (400, 300)
    rope_anchor_pos = (400, 100)
    chain = Chain(chain_start_pos, 5, 20, math.pi / 4)
    rope = VerletRope(rope_anchor_pos, 30, 8)

    while running:
        screen.fill(background_color)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if game_over and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Reset game
                    game_over = False
                    chain = Chain(chain_start_pos, 5, 20, math.pi / 4)
                    rope = VerletRope(rope_anchor_pos, 10, 25)

        if not game_over:
            if rope.check_collision_with_chain(chain):
                game_over = True

            mouse_pos = pygame.mouse.get_pos()

            chain.update(mouse_pos)
            chain_end = chain.joints[-1]

            chain.draw(screen)
            rope.update(mouse_pos, chain_end)
            rope.draw(screen)
        else:
            display_game_over(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()