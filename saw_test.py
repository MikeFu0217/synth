import numpy as np
import sounddevice as sd

# 生成 sawtooth 波
duration = 1.0  # seconds
sample_rate = 44100
frequency = 440.0
t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
wave = 2.0 * (t * frequency - np.floor(t * frequency + 0.5))  # [-1, 1] sawtooth

# 播放
sd.play(wave, samplerate=sample_rate)
sd.wait()