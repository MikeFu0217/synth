# audiothread.py
import sounddevice as sd
import numpy as np
import threading

class AudioThread(threading.Thread):
    def __init__(self, sound, note_event, samplerate=44100):
        super().__init__()
        self.sound = sound
        self.samplerate = samplerate
        self.running = threading.Event()
        self.running.set()
        self.note_event = note_event

    def audio_callback(self, outdata, frames, time_info, status):
        
        if self.note_event.is_set():
            self.sound.note_on()
        else:
            self.sound.note_off()

        sig = self.sound.process(frames)
        outdata[:, 0] = np.clip(sig, -1.0, 1.0)

    def run(self):
        with sd.OutputStream(
            samplerate=self.samplerate,
            channels=1,
            dtype='float32',
            callback=self.audio_callback
        ):
            while self.running.is_set():
                sd.sleep(100)

    def stop(self):
        self.running.clear()