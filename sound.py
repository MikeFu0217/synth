from channel import *

class Sound:
    def __init__(self, sr=44100):
        self.sr = sr
        self.channels = []
        self.volumes = []

    def add_channel(self, channel):
        """Add a channel to the sound."""
        self.channels.append(channel)

    def process(self, frames):
        """Process all channels and mix them down to a single output."""
        sig = np.zeros(frames)
        for channel in self.channels:
            sig += channel.process(frames)
        return sig

    def note_on(self):
        """Trigger note on for all channels."""
        for channel in self.channels:
            channel.envelopes[0].note_on()
    
    def note_off(self):
        """Trigger note off for all channels."""
        for channel in self.channels:
            channel.envelopes[0].note_off()