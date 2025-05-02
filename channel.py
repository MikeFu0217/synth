import numpy as np
import sounddevice as sd
import time

std_range = [0.0, 1.0]

class Channel:
    def __init__(
        self,
        waveform, envelopes, filters, reverbs,
        sr=44100, volume=1.0
        ):
        """
        Channel encapsulates waveform, ADSR envelope, filters, reverbs, and volume.
        env_params: tuple (attack, decay, sustain, release)
        """
        self.waveform = waveform
        self.envelopes = [envelopes]
        self.filters = [filters]
        self.reverbs = [reverbs]
        self.sr = sr
        self.volume = volume
        self.phase = 0

        self.vol_range = [0.0, 1.0]

        self.env_att_range = [0.0, 1.0]
        self.env_dec_range = [0.0, 1.0]
        self.env_sus_range = [0.0, 1.0]
        self.env_rel_range = [0.0, 1.0]

        self.filter_l_range = [0.0, 1.0]
        self.filter_m_range = [0.0, 1.0]
        self.filter_h_range = [0.0, 1.0]
        
        self.rev_dec_range = [0.0, 1.0]
        self.rev_del_range = [0.0, 0.2]
        self.rev_wet_range = [0.0, 1.0]

    def process(self, frames):
        """Generate a mono buffer for this channel."""
        ar = np.arange(frames)
        idx = (self.phase + ar) % self.waveform.length
        sig = self.waveform.data[idx].copy()

        # Apply ADSR envelope
        for env in self.envelopes:
            sig *= env.process(frames)
        # Apply filters
        for fl in self.filters:
            sig = fl.apply(sig)
        # Apply reverbs
        for rv in self.reverbs:
            sig = rv.apply(sig)

        sig *= self.volume
        self.phase = (self.phase + frames) % self.waveform.length
        return sig

class Waveform:
    def __init__(self, name, sr=44100, frequency=440.0):
        """
        Initialize a waveform generator with given type.
        name: 'saw', 'sin', or 'square'
        sr: sample rate
        frequency: tone frequency in Hz
        """
        self.name = name
        self.frequency = frequency
        self.length = int(sr / frequency)
        t = np.arange(self.length) / sr
        if name == 'saw':
            self.data = (2 * (t * frequency - np.floor(t * frequency + 0.5))).astype('float32')
        elif name == 'sin':
            self.data = np.sin(2 * np.pi * frequency * t).astype('float32')
        elif name == 'sqr':
            self.data = np.sign(np.sin(2 * np.pi * frequency * t)).astype('float32')
        else:
            raise ValueError(f"Unknown waveform '{name}'")

class Envelope:
    def __init__(self, sr=44100, attack=0.2, decay=0.3, sustain=0.5, release=0.4):
        self.sr = sr
        self.attack_time = attack
        self.decay_time = decay
        self.sustain_level = sustain
        self.release_time = release

        self.state = 'idle'
        self.progress = 0.0
        self.current_amp = 0.0

        self.update_samples()

    def update_samples(self):
        self.a_samps = max(1, int(self.attack_time * self.sr))
        self.d_samps = max(1, int(self.decay_time * self.sr))
        self.r_samps = max(1, int(self.release_time * self.sr))

    def note_on(self):
        self.state = 'attack'
        self.progress = 0.0
        self.update_samples()

    def note_off(self):
        if self.state in ('attack', 'decay', 'sustain'):
            self.state = 'release'
            self.progress = 0.0
            self.start_amp = self.current_amp
            self.update_samples()

    def process(self, frames):
        env = np.zeros(frames, dtype='float32')

        if self.state == 'idle':
            return env

        self.update_samples()

        for i in range(frames):
            if self.state == 'attack':
                self.progress += 1.0 / self.a_samps
                self.current_amp = min(self.progress, 1.0)
                env[i] = self.current_amp
                if self.progress >= 1.0:
                    self.state = 'decay'
                    self.progress = 0.0
            elif self.state == 'decay':
                self.progress += 1.0 / self.d_samps
                self.current_amp = 1.0 - (1.0 - self.sustain_level) * self.progress
                env[i] = self.current_amp
                if self.progress >= 1.0:
                    self.state = 'sustain'
            elif self.state == 'sustain':
                self.current_amp = self.sustain_level
                env[i] = self.current_amp
            elif self.state == 'release':
                self.progress += 1.0 / self.r_samps
                self.current_amp = max(self.start_amp * (1.0 - self.progress), 0.0)
                env[i] = self.current_amp
                if self.progress >= 1.0:
                    self.state = 'idle'
                    self.current_amp = 0.0
            else:
                env[i] = 0.0

        print(f"\rState: {self.state}\t, Progress: {self.progress:.4f}, Current Amp: {self.current_amp:.4f}", end="")

        return env

class Filter:
    def __init__(self, low=1.0, mid=1.0, high=1.0, sr=44100):
        """Simple three-band filter."""
        self.low = low
        self.mid = mid
        self.high = high
        self.sr = sr

    def apply(self, signal):
        """Apply band-specific gains."""
        fft = np.fft.rfft(signal)
        freqs = np.fft.rfftfreq(len(signal), d=1/self.sr)
        fft[freqs < 400] *= self.low
        fft[(freqs >= 400) & (freqs < 4000)] *= self.mid
        fft[freqs >= 4000] *= self.high
        return np.fft.irfft(fft, n=len(signal))

class Reverb:
    def __init__(self, decay=0.5, delay=0.1, reflections=20, wet=0.0, sr=44100):
        self.decay = decay
        self.delay = delay
        self.reflections = reflections
        self.wet = wet
        self.sr = sr
        self.buffer = np.zeros(sr // 2)

    def apply(self, signal):
        out = np.copy(signal)
        d_samp = int(self.delay * self.sr)

        for i in range(1, self.reflections + 1):
            idx = d_samp * i

            if idx <= 0:
                continue
            if idx >= len(signal):
                break

            random_offset = np.random.randint(-3, 3)
            real_idx = max(0, idx + random_offset)

            if real_idx < len(signal):
                out[real_idx:] += signal[:-real_idx] * (self.decay ** i) * 2.0

        buffer_len = len(self.buffer)
        min_len = min(buffer_len, len(out))
        out[:min_len] += self.buffer[:min_len] * 0.5


        self.buffer = np.roll(self.buffer, -len(signal))
        self.buffer[-len(signal):] = out

        return (1.0 - self.wet) * signal + self.wet * out