import pygame
import random
import math
from Chain import Chain
from VerletRope import VerletRope
from rope_optimizer import generate_optimized_ropes
from SlimeObstacle import SlimeObstacle
from camera import Camera
from coin import Coin
from blue_tentacle import BlueTentacle

def display_message(screen, message, color, window_size):
    font = pygame.font.SysFont(None, 55)
    text = font.render(message, True, color)
    text_rect = text.get_rect(center=(window_size[0] / 2, window_size[1] / 2))
    screen.blit(text, text_rect)

def generate_world_content(num_slimes):
    return [SlimeObstacle((random.randint(100, 3100), random.randint(100, 2300)), 30, 20) for _ in range(num_slimes)]

def generate_ropes(world_size, num_of_ropes, start_area, end_area):
    optimized_rope_config = generate_optimized_ropes(world_size, num_of_ropes, start_area, end_area)
    return [VerletRope((x, y), points, length) for (x, y, length, points) in optimized_rope_config]

def generate_blue_tentacles(world_size, num_of_tentacles):
    return [BlueTentacle((random.randint(100, 3100), random.randint(100, 2300)), points=5, segment_length=40)
            for _ in range(num_of_tentacles)]

def main():
    pygame.init()
    window_size = (800, 600)
    world_size = (3200, 2400)
    screen = pygame.display.set_mode(window_size)
    pygame.display.set_caption("Chain and Rope Game")
    background_color = (255, 255, 255)
    start_area_color = (0, 255, 0)
    end_area_color = (0, 0, 255)
    start_area = pygame.Rect(1400, 2350, 200, 50)
    end_area = pygame.Rect(1500, 0, 100, 50)
    num_of_ropes = 50
    num_of_slimes = 20
    num_of_blue_tentacles = 20
    clock = pygame.time.Clock()
    running = True
    game_over = False
    game_won = False
    game_started = False
    show_full_map = False
    camera = Camera(window_size, world_size)
    slimes = generate_world_content(num_of_slimes)
    chain_start_pos = (1600, 2300)
    chain = Chain(chain_start_pos, 5, 20, math.pi / 4)
    ropes = generate_ropes(world_size, num_of_ropes, start_area, end_area)
    blue_tentacles = generate_blue_tentacles(world_size, num_of_blue_tentacles)
    coin = Coin((1650, 2300), follow_distance=20)

    while running:
        delta_time = clock.get_time() / 1000.0
        screen.fill(background_color)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    show_full_map = not show_full_map
                if (game_over or game_won) and event.key == pygame.K_SPACE:
                    game_over = False
                    game_won = False
                    game_started = False
                    VerletRope.clear_cache()
                    ropes = generate_ropes(world_size, num_of_ropes, start_area, end_area)
                    slimes = generate_world_content(num_of_slimes)
                    blue_tentacles = generate_blue_tentacles(world_size, num_of_blue_tentacles)
                    chain = Chain(chain_start_pos, 5, 20, math.pi / 4)
                    coin = Coin((1650, 2300), follow_distance=20)

            if event.type == pygame.MOUSEBUTTONDOWN and not game_started:
                mouse_world_pos = pygame.Vector2(event.pos) + camera.offset
                if start_area.collidepoint(mouse_world_pos):
                    game_started = True

        if show_full_map:
            game_surface = pygame.Surface(world_size)
            game_surface.fill(background_color)
            for rope in ropes:
                rope.draw(game_surface, camera)
            chain.draw(game_surface, camera)
            for slime in slimes:
                slime.draw(game_surface, camera)
            for tentacle in blue_tentacles:
                tentacle.draw(game_surface, camera)
            coin.draw(game_surface, camera)
            pygame.draw.rect(game_surface, start_area_color, start_area)
            pygame.draw.rect(game_surface, end_area_color, end_area)
            scaled_surface = pygame.transform.scale(game_surface, window_size)
            screen.blit(scaled_surface, (0, 0))
            display_message(screen, "Full Map View: Press M to Toggle", (0, 0, 0), window_size)
        else:
            if not game_started:
                camera.update(pygame.Vector2(chain.joints[0]))
                transformed_start_area = pygame.Rect(
                    camera.apply(pygame.Vector2(start_area.topleft)),
                    start_area.size
                )
                pygame.draw.rect(screen, start_area_color, transformed_start_area)
                display_message(screen, "Click to Start!", (0, 0, 0), window_size)
            elif not game_over and not game_won:
                camera.update(pygame.Vector2(chain.joints[0]))
                mouse_world_pos = pygame.Vector2(pygame.mouse.get_pos()) + camera.offset
                chain.update(mouse_world_pos)
                chain_end = chain.joints[-1]
                coin.update(chain)
                for rope in ropes:
                    rope.update(mouse_world_pos, chain_end)
                    if rope.check_collision_with_chain(chain):
                        game_over = True
                for slime in slimes:
                    slime.update(delta_time)
                    if slime.check_collision(chain):
                        game_over = True
                for tentacle in blue_tentacles:
                    tentacle.update(chain, coin)
                    if tentacle.has_coin and tentacle.points[0].distance_to(chain.joints[0]) < 25:
                        coin.collected = True
                        tentacle.has_coin = False
                if end_area.collidepoint(chain_end):
                    game_won = True

            chain.draw(screen, camera)
            for rope in ropes:
                rope.draw(screen, camera)
            for slime in slimes:
                slime.draw(screen, camera)
            for tentacle in blue_tentacles:
                tentacle.draw(screen, camera)
            coin.draw(screen, camera)
            transformed_end_area = pygame.Rect(
                camera.apply(pygame.Vector2(end_area.topleft)),
                end_area.size
            )
            pygame.draw.rect(screen, end_area_color, transformed_end_area)

            if game_over:
                display_message(screen, "Caught! Press SPACE to Restart", (255, 0, 0), window_size)
            elif game_won:
                display_message(screen, "You Won! Press SPACE to Play Again", (0, 0, 255), window_size)

        pygame.display.flip()
        clock.tick(60)
    pygame.quit()

if __name__ == "__main__":
    main()