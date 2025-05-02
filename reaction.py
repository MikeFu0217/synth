import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import tempfile
import openai
import json
import os
import time
import subprocess
from vosk import Model, KaldiRecognizer

# ------------ Synth LLM Config ------------

SYSTEM_PROMPT = """You are a professional synthesizer sound designer assistant.

Your job is: based on a user's natural language description of the desired sound characteristics (such as tone, feeling, attack speed, reverb strength, etc.), infer appropriate synthesizer parameters, and generate a full JSON configuration, as follows:

- Output an overall "description" field (a short 1-2 sentence natural language description summarizing the intended sound character based on the user's input).
- Then output a "channels" field, which is a list of 3 sound channels, each configured as below:
  - The first channel must always use waveform "saw"
  - The second channel must always use waveform "sin"
  - The third channel must always use waveform "sqr"

Each channel must contain:
- waveform (name fixed + frequency matching the description if specified)
- envelope (attack_time, decay_time, sustain_level, release_time)
- filter (low, mid, high gain settings)
- reverb (decay, delay, reflections, wet)
- volume

If the user specifies tone (e.g., "punchy", "smooth", "ambient"), modify attack, decay, reverb, and volume accordingly to match the feel.

If the user specifies a frequency, apply it uniformly across all channels unless otherwise indicated.

Example structure:

{
  "description": "A punchy and ambient preset with fast attack and rich reverb, suitable for energetic leads.",
  "channels": [
    {
      "waveform": {
        "name": "saw",
        "frequency": 440.0
      },
      "envelope": {
        "attack_time": 0.1,
        "decay_time": 0.3,
        "sustain_level": 0.7,
        "release_time": 0.4
      },
      "filter": {
        "low": 1.0,
        "mid": 0.8,
        "high": 1.2
      },
      "reverb": {
        "decay": 0.5,
        "delay": 0.1,
        "reflections": 20,
        "wet": 0.3
      },
      "volume": 0.8
    },
    ...
  ]
}

Only output valid JSON.
"""

# ------------ Classes ------------

class LLMClient:
    def __init__(self, api_key_path, model="gpt-4o-mini"):
        with open(api_key_path, 'r') as f:
            self.api_key = f.read().strip()
        if not self.api_key:
            raise ValueError("API key not found.")
        self.model = model
        self.client = openai.OpenAI(api_key=self.api_key)

    def gen_resp(self, prompt):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.7
        )
        return json.loads(response.choices[0].message.content)

class SpeechToTextLocal:
    def __init__(self,
                 model_path: str = "model/vosk-model-small-en-us-0.15",
                 samplerate: int = 44100,
                 threshold: float = 0.02,
                 silence_duration: float = 1.0,
                 max_record_time: float = 30.0):
        """
        model_path:       path to your Vosk model folder
        samplerate:       recording sample rate
        threshold:        RMS level above which we consider 'speech'
        silence_duration: seconds of silence to auto‐stop after speaking
        max_record_time:  absolute cap on recording length
        """
        # load the Vosk model (may take ~1s)
        print(f"Loading Vosk model from {model_path} …")
        self.model = Model(model_path)
        self.samplerate = samplerate
        self.threshold = threshold
        self.silence_duration = silence_duration
        self.max_record_time = max_record_time

    def record_and_transcribe(self) -> str:
        """
        1) wait for speech (RMS > threshold)
        2) record until silence_duration of quiet or max_record_time
        3) feed entire waveform to Vosk and return transcript
        """
        print("⏳ Waiting for speech…")
        frames = []
        in_speech = False
        silence_start = None
        start_time = sd.get_stream().time if False else __import__('time').time()

        def callback(indata, _frames, _time, _status):
            nonlocal in_speech, silence_start, start_time
            rms = np.linalg.norm(indata) / np.sqrt(indata.size)
            now = __import__('time').time()

            # timeout
            if now - start_time > self.max_record_time:
                raise sd.CallbackStop()

            if rms > self.threshold:
                if not in_speech:
                    in_speech = True
                    print("🎤 Detected speech, recording…")
                silence_start = None
                frames.append(indata.copy())
            else:
                if in_speech:
                    if silence_start is None:
                        silence_start = now
                    elif now - silence_start >= self.silence_duration:
                        print("🤫 Silence after speech, stopping.")
                        raise sd.CallbackStop()
                    frames.append(indata.copy())

        # open stream and block until stop
        with sd.InputStream(channels=1,
                            samplerate=self.samplerate,
                            callback=callback):
            sd.sleep(int(self.max_record_time * 1000))

        if not frames:
            print("⚠️  No speech detected.")
            return ""

        # concatenate and convert to 16-bit PCM
        audio = np.concatenate(frames, axis=0)
        pcm_data = (audio * 32767).astype(np.int16).tobytes()

        # recognize with Vosk
        rec = KaldiRecognizer(self.model, self.samplerate)
        rec.SetWords(False)
        rec.AcceptWaveform(pcm_data)
        result = rec.FinalResult()
        text = json.loads(result).get("text", "")
        print("📝 Transcription:", text)
        return text

class TextToSpeech:
    def __init__(self, rate: int = 180, volume: int = 200):
        """
        rate:    speaking rate (words per minute)
        volume:  amplitude (0–200)
        """
        self.rate = rate
        self.volume = volume

    def speak(self, text: str):
        """
        Synchronously speak the given text using espeak.
        espeak handles playback itself; no external player needed.
        All espeak output is suppressed to keep the console clean.
        """
        subprocess.call(
            [
                'espeak',
                f'-s{self.rate}',    # set speaking rate
                f'-a{self.volume}',  # set volume amplitude
                text
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )