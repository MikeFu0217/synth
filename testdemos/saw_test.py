import numpy as np
import sounddevice as sd

# 生成 sawtooth 波
duration = 1.0  # seconds
sample_rate = 44100
frequency = 440.0
t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
wave = 2.0 * (t * frequency - np.floor(t * frequency + 0.5))  # [-1, 1] sawtooth

# add envolope
def envelope(t, attack_time, decay_time, sustain_level, release_time, total_duration):
    envelope = np.zeros_like(t)

    attack_end = attack_time
    decay_end = attack_end + decay_time
    release_start = total_duration - release_time

    # Attack: 0 → 1
    attack_mask = (t >= 0) & (t < attack_end)
    envelope[attack_mask] = (t[attack_mask] / attack_time) if attack_time > 0 else 1

    # Decay: 1 → sustain_level
    decay_mask = (t >= attack_end) & (t < decay_end)
    if decay_time > 0:
        envelope[decay_mask] = 1 - ((t[decay_mask] - attack_end) / decay_time) * (1 - sustain_level)
    else:
        envelope[decay_mask] = sustain_level

    # Sustain
    sustain_mask = (t >= decay_end) & (t < release_start)
    envelope[sustain_mask] = sustain_level

    # Release: sustain_level → 0
    release_mask = (t >= release_start) & (t <= total_duration)
    if release_time > 0:
        envelope[release_mask] = sustain_level * (1 - (t[release_mask] - release_start) / release_time)
    else:
        envelope[release_mask] = 0

    return envelope

attack_time = 0
decay_time = 0.2
sustain_level = 0
release_time = 0
duration = 1.0

t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
env = envelope(t, attack_time, decay_time, sustain_level, release_time, duration)

wave *= env

# 播放
sd.play(wave, samplerate=sample_rate)
sd.wait()
