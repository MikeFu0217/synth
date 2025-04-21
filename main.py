import os
import sys
import time
import pygame, pigame
import RPi.GPIO as GPIO
from pygame.locals import *

from channel import *
from sound import *

# Set up the piTFT display
os.putenv('SDL_VIDEODRIVER', 'fbcon')
os.putenv('SDL_FBDEV', '/dev/fb1')
os.putenv('SDL_MOUSEDRV', 'dummy')
os.putenv('SDL_MOUSEDEV', '/dev/null')
os.putenv('DISPLAY','')

# pygame initialize
pygame.init()
pitft = pigame.PiTft()
size = width, height = 320, 240
white = (255, 255, 255)
black = (0, 0, 0)
screen = pygame.display.set_mode(size)
screen.fill(black)
pygame.display.update()
pygame.mouse.set_visible(False)

# GPIO initialize
button_pins = {17: "play", 22: "wave_sel", 23: "param_sel"}
GPIO.setmode(GPIO.BCM)
for pin, cmd in button_pins.items():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Sound
sound = Sound(sample_rate=44100)

channel1 = Channel(duration=2.0, sample_rate=44100)
channel2 = Channel(duration=2.0, sample_rate=44100)
channel3 = Channel(duration=2.0, sample_rate=44100)

saw_wave = Waveform("saw", frequency=440, sample_rate=44100, duration=1.0)
sine_wave = Waveform("sine", frequency=550, sample_rate=44100, duration=1.0)
square_wave = Waveform("square", frequency=660, sample_rate=44100, duration=1.0)

channel1.set_waveform(saw_wave)
channel2.set_waveform(sine_wave)
channel3.set_waveform(square_wave)

sound.add_channel(channel1, 0.7)
sound.add_channel(channel2, 0.8)
sound.add_channel(channel3, 0.1)

# GPIO callback function & event detection
def GPIO17_callback(channel):
    cmd = button_pins[17]
    print(f"Button 17 has been pressed with command {cmd}")
    sound.play()
GPIO.add_event_detect(17, GPIO.FALLING, callback=GPIO17_callback, bouncetime=300)

wave_sel = 0
def GPIO22_callback(channel):
    global wave_sel
    wave_sel = (wave_sel + 1) % 3
    print(f"Waveform selection changed to {wave_sel}")
GPIO.add_event_detect(22, GPIO.FALLING, callback=GPIO22_callback, bouncetime=300)

param_sel = 0
def GPIO23_callback(channel):
    global param_sel
    param_sel = (param_sel + 1)
    print(f"Parameter selection changed to {param_sel}")
GPIO.add_event_detect(23, GPIO.FALLING, callback=GPIO23_callback, bouncetime=300)

# Draw
def draw_texts():
    font = pygame.font.Font(None, 25)
    text_saw = font.render('saw', True, white)
    rect_saw = text_saw.get_rect(center=(width // 9 * 2, height // 16))
    screen.blit(text_saw, rect_saw)
    text_sin = font.render('sin', True, white)
    rect_sin = text_sin.get_rect(center=(width // 9 * 3, height // 16))
    screen.blit(text_sin, rect_sin)
    text_sqr = font.render('sqr', True, white)
    rect_sqr = text_sqr.get_rect(center=(width // 9 * 4, height // 16))
    screen.blit(text_sqr, rect_sqr)

    text_vol = font.render('vol', True, white)
    rect_vol = text_vol.get_rect(center=(width // 9 * 1, height // 16 * 2))
    screen.blit(text_vol, rect_vol)
    
    text_att = font.render('att', True, white)
    rect_att = text_att.get_rect(center=(width // 9 * 1, height // 16 * 4))
    screen.blit(text_att, rect_att)
    text_dec = font.render('dec', True, white)
    rect_dec = text_dec.get_rect(center=(width // 9 * 1, height // 16 * 5))
    screen.blit(text_dec, rect_dec)
    text_sus = font.render('sus', True, white)
    rect_sus = text_sus.get_rect(center=(width // 9 * 1, height // 16 * 6))
    screen.blit(text_sus, rect_sus)
    text_rel = font.render('rel', True, white)
    rect_rel = text_rel.get_rect(center=(width // 9 * 1, height // 16 * 7))
    screen.blit(text_rel, rect_rel)

    text_L = font.render('L', True, white)
    rect_L = text_L.get_rect(center=(width // 9 * 1, height // 16 * 9))
    screen.blit(text_L, rect_L)
    text_M = font.render('M', True, white)
    rect_M = text_M.get_rect(center=(width // 9 * 1, height // 16 * 10))
    screen.blit(text_M, rect_M)
    text_H = font.render('H', True, white)
    rect_H = text_H.get_rect(center=(width // 9 * 1, height // 16 * 11))
    screen.blit(text_H, rect_H)

    text_dec2 = font.render('dec', True, white)
    rect_dec2 = text_dec2.get_rect(center=(width // 9 * 1, height // 16 * 13))
    screen.blit(text_dec2, rect_dec2)
    text_del = font.render('del', True, white)
    rect_del = text_del.get_rect(center=(width // 9 * 1, height // 16 * 14))
    screen.blit(text_del, rect_del)
    text_ref = font.render('ref', True, white)
    rect_ref = text_ref.get_rect(center=(width // 9 * 1, height // 16 * 15))
    screen.blit(text_ref, rect_ref)

def draw_vols():
    for i, channel in enumerate(sound.channels):
        volume = sound.get_volume(channel)
        font_vol = pygame.font.Font(None, 25)
        text_vol = font_vol.render(f'{volume:.1f}', True, white)
        rect_vol = text_vol.get_rect(center=(width // 9 * (2 + i), height // 16 * 2))
        screen.blit(text_vol, rect_vol)

draw_texts()
draw_vols()
pygame.display.update()

# Start process
running = True
start_time = time.time()
fixed_duration = 60  # Bail out after 30 seconds
clock = pygame.time.Clock()
try:
    while running:
        pitft.update()

        for event in pygame.event.get():
            if event.type is QUIT:
                running = False
            elif event.type is MOUSEBUTTONUP:
                x, y = pygame.mouse.get_pos()
                print(f"Touch at ({x},{y})")

                sens_x = 80
                sens_y = 40

                if x>center_quit[0]-sens_x and x<center_quit[0]+sens_x and y>center_quit[1]-sens_y and y<center_quit[1]+sens_y:
                    print("Quit button pressed! Exiting...")
                    # GPIO.cleanup()
                    pygame.quit()
                    sys.exit()

                if x>center_start[0]-sens_x and x<center_start[0]+sens_x and y>center_start[1]-sens_y and y<center_start[1]+sens_y:
                    print("Start displaying two collide!")
                    SHOW_TWO_COLLIDE = True


        if (time.time() - start_time) > fixed_duration:
            print('Timeout reached, exiting...')
            running = False

except KeyboardInterrupt:
    pass
finally:
    del(pitft)