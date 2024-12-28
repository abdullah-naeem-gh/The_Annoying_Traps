import pygame
import math
import random
from Chain import Chain
from VerletRope import VerletRope
from rope_optimizer import generate_optimized_ropes

pygame.init()
window_size = (800, 600)
screen = pygame.display.set_mode(window_size)
pygame.display.set_caption("Chain and Rope Game")

background_color = (255, 255, 255)
start_area_color = (0, 255, 0)
end_area_color = (0, 0, 255)

start_area = pygame.Rect(300, 550, 200, 50)
end_area = pygame.Rect(350, 0, 100, 50)
num_of_ropes = 10

def display_message(screen, message, color):
    font = pygame.font.SysFont(None, 55)
    text = font.render(message, True, color)
    text_rect = text.get_rect(center=(window_size[0] / 2, window_size[1] / 2))
    screen.blit(text, text_rect)

def main():
    running = True
    clock = pygame.time.Clock()
    game_over = False
    game_won = False
    game_started = False

    # Create optimized ropes
    optimized_rope_config = generate_optimized_ropes(window_size, num_of_ropes, start_area, end_area)
    ropes = [VerletRope((x, y), points, length) for (x, y, length, points) in optimized_rope_config]

    chain_start_pos = (400, 575)
    chain = Chain(chain_start_pos, 5, 20, math.pi / 4)

    while running:
        screen.fill(background_color)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and not game_started:
                if start_area.collidepoint(event.pos):
                    game_started = True
            if (game_over or game_won) and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    game_over = False
                    game_won = False
                    game_started = False
                    optimized_rope_config = generate_optimized_ropes(window_size, num_of_ropes, start_area, end_area)
                    ropes = [VerletRope((x, y), points, length) for (x, y, length, points) in optimized_rope_config]
                    chain = Chain(chain_start_pos, 5, 20, math.pi / 4)

        if not game_started:
            pygame.draw.rect(screen, start_area_color, start_area)
            display_message(screen, "Click to Start!", (0, 0, 0))
        else:
            if not game_over and not game_won:
                mouse_pos = pygame.mouse.get_pos()
                chain.update(mouse_pos)
                chain_end = chain.joints[-1]

                for rope in ropes:
                    rope.update(mouse_pos, chain_end)
                    if rope.check_collision_with_chain(chain):
                        game_over = True

                if end_area.collidepoint(chain_end):
                    game_won = True

                chain.draw(screen)
                for rope in ropes:
                    rope.draw(screen)
                pygame.draw.rect(screen, end_area_color, end_area)

            elif game_over:
                display_message(screen, "Caught! Press SPACE to Restart", (255, 0, 0))
            elif game_won:
                display_message(screen, "You Won! Press SPACE to Play Again", (0, 0, 255))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()