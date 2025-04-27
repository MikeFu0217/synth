from channel import *

class Sound:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.channels = []
        self.volumes = []
        self.duration = 0.0

        # ---- 新增 ----
        self.blocksize = 1024                # ← 你也可以试 2048 或 4096
        self._arange = np.arange(self.blocksize, dtype=np.int32)
        self.stream = sd.OutputStream(
            samplerate=self.sample_rate,
            blocksize=self.blocksize,
            channels=1,
            dtype='float32',                # 避免每次都做类型转换
            latency='low',                  # “低延迟”模式也能稍微优化
            callback=self._audio_callback
        )
        self.stream.start()

        # gate 及时钟
        self.gate = False       # False = note off, True = note on
        self.sample_counter = 0 # 用来在回调里追踪时间
        self.note_off_sample = None

    def _audio_callback(self, outdata, frames, time, status):
        """
        每次声卡请求 `frames` 个采样时调用。
        根据当前 gate 状态生成波形并打上包络（包括 release 阶段）。
        """
        ar = self._arange[:frames]
        t_rel = (ar + self.sample_counter) / self.sample_rate
        buffer = np.zeros(frames)

        # 遍历每个 channel，叠加它们
        for ch, vol in zip(self.channels, self.volumes):
            # 1) 生成循环波形
            idx = (self.sample_counter + ar) % len(ch.wave_data)
            wave = ch.wave_data[idx]

            # 2) 根据 gate 状态选 ADSR 段
            if self.gate:
                env = ch.envelopes[0].apply_adsr(t_rel)
            else:
                # 计算从 NOTE OFF 起的时间
                if self.note_off_sample is None:
                    env = np.zeros_like(wave)
                else:
                    rel_t = (self.sample_counter + ar - self.note_off_sample) / self.sample_rate
                    env = ch.envelopes[0].apply_release_only(rel_t)

            buffer += wave * env * vol

        # 限幅
        buffer = np.clip(buffer, -1.0, 1.0)

        # 写回声卡
        outdata[:,0] = buffer
        self.sample_counter += frames

    def note_on(self):
        self.gate = True
        # 重置计数，重新从头开始包络
        self.sample_counter = 0
        self.note_off_sample = None

    def note_off(self):
        # 记录什么时候进入 release
        self.gate = False
        self.note_off_sample = self.sample_counter

    def add_channel(self, channel, volume=1.0):
        """Add a channel to the sound."""
        self.channels.append(channel)
        self.volumes.append(volume)
        self.duration = max(self.duration, channel.duration)

    def remove_channel(self, channel):
        """Remove a channel from the sound."""
        if channel in self.channels:
            self.channels.remove(channel)
            index = self.channels.index(channel)
            self.volumes.pop(index)
            self.duration = max([c.duration for c in self.channels]) if self.channels else 0.0

    def get_volume(self, channel):
        """Get the volume for a specific channel."""
        if channel in self.channels:
            index = self.channels.index(channel)
            return self.volumes[index]
        else:
            raise ValueError("Channel not found in sound.")
    
    def set_volume(self, channel, volume):
        """Set the volume for a specific channel."""
        if channel in self.channels:
            index = self.channels.index(channel)
            self.volumes[index] = volume
        else:
            raise ValueError("Channel not found in sound.")

    def get_env_att(self, channel, envid=0):
        """Get the attack time for a specific envelope."""
        if channel in self.channels:
            index = self.channels.index(channel)
            return channel.envelopes[envid].attack_time
        else:
            raise ValueError("Channel not found in sound.")
    
    def set_env_att(self, channel, attack_time, envid=0):
        """Set the attack time for a specific envelope."""
        if channel in self.channels:
            index = self.channels.index(channel)
            channel.envelopes[envid].attack_time = attack_time
        else:
            raise ValueError("Channel not found in sound.")

    def get_env_dec(self, channel, envid=0):
        """Get the decay time for a specific envelope."""
        if channel in self.channels:
            index = self.channels.index(channel)
            return channel.envelopes[envid].decay_time
        else:
            raise ValueError("Channel not found in sound.")

    def set_env_dec(self, channel, decay_time, envid=0):
        """Set the decay time for a specific envelope."""
        if channel in self.channels:
            index = self.channels.index(channel)
            channel.envelopes[envid].decay_time = decay_time
        else:
            raise ValueError("Channel not found in sound.")
    
    def get_env_sus(self, channel, envid=0):
        """Get the sustain level for a specific envelope."""
        if channel in self.channels:
            index = self.channels.index(channel)
            return channel.envelopes[envid].sustain_level
        else:
            raise ValueError("Channel not found in sound.")

    def set_env_sus(self, channel, sustain_level, envid=0):
        """Set the sustain level for a specific envelope."""
        if channel in self.channels:
            index = self.channels.index(channel)
            channel.envelopes[envid].sustain_level = sustain_level
        else:
            raise ValueError("Channel not found in sound.")
    
    def get_env_rel(self, channel, envid=0):
        """Get the release time for a specific envelope."""
        if channel in self.channels:
            index = self.channels.index(channel)
            return channel.envelopes[envid].release_time
        else:
            raise ValueError("Channel not found in sound.")
    
    def set_env_rel(self, channel, release_time, envid=0):
        """Set the release time for a specific envelope."""
        if channel in self.channels:
            index = self.channels.index(channel)
            channel.envelopes[envid].release_time = release_time
        else:
            raise ValueError("Channel not found in sound.")

    def get_filter_L(self, channel, filterid=0):
        """Get the low-pass filter value for a specific filter."""
        if channel in self.channels:
            index = self.channels.index(channel)
            return channel.filters[filterid].low
        else:
            raise ValueError("Channel not found in sound.")

    def set_filter_L(self, channel, low, filterid=0):
        """Set the low-pass filter value for a specific filter."""
        if channel in self.channels:
            index = self.channels.index(channel)
            channel.filters[filterid].low = low
        else:
            raise ValueError("Channel not found in sound.")

    def get_filter_M(self, channel, filterid=0):
        """Get the mid-pass filter value for a specific filter."""
        if channel in self.channels:
            index = self.channels.index(channel)
            return channel.filters[filterid].mid
        else:
            raise ValueError("Channel not found in sound.")

    def set_filter_M(self, channel, mid, filterid=0):
        """Set the mid-pass filter value for a specific filter."""
        if channel in self.channels:
            index = self.channels.index(channel)
            channel.filters[filterid].mid = mid
        else:
            raise ValueError("Channel not found in sound.")
    
    def get_filter_H(self, channel, filterid=0):
        """Get the high-pass filter value for a specific filter."""
        if channel in self.channels:
            index = self.channels.index(channel)
            return channel.filters[filterid].high
        else:
            raise ValueError("Channel not found in sound.")
    
    def set_filter_H(self, channel, high, filterid=0):
        """Set the high-pass filter value for a specific filter."""
        if channel in self.channels:
            index = self.channels.index(channel)
            channel.filters[filterid].high = high
        else:
            raise ValueError("Channel not found in sound.")
    
    def get_reverb_dec(self, channel, reverbid=0):
        """Get the decay time for a specific reverb."""
        if channel in self.channels:
            index = self.channels.index(channel)
            return channel.reverbs[reverbid].decay
        else:
            raise ValueError("Channel not found in sound.")

    def set_reverb_dec(self, channel, decay_time, reverbid=0):
        """Set the decay time for a specific reverb."""
        if channel in self.channels:
            index = self.channels.index(channel)
            channel.reverbs[reverbid].decay = decay_time
        else:
            raise ValueError("Channel not found in sound.")
    
    def get_reverb_del(self, channel, reverbid=0):
        """Get the delay time for a specific reverb."""
        if channel in self.channels:
            index = self.channels.index(channel)
            return channel.reverbs[reverbid].delay
        else:
            raise ValueError("Channel not found in sound.")
    
    def set_reverb_del(self, channel, delay_time, reverbid=0):
        """Set the delay time for a specific reverb."""
        if channel in self.channels:
            index = self.channels.index(channel)
            channel.reverbs[reverbid].delay = delay_time
        else:
            raise ValueError("Channel not found in sound.")

    def get_reverb_ref(self, channel, reverbid=0):
        """Get the reflection count for a specific reverb."""
        if channel in self.channels:
            index = self.channels.index(channel)
            return channel.reverbs[reverbid].reflections
        else:
            raise ValueError("Channel not found in sound.")

    def set_reverb_ref(self, channel, reflections, reverbid=0):
        """Set the reflection count for a specific reverb."""
        if channel in self.channels:
            index = self.channels.index(channel)
            channel.reverbs[reverbid].reflections = reflections
        else:
            raise ValueError("Channel not found in sound.")

    def get_soundarray(self):
        wave = np.zeros(int(self.duration * self.sample_rate))
        for channel in self.channels:
            channel_wave = channel.get_soundarray()
            wave[:len(channel_wave)] += channel_wave * self.volumes[self.channels.index(channel)]
        wave = np.clip(wave, -1.0, 1.0)
        return wave

    def play(self):
        """Play the generated sound."""
        soundarray = self.get_soundarray()
        sd.play(soundarray, samplerate=self.sample_rate)
        sd.wait()