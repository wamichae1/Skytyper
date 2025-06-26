import pygame
import random
import sys
from pygame.locals import *
import json
import asyncio
import urllib.request

try:
    import js
    from js import window
    import builtins

    if hasattr(js, "console") and hasattr(js.console, "log"):
        builtins.print = js.console.log  # Redirect print to browser console
        js.console.log("Fetch is available" if hasattr(js, "fetch") else "Fetch NOT available")
except Exception as e:
    print(f"[Warning] JS bridge not available: {e}")



pygame.init()

#Screen size
WIDTH, HEIGHT = 1280,720
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("SkyTyper!")

#Backgrounds
SKYDAY = pygame.image.load("sky_day.jpg")
SKYNIGHT = pygame.image.load("sky_night.jpg") 
background_image = SKYDAY  #Default 
background_scaled = pygame.transform.scale(background_image, (WIDTH, HEIGHT))

#Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 71, 77)
BLUE = (95, 144, 250)
GREEN = (57, 248, 72)
TEXT_GREEN = (119,228,119)
PINK = (255, 105, 180)
GRAY = (251, 251, 251)
YELLOW = (255, 255, 0)

#Fonts
font = pygame.font.Font("PressStart2P-Regular.ttf", 32)
small_font = pygame.font.Font("PressStart2P-Regular.ttf", 24)

#Clock for controlling frame rate
clock = pygame.time.Clock()

#Game states
START = "start"
SETTINGS = "settings"
PLAYING = "playing"
GAME_OVER = "game_over"
INSTRUCTIONS = "instructions"
ACHIEVEMENTS = "achievements" 
POWERUPS = "powerups"
game_state = START




#Word lists
word_list = ["Apple", "Banana", "Cat", "Dog", "Eel", "Flower", "Grapes", "Honey", "Idea", "Juice", "Key", "Lemon","Monkey", "Night", "Owl", "Play"]
word_list_hard = ["Algorithm", "Binary", "California", "Dragonfruit", "Encryption", "Fireball", "Gatekeeper", "Hypertext", "Intelligence", "Kaleidoscope", "Laboratory", "Monkeytype", "Nitrotype", "Organization"]

#Load heart images
HEART_IMAGE = pygame.image.load("heart.png").convert_alpha()  # Ensure you have a heart.png file
EMPTY_HEART_IMAGE = pygame.image.load("empty_heart.png").convert_alpha()  # Ensure you have an empty_heart.png file
HEART_SIZE = 40  # Size of the heart images

# Powerups
powerups = {
    'shield': {'unlocked': False, 'equipped': False, 'uses': 0, 'active': False, 'duration': 0},
    'slow_time': {'unlocked': False, 'equipped': False, 'uses': 0, 'active': False, 'duration': 0},
    'word_clear': {'unlocked': False, 'equipped': False, 'uses': 0, 'active': False, 'duration': 0},
    'auto_type': {'unlocked': False, 'equipped': False, 'uses': 0, 'active': False, 'duration': 0}
}

equipped_powerups = []  # Max 2 powerups
powerup_cooldowns = {}  # Track cooldowns for each powerup

# Power-up constants
SHIELD_DURATION = 3000
SHIELD_COOLDOWN = 10000 # 3 seconds of protection
SLOW_TIME_DURATION = 5000  # 5 seconds of slow motion
SLOW_TIME_COOLDOWN = 10000
WORD_CLEAR_COOLDOWN = 20000  # 20 second cooldown
AUTO_TYPE_COOLDOWN = 10000  # 10 second cooldown

# Achievement tracking for power-ups
total_shields_used = 0
total_slow_times_used = 0
total_word_clears_used = 0
total_auto_types_used = 0

total_words_completed = 0
total_play_time = 0
session_start_time = 0

class FallingWord:
    def __init__(self, text, speed, is_hard=False):
        self.text = text
        self.speed = speed
        self.width = font.size(text)[0]  #Get the width 
        self.height = font.size(text)[1]  #Get the height
        self.x = random.randint(50, WIDTH - self.width - 50)  
        self.y = 0
        self.progress = 0  #Track how many letters have been typed
        self.completed = False  #Track if the word is fully typed
        self.completion_time = 0  #Track when completed
        self.is_hard = is_hard
    def check_completion(self):
        if self.progress == len(self.text):
            self.completed = True
            self.completion_time = pygame.time.get_ticks()
            self.progress = 0
    def move(self):
        if not self.completed:
            self.y += self.speed

    def draw(self, screen):
        if self.completed:
            fadetime = 750
            #Glow red for hard words, green for normal words
            elapsed = pygame.time.get_ticks() - self.completion_time
            if elapsed < fadetime:
                alpha = max(0, 255 - int(255 * (elapsed / fadetime)))  #Fade effect
                fade_up = int(30 * (elapsed / fadetime))  #Move upward while fading
                color = RED if self.is_hard else GREEN
                text_surface = font.render(self.text, True, color)
                text_surface.set_alpha(alpha)
                screen.blit(text_surface, (self.x, (self.y - fade_up)))
            return

        #Color typed part in blue (pink for hard words)
        correct_part = self.text[:self.progress]
        color = PINK if self.is_hard else BLUE
        correct_surface = font.render(correct_part, True, color)
        screen.blit(correct_surface, (self.x, self.y))

        
        remaining_part = self.text[self.progress:]
        remaining_surface = font.render(remaining_part, True, text_color)
        screen.blit(remaining_surface, (self.x + correct_surface.get_width(), self.y))

    def off_screen(self):
        return self.y > HEIGHT


    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

#Function to check if a new word overlaps with existing words
def is_overlapping(new_word, existing_words):
    new_rect = new_word.get_rect()
    for word in existing_words:
        if new_rect.colliderect(word.get_rect()):
            return True
    return False

#Function to count instances of a word on the screen
def count_word_instances(word_text):
    return sum(1 for word in falling_words if word.text == word_text)

# Function to draw a button
def draw_button(text, x, y, width, height, border_color, hover=False):

    if text_color == BLACK:
        inactive_color = WHITE
        hover_color = BLUE
    else:
        inactive_color = BLUE
        hover_color = (70,120,200)

    color = hover_color if hover else inactive_color
    

    # Draw the border (slightly larger than the button)
    if text_color == WHITE  and border_color == BLUE:
        dynamic_border = WHITE
    else:
        dynamic_border = border_color
    border_rect = pygame.Rect(x - 2, y - 2, width + 4, height + 4)
    pygame.draw.rect(screen, dynamic_border, border_rect)

    # Draw the button
    button_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(screen, color, button_rect)

    # Draw the text
    text_surface = small_font.render(text, True, text_color)
    text_rect = text_surface.get_rect(center=(x + width / 2, y + height / 2))
    screen.blit(text_surface, text_rect)

# Function to resize the screen
def resize_screen(width, height):
    global WIDTH, HEIGHT, screen, background_scaled
    WIDTH, HEIGHT = width, height
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    background_scaled = pygame.transform.scale(background_image, (WIDTH, HEIGHT))

# Function to draw hearts
def draw_hearts(lives):
    for i in range(3):  
        x = WIDTH - (3 - i) * (HEART_SIZE + 20) 
        y = 45
        if i < lives:
            screen.blit(HEART_IMAGE, (x, y))  
        else:
            screen.blit(EMPTY_HEART_IMAGE, (x, y))  

# Function to draw combo
def draw_combo(combo_level, combo_lost_time, last_combo, combo_display_time):
    current_time = pygame.time.get_ticks()
    
    # Show combo when active
    if combo_level > 0:
        elapsed = current_time - last_combo
        if elapsed < combo_display_time:
            alpha = max(0, 255 - int(255 * (elapsed / combo_display_time)))
            combo_text = f"COMBO x{combo_level}!"
            combo_surface = font.render(combo_text, True, GREEN)
            combo_surface.set_alpha(alpha)
            screen.blit(combo_surface, (WIDTH // 2 - combo_surface.get_width() // 2, 40))
    
    # FIXED: Show "COMBO LOST!" when combo is lost
    elif combo_lost_time > 0:  # NEW: Check if we have a lost time recorded
        elapsed = current_time - combo_lost_time
        if elapsed < combo_display_time:
            alpha = max(0, 255 - int(255 * (elapsed / combo_display_time)))
            lost_text = "COMBO LOST!"
            lost_surface = font.render(lost_text, True, RED)
            lost_surface.set_alpha(alpha)
            screen.blit(lost_surface, (WIDTH // 2 - lost_surface.get_width() // 2, 40))
        else:
            # FIXED: Clear the combo_lost_time after display period ends
            combo_lost_time = 0

def use_powerup(powerup_name):
    global lives, falling_words, word_speed, powerups, powerup_cooldowns
    global total_shields_used, total_slow_times_used, total_word_clears_used, total_auto_types_used
    global combo_level, score
    current_time = pygame.time.get_ticks()
    
    # Check if powerup is on cooldown
    if powerup_name in powerup_cooldowns and current_time < powerup_cooldowns[powerup_name]:
        return  # Still on cooldown
    
    if powerup_name == 'shield':
        powerups['shield']['active'] = True
        powerups['shield']['duration'] = current_time + SHIELD_DURATION
        powerups['shield']['uses'] += 1
        total_shields_used += 1
        
        
    elif powerup_name == 'slow_time':
        powerups['slow_time']['active'] = True
        powerups['slow_time']['duration'] = current_time + SLOW_TIME_DURATION
        powerups['slow_time']['uses'] += 1
        total_slow_times_used += 1
        

    elif powerup_name == 'word_clear':
        falling_words.clear()  # Remove all words
        powerup_cooldowns['word_clear'] = current_time + WORD_CLEAR_COOLDOWN
        powerups['word_clear']['uses'] += 1
        total_word_clears_used += 1
        
    elif powerup_name == 'auto_type':
        # Auto-complete the first word
        if falling_words:
            word = falling_words[0]
            word.progress = len(word.text)
            word.check_completion()
            if word.completed:
                base_points = 500 if word.is_hard else 100
                combo_level += 1
                bonus_points = combo_level * 10
                score += (base_points + bonus_points)
        
        powerup_cooldowns['auto_type'] = current_time + AUTO_TYPE_COOLDOWN
        powerups['auto_type']['uses'] += 1
        total_auto_types_used += 1

def update_powerups():
    """Update power-up states and durations"""
    current_time = pygame.time.get_ticks()
    
    # Check shield duration
    if powerups['shield']['active'] and current_time > powerups['shield']['duration']:
        powerups['shield']['active'] = False
        # Cooldown
        powerup_cooldowns['shield'] = current_time + SHIELD_COOLDOWN
    # Check slow time duration
    if powerups['slow_time']['active'] and current_time > powerups['slow_time']['duration']:
        powerups['slow_time']['active'] = False
        # Cooldown
        powerup_cooldowns['slow_time'] = current_time + SLOW_TIME_COOLDOWN
def check_powerup_unlocks():
    """Check if player has met requirements to unlock power-ups"""
    # Shield: Score 5,000 points
    if max_score >= 5000 or max_hard_score >= 5000:
        powerups['shield']['unlocked'] = True
    
    # Slow Time: Get a 10x combo
    if combo_level >= 10:
        powerups['slow_time']['unlocked'] = True
    
    # Word Clear: Complete 500 words total
    # (You'd need to add a word completion counter)
    if total_words_completed >= 10:
        powerups['word_clear']['unlocked'] = True
    
    # Auto Type: Play for 10 minutes total
    # (You'd need to add total play time tracking)
    if total_play_time >= 60000:  # 1 minutes in milliseconds
        powerups['auto_type']['unlocked'] = True

def draw_powerup_ui():
    """Draw power-up UI elements during gameplay"""
    current_time = pygame.time.get_ticks()
    
    # Draw equipped power-ups
    for i, powerup_name in enumerate(equipped_powerups):
        x = 10 + i * 200
        y = HEIGHT - 140
        
        # Power-up box
        powerup_rect = pygame.Rect(x, y, 180, 80)
        
        # Check if on cooldown
        on_cooldown = powerup_name in powerup_cooldowns and current_time < powerup_cooldowns[powerup_name]
        
        if powerups[powerup_name]['active']:
            color = GREEN
        elif on_cooldown:
            color = RED
        else:
            color = BLUE
            
        pygame.draw.rect(screen, color, powerup_rect)
        pygame.draw.rect(screen, text_color, powerup_rect, 2)
        
        # Power-up name
        name_surface = pygame.font.Font("PressStart2P-Regular.ttf", 14).render(powerup_name.replace('_', ' ').title(), True, text_color)
        name_rect = name_surface.get_rect(center=(x + 90, y + 15))
        screen.blit(name_surface, name_rect)
        
        # Key binding
        key_surface = pygame.font.Font("PressStart2P-Regular.ttf", 13).render(f"Press {i+1}", True, text_color)
        key_rect = key_surface.get_rect(center=(x + 90, y + 35))
        screen.blit(key_surface, key_rect)
        
        # Cooldown timer
        if on_cooldown:
            cooldown_remaining = (powerup_cooldowns[powerup_name] - current_time) // 1000
            timer_surface = pygame.font.Font("PressStart2P-Regular.ttf", 12).render(f"{cooldown_remaining}s", True, WHITE)
            screen.blit(timer_surface, (x + 90, y + 55))

        elif powerups[powerup_name]['active'] and powerup_name in ['shield', 'slow_time']:
            duration_remaining = (powerups[powerup_name]['duration'] - current_time) // 1000
            if duration_remaining > 0:
                duration_surface = pygame.font.Font("PressStart2P-Regular.ttf", 12).render(f"Active: {duration_remaining}s", True, WHITE)
                duration_rect = duration_surface.get_rect(center=(x + 90, y + 55))
                screen.blit(duration_surface, duration_rect)
    effect_y =160
    # Draw active effects
    if powerups['shield']['active']:
        shield_text = "SHIELD ACTIVE!"
        shield_surface = font.render(shield_text, True, GREEN)
        screen.blit(shield_surface, (WIDTH // 2 - shield_surface.get_width() // 2, 100))
        effect_y += 40
    if powerups['slow_time']['active']:
        slow_text = "TIME SLOWED!"
        slow_surface = font.render(slow_text, True, BLUE)
        screen.blit(slow_surface, (WIDTH // 2 - slow_surface.get_width() // 2, 140))

def end_game_session():
    global total_play_time, session_start_time
    if session_start_time > 0:
        session_duration = pygame.time.get_ticks() - session_start_time
        total_play_time += session_duration
        session_start_time = 0
        print(f"[DEBUG] Session ended. Duration: {session_duration}ms, Total: {total_play_time}ms")


#Game variables
text_color = BLACK
lives = 3
score = 0
falling_words = []
word_speed = 2
spawn_rate = 2
word_speed_add = 0.00001
spawn_rate_add = 0.00001
input_text = ""
button_width = 400
start_time = pygame.time.get_ticks()
MAX_WORDS_ON_SCREEN = 20

# Combo

combo_level = 0
combo_start_time = 0
combo_lost_time = 0
combo_display_time = 3000
last_combo = 0

#For entering name and saving score
player_name = ""
active_input = False
input_box = pygame.Rect(WIDTH // 2 -150, HEIGHT //2, 300, 50)


# Backspace continuous deletion 
backspace_held = False
backspace_start_time = 0
last_backspace_time = 0
BACKSPACE_HOLD = 500
BACKSPACE_REPEAT = 100


clear_input = False  
is_fullscreen = False
windowed_size = (WIDTH, HEIGHT)
hard_mode = False
prev_mouse_click = False

# Achievement tracking - ADD THESE
max_score = 0
max_hard_score = 0
scroll_offset = 0  # For scrolling
SCROLL_SPEED = 20

#Main loop
async def main():


    global input_text, clear_input, backspace_held, backspace_start_time, last_backspace_time, BACKSPACE_HOLD, BACKSPACE_REPEAT
    global combo_level, combo_start_time, last_combo, combo_display_time, combo_lost_time
    global player_name, active_input, input_box
    global game_state, lives, score, falling_words, word_speed, spawn_rate, word_speed_add, spawn_rate_add, MAX_WORDS_ON_SCREEN
    global WIDTH, HEIGHT, screen, background_image, background_scaled, text_color, is_fullscreen, windowed_size
    global HEART_IMAGE, EMPTY_HEART_IMAGE, HEART_SIZE
    global font, small_font, clock, button_width
    global hard_mode, prev_mouse_click
    global max_score, max_hard_score, scroll_offset
    global total_words_completed, total_play_time, session_start_time
    global total_shields_used, total_slow_times_used, total_word_clears_used, total_auto_types_used

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_pressed()
        current_time = pygame.time.get_ticks()
        try:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False


                elif event.type == pygame.VIDEORESIZE:
                    # Handle screen resizing
                    resize_screen(event.w, event.h)

                elif event.type == pygame.KEYDOWN:
                    if game_state == PLAYING:
                        if event.key == pygame.K_BACKSPACE:
                            input_text = input_text[:-1]  
                            backspace_held = True
                            backspace_start_time = current_time

                            # Combo lost
                            if combo_level > 0:  # Only show "COMBO LOST!" if there was actually a combo
                                combo_lost_time = pygame.time.get_ticks()  # NEW: Record when combo was lost
                            combo_level = 0
                        
                        # Powerups - MOVED INSIDE KEYDOWN CHECK
                        elif event.key == pygame.K_1:  # Use first equipped power-up
                            if len(equipped_powerups) > 0:
                                use_powerup(equipped_powerups[0])
                        elif event.key == pygame.K_2:  # Use second equipped power-up
                            if len(equipped_powerups) > 1:
                                use_powerup(equipped_powerups[1])

                        else:
                            if event.unicode.isalpha():
                                if clear_input:
                                    input_text = ""
                                    clear_input = False

                                input_text += event.unicode  #add typed character
                            
                                completed_word = False

                                #Update for words that match the input
                                for word in falling_words:
                                    

                                    if word.text.startswith(input_text):
                                        word.progress = len(input_text)
                                        word.check_completion()
                                        if word.completed:
                                            if word.is_hard and lives < 3 and not hard_mode:
                                                lives += 1

                                            #Points
                                            base_points = 500 if word.is_hard else 100
                                            combo_level += 1
                                            bonus_points = combo_level * 10
                                            score += (base_points + bonus_points)
                                            
                                            # Achievemnets
                                            total_words_completed += 1
                                            if hard_mode:
                                                max_hard_score = max(max_hard_score, score)
                                            else:
                                                max_score = max(max_score, score)
                                            

                                            input_text = ""
                                            clear_input = True
                                            completed_word = True

                                            #Combo display
                                            
                                            last_combo = pygame.time.get_ticks()
                                    else:
                                        word.progress = 0



                # Scroll and mouse handling - SEPARATE FROM KEYDOWN
                elif event.type == pygame.MOUSEBUTTONDOWN:

                    # Scroll handling
                    if game_state == ACHIEVEMENTS:
                        if event.button == 4:  # Scroll up
                            scroll_offset = max(0, scroll_offset - SCROLL_SPEED)
                        elif event.button == 5:  # Scroll down
                            scroll_offset = min(200, scroll_offset + SCROLL_SPEED)  # Limit scroll

                #Stop deleting
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_BACKSPACE:
                        backspace_held = False

            #Held Deletion    
            if backspace_held and game_state == PLAYING:
                if current_time - backspace_start_time >= BACKSPACE_HOLD:
                    if current_time - last_backspace_time >= BACKSPACE_REPEAT:
                        if input_text:
                            input_text = input_text[:-1]

                            # Combo lost
                            if combo_level > 0:  # Only show "COMBO LOST!" if there was actually a combo
                                combo_lost_time = pygame.time.get_ticks()  # NEW: Record when combo was lost
                            combo_level = 0


                            last_backspace_time = current_time
                        for word in falling_words:
                            if word.text.startswith(input_text):
                                word.progress = len(input_text)
                            else:
                                word.progress = 0


            #Clear Screen
            screen.blit(background_scaled, (0, 0))

            #Title Screen
            if game_state == START:

                title_surface = font.render("SkyTyper!", True, text_color)
                title_rect = title_surface.get_rect(center=(WIDTH // 2, HEIGHT // 4))
                screen.blit(title_surface, title_rect)

                #Instructions
                instructions_button = pygame.Rect(20, 20, 50, 50)  # Top left corner
                draw_button("?", instructions_button.x, instructions_button.y, instructions_button.width, instructions_button.height, YELLOW, instructions_button.collidepoint(mouse_pos))
                if instructions_button.collidepoint(mouse_pos) and mouse_click[0]:
                    game_state = INSTRUCTIONS

                #Start button
                start_button = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 - 50, button_width, 50)
                draw_button("Start", start_button.x, start_button.y, start_button.width, start_button.height, GREEN, start_button.collidepoint(mouse_pos))
                if start_button.collidepoint(mouse_pos) and mouse_click[0]:
                    game_state = PLAYING
                    lives = 3  
                    score = 0  
                    falling_words = []  
                    input_text = ''
                    start_time = pygame.time.get_ticks()  
                    powerup_cooldowns.clear()
                    session_start_time = pygame.time.get_ticks()
                    for powerup in powerups.values():
                        powerup['active'] = False
                        powerup['duration'] = 0

                # Settings button
                settings_button = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 + 50, button_width, 50)
                draw_button("Settings", settings_button.x, settings_button.y, settings_button.width, settings_button.height, BLUE, settings_button.collidepoint(mouse_pos))
                if settings_button.collidepoint(mouse_pos) and mouse_click[0]:
                    game_state = SETTINGS

                # Powerup_button
                powerup_button = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 + 150, button_width, 50)
                draw_button("Power-Ups", powerup_button.x, powerup_button.y, powerup_button.width, powerup_button.height, PINK, powerup_button.collidepoint(mouse_pos))
                if powerup_button.collidepoint(mouse_pos) and mouse_click[0]:
                    game_state = POWERUPS
                
                # Achievements button
                achievements_button = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 + 250, button_width, 50)
                draw_button("Achievements", achievements_button.x, achievements_button.y, achievements_button.width, achievements_button.height, YELLOW, achievements_button.collidepoint(mouse_pos))
                if achievements_button.collidepoint(mouse_pos) and mouse_click[0]:
                    game_state = ACHIEVEMENTS

            elif game_state == INSTRUCTIONS:
                # Draw instructions screen
                title_surface = font.render("Instructions", True, text_color)
                title_rect = title_surface.get_rect(center=(WIDTH // 2, HEIGHT // 4 - 100))
                screen.blit(title_surface, title_rect)

                instructions = [
                    [('- Type the words that fall from the sky!', text_color)],
                    [('-', text_color), ('Normal words', BLUE), ('are worth', text_color), ('100 points...', BLUE)],
                    [('  ... while', text_color), ('hard words', PINK), ('are worth', text_color), ('500!', PINK)],
                    [('- Consecutive words add to a', text_color), ('combo...', TEXT_GREEN)],
                    [('  ... which gives', text_color), ('bonus score!', TEXT_GREEN)],
                    [('- But making mistakes will', text_color), ('lose', RED), ('the combo!', text_color)],
                    [('BONUS!', text_color), ("Hard Mode", RED), ("for a extra challenge!", text_color)],
                    [("(More", text_color), ("hard words", PINK), (", no healing.)", text_color)]
                ] 
                
                        
                # Instruction box dimensions
                box_width = 1080
                box_height = len(instructions) * 40 + 40
                box_x = WIDTH // 2 - box_width // 2
                box_y = HEIGHT // 4 

                # Semi-transparent box surface
                instruction_box = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
                instruction_box.fill((255, 255, 255, 100))  # RGBA: black with alpha 180 (semi-transparent)

                screen.blit(instruction_box, (box_x, box_y))
            
                for i, line_parts in enumerate(instructions):
                    x_cursor = WIDTH // 8  # Start x position
                    y = HEIGHT // 4 + 40 + i * 40  # y position for the line

                    for word, color in line_parts:
                        word_surface = small_font.render(word + " ", True, color)
                        screen.blit(word_surface, (x_cursor, y))
                        x_cursor += word_surface.get_width()
                

                # Back button
                back_button = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 + 200, button_width, 50)
                draw_button("Back", back_button.x, back_button.y, back_button.width, back_button.height, RED, back_button.collidepoint(mouse_pos))
                if back_button.collidepoint(mouse_pos) and mouse_click[0]:
                    game_state = START

            elif game_state == SETTINGS:
                # Draw settings screen 
                title_surface = font.render("Settings", True, text_color)
                title_rect = title_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 200))
                screen.blit(title_surface, title_rect)

                # Day background button
                day_button = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2-100, button_width, 50)
                draw_button("Day time", day_button.x, day_button.y, day_button.width, day_button.height, BLUE, day_button.collidepoint(mouse_pos))
                if day_button.collidepoint(mouse_pos) and mouse_click[0]:
                    background_image = SKYDAY  # Set to day background
                    background_scaled = pygame.transform.scale(background_image, (WIDTH, HEIGHT))
                    text_color = BLACK

                # Night background button
                night_button = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2, button_width, 50)
                draw_button("Night time ", night_button.x, night_button.y, night_button.width, night_button.height, BLUE, night_button.collidepoint(mouse_pos))
                if night_button.collidepoint(mouse_pos) and mouse_click[0]:
                    background_image = SKYNIGHT  # Set to night background
                    background_scaled = pygame.transform.scale(background_image, (WIDTH, HEIGHT))
                    text_color = WHITE

                # Hard mode toggle button
                hard_mode_button = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 + 100, button_width, 50)
                button_text = "Hard Mode: ON" if hard_mode else "Hard Mode: OFF"
                button_color = RED if hard_mode else BLUE
                draw_button(button_text, hard_mode_button.x, hard_mode_button.y, hard_mode_button.width, hard_mode_button.height, button_color, hard_mode_button.collidepoint(mouse_pos))

                # Only toggle if mouse was just pressed (not held)
                if hard_mode_button.collidepoint(mouse_pos) and mouse_click[0] and not prev_mouse_click:
                    hard_mode = not hard_mode

                # Update previous mouse state at the end of the main loop
                prev_mouse_click = mouse_click[0]

                # Back button
                back_button = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 + 200, button_width, 50)
                draw_button("Back", back_button.x, back_button.y, back_button.width, back_button.height, RED, back_button.collidepoint(mouse_pos))
                if back_button.collidepoint(mouse_pos) and mouse_click[0]:
                    game_state = START

            elif game_state == PLAYING:

                # Add new words, no duplicates and overlaps
                if random.randint(1, 100) < spawn_rate and len(falling_words) < MAX_WORDS_ON_SCREEN:
                    print(f"[DEBUG] Attempting to spawn word. Current words: {len(falling_words)}, Spawn rate: {spawn_rate}")
                    is_hard = random.randint(1, 10) == 1 if hard_mode else random.randint(1, 40) == 1
                    word_pool = word_list_hard if is_hard else word_list
                    new_word_text = random.choice(word_pool)
                    print(f"[DEBUG] Selected word: {new_word_text}, Is hard: {is_hard}")

                    if count_word_instances(new_word_text) < 1:
                        speed = word_speed * 1.25 if is_hard else word_speed  # Hard words fall faster
                        new_word = FallingWord(new_word_text, speed, is_hard)

                        # Ensure the new word does not overlap with existing words
                        attempts = 0
                        while is_overlapping(new_word, falling_words) and attempts < 100:
                            new_word.x = random.randint(50, WIDTH - new_word.width - 50)
                            attempts += 1
                        print(f"[DEBUG] Overlap attempts: {attempts}")

                        if attempts < 100:  # Only add the word if a valid position is found
                            falling_words.append(new_word)
                            print(f"[DEBUG] Word added successfully! Total words now: {len(falling_words)}")
                        else:
                             print("[DEBUG] Failed to find non-overlapping position")
                    else:
                        print(f"[DEBUG] Word {new_word_text} already exists on screen")

                # Update word positions and remove completed words after 1 second
                for word in falling_words[:]:  

                    if powerups['slow_time']['active']:
                        original_speed = word.speed
                        word.speed *= 0.3
                        word.move()
                        word.speed = original_speed
                    else:
                        word.move()

                    if word.off_screen():
                        if powerups['shield']['active']:
                            falling_words.remove(word)
                        else:

                            lives -= 1

                            # Combo lost
                            if combo_level > 0:  # Only show "COMBO LOST!" if there was actually a combo
                                combo_lost_time = pygame.time.get_ticks()  # NEW: Record when combo was lost
                            combo_level = 0
                            falling_words.remove(word)
                    if lives == 0:
                        end_game_session()
                        game_state = GAME_OVER
                    
                    elif word.completed and pygame.time.get_ticks() - word.completion_time >= 1000:
                        falling_words.remove(word)  # Remove the word after glowing for 1 second

                #Increase speed over time
                word_speed += word_speed_add
                spawn_rate += spawn_rate_add

                #Draw falling words
                for word in falling_words:
                    word.draw(screen)

                #Draw input text
                input_surface = font.render(input_text, True, text_color)
                screen.blit(input_surface, (10, HEIGHT - 50))

                #Draw score, timer, and hearts
                elapsed_time = (pygame.time.get_ticks() - start_time) // 1000  
                score_surface = font.render(f"Score: {score}", True, text_color)
                timer_surface = font.render(f"Time: {elapsed_time}", True, text_color)
                screen.blit(score_surface, (10, 10))
                screen.blit(timer_surface, (WIDTH - 300, 10))
                draw_hearts(lives)
                draw_combo(combo_level, combo_lost_time, last_combo, combo_display_time)
                draw_powerup_ui()
                update_powerups()
                check_powerup_unlocks()

            elif game_state == GAME_OVER:
                #time
                if session_start_time > 0:
                    session_duration = pygame.time.get_ticks() - session_start_time 
                    total_play_time += session_duration
                    session_start_time = 0
                    print(total_play_time)
                
                #Draw game over screen
                title_surface = font.render("Game Over", True, text_color)
                title_rect = title_surface.get_rect(center=(WIDTH // 2, HEIGHT // 4 + 50))
                screen.blit(title_surface, title_rect)
                #Score
                score_surface = font.render(f"score:{score}", True, text_color)
                score_rect = score_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 25))
                screen.blit(score_surface, score_rect)
                
                #Return to home button
                home_button = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 + 100, button_width, 50)
                draw_button("Home", home_button.x, home_button.y, home_button.width, home_button.height, BLUE, home_button.collidepoint(mouse_pos))
                if home_button.collidepoint(mouse_pos) and mouse_click[0]:
                    game_state = START
                    #Reset allat
                    lives = 3  
                    score = 0  
                    falling_words = []  
                    word_speed = 2 
                    spawn_rate = 2
                    player_name = ""  
                    hard_mode = False
                    powerup_cooldowns.clear()
                    for powerup in powerups.values():
                        powerup['active'] = False
                        powerup['duration'] = 0
                

            elif game_state == ACHIEVEMENTS:
                # Achievement definitions
                achievements = [
                    # Score achievements
                    {"name": "Rookie Scorer", "desc": "Score 10,000 points", "unlocked": max_score >= 10000},
                    {"name": "High Scorer", "desc": "Score 20,000 points", "unlocked": max_score >= 20000},
                    {"name": "Score Master", "desc": "Score 50,000 points", "unlocked": max_score >= 50000},
                    # Hard mode achievements  
                    {"name": "Hard Rookie", "desc": "Score 10,000 points in Hard Mode", "unlocked": max_hard_score >= 10000},
                    {"name": "Hard Scorer", "desc": "Score 20,000 points in Hard Mode", "unlocked": max_hard_score >= 20000},
                    {"name": "Hard Master", "desc": "Score 50,000 points in Hard Mode", "unlocked": max_hard_score >= 50000},
                    # Powerup achievements
                    {"name": "First Shield", "desc": "Score 5,000 points to unlock Shield", "unlocked": powerups['shield']['unlocked']},
                    {"name": "Time Master", "desc": "Get 10x combo to unlock Slow Time", "unlocked": powerups['slow_time']['unlocked']},
                    {"name": "Word Warrior", "desc": "Complete 10 words to unlock Word Clear", "unlocked": powerups['word_clear']['unlocked']},
                    {"name": "Speed Typer", "desc": "Play 1 minutes to unlock Auto Type", "unlocked": powerups['auto_type']['unlocked']},
                    
                    # Power-up usage achievements
                    {"name": "Shield Bearer", "desc": "Use Shield power-up 25 times", "unlocked": total_shields_used >= 25},
                    {"name": "Time Turtle", "desc": "Use Slow Time 25 times", "unlocked": total_slow_times_used >= 25},
                    {"name": "Clear Skies", "desc": "Use Word Clear 25 times", "unlocked": total_word_clears_used >= 25},
                    {"name": "Lazy Typer", "desc": "Use Auto Type 25 times", "unlocked": total_auto_types_used >= 25},
                ]

                # Helper function to wrap text
                def wrap_text(text, font, max_width):
                    """Split text into multiple lines that fit within max_width"""
                    words = text.split(' ')
                    lines = []
                    current_line = ""
                    
                    for word in words:
                        test_line = current_line + (" " if current_line else "") + word
                        test_width = font.size(test_line)[0]
                        
                        if test_width <= max_width:
                            current_line = test_line
                        else:
                            if current_line:
                                lines.append(current_line)
                            current_line = word
                    
                    if current_line:
                        lines.append(current_line)
                    
                    return lines

                # Achievement display settings
                achievement_width = 380
                achievement_height = 120   # Increased from 100 to accommodate more lines
                achievements_per_row = 3
                spacing_x = 20
                spacing_y = 140  # Increased spacing for taller boxes
                start_x = WIDTH // 2 - (achievements_per_row * achievement_width + (achievements_per_row - 1) * spacing_x) // 2
                start_y = HEIGHT // 4 - 50 - scroll_offset 

                # Create fonts for text wrapping
                desc_font = pygame.font.Font("PressStart2P-Regular.ttf", 16)


                # Draw achievements
                for i, achievement in enumerate(achievements):
                    row = i // achievements_per_row
                    col = i % achievements_per_row
                    
                    x = start_x + col * (achievement_width + spacing_x)
                    y = start_y + row * spacing_y
                    
                    # Only draw if visible on screen AND below the title bar
                    if y + achievement_height > 80 and y < HEIGHT:

                        if text_color == BLACK:  # Day mode
                            inactive_color = WHITE
                            hover_color = BLUE
                        else:  # Night mode
                            inactive_color = BLUE
                            hover_color = (70, 120, 200)

                        # Achievement box
                        achievement_rect = pygame.Rect(x, y, achievement_width, achievement_height)
                        is_hovering = achievement_rect.collidepoint(mouse_pos)
                        if achievement["unlocked"]:
                            box_color = hover_color if is_hovering else inactive_color
                        else:
                            box_color = hover_color if is_hovering else inactive_color                 
                        pygame.draw.rect(screen, box_color, achievement_rect)

                        # Border color based on unlock status
                        border_color = GREEN if achievement["unlocked"] else text_color
                        pygame.draw.rect(screen, border_color, achievement_rect, 3)
                        
                        # Achievement name
                        name_surface = small_font.render(achievement["name"], True, text_color)
                        name_rect = name_surface.get_rect(center=(x + achievement_width // 2, y + 20))
                        screen.blit(name_surface, name_rect)
                        
                        # Wrap the description text
                        max_desc_width = achievement_width - 20  # Leave 10px padding on each side
                        wrapped_lines = wrap_text(achievement["desc"], desc_font, max_desc_width)
                        
                        # Draw wrapped description lines
                        line_height = 18  # Space between lines
                        total_text_height = len(wrapped_lines) * line_height
                        start_desc_y = y + 50  # Start description below the name
                        
                        for line_idx, line in enumerate(wrapped_lines):
                            line_surface = desc_font.render(line, True, text_color)
                            line_rect = line_surface.get_rect(center=(x + achievement_width // 2, start_desc_y + line_idx * line_height))
                            screen.blit(line_surface, line_rect)

                # Draw FIXED title bar at top
                title_bar_height = 80
                title_bar = pygame.Surface((WIDTH, title_bar_height), pygame.SRCALPHA)
                title_bar.fill((179, 235, 242, 190)) #179,235,242
                screen.blit(title_bar, (0, 0))
                
                title_surface = font.render("Achievements", True, WHITE)
                title_rect = title_surface.get_rect(center=(WIDTH // 2, title_bar_height // 2))
                screen.blit(title_surface, title_rect)

                # Scroll indicator
                if len(achievements) > 6 and scroll_offset == 0:
                    scroll_text = "Scroll to see more"
                    scroll_surface = pygame.font.Font("PressStart2P-Regular.ttf", 16).render(scroll_text, True, text_color)
                    scroll_rect = scroll_surface.get_rect(center=(WIDTH // 2, HEIGHT - 80))
                    screen.blit(scroll_surface, scroll_rect)

                # Back button at bottom
                back_button = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT - 60, button_width, 50)
                draw_button("Back", back_button.x, back_button.y, back_button.width, back_button.height, RED, back_button.collidepoint(mouse_pos))
                if back_button.collidepoint(mouse_pos) and mouse_click[0]:
                    game_state = START
                    scroll_offset = 0
            
            elif game_state == POWERUPS:
                # Draw power-up equipment screen
                title_surface = font.render("Power-Up Equipment", True, text_color)
                title_rect = title_surface.get_rect(center=(WIDTH // 2, 80))
                screen.blit(title_surface, title_rect)
                
                if text_color == BLACK:
                    inactive_color = WHITE
                    hover_color = BLUE
                else:
                    inactive_color = BLUE                        
                    hover_color = (70, 120, 200)

                # Equipment slots
                slot_width = 200
                slot_height = 60
                slot1_rect = pygame.Rect(WIDTH // 2 - 220, 200, slot_width, slot_height)
                slot2_rect = pygame.Rect(WIDTH // 2 + 20, 200, slot_width, slot_height)
                
                # Draw equipment slots
                pygame.draw.rect(screen, BLUE if len(equipped_powerups) > 0 else inactive_color, slot1_rect)
                pygame.draw.rect(screen, text_color, slot1_rect, 3)
                
                pygame.draw.rect(screen, BLUE if len(equipped_powerups) > 1 else inactive_color, slot2_rect)
                pygame.draw.rect(screen, text_color, slot2_rect, 3)
                
                # Slot labels
                slot1_text = "SLOT [1]"
                slot2_text = "SLOT [2]"
                
                slot1_surface = small_font.render(slot1_text, True, text_color)
                slot1_text_rect = slot1_surface.get_rect(center=(slot1_rect.centerx, slot1_rect.y - 20))
                screen.blit(slot1_surface, slot1_text_rect)
                
                slot2_surface = small_font.render(slot2_text, True, text_color)
                slot2_text_rect = slot2_surface.get_rect(center=(slot2_rect.centerx, slot2_rect.y - 20))
                screen.blit(slot2_surface, slot2_text_rect)
                
                # Show equipped power-ups in slots
                if len(equipped_powerups) > 0:
                    equipped1_surface = pygame.font.Font("PressStart2P-Regular.ttf", 16).render(
                        equipped_powerups[0].replace('_', ' ').title(), True, text_color)
                    equipped1_rect = equipped1_surface.get_rect(center=slot1_rect.center)
                    screen.blit(equipped1_surface, equipped1_rect)
                else:
                    empty1_surface = pygame.font.Font("PressStart2P-Regular.ttf", 16).render("Empty", True, text_color)
                    empty1_rect = empty1_surface.get_rect(center=slot1_rect.center)
                    screen.blit(empty1_surface, empty1_rect)
                
                if len(equipped_powerups) > 1:
                    equipped2_surface = pygame.font.Font("PressStart2P-Regular.ttf", 16).render(
                        equipped_powerups[1].replace('_', ' ').title(), True, text_color)
                    equipped2_rect = equipped2_surface.get_rect(center=slot2_rect.center)
                    screen.blit(equipped2_surface, equipped2_rect)
                else:
                    empty2_surface = pygame.font.Font("PressStart2P-Regular.ttf", 16).render("Empty", True, text_color)
                    empty2_rect = empty2_surface.get_rect(center=slot2_rect.center)
                    screen.blit(empty2_surface, empty2_rect)
                
                # Available power-ups
                available_y = 280
                powerup_names = ['shield', 'slow_time', 'word_clear', 'auto_type']
                powerup_descriptions = {
                    'shield': 'Blocks one missed word',
                    'slow_time': 'Slows down falling words',
                    'word_clear': 'Clears all words on screen',
                    'auto_type': 'Auto-completes one word'
                }
                

                for i, powerup_name in enumerate(powerup_names):
                    y = available_y + i * 80
                    
                    # Power-up box
                    powerup_rect = pygame.Rect(WIDTH // 2 - 400, y, 800, 70)
                    
                    if text_color == BLACK:
                        inactive_color = WHITE
                        hover_color = BLUE
                    else:
                        inactive_color = BLUE
                        hover_color = (70, 120, 200)

                    if powerups[powerup_name]['unlocked']:
                        if powerup_name in equipped_powerups:
                            color = GREEN  # Equipped
                        elif powerup_rect.collidepoint(mouse_pos):
                            color = hover_color   # Hovering
                        else:
                            color = inactive_color  # Available
                    else:
                        color = inactive_color  # Locked
                    
                    pygame.draw.rect(screen, color, powerup_rect)
                    pygame.draw.rect(screen, text_color if powerups[powerup_name]['unlocked'] else RED, powerup_rect, 3)
                    
                    # Power-up info
                    name_text = powerup_name.replace('_', ' ').title()
                    if not powerups[powerup_name]['unlocked']:
                        name_text += " (LOCKED)"
                    
                    name_surface = small_font.render(name_text, True, text_color)
                    desc_surface = pygame.font.Font("PressStart2P-Regular.ttf", 16).render(
                        powerup_descriptions[powerup_name], True, text_color)
                    
                    screen.blit(name_surface, (powerup_rect.x + 10, powerup_rect.y + 10))
                    screen.blit(desc_surface, (powerup_rect.x + 10, powerup_rect.y + 35))
                    
                    # Status text
                    if powerup_name in equipped_powerups:
                        status_text = "EQUIPPED"
                        status_color = GREEN
                    elif powerups[powerup_name]['unlocked']:
                        status_text = "CLICK TO EQUIP"
                        status_color = BLUE
                    else:
                        status_text = "COMPLETE ACHIEVEMENT"
                        status_color = RED
                    
                    status_surface = pygame.font.Font("PressStart2P-Regular.ttf", 14).render(status_text, True, status_color)
                    status_rect = status_surface.get_rect(right=powerup_rect.right - 10, centery=powerup_rect.centery)
                    screen.blit(status_surface, status_rect)
                    
                    # Handle clicking to equip/unequip
                    if powerup_rect.collidepoint(mouse_pos) and mouse_click[0] and not prev_mouse_click:
                        if powerups[powerup_name]['unlocked']:
                            if powerup_name in equipped_powerups:
                                # Unequip
                                equipped_powerups.remove(powerup_name)
                                powerups[powerup_name]['equipped'] = False
                            elif len(equipped_powerups) < 2:
                                # Equip
                                equipped_powerups.append(powerup_name)
                                powerups[powerup_name]['equipped'] = True
                prev_mouse_click = mouse_click[0]
                
                # Instructions
                instruction_text = "Complete achievements to unlock new power-ups!"
                instruction_surface = pygame.font.Font("PressStart2P-Regular.ttf", 14).render(instruction_text, True, text_color)
                instruction_rect = instruction_surface.get_rect(center=(WIDTH // 2, HEIGHT - 100))
                screen.blit(instruction_surface, instruction_rect)
                
                # Back button
                back_button = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT - 60, button_width, 50)
                draw_button("Back", back_button.x, back_button.y, back_button.width, back_button.height, RED, back_button.collidepoint(mouse_pos))
                if back_button.collidepoint(mouse_pos) and mouse_click[0]:
                    game_state = START
                

            #Update the display 60fps
            pygame.display.flip()
            clock.tick(60) 
            await asyncio.sleep(0)
        
        except Exception as e:
            print(f"[Debug] Main loop exception: {e}")
            error_message = f"Main loop error: {str(e)}"
            error_start_time = pygame.time.get_ticks()
    

if __name__ == "__main__":
    asyncio.run(main())


