from channel import *

class Sound:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.channels = []
        self.volumes = []
        self.duration = 0.0

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