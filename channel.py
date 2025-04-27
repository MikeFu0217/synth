import numpy as np
import sounddevice as sd

sd.default.device = 0

std_range = [0.0, 1.0]

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

        self.vol_range = [0.0, 1.0]

        self.env_att_range = [0.0, 1.0]
        self.env_dec_range = [0.0, 1.0]
        self.env_sus_range = [0.0, 1.0]
        self.env_rel_range = [0.0, 1.0]

        self.filter_l_range = [0.0, 1.0]
        self.filter_m_range = [0.0, 1.0]
        self.filter_h_range = [0.0, 1.0]
        
        self.rev_dec_range = [0.0, 1.0]
        self.rev_del_range = [0.0, 0.5]
        self.rev_ref_range = [0, 20]

    def set_waveform(self, waveform):
        """
        Set a waveform for the channel. Waveform duration must be
        shorter or equal to channel duration.
        """
        if waveform.duration > self.duration:
            raise ValueError("Waveform duration cannot exceed channel duration.")
        self.waveform = waveform

        # —— 新增：只生成一次整段样本，后面回调只做索引
        self.wave_data = waveform.generate_waveform().astype(np.float32)

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
        elif self.name == "sin":
            return np.sin(2 * np.pi * self.frequency * self.t)
        elif self.name == "sqr":
            return np.sign(np.sin(2 * np.pi * self.frequency * self.t))
        else:
            return np.zeros_like(self.t)


# class Envelope:
#     def __init__(self, attack_time=0, decay_time=0, sustain_level=1, release_time=0):
#         self.attack_time = attack_time
#         self.decay_time = decay_time
#         self.sustain_level = sustain_level
#         self.release_time = release_time

#     def apply_envelope(self, t):
#         env = np.ones_like(t)
#         total_duration = t[-1]

#         attack_end = self.attack_time
#         decay_end = attack_end + self.decay_time
#         release_start = total_duration - self.release_time

#         env[t < attack_end] = (t[t < attack_end] / self.attack_time) if self.attack_time > 0 else 1

#         decay_mask = (t >= attack_end) & (t < decay_end)
#         if self.decay_time > 0:
#             env[decay_mask] = 1 - ((t[decay_mask] - attack_end) / self.decay_time) * (1 - self.sustain_level)

#         sustain_mask = (t >= decay_end) & (t < release_start)
#         env[sustain_mask] = self.sustain_level

#         release_mask = t >= release_start
#         if self.release_time > 0:
#             env[release_mask] = self.sustain_level * (1 - (t[release_mask] - release_start) / self.release_time)
#         else:
#             env[release_mask] = 0

#         return env
    
#     def apply_release_only(self, rel_t):
#         """
#         rel_t: 从松键时刻起算的相对时间数组，
#         松键前 rel_t<0 返回 1；0≤rel_t≤release_time 做线性衰减；其后返回 0。
#         """
#         # 初始化全 0
#         env = np.zeros_like(rel_t)

#         # 松键前，保持 1
#         env[rel_t < 0] = 1.0

#         # 只有 release_time>0 时才做衰减运算，避免除以零
#         if self.release_time > 0:
#             mask = (rel_t >= 0) & (rel_t <= self.release_time)
#             env[mask] = self.sustain_level * (1 - rel_t[mask] / self.release_time)
#             # release_time 之后 env 已是 0，无需再写

#         return env

class Envelope:
    def __init__(self, attack_time=0, decay_time=0, sustain_level=1, release_time=0):
        # … 现有 init …
        self.attack_time  = attack_time
        self.decay_time   = decay_time
        self.sustain_level= sustain_level
        self.release_time = release_time

    def apply_adsr(self, t: np.ndarray) -> np.ndarray:
        """
        t: 从 NOTE ON 时刻起算的相对时间向量
        返回 A–D–S 电平，不含 Release。
        """
        env = np.zeros_like(t)

        # Attack
        if self.attack_time > 0:
            mask = (t >= 0) & (t < self.attack_time)
            env[mask] = t[mask] / self.attack_time
        else:
            env[t >= 0] = 1.0

        # Decay
        decay_end = self.attack_time + self.decay_time
        if self.decay_time > 0:
            mask = (t >= self.attack_time) & (t < decay_end)
            env[mask] = 1 - ((t[mask] - self.attack_time) / self.decay_time) * (1 - self.sustain_level)

        # Sustain (从 decay_end 到 key-off)
        mask = t >= decay_end
        env[mask] = self.sustain_level

        return env

    def apply_release_only(self, rel_t: np.ndarray) -> np.ndarray:
        """
        rel_t: 从 NOTE OFF 时刻起算的相对时间向量
        返回 Release 电平，之前为 1，之后线性降到 0。
        """
        env = np.zeros_like(rel_t)

        # 松键前保持 1
        env[rel_t < 0] = 1.0

        # Release 阶段
        if self.release_time > 0:
            mask = (rel_t >= 0) & (rel_t <= self.release_time)
            env[mask] = self.sustain_level * (1 - rel_t[mask] / self.release_time)
            # rel_t > release_time 时 env 保持 0
        # release_time == 0 时直接全 0

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
    def __init__(self, decay=0, delay=0, reflections=0):
        self.decay = decay
        self.delay = delay
        self.reflections = reflections

    def apply_reverb(self, wave, sample_rate):
        if self.decay == 0:
            return wave
        output = np.copy(wave)
        delay_samples = int(self.delay * sample_rate)
        for i in range(1, self.reflections + 1):
            idx = delay_samples * i
            if idx < len(wave):
                output[idx:] += wave[:-idx] * (self.decay ** i)
        return output
