#!/usr/bin/env python3
import numpy as np
import sounddevice as sd
import RPi.GPIO as GPIO
import threading
import time

# GPIO pin assignments (BCM numbering)
BUTTON_PIN = 17   # Key press for tone on/off
RECORD_PIN = 27   # Control recording/playback sequence

# Audio settings
SAMPLE_RATE = 44100    # Sampling rate in Hz
FREQUENCY   = 440.0    # Tone frequency (A4) in Hz

class Waveform:
    def __init__(self, name, sr, frequency):
        """
        Initialize a waveform generator with given type.
        name: 'saw', 'sin', or 'square'
        sr: sample rate
        frequency: tone frequency in Hz
        """
        self.name = name
        self.length = int(sr / frequency)
        t = np.arange(self.length) / sr
        if name == 'saw':
            self.data = (2 * (t * frequency - np.floor(t * frequency + 0.5))).astype('float32')
        elif name == 'sin':
            self.data = np.sin(2 * np.pi * frequency * t).astype('float32')
        elif name == 'square':
            self.data = np.sign(np.sin(2 * np.pi * frequency * t)).astype('float32')
        else:
            raise ValueError(f"Unknown waveform '{name}'")

class Envelope:
    def __init__(self, sr, attack, decay, sustain, release):
        """
        Initialize ADSR envelope with sample rate and parameters.
        attack, decay, release in seconds, sustain in 0.0–1.0 range.
        """
        self.a_samps = int(attack  * sr)
        self.d_samps = int(decay   * sr)
        self.r_samps = int(release * sr)
        self.sustain_level = sustain
        self.state = 'idle'
        self.idx = 0

    def note_on(self):
        """Start attack stage."""
        self.state = 'attack'
        self.idx = 0

    def note_off(self):
        """Start release stage."""
        self.state = 'release'
        self.idx = 0

    def process(self, frames):
        """Generate ADSR envelope values for 'frames' samples."""
        env = np.zeros(frames, dtype='float32')
        for i in range(frames):
            if self.state == 'attack':
                if self.idx < self.a_samps:
                    env[i] = self.idx / self.a_samps
                else:
                    self.state = 'decay'
                    self.idx = 0
                    env[i] = 1.0
            elif self.state == 'decay':
                if self.idx < self.d_samps:
                    env[i] = 1.0 - (1.0 - self.sustain_level) * (self.idx / self.d_samps)
                else:
                    self.state = 'sustain'
                    self.idx = 0
                    env[i] = self.sustain_level
            elif self.state == 'sustain':
                env[i] = self.sustain_level
            elif self.state == 'release':
                if self.idx < self.r_samps:
                    env[i] = self.sustain_level * (1.0 - self.idx / self.r_samps)
                else:
                    self.state = 'idle'
                    env[i] = 0.0
            else:
                env[i] = 0.0
            self.idx += 1
        return env

class Filter:
    def __init__(self, low=1.0, mid=1.0, high=1.0):
        """Simple three-band filter."""
        self.low = low
        self.mid = mid
        self.high = high
        self.sr = SAMPLE_RATE

    def apply(self, signal):
        """Apply band-specific gains."""
        fft = np.fft.rfft(signal)
        freqs = np.fft.rfftfreq(len(signal), d=1/self.sr)
        fft[freqs < 400] *= self.low
        fft[(freqs >= 400) & (freqs < 4000)] *= self.mid
        fft[freqs >= 4000] *= self.high
        return np.fft.irfft(fft, n=len(signal))

class Reverb:
    def __init__(self, decay=0.5, delay=0.05, reflections=5):
        """Basic comb-style reverb."""
        self.decay = decay
        self.delay = delay
        self.reflections = reflections

    def apply(self, signal):
        """Add delayed, attenuated copies."""
        out = np.copy(signal)
        d_samp = int(self.delay * SAMPLE_RATE)
        for i in range(1, self.reflections+1):
            idx = d_samp * i
            if idx < len(signal):
                out[idx:] += signal[:-idx] * (self.decay ** i)
        return out

class Channel:
    def __init__(self, waveform, sr, env_params, filters=None, reverbs=None, volume=1.0):
        """
        Channel encapsulates wavetable, ADSR envelope, filters, reverbs, and volume.
        env_params: tuple (attack, decay, sustain, release)
        """
        self.wavetable = waveform
        attack, decay, sustain, release = env_params
        self.envelope = Envelope(sr, attack, decay, sustain, release)
        self.filters = filters or []
        self.reverbs = reverbs or []
        self.volume = volume
        self.phase = 0

    def process(self, frames):
        """Generate a mono buffer for this channel."""
        ar = np.arange(frames)
        idx = (self.phase + ar) % self.wavetable.length
        sig = self.wavetable.data[idx].copy()

        # Apply ADSR envelope
        sig *= self.envelope.process(frames)
        # Apply filters
        for fl in self.filters:
            sig = fl.apply(sig)
        # Apply reverbs
        for rv in self.reverbs:
            sig = rv.apply(sig)

        sig *= self.volume
        self.phase = (self.phase + frames) % self.wavetable.length
        return sig

# Instantiate a Channel with ADSR parameters instead of globals
env_params = (0.01, 0.1, 0.3, 0.2)  # attack, decay, sustain, release
chan = Channel(Waveform('saw', SAMPLE_RATE, FREQUENCY), SAMPLE_RATE,
               env_params,
               filters=[Filter(1.2,1.0,0.8)],
               reverbs=[Reverb(0.6,0.03,4)],
               volume=1.0)

# Recording state
record_state = 0   # 0 = idle, 1 = recording, 2 = recorded
events = []        # List of (time_offset, 'on'/'off')
start_time = 0

# Audio callback
def audio_callback(outdata, frames, time_info, status):
    """PortAudio callback: process Channel."""
    sig = chan.process(frames)
    outdata[:,0] = np.clip(sig, -1.0, 1.0)

# Key press callback
def button_event(pin):
    """Trigger envelope and record events if active."""
    global events, start_time, record_state
    now = time.time()
    if GPIO.input(BUTTON_PIN) == GPIO.LOW:
        chan.envelope.note_on()
        if record_state == 1:
            events.append((now - start_time, 'on'))
    else:
        chan.envelope.note_off()
        if record_state == 1:
            events.append((now - start_time, 'off'))

# Record/playback control
def record_button(pin):
    """Cycle through record -> stop -> playback."""
    global record_state, start_time
    if GPIO.input(RECORD_PIN) == GPIO.LOW:
        if record_state == 0:
            record_state = 1
            events.clear()
            start_time = time.time()
            print("Recording started")
        elif record_state == 1:
            record_state = 2
            print("Recording stopped")
        elif record_state == 2:
            print("Playback started")
            def play_events():
                last_offset = 0
                for offset, ev in events:
                    time.sleep(offset - last_offset)
                    getattr(chan.envelope, 'note_' + ev)()
                    last_offset = offset
                print("Playback finished")
            threading.Thread(target=play_events, daemon=True).start()
            record_state = 0

# Main setup
def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(RECORD_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(BUTTON_PIN, GPIO.BOTH, callback=button_event, bouncetime=5)
    GPIO.add_event_detect(RECORD_PIN, GPIO.FALLING, callback=record_button, bouncetime=200)
    with sd.OutputStream(samplerate=SAMPLE_RATE, channels=1, dtype='float32', callback=audio_callback):
        print("Hold GPIO17 to play tone; GPIO27 to record/play.")
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            GPIO.cleanup()

if __name__ == '__main__':
    main()
