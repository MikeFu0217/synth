import numpy as np
import sounddevice as sd

class Sound:
    def __init__(self):
        self.waveforms = []
        self.envelopes = []
        self.channels = []
    


class Waveform:
    def __init__(self, waveform="saw", duration=1.0, sample_rate=44100, frequency=440.0):
        """
        Initialize the Waveform object.
        :param duration: Duration of the waveform in seconds.
        :param sample_rate: Sample rate in Hz.
        :param frequency: Frequency of the waveform in Hz.
        """
        self.duration = duration
        self.sample_rate = sample_rate
        self.frequency = frequency
        self.t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

        if waveform == "saw":
            self.wave = 2.0 * (t * frequency - np.floor(t * frequency + 0.5))  # [-1, 1] sawtooth
        elif waveform == "sine":
            self.wave = np.sin(2 * np.pi * frequency * self.t)
        elif waveform == "square":
            self.wave = np.sign(np.sin(2 * np.pi * frequency * self.t))

class Envelope:
    def __init__(self, attack_time=0, decay_time=0.2, sustain_level=0, release_time=0, total_duration=1.0):
        """
        Initialize the Envelope object.
        :param attack_time: Attack time in seconds.
        :param decay_time: Decay time in seconds.
        :param sustain_level: Sustain level (0 to 1).
        :param release_time: Release time in seconds.
        :param total_duration: Total duration of the envelope in seconds.
        """
        self.attack_time = attack_time
        self.decay_time = decay_time
        self.sustain_level = sustain_level
        self.release_time = release_time
        self.total_duration = total_duration