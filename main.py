from channel import *

def test_week2():
    # Create a channel
    channel1 = Channel(duration=2.0, sample_rate=44100)
    # Create a waveform (e.g., sawtooth)
    waveform = Waveform(frequency=440, sample_rate=44100, duration=1.0)    
    # Add waveform to channel
    channel1.set_waveform(waveform)

    channel1.play()

    # Create an envelope
    envelope = Envelope(attack_time=0.1, decay_time=0.2, sustain_level=0.5, release_time=0.3)
    # Apply envelope to waveform
    channel1.add_envelope(envelope)

    channel1.play()

    # Create a filter
    filter = Filter(low=0.5, mid=1.0, high=0.5)
    # Apply filter to waveform
    channel1.add_filter(filter)

    channel1.play()

    # Create a reverb
    reverb = Reverb(decay=0.5, delay=0.2, reflections=5)
    # Apply reverb to waveform
    channel1.add_reverb(reverb)

    channel1.play()


def main():
    
    

if __name__ == "__main__":
    main()