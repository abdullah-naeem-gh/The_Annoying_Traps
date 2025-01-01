import pygame

class DifficultySettings:
    def __init__(self):
        self.difficulties = {
            'EASY': {
                'num_slimes': 15,
                'num_tentacles': 15,
                'num_ropes': 40
            },
            'MEDIUM': {
                'num_slimes': 20,
                'num_tentacles': 20,
                'num_ropes': 50
            },
            'HARD': {
                'num_slimes': 25,
                'num_tentacles': 25,
                'num_ropes': 60
            }
        }
        self.current_difficulty = 'EASY'
    
    def get_settings(self):
        return self.difficulties[self.current_difficulty]
    
    def set_difficulty(self, difficulty):
        if difficulty in self.difficulties:
            self.current_difficulty = difficulty

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.font = pygame.font.SysFont(None, 36)
        
    def draw(self, screen):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, (0, 0, 0), self.rect, 2, border_radius=10)
        
        text_surface = self.font.render(self.text, True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                return True
        return False

class MainMenu:
    def __init__(self, screen_size):
        self.screen_size = screen_size
        self.difficulty_settings = DifficultySettings()
        
        # Colors for different buttons
        self.button_colors = {
            'PLAY': {
                'normal': (34, 139, 34),  # Green
                'hover': (135, 206, 235)  # Light Blue
            },
            'EASY': {
                'normal': (200, 200, 200),
                'hover': (180, 180, 180),
                'selected': (150, 255, 150),
                'selected_hover': (130, 235, 130)
            },
            'MEDIUM': {
                'normal': (200, 200, 200),
                'hover': (255, 165, 0),  # Orange
                'selected': (255, 140, 0),  # Dark Orange
                'selected_hover': (255, 165, 0)
            },
            'HARD': {
                'normal': (200, 200, 200),
                'hover': (255, 0, 0),  # Red
                'selected': (220, 0, 0),  # Dark Red
                'selected_hover': (255, 0, 0)
            }
        }
        
        # Button dimensions
        play_button_width = 300  # Larger width for play button
        play_button_height = 80  # Larger height for play button
        difficulty_button_width = 150
        button_height = 50
        button_spacing = 20

        # Create play button (centered)
        play_y = screen_size[1] // 2 - play_button_height // 2  # Perfectly centered vertically
        self.play_button = Button(
            screen_size[0] // 2 - play_button_width // 2,
            play_y - 30,
            play_button_width,
            play_button_height,
            "Play",
            self.button_colors['PLAY']['normal'],
            self.button_colors['PLAY']['hover']
        )
        
        # Create difficulty buttons (horizontal layout)
        difficulties_y = play_y + play_button_height + button_spacing
        total_width = (difficulty_button_width * 3) + (button_spacing * 2)
        start_x = screen_size[0] // 2 - total_width // 2
        
        self.difficulty_buttons = {
            'EASY': Button(
                start_x,
                difficulties_y,
                difficulty_button_width,
                button_height,
                "Easy",
                self.button_colors['EASY']['normal'],
                self.button_colors['EASY']['hover']
            ),
            'MEDIUM': Button(
                start_x + difficulty_button_width + button_spacing,
                difficulties_y,
                difficulty_button_width,
                button_height,
                "Medium",
                self.button_colors['MEDIUM']['selected'],  # Start with Medium selected
                self.button_colors['MEDIUM']['selected_hover']
            ),
            'HARD': Button(
                start_x + (difficulty_button_width + button_spacing) * 2,
                difficulties_y,
                difficulty_button_width,
                button_height,
                "Hard",
                self.button_colors['HARD']['normal'],
                self.button_colors['HARD']['hover']
            )
        }
        
    def draw(self, screen):
        screen.fill((255, 255, 255))
        
        # Draw title higher up
        font = pygame.font.SysFont(None, 82)
        title = font.render("Slime Run", True, (0, 0, 0))
        title_rect = title.get_rect(center=(self.screen_size[0] // 2, self.screen_size[1] // 5))
        screen.blit(title, title_rect)
        
        # Draw buttons
        self.play_button.draw(screen)
        for button in self.difficulty_buttons.values():
            button.draw(screen)
            
    def handle_event(self, event):
        if self.play_button.handle_event(event):
            return 'PLAY', self.difficulty_settings.get_settings()
            
        for difficulty, button in self.difficulty_buttons.items():
            if button.handle_event(event):
                self.update_difficulty_selection(difficulty)
                return 'DIFFICULTY_CHANGE', None
                
        return None, None
        
    def update_difficulty_selection(self, selected_difficulty):
        self.difficulty_settings.set_difficulty(selected_difficulty)
        
        # Update button colors
        for difficulty, button in self.difficulty_buttons.items():
            colors = self.button_colors[difficulty]
            if difficulty == selected_difficulty:
                button.color = colors['selected']
                button.hover_color = colors['selected_hover']
            else:
                button.color = colors['normal']
                button.hover_color = colors['hover']