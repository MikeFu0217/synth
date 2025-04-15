import numpy as np
import sounddevice as sd

class Channel:
    def __init__(self, duration=2.0, sample_rate=44100):
        """
        Initialize a Channel object.
        :param duration: Total duration of the channel in seconds.
        :param sample_rate: Sample rate in Hz.
        """
        self.duration = duration
        self.sample_rate = sample_rate
        self.t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        self.waveform = None
        self.envelopes = []
        self.filters = []
        self.reverbs = []

    def set_waveform(self, waveform):
        """
        Set a waveform for the channel. Waveform duration must be shorter or equal to channel duration.
        :param waveform: Waveform object.
        """
        if waveform.duration > self.duration:
            raise ValueError("Waveform duration cannot exceed channel duration.")
        self.waveform = waveform

    def remove_waveform(self):
        """Remove the waveform from the channel."""
        self.waveform = None

    def add_envelope(self, envelope):
        """Add an envelope to the channel."""
        self.envelopes.append(envelope)

    def remove_envelope(self, envelope):
        """Remove an envelope from the channel."""
        if envelope in self.envelopes:
            self.envelopes.remove(envelope)

    def add_filter(self, filter_obj):
        """Add a filter to the channel."""
        self.filters.append(filter_obj)

    def remove_filter(self, filter_obj):
        """Remove a filter from the channel."""
        if filter_obj in self.filters:
            self.filters.remove(filter_obj)

    def add_reverb(self, reverb):
        """Add a reverb to the channel."""
        self.reverbs.append(reverb)

    def remove_reverb(self, reverb):
        """Remove a reverb from the channel."""
        if reverb in self.reverbs:
            self.reverbs.remove(reverb)

    def get_soundarray(self):
        """
        Generate the final sound array for playback.
        :return: Sound array after applying waveform, envelopes, filters, and reverbs.
        """
        wave = np.zeros_like(self.t)

        if self.waveform:
            waveform_array = self.waveform.generate_waveform()
            wave[:len(waveform_array)] = waveform_array

            for envelope in self.envelopes:
                env_array = envelope.apply_envelope(self.waveform.t)
                wave[:len(env_array)] *= env_array

        for filter_obj in self.filters:
            wave = filter_obj.apply_filter(wave, self.sample_rate)

        for reverb in self.reverbs:
            wave = reverb.apply_reverb(wave, self.sample_rate)

        return wave

    def play(self):
        """Play the generated waveform."""
        soundarray = self.get_soundarray()
        sd.play(soundarray, samplerate=self.sample_rate)
        sd.wait()


class Waveform:
    def __init__(self, name="saw", duration=1.0, frequency=440.0, sample_rate=44100):
        self.name = name
        self.duration = duration
        self.frequency = frequency
        self.sample_rate = sample_rate
        self.t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

    def generate_waveform(self):
        if self.name == "saw":
            return 2.0 * (self.t * self.frequency - np.floor(self.t * self.frequency + 0.5))
        elif self.name == "sine":
            return np.sin(2 * np.pi * self.frequency * self.t)
        elif self.name == "square":
            return np.sign(np.sin(2 * np.pi * self.frequency * self.t))
        else:
            return np.zeros_like(self.t)


class Envelope:
    def __init__(self, attack_time=0, decay_time=0.2, sustain_level=0, release_time=0):
        self.attack_time = attack_time
        self.decay_time = decay_time
        self.sustain_level = sustain_level
        self.release_time = release_time

    def apply_envelope(self, t):
        env = np.ones_like(t)
        total_duration = t[-1]

        attack_end = self.attack_time
        decay_end = attack_end + self.decay_time
        release_start = total_duration - self.release_time

        env[t < attack_end] = (t[t < attack_end] / self.attack_time) if self.attack_time > 0 else 1

        decay_mask = (t >= attack_end) & (t < decay_end)
        if self.decay_time > 0:
            env[decay_mask] = 1 - ((t[decay_mask] - attack_end) / self.decay_time) * (1 - self.sustain_level)

        sustain_mask = (t >= decay_end) & (t < release_start)
        env[sustain_mask] = self.sustain_level

        release_mask = t >= release_start
        if self.release_time > 0:
            env[release_mask] = self.sustain_level * (1 - (t[release_mask] - release_start) / self.release_time)
        else:
            env[release_mask] = 0

        return env


class Filter:
    def __init__(self, low=1.0, mid=1.0, high=1.0):
        self.low = low
        self.mid = mid
        self.high = high

    def apply_filter(self, wave, sample_rate):
        fft_wave = np.fft.rfft(wave)
        frequencies = np.fft.rfftfreq(len(wave), 1 / sample_rate)

        fft_wave[frequencies < 400] *= self.low
        fft_wave[(frequencies >= 400) & (frequencies < 4000)] *= self.mid
        fft_wave[frequencies >= 4000] *= self.high

        return np.fft.irfft(fft_wave, n=len(wave))


class Reverb:
    def __init__(self, decay=0.5, delay=0.1, reflections=5):
        self.decay = decay
        self.delay = delay
        self.reflections = reflections

    def apply_reverb(self, wave, sample_rate):
        output = np.copy(wave)
        delay_samples = int(self.delay * sample_rate)
        for i in range(1, self.reflections + 1):
            idx = delay_samples * i
            if idx < len(wave):
                output[idx:] += wave[:-idx] * (self.decay ** i)
        return output
