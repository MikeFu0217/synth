import os
import sys
import time
import pygame, pigame
import RPi.GPIO as GPIO
from pygame.locals import *

from channel import *
from sound import *
import view

# Set up the piTFT display
os.putenv('SDL_VIDEODRIVER', 'fbcon')
os.putenv('SDL_FBDEV', '/dev/fb0')
os.putenv('SDL_MOUSEDRV', 'dummy')
os.putenv('SDL_MOUSEDEV', '/dev/null')
os.putenv('DISPLAY','')

# pygame initialize
pygame.init()
pitft = pigame.PiTft()
screen = pygame.display.set_mode(view.size)
view.initialize_view(screen)
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
sine_wave = Waveform("sin", frequency=550, sample_rate=44100, duration=1.0)
square_wave = Waveform("sqr", frequency=660, sample_rate=44100, duration=1.0)

env1 = Envelope()
env2 = Envelope()
env3 = Envelope()

filter1 = Filter()
filter2 = Filter()
filter3 = Filter()

rvb1 = Reverb()
rvb2 = Reverb()
rvb3 = Reverb()

channel1.set_waveform(saw_wave), channel1.add_envelope(env1), channel1.add_filter(filter1), channel1.add_reverb(rvb1)
channel2.set_waveform(sine_wave), channel2.add_envelope(env2), channel2.add_filter(filter2), channel2.add_reverb(rvb2)
channel3.set_waveform(square_wave), channel3.add_envelope(env3), channel3.add_filter(filter3), channel3.add_reverb(rvb3)

sound.add_channel(channel1, 0.7)
sound.add_channel(channel2, 0.8)
sound.add_channel(channel3, 0.1)

# View
font = pygame.font.Font(None, 25)
box_sel_idx = [0, 0]
wave_names = ["saw", "sin", "sqr"]
param_names = ["vol", "att", "dec", "sus", "rel", "L", "M", "H", "dec2", "del", "ref"]

view.draw_texts(screen, font)
view.draw_params(screen, font, sound)
view.draw_box(screen, "saw", "vol")
view.draw_waveform_preview(screen, "saw")
pygame.display.update()

# GPIO callback function & event detection
def GPIO17_callback(channel):
    cmd = button_pins[17]
    print(f"Button 17 has been pressed with command {cmd}")
    sound.play()
GPIO.add_event_detect(17, GPIO.FALLING, callback=GPIO17_callback, bouncetime=300)

def GPIO22_callback(channel):
    global box_sel_idx
    box_sel_idx[0] = (box_sel_idx[0] + 1) % len(wave_names)
    view.draw_screen(screen, font, sound, wave_names[box_sel_idx[0]], param_names[box_sel_idx[1]])
    print(f"Waveform selection changed to {wave_names[box_sel_idx[0]]}")
GPIO.add_event_detect(22, GPIO.FALLING, callback=GPIO22_callback, bouncetime=300)

def GPIO23_callback(channel):
    global box_sel_idx
    box_sel_idx[1] = (box_sel_idx[1] + 1) % len(param_names)
    view.draw_screen(screen, font, sound, wave_names[box_sel_idx[0]], param_names[box_sel_idx[1]])
    print(f"Parameter selection changed to {param_names[box_sel_idx[1]]}")
GPIO.add_event_detect(23, GPIO.FALLING, callback=GPIO23_callback, bouncetime=300)

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
            # elif event.type is MOUSEBUTTONUP:
            #     x, y = pygame.mouse.get_pos()
            #     print(f"Touch at ({x},{y})")

            #     sens_x = 80
            #     sens_y = 40

            #     if x>center_quit[0]-sens_x and x<center_quit[0]+sens_x and y>center_quit[1]-sens_y and y<center_quit[1]+sens_y:
            #         print("Quit button pressed! Exiting...")
            #         # GPIO.cleanup()
            #         pygame.quit()
            #         sys.exit()

            #     if x>center_start[0]-sens_x and x<center_start[0]+sens_x and y>center_start[1]-sens_y and y<center_start[1]+sens_y:
            #         print("Start displaying two collide!")
            #         SHOW_TWO_COLLIDE = True


        if (time.time() - start_time) > fixed_duration:
            print('Timeout reached, exiting...')
            running = False

except KeyboardInterrupt:
    pass
finally:
    del(pitft)