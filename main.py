import os
import sys
import time
import pygame, pigame
import RPi.GPIO as GPIO
from pygame.locals import *
import threading

import numpy as np
import sounddevice as sd

from channel import *
from sound import *
import view
import knob
import reaction

# Set up the piTFT display
os.putenv('SDL_VIDEODRIVER', 'fbcon')
os.putenv('SDL_FBDEV', '/dev/fb0')
os.putenv('SDL_MOUSEDRV', 'dummy')
os.putenv('SDL_MOUSEDEV', '/dev/null')
os.putenv('DISPLAY','')

# constants
SAMPLE_RATE = 44100

# pygame initialize
pygame.init()
pitft = pigame.PiTft()
screen = pygame.display.set_mode(view.size)
pygame.display.update()
pygame.mouse.set_visible(False)

# GPIO initialize
button_pins = {17: "play", 22: "wave_sel", 23: "param_sel_up", 27: "param_sel_down", 19: "record_playback", 26: "AI"}
GPIO.setmode(GPIO.BCM)
for pin, cmd in button_pins.items():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Knob initialize
knob_in0 = knob.KnobInput(cid=0)

# Sound setup
sound = Sound(sr=SAMPLE_RATE)

saw_wave = Waveform("saw", sr=SAMPLE_RATE)
sine_wave = Waveform("sin", sr=SAMPLE_RATE)
square_wave = Waveform("sqr", sr=SAMPLE_RATE)

env1 = Envelope(sr=SAMPLE_RATE)
env2 = Envelope(sr=SAMPLE_RATE)
env3 = Envelope(sr=SAMPLE_RATE)

filter1 = Filter(sr=SAMPLE_RATE)
filter2 = Filter(sr=SAMPLE_RATE)
filter3 = Filter(sr=SAMPLE_RATE)

rvb1 = Reverb(sr=SAMPLE_RATE)
rvb2 = Reverb(sr=SAMPLE_RATE)
rvb3 = Reverb(sr=SAMPLE_RATE)

channel1 = Channel(saw_wave, env1, filter1, rvb1, sr=SAMPLE_RATE, volume=1.0)
channel2 = Channel(sine_wave, env2, filter2, rvb2, sr=SAMPLE_RATE, volume=0.0)
channel3 = Channel(square_wave, env3, filter3, rvb3, sr=SAMPLE_RATE, volume=0.0)

sound.add_channel(channel1)
sound.add_channel(channel2)
sound.add_channel(channel3)

# View setup
font = pygame.font.Font(None, 25)
box_sel_idx = [0, 0]
wave_names = ["saw", "sin", "sqr"]
param_names = ["vol", "att", "dec", "sus", "rel", "L", "M", "H", "dec2", "del", "wet"]

view.draw_screen(screen, font, sound, "saw", "vol")

# Recording/playback state
dirty = False
record_state = 0       # 0=idle, 1=recording, 3=playback
record_frames = []     # list of numpy arrays
playback_buffer = None
playback_pos = 0

# AI setup
AI_state = "idle"
exit_event = threading.Event()
api_key_path = ".openai_api_key"
llm = reaction.LLMClient(api_key_path=api_key_path)
with open(api_key_path) as f:
    api_key = f.read().strip()
stt = reaction.SpeechToTextLocal(
    model_path="/home/pi/vosk_models/vosk-model-small-en-us-0.15",
    samplerate=44100,
    threshold=0.02,
    silence_duration=1.0,
    max_record_time=30.0
)
tts = reaction.TextToSpeech()

def ai_conversation_loop():
    """
    Runs in its own thread.  
    Cycles: silence → listen → speak → silence …  
    Exits immediately if exit_event is set.
    """
    global AI_state, dirty

    while not exit_event.is_set():
        if AI_state == "silence":
            dirty = True
            AI_state = "listen"
            continue

        if AI_state == "listen":
            dirty = True
            try:
                user_text = stt.record_and_transcribe()
            except Exception:
                user_text = ""
            # if user presses GPIO26 mid-record, we still finish record_and_transcribe,
            # but the moment it returns we'll see exit_event and break.
            if exit_event.is_set():
                break

            if user_text.strip().lower() == "quit":
                tts.speak("Quitting AI assistant.")
                break

            AI_state = "speak"
            continue

        if AI_state == "speak":
            dirty = True
            response_text = f"I heard you say: {user_text}"
            tts.speak(response_text)
            if exit_event.is_set():
                break
            AI_state = "silence"
            continue

        # small sleep so we don't tight-spin if state is unexpected
        time.sleep(0.05)

    # cleanup on exit
    AI_state = "idle"
    dirty = True

# GPIO callbacks
def GPIO19_callback(channel):
    # Record/Playback button callback
    global record_state, record_frames, playback_buffer, playback_pos
    time.sleep(0.05)
    if record_state == 0:
        # start recording
        record_frames = []
        record_state = 1
        print("\nRecording started")
    elif record_state == 1:
        # stop recording
        if record_frames:
            playback_buffer = np.concatenate(record_frames, axis=0).flatten()
        else:
            playback_buffer = np.array([], dtype='float32')
        playback_pos = 0
        record_state = 2
        print("\nRecording stopped")
    elif record_state == 2:
        # start playback
        record_state = 3
        print("\nStart playback")
GPIO.add_event_detect(19, GPIO.FALLING, callback=GPIO19_callback, bouncetime=300)

def GPIO26_callback(channel):
    """
    Light callback: toggle AI mode on/off, signal the worker thread.
    """
    global AI_state, dirty

    time.sleep(0.05)

    # entering AI mode?
    if AI_state == "idle":
        exit_event.clear()           # ensure the flag is off
        AI_state = "silence"
        dirty = True
        # start the daemon thread
        t = threading.Thread(target=ai_conversation_loop, daemon=True)
        t.start()

    # exiting AI mode?
    else:
        exit_event.set()             # tell the thread to stop ASAP
        print("Exiting AI mode")
        # thread will reset AI_state to 'idle' on its own
        # but we can force it right away
        AI_state = "idle"
        dirty = True
GPIO.add_event_detect(26, GPIO.FALLING, callback=GPIO26_callback, bouncetime=300)

def GPIO17_callback(channel):
    # Play/Stop button callback
    if GPIO.input(17) == GPIO.LOW:
        sound.note_on()
        print("\nNote key pressed")
    else:
        sound.note_off()
        print("\nNote key released")
GPIO.add_event_detect(17, GPIO.BOTH, callback=GPIO17_callback, bouncetime=10)

def GPIO22_callback(channel):
    # Waveform selection button callback
    global box_sel_idx, dirty
    box_sel_idx[0] = (box_sel_idx[0] + 1) % len(wave_names)
    dirty = True
    print(f"Waveform selection changed to {wave_names[box_sel_idx[0]]}")
GPIO.add_event_detect(22, GPIO.FALLING, callback=GPIO22_callback, bouncetime=300)

def GPIO23_callback(channel):
    # Parameter selection up button callback
    global box_sel_idx, dirty
    box_sel_idx[1] = (box_sel_idx[1] - 1) % len(param_names)
    dirty = True
    print(f"Parameter selection changed to {param_names[box_sel_idx[1]]}")
GPIO.add_event_detect(23, GPIO.FALLING, callback=GPIO23_callback, bouncetime=300)

def GPIO27_callback(channel):
    # Parameter selection down button callback
    global box_sel_idx, dirty
    box_sel_idx[1] = (box_sel_idx[1] + 1) % len(param_names)
    dirty = True
    print(f"Parameter selection changed to {param_names[box_sel_idx[1]]}")
GPIO.add_event_detect(27, GPIO.FALLING, callback=GPIO27_callback, bouncetime=300)

# Knob voltage change callback (unchanged)
QUANT_STEPS = {'vol':100,'att':100,'dec':100,'sus':100,'rel':100,'L':100,'M':100,'H':100,'dec2':50,'del':50,'wet':50}

def set_quantized(obj, attr, range_list, v, steps):
    min_r, span = range_list
    vq = round(v * steps) / steps
    setattr(obj, attr, min_r + vq * span)

def on_knob_in0_voltage_change(voltage):
    # Set the voltage to a value between 0.0 and 3.3
    # and map it to the parameter range
    global dirty
    v = min(max(voltage, 0.0), 3.3) / 3.3
    cha   = sound.channels[box_sel_idx[0]]
    key   = param_names[box_sel_idx[1]]
    steps = QUANT_STEPS.get(key, 100)
    PARAM_MAP = {
        'vol':  (cha,                'volume',        cha.vol_range),
        'att':  (cha.envelopes[0],   'attack_time',   cha.env_att_range),
        'dec':  (cha.envelopes[0],   'decay_time',    cha.env_dec_range),
        'sus':  (cha.envelopes[0],   'sustain_level', cha.env_sus_range),
        'rel':  (cha.envelopes[0],   'release_time',  cha.env_rel_range),
        'L':    (cha.filters[0],     'low',           cha.filter_l_range),
        'M':    (cha.filters[0],     'mid',           cha.filter_m_range),
        'H':    (cha.filters[0],     'high',          cha.filter_h_range),
        'dec2': (cha.reverbs[0],     'decay',         cha.rev_dec_range),
        'del':  (cha.reverbs[0],     'delay',         cha.rev_del_range),
        'wet':  (cha.reverbs[0],     'wet',           cha.rev_wet_range),
    }
    if key not in PARAM_MAP:
        raise ValueError(f"Unknown index: {key}")
    target, attr, range_list = PARAM_MAP[key]
    set_quantized(target, attr, range_list, v, steps)
    dirty = True

# Audio callback with integrated recording & playback
def audio_callback(outdata, frames, time_info, status):
    global record_state, record_frames, playback_buffer, playback_pos
    # recording phase: capture synth output
    if record_state == 1:
        sig = sound.process(frames)
        record_frames.append(sig.copy())
        outdata[:,0] = np.clip(sig, -1.0, 1.0)
        return
    # playback recorded data
    if record_state == 3 and playback_buffer is not None:
        start = playback_pos
        end   = start + frames
        chunk = playback_buffer[start:end]
        if len(chunk) < frames:
            outdata[:len(chunk),0] = chunk
            outdata[len(chunk):,0] = 0
            record_state = 0
            playback_buffer = None
            print("Playback finished")
        else:
            outdata[:,0] = chunk
            playback_pos += frames
        return
    # normal synthesis output
    sig = sound.process(frames)
    outdata[:,0] = np.clip(sig, -1.0, 1.0)

# Main loop
running = True
dirty = True
clock = pygame.time.Clock()
knob_in0.last_time = time.time()
knob_in0.last_voltage = knob_in0.channel.voltage

with sd.OutputStream(samplerate=SAMPLE_RATE, channels=1, dtype='float32', callback=audio_callback):
    try:
        while running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
            # knob polling
            now = time.time()
            if now - knob_in0.last_time > knob_in0.poll_interval:
                knob_in0.last_time = now
                new_voltage = knob_in0.channel.voltage
                if abs(new_voltage - knob_in0.last_voltage) > knob_in0.threshold:
                    knob_in0.last_voltage = new_voltage
                    on_knob_in0_voltage_change(new_voltage)
            # redraw if needed
            if AI_state != "idle":
                view.draw_AI_interface(screen, font, AI_state)
            else:
                if dirty:
                    view.draw_screen(screen, font, sound, wave_names[box_sel_idx[0]], param_names[box_sel_idx[1]])
                    dirty = False
                clock.tick(30)
    except KeyboardInterrupt:
        pass
    finally:
        del pitft
