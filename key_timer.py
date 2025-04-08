import pygame
import time

pygame.init()
screen = pygame.display.set_mode((400, 200))
pygame.display.set_caption("Key Timer")

font = pygame.font.SysFont(None, 36)
key_down_times = {}
display_text = ""

running = True
while running:
    screen.fill((0, 0, 0))

    # Draw current text
    if display_text:
        text_surface = font.render(display_text, True, (0, 255, 0))
        screen.blit(text_surface, (20, 80))

    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key not in key_down_times:
                key_down_times[event.key] = time.time()

        elif event.type == pygame.KEYUP:
            if event.key in key_down_times:
                elapsed = time.time() - key_down_times[event.key]
                key_name = pygame.key.name(event.key)
                display_text = f"Key '{key_name}' pressed for {elapsed:.2f} sec"
                print(display_text)
                del key_down_times[event.key]

pygame.quit()
