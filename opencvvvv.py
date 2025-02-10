import cv2
import mediapipe as mp
import pygame
import numpy as np

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

# Initialize Pygame
pygame.init()
WIDTH, HEIGHT = 800, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dino Game")
clock = pygame.time.Clock()

# Load Dino Assets
dino_run = [pygame.transform.scale(pygame.image.load("dino1.png"), (50, 50)),
            pygame.transform.scale(pygame.image.load("dino2.png"), (50, 50))]
dino_jump = pygame.transform.scale(pygame.image.load("dino_jump.png"), (50, 50))
dino_duck = pygame.transform.scale(pygame.image.load("dino_duck.png"), (50, 50))
dino_index = 0
dino = dino_run[dino_index]
dino_rect = dino.get_rect(midbottom=(80, HEIGHT - 30))

ground_y = HEIGHT - 30  # Adjusted ground position
jump = False
duck = False
velocity = 0
g = 0.5  # Gravity

# Load Obstacle Assets
cactus_img = pygame.transform.scale(pygame.image.load("cactus.png"), (40, 60))
obstacles = []

# Function to add new obstacles
def add_obstacle():
    obstacle_rect = cactus_img.get_rect(midbottom=(WIDTH, ground_y))
    obstacles.append(obstacle_rect)

# Function to detect gesture
def detect_gesture(hand_landmarks):
    thumb_tip = hand_landmarks[4]
    index_tip = hand_landmarks[8]
    pinky_tip = hand_landmarks[20]
    distance = np.linalg.norm(np.array([index_tip.x, index_tip.y]) - np.array([pinky_tip.x, pinky_tip.y]))
    if distance > 0.15:
        return "JUMP"
    else:
        return "DUCK"

# OpenCV Video Capture
cap = cv2.VideoCapture(0)
running = True
score = 0
obstacle_timer = 0
game_over = False
highest_score = 0

# Load Sounds
jump_sound = pygame.mixer.Sound("jump.wav")
score_sound = pygame.mixer.Sound("score.wav")
pygame.mixer.music.load("backgroundmusic.wav")
pygame.mixer.music.play(-1)  # Loop the background music

def reset_game():
    global score, obstacles, jump, duck, velocity, dino_rect, dino_index, game_over
    score = 0
    obstacles.clear()
    jump = False
    duck = False
    velocity = 0
    dino_index = 0
    dino_rect = dino_run[dino_index].get_rect(midbottom=(80, HEIGHT - 30))
    game_over = False

def game_over_screen():
    global highest_score
    if score > highest_score:
        highest_score = score
    font = pygame.font.Font(None, 74)
    text = font.render("Game Over", True, (255, 0, 0))
    score_text = font.render(f"Score: {score}", True, (0, 0, 0))
    high_score_text = font.render(f"High Score: {highest_score}", True, (0, 0, 0))
    
    retry_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 50, 200, 50)
    exit_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 120, 200, 50)

    screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2 - 20))
    screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2 + 20))
    screen.blit(high_score_text, (WIDTH // 2 - high_score_text.get_width() // 2, HEIGHT // 2 + 90))
    
    pygame.draw.rect(screen, (0, 255, 0), retry_button)  # Green retry button
    pygame.draw.rect(screen, (255, 0, 0), exit_button)  # Red exit button
    retry_text = font.render("Retry", True, (255, 255, 255))
    exit_text = font.render("Exit", True, (255, 255, 255))
    screen.blit(retry_text, (retry_button.x + retry_button.width // 2 - retry_text.get_width() // 2, retry_button.y + retry_button.height // 2 - retry_text.get_height() // 2))
    screen.blit(exit_text, (exit_button.x + exit_button.width // 2 - exit_text.get_width() // 2, exit_button.y + exit_button.height // 2 - exit_text.get_height() // 2))
    
    pygame.display.update()
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if retry_button.collidepoint(event.pos):
                    reset_game()
                    waiting = False
                elif exit_button.collidepoint(event.pos):
                    pygame.quit()
                    exit()

while running:
    screen.fill((255, 255, 255))  # White background
    pygame.draw.line(screen, (0, 0, 0), (0, ground_y), (WIDTH, ground_y), 3)  # Road line
    
    ret, frame = cap.read()
    if not ret:
        continue
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_frame)
    gesture = None
    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            gesture = detect_gesture(hand_landmarks.landmark)
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
    
    # Gesture Controls
    if gesture == "JUMP" and not jump and not game_over:
        jump = True
        duck = False
        velocity = -10
        jump_sound.play()
    elif gesture == "DUCK" and not game_over:
        duck = True
        jump = False
    else:
        duck = False
    
    # Jump Mechanics
    if jump:
        dino_rect.y += velocity
        velocity += g  # Gravity effect
        if dino_rect.bottom >= ground_y:
            dino_rect.bottom = ground_y
            jump = False
    
    # Dino Animation
    if jump:
        dino = dino_jump
    elif duck:
        dino = dino_duck
        dino_rect.y = ground_y - 20
    else:
        dino_index = (dino_index + 1) % 2
        dino = dino_run[dino_index]
        dino_rect.bottom = ground_y
    
    # Obstacle Mechanics
    if obstacle_timer > 50:
        add_obstacle()
        obstacle_timer = 0
    obstacle_timer += 1

    for obstacle in obstacles[:]:
        obstacle.x -= 5 + score // 5  # Increase speed with score
        if obstacle.right < 0:
            obstacles.remove(obstacle)
            score += 1  # Increase score
            score_sound.play()  # Play score sound
        if dino_rect.colliderect(obstacle):
            game_over = True  # Set game over flag
            break  # Exit the loop to avoid multiple game overs

    if game_over:
        game_over_screen()  # Show game over screen
        continue  # Skip the rest of the loop

    # Draw elements
    screen.blit(dino, dino_rect)
    for obstacle in obstacles:
        screen.blit(cactus_img, obstacle)

    # Score Display
    font = pygame.font.Font(None, 36)
    score_text = font.render(f"Score: {score}", True, (0, 0, 0))
    screen.blit(score_text, (10, 10))

    pygame.display.flip()  # Update the display
    clock.tick(60)  # Control the frame rate to 60 FPS

cap.release()  # Release the video capture
pygame.quit()  # Quit Pygame