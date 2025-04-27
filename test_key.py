#!/usr/bin/env python3
import numpy as np
import sounddevice as sd
import RPi.GPIO as GPIO
import time

# GPIO pin for the button (using BCM numbering)
BUTTON_PIN = 17

# Audio settings
SAMPLE_RATE = 44100      # Hz
FREQUENCY = 440.0        # A4 tone, Hz

# State
gate = False             # True = play tone, False = silence
phase = 0                # phase accumulator for the sine wave

def audio_callback(outdata, frames, time_info, status):
    global gate, phase
    t = (np.arange(frames) + phase) / SAMPLE_RATE
    if gate:
        # generate sine wave
        out = np.sin(2 * np.pi * FREQUENCY * t)
    else:
        # silence
        out = np.zeros(frames)
    outdata[:] = out.reshape(-1, 1)
    phase = (phase + frames) % SAMPLE_RATE

def button_event(channel):
    global gate
    # Button is active-low: pressed = LOW, released = HIGH
    if GPIO.input(BUTTON_PIN) == GPIO.LOW:
        gate = True
    else:
        gate = False

def main():
    global gate, phase

    # Set up GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(BUTTON_PIN, GPIO.BOTH, callback=button_event, bouncetime=50)

    # Open audio stream
    with sd.OutputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype='float32',
        callback=audio_callback
    ):
        print("Press and hold the button on GPIO17 to play the tone.")
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            GPIO.cleanup()

if __name__ == "__main__":
    main()