import pygame
import random
import math
from Chain import Chain
from rope_optimizer import generate_optimized_ropes
from SlimeObstacle import SlimeObstacle
from camera import Camera
from coin import Coin
from smart_blue_tentacle import SmartBlueTentacle
from smart_verlet_rope import SmartVerletRope
from MainMenu import MainMenu
from alert import FuzzyAlert, calculate_distance, calculate_velocity

def display_message(screen, message, color, window_size):
    font = pygame.font.SysFont(None, 55)
    text = font.render(message, True, color)
    text_rect = text.get_rect(center=(window_size[0] / 2, window_size[1] / 2))
    screen.blit(text, text_rect)

def generate_world_content(num_slimes):
    return [SlimeObstacle((random.randint(100, 3100), random.randint(100, 2300)), 30, 20) 
            for _ in range(num_slimes)]

def generate_ropes(world_size, num_of_ropes, start_area, end_area):
    optimized_rope_config = generate_optimized_ropes(world_size, num_of_ropes, start_area, end_area)
    return [SmartVerletRope((x, y), points, length) 
            for (x, y, length, points) in optimized_rope_config]

def generate_blue_tentacles(world_size, num_of_tentacles):
    return [SmartBlueTentacle((random.randint(100, 3100), random.randint(100, 2300)), 
            points=5, segment_length=40) for _ in range(num_of_tentacles)]

def initialize_game(difficulty_settings, window_size, world_size, start_area, end_area):
    num_of_ropes = difficulty_settings['num_ropes']
    num_of_slimes = difficulty_settings['num_slimes']
    num_of_blue_tentacles = difficulty_settings['num_tentacles']
    
    slimes = generate_world_content(num_of_slimes)
    chain_start_pos = (1600, 2300)
    chain = Chain(chain_start_pos, 5, 20, math.pi / 4)
    ropes = generate_ropes(world_size, num_of_ropes, start_area, end_area)
    blue_tentacles = generate_blue_tentacles(world_size, num_of_blue_tentacles)
    coin = Coin((1650, 2300), follow_distance=20)
    
    return slimes, chain, ropes, blue_tentacles, coin

def main():
    pygame.init()
    window_size = (800, 600)
    world_size = (3200, 2400)
    screen = pygame.display.set_mode(window_size)
    pygame.display.set_caption("Slime Run")
    
    # Initialize colors and areas
    background_color = (255, 255, 255)
    start_area_color = (0, 255, 0)
    end_area_color = (0, 0, 255)
    start_area = pygame.Rect(1400, 2350, 200, 50)
    end_area = pygame.Rect(1500, 0, 100, 50)
    
    # Initialize game components
    clock = pygame.time.Clock()
    camera = Camera(window_size, world_size)
    main_menu = MainMenu(window_size)

    # Initialize Fuzzy Alert System
    alert_system = FuzzyAlert()
    
    # Initialize game states
    running = True
    game_over = False
    game_won = False
    game_started = False
    show_full_map = False
    in_main_menu = True
    
    # Create UI buttons
    restart_button = pygame.Rect(window_size[0] // 4, window_size[1] // 2 + 50, 150, 50)
    menu_button = pygame.Rect(window_size[0] * 3 // 4 - 150, window_size[1] // 2 + 50, 150, 50)
    
    # Initialize game objects with default settings
    current_settings = main_menu.difficulty_settings.get_settings()
    slimes, chain, ropes, blue_tentacles, coin = initialize_game(
        current_settings, window_size, world_size, start_area, end_area
    )

    while running:
        delta_time = clock.get_time() / 1000.0
        screen.fill(background_color)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            if in_main_menu:
                action, settings = main_menu.handle_event(event)
                if action == 'PLAY':
                    in_main_menu = False
                    game_started = False
                    game_over = False
                    game_won = False
                    current_settings = settings
                    slimes, chain, ropes, blue_tentacles, coin = initialize_game(
                        current_settings, window_size, world_size, start_area, end_area
                    )
            else:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_m:
                        show_full_map = not show_full_map
                        
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    if game_over or game_won:
                        if restart_button.collidepoint(mouse_pos):
                            game_over = False
                            game_won = False
                            game_started = False
                            SmartVerletRope.clear_cache()
                            slimes, chain, ropes, blue_tentacles, coin = initialize_game(
                                current_settings, window_size, world_size, start_area, end_area
                            )
                        elif menu_button.collidepoint(mouse_pos):
                            in_main_menu = True
                    elif not game_started:
                        mouse_world_pos = pygame.Vector2(event.pos) + camera.offset
                        if start_area.collidepoint(mouse_world_pos):
                            game_started = True

        if in_main_menu:
            main_menu.draw(screen)
        else:
            # Update visibility of game objects
            for tentacle in blue_tentacles:
                tentacle.is_visible = tentacle.is_in_view(camera, window_size)
            for rope in ropes:
                rope.is_visible = rope.is_in_view(camera, window_size)

            if show_full_map:
                # Draw full map view
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
                    # Draw start screen
                    camera.update(pygame.Vector2(chain.joints[0]))
                    transformed_start_area = pygame.Rect(
                        camera.apply(pygame.Vector2(start_area.topleft)),
                        start_area.size
                    )
                    pygame.draw.rect(screen, start_area_color, transformed_start_area)
                    display_message(screen, "Click to Start!", (0, 0, 0), window_size)
                elif not game_over and not game_won:
                    # Update game state
                    camera.update(pygame.Vector2(chain.joints[0]))
                    mouse_world_pos = pygame.Vector2(pygame.mouse.get_pos()) + camera.offset
                    chain.update(mouse_world_pos)
                    chain_end = chain.joints[-1]
                    coin.update(chain)
                    
                    # Update game objects and check collisions
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

                    
                    # Update alert system
                    threats = []

                    # Check ropes (primary threat)
                    for rope in ropes:
                        if rope.is_visible:
                            dist = calculate_distance(
                                chain.joints[0],
                                rope.points[0]
                            )
                            if dist < 180:
                                threats.append((
                                    dist,
                                    calculate_velocity(rope),
                                    'rope'
                                ))

                    # Check tentacles (secondary threat)
                    for tentacle in blue_tentacles:
                        if tentacle.is_visible:
                            dist = calculate_distance(
                                chain.joints[0],
                                tentacle.points[0]
                            )
                            if dist < 180:
                                threats.append((
                                    dist,
                                    calculate_velocity(tentacle),
                                    'tentacle'
                                ))

                    # Update and draw alert overlay
                    alert_system.update_danger_level(threats)
                    alert_system.create_overlay(window_size)

                # Draw game objects
                chain.draw(screen, camera)
                for rope in ropes:
                    rope.draw(screen, camera)
                for slime in slimes:
                    slime.draw(screen, camera)
                for tentacle in blue_tentacles:
                    tentacle.draw(screen, camera)
                coin.draw(screen, camera)
                
                # Draw end area
                transformed_end_area = pygame.Rect(
                    camera.apply(pygame.Vector2(end_area.topleft)),
                    end_area.size
                )
                pygame.draw.rect(screen, end_area_color, transformed_end_area)

                # Draw alert overlay
                if not game_over and not game_won and game_started:
                    alert_system.draw(screen)

                # Handle game over state
                if game_over:
                    overlay = pygame.Surface(window_size, pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 128))
                    screen.blit(overlay, (0, 0))
                    display_message(screen, "Game Over!", (255, 0, 0), 
                                 (window_size[0], window_size[1] - 100))
                    
                    # Draw UI buttons
                    pygame.draw.rect(screen, (200, 200, 200), restart_button, border_radius=10)
                    pygame.draw.rect(screen, (0, 0, 0), restart_button, 2, border_radius=10)
                    font = pygame.font.SysFont(None, 36)
                    restart_text = font.render("Restart", True, (0, 0, 0))
                    restart_text_rect = restart_text.get_rect(center=restart_button.center)
                    screen.blit(restart_text, restart_text_rect)
                    
                    pygame.draw.rect(screen, (200, 200, 200), menu_button, border_radius=10)
                    pygame.draw.rect(screen, (0, 0, 0), menu_button, 2, border_radius=10)
                    menu_text = font.render("Main Menu", True, (0, 0, 0))
                    menu_text_rect = menu_text.get_rect(center=menu_button.center)
                    screen.blit(menu_text, menu_text_rect)
                    
                elif game_won:
                    overlay = pygame.Surface(window_size, pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 128))
                    screen.blit(overlay, (0, 0))
                    display_message(screen, "Victory!", (0, 255, 0), 
                                 (window_size[0], window_size[1] - 100))
                    
                    # Draw UI buttons
                    pygame.draw.rect(screen, (200, 200, 200), restart_button, border_radius=10)
                    pygame.draw.rect(screen, (0, 0, 0), restart_button, 2, border_radius=10)
                    font = pygame.font.SysFont(None, 36)
                    restart_text = font.render("Play Again", True, (0, 0, 0))
                    restart_text_rect = restart_text.get_rect(center=restart_button.center)
                    screen.blit(restart_text, restart_text_rect)
                    
                    pygame.draw.rect(screen, (200, 200, 200), menu_button, border_radius=10)
                    pygame.draw.rect(screen, (0, 0, 0), menu_button, 2, border_radius=10)
                    menu_text = font.render("Main Menu", True, (0, 0, 0))
                    menu_text_rect = menu_text.get_rect(center=menu_button.center)
                    screen.blit(menu_text, menu_text_rect)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()