import pygame
import random
import sys
from pygame.locals import *
import json
import asyncio
try:
    from js import window
except ImportError:
    window = None

pygame.init()

#Screen size
WIDTH, HEIGHT = 800, 600
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
PINK = (255, 105, 180)
GRAY = (251, 251, 251)

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
ENTER_NAME = "enter_name"
LEADERBOARD = "leaderboard"
game_state = START



#Word lists
word_list = ["apple", "banana", "cat", "dog", "elephant", "flower", "grapes", "honey", "idea", "juice",  ]
word_list_hard = ["algorithm", "binary", "california", "dragonfruit", "encryption", "firewall", "gateway", "hypertext"]

#Load heart images
HEART_IMAGE = pygame.image.load("heart.png").convert_alpha()  # Ensure you have a heart.png file
EMPTY_HEART_IMAGE = pygame.image.load("empty_heart.png").convert_alpha()  # Ensure you have an empty_heart.png file
HEART_SIZE = 40  # Size of the heart images



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
        dynamic_inactive = WHITE
        dynamic_hover = BLUE
    else:
        dynamic_inactive = BLUE
        dynamic_hover = (70,120,200)

    color = dynamic_hover if hover else dynamic_inactive
    

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
def draw_combo(combo_active, combo_count, combo_lost, combo_start_time, last_combo, combo_display_time):
    current_time = pygame.time.get_ticks()
    if combo_active and combo_count > 0:
        elapsed = current_time - last_combo
        if elapsed < combo_display_time:
            alpha = max(0, 255 - int(255 * (elapsed / combo_display_time)))
            combo_text = f"COMBO x{combo_count}!"
            combo_surface = small_font.render(combo_text, True, GREEN)
            combo_surface.set_alpha(alpha)
            screen.blit(combo_surface, (WIDTH - combo_surface.get_width() - 20, HEIGHT - 40))
    elif combo_lost:
        elapsed = current_time - combo_start_time
        if elapsed < combo_display_time:
            alpha = max(0, 255 - int(255 * (elapsed / combo_display_time)))
            loss_text = "COMBO LOST!"
            loss_surface = small_font.render(loss_text, True, RED)
            screen.blit(loss_surface, (WIDTH - loss_surface.get_width() - 20, HEIGHT - 40))

# Save score
def save_to_leaderboard(name, score):
    if window:
        leaderboard_json = window.localStorage.getItem("leaderboard")
        leaderboard = json.loads(leaderboard_json) if leaderboard_json else []
        leaderboard.append({"name": name, "score": score})
        leaderboard.sort(key=lambda x: x["score"], reverse=True)
        leaderboard = leaderboard[:5]  # Top 5
        window.localStorage.setItem("leaderboard", json.dumps(leaderboard))

# Load scores
def load_leaderboard():
    if window:
        leaderboard_json = window.localStorage.getItem("leaderboard")
        return json.loads(leaderboard_json) if leaderboard_json else []
    else:
        return []



#Game variables
text_color = BLACK
lives = 3
score = 0
falling_words = []
word_speed = 1
spawn_rate = 2
word_speed_add = 0.0001
spawn_rate_add = 0.0001
input_text = ""
button_width = 400
start_time = pygame.time.get_ticks()
MAX_WORDS_ON_SCREEN = 15

#Combo
combo_count = 0
combo_active = False
combo_start_time = 0
combo_lost = False
in_a_row = 0

#combo display type
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

#Screen size
clear_input = False  
is_fullscreen = False
windowed_size = (WIDTH, HEIGHT)

#Main loop
async def main():
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_pressed()
        current_time = pygame.time.get_ticks()

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
                        combo_active = False
                        combo_count = 0
                        in_a_row = 0
                        combo_lost = True
                        combo_start_time = pygame.time.get_ticks()
                        last_combo = pygame.time.get_ticks()
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
                                    if word.is_hard and lives < 3:
                                        lives += 1

                                    #Points
                                    base_points = 500 if word.is_hard else 100
                                    bonus_points = (10* combo_count) if combo_active else 0
                                    score += (base_points + bonus_points)


                                    clear_input = True
                                    completed_word = True

                                    #Combo
                                    in_a_row += 1
                                    if in_a_row >= 5:
                                        combo_active = True
                                        combo_count += 1
                                        combo_start_time = pygame.time.get_ticks()
                                        combo_lost = False
                                        last_combo = pygame.time.get_ticks()
                            else:
                                word.progress = 0

                        #Clear input when word is completed
                        if completed_word and clear_input:
                            input_text = ""
                            clear_input = False
                elif game_state == ENTER_NAME and active_input: 
                    if event.key == pygame.K_BACKSPACE:
                        player_name = player_name[:-1]
                    elif len(player_name) < 20 and event.unicode.isprintable():
                        player_name += event.unicode
            
            elif event.type == pygame.KEYUP:
                if game_state == PLAYING and event.key == pygame.K_BACKSPACE:
                    # Stop deleting
                    backspace_held = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if game_state == ENTER_NAME:
                    # Activate input box on click
                    if input_box.collidepoint(event.pos):
                        active_input = True
                    else:
                        active_input = False
                
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
                        combo_active = False
                        combo_count = 0
                        in_a_row = 0
                        combo_lost = True
                        combo_start_time = pygame.time.get_ticks()
                        last_combo = pygame.time.get_ticks()

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

            # Settings button
            settings_button = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 + 50, button_width, 50)
            draw_button("Settings", settings_button.x, settings_button.y, settings_button.width, settings_button.height, BLUE, settings_button.collidepoint(mouse_pos))
            if settings_button.collidepoint(mouse_pos) and mouse_click[0]:
                game_state = SETTINGS
                

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

            # Full-screen button
            fullscreen_button = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 + 100, button_width, 50)
            draw_button("Display", fullscreen_button.x, fullscreen_button.y, fullscreen_button.width, fullscreen_button.height, BLUE, fullscreen_button.collidepoint(mouse_pos))
            if fullscreen_button.collidepoint(mouse_pos) and mouse_click[0]:
                if not is_fullscreen:
                    windowed_size = (WIDTH, HEIGHT)  # Save current size
                    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    WIDTH, HEIGHT = screen.get_size()
                    is_fullscreen = True
                else:
                    screen = pygame.display.set_mode(windowed_size, pygame.RESIZABLE)
                    WIDTH, HEIGHT = windowed_size
                    is_fullscreen = False
                background_scaled = pygame.transform.scale(background_image, (WIDTH, HEIGHT))

            # Back button
            back_button = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 + 200, button_width, 50)
            draw_button("Back", back_button.x, back_button.y, back_button.width, back_button.height, RED, back_button.collidepoint(mouse_pos))
            if back_button.collidepoint(mouse_pos) and mouse_click[0]:
                game_state = START

        elif game_state == PLAYING:
            # Add new words, no duplicates and overlaps
            if random.randint(1, 100) < spawn_rate and len(falling_words) < MAX_WORDS_ON_SCREEN:
                is_hard = random.randint(1, 20) == 1
                word_pool = word_list_hard if is_hard else word_list
                new_word_text = random.choice(word_pool)
                if count_word_instances(new_word_text) < 1:
                    speed = word_speed * 1.25 if is_hard else word_speed  # Hard words fall faster
                    new_word = FallingWord(new_word_text, speed, is_hard)

                    # Ensure the new word does not overlap with existing words
                    attempts = 0
                    while is_overlapping(new_word, falling_words) and attempts < 100:
                        new_word.x = random.randint(50, WIDTH - new_word.width - 50)
                        attempts += 1

                    if attempts < 100:  # Only add the word if a valid position is found
                        falling_words.append(new_word)

            # Update word positions and remove completed words after 1 second
            for word in falling_words[:]:  
                word.move()
                if word.off_screen():
                    lives -= 1

                    # Combo lost
                    combo_active = False
                    combo_count = 0
                    in_a_row = 0
                    combo_lost = True
                    combo_start_time = pygame.time.get_ticks()
                    last_combo = pygame.time.get_ticks()


                    falling_words.remove(word)
                    if lives == 0:
                        game_state = ENTER_NAME  # Switch to entername screen
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
            screen.blit(timer_surface, (WIDTH - 275, 10))
            draw_hearts(lives)
            draw_combo(combo_active, combo_count, combo_lost, combo_start_time, last_combo, combo_display_time)


        elif game_state == ENTER_NAME:
            #Enter name screen
            title_surface = font.render("Enter Your Name!", True, text_color)
            title_rect = title_surface.get_rect(center=(WIDTH // 2, HEIGHT // 4))
            screen.blit(title_surface, title_rect)

            #Input box 
            input_box = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2, 300, 50)
            box_color = BLUE if active_input else GRAY
            pygame.draw.rect(screen, box_color, input_box, 2)

            name_surface = font.render(player_name, True, text_color)
            screen.blit(name_surface, (input_box.x + 10, input_box.y + 10))

            # Submit button
            is_name_entered = len(player_name.strip()) > 0
            home_button = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 + 100, button_width, 50)
            
            hovering = home_button.collidepoint(mouse_pos)
            draw_button("Submit", home_button.x, home_button.y, home_button.width, home_button.height, BLUE if is_name_entered else GRAY, hovering)

            if hovering and mouse_click[0] and is_name_entered:

                # Save to leaderboard
                save_to_leaderboard(player_name, score)

                # Get rank
                leaderboard = load_leaderboard().copy()
                rank = next((i for i, entry in enumerate(leaderboard) if entry["name"] == player_name and entry["score"] == score), None)


                game_state = GAME_OVER
                
        
        elif game_state == GAME_OVER:
            #Draw game over screen
            title_surface = font.render("Game Over", True, text_color)
            title_rect = title_surface.get_rect(center=(WIDTH // 2, HEIGHT // 4 + 50))
            screen.blit(title_surface, title_rect)
            #Score
            score_surface = font.render(f"{player_name}:{score}", True, text_color)
            score_rect = score_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 25))
            screen.blit(score_surface, score_rect)
            #Leaderboards button
            leader_button = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 + 50 , button_width, 50)
            draw_button("Leaderboards", leader_button.x, leader_button.y, leader_button.width, leader_button.height, BLUE, leader_button.collidepoint(mouse_pos))
            if leader_button.collidepoint(mouse_pos) and mouse_click[0]:
                game_state = LEADERBOARD
            #Return to home button
            home_button = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 + 150, button_width, 50)
            draw_button("Home", home_button.x, home_button.y, home_button.width, home_button.height, BLUE, home_button.collidepoint(mouse_pos))
            if home_button.collidepoint(mouse_pos) and mouse_click[0]:
                game_state = START
                #Reset allat
                lives = 3  
                score = 0  
                falling_words = []  
                word_speed = 1  
                spawn_rate = 2
                player_name = ""  

        elif game_state == LEADERBOARD:
            # Draw leaderbord screen
            leaderboard_surface = font.render("Leaderboard", True, text_color)
            leaderboard_rect = leaderboard_surface.get_rect(center=(WIDTH // 2, HEIGHT // 4 - 100))
            screen.blit(leaderboard_surface, leaderboard_rect)
            
            leaderboard = load_leaderboard()

            for i, entry in enumerate(leaderboard):
                name = entry["name"]
                score = entry ["score"]


                text = f"{i+1}. {name}: {score}"
                entry_surface = small_font.render(text, True, text_color)
                screen.blit(entry_surface, (WIDTH // 2 - 200, HEIGHT // 4 + i * 40))


            #Return to home button
            gback_button = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT - 100, button_width, 50)
            draw_button("Back", gback_button.x, gback_button.y, gback_button.width, gback_button.height, RED, gback_button.collidepoint(mouse_pos))
            if gback_button.collidepoint(mouse_pos) and mouse_click[0]:
                game_state = GAME_OVER


        #Update the display 60fps
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    if hasattr(sys, "_called_from_pyodide"):
        asyncio.run(main())
    else:
        ayncio.run(main())
