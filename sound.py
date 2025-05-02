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

    def get_current_params(self):
        """Get a string representation of the current parameters."""
        params = []
        for channel in self.channels:
            param = {}
            param['waveform'] = {}
            param['waveform']['name'] = channel.waveform.name
            param['waveform']['frequency'] = channel.waveform.frequency

            param['envelope'] = {}
            param['envelope']['attack_time'] = channel.envelopes[0].attack_time
            param['envelope']['decay_time'] = channel.envelopes[0].decay_time
            param['envelope']['sustain_level'] = channel.envelopes[0].sustain_level
            param['envelope']['release_time'] = channel.envelopes[0].release_time

            param['filter'] = {}
            param['filter']['low'] = channel.filters[0].low
            param['filter']['mid'] = channel.filters[0].mid
            param['filter']['high'] = channel.filters[0].high

            param['reverb'] = {}
            param['reverb']['decay'] = channel.reverbs[0].decay
            param['reverb']['delay'] = channel.reverbs[0].delay
            param['reverb']['wet'] = channel.reverbs[0].wet

            param['volume'] = channel.volume

            params.append(param)
        return params