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
import tempfile

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
- reverb (decay, delay, wet)
- volume

The range of each parameter is as follows:
- attack_time: 0.0 to 1.0
- decay_time: 0.0 to 1.0
- sustain_level: 0.0 to 1.0
- release_time: 0.0 to 1.0
- low: 0.0 to 1.0
- mid: 0.0 to 1.0
- high: 0.0 to 1.0
- decay: 0.0 to 1.0
- delay: 0.0 to 0.2
- wet: 0.0 to 1.0
- volume: 0.0 to 1.0

If the user specifies tone (e.g., "punchy", "smooth", "ambient"), modify attack, decay, reverb, and volume accordingly to match the feel.
If the user specifies a frequency, apply it uniformly across all channels unless otherwise indicated.
If the user implies to that the parameter is right and want exit, set exit to 1, oherwise set it to 0.

Notice:
- The input of user is retrieved from a microphone, so the text may be inaccurate. Please notice this and try get the user's meaning as much as you can.
- You are able to set different parameters for saw, sin and sqr waveforms. Just do your best to make the sound as close to the user's description as possible.

Example structure:

{
  "exit": 0,
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

def call_synth_llm(llm: LLMClient, prompt: str) -> dict:
    """
    Send `prompt` to your LLMClient.gen_resp, return dict with:
     - exit (0/1)
     - description (str)
     - channels (list of channel configs)
    """
    try:
        resp = llm.gen_resp(prompt)
        # ensure it has the keys we expect:
        for k in ("exit", "description", "channels"):
            if k not in resp:
                raise KeyError(f"Missing '{k}' in LLM response")
        return resp
    except Exception as e:
        print("LLM call failed:", e)
        return {"exit": 1, "description": "", "channels": []}

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
        print(f"Loading Vosk model from {model_path} …")
        self.model = Model(model_path)
        self.samplerate       = samplerate
        self.threshold        = threshold
        self.silence_duration = silence_duration
        self.max_record_time  = max_record_time

    def record_and_transcribe(self) -> str:
        """
        1) wait for speech (RMS > threshold)
        2) record until silence_duration of quiet or max_record_time
        3) feed PCM to Vosk and return transcript
        """
        print("⏳ Waiting for speech…")
        frames         = []
        in_speech      = False
        silence_start  = None
        stop_recording = False
        start_time     = time.time()

        def callback(indata, _frames, _time, _status):
            nonlocal in_speech, silence_start, stop_recording, start_time
            # compute RMS on float32 audio in [-1,1]
            rms = np.sqrt(np.mean(indata**2))
            now = time.time()

            # overall timeout
            if self.max_record_time and now - start_time > self.max_record_time:
                stop_recording = True
                raise sd.CallbackStop()

            # speech start
            if rms > self.threshold:
                if not in_speech:
                    in_speech = True
                    print("🎤 Speech detected, recording…")
                silence_start = None
                frames.append(indata.copy())

            # speech has started → watch for silence
            elif in_speech:
                if silence_start is None:
                    silence_start = now
                elif now - silence_start >= self.silence_duration:
                    print("🤫 Silence detected, stopping.")
                    stop_recording = True
                    raise sd.CallbackStop()
                frames.append(indata.copy())

        # open stream and spin until we hit stop_recording
        with sd.InputStream(
            channels=1,
            samplerate=self.samplerate,
            dtype='float32',
            callback=callback
        ):
            while not stop_recording:
                time.sleep(0.05)

        # no speech?
        if not frames:
            print("⚠️ No speech detected.")
            return ""

        # convert to 16-bit PCM bytes for Vosk
        audio = np.concatenate(frames, axis=0)
        pcm_data = (audio * 32767).astype(np.int16).tobytes()

        # feed into Vosk recognizer
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

class SpeechToTextWhisper:
    def __init__(
        self,
        api_key_path: str,
        model: str = "whisper-1",
        samplerate: int = 44100,
        threshold: float = 0.02,
        silence_duration: float = 1.0,
        max_record_time: float = None
    ):
        """
        threshold: RMS level (0–1) to detect start of speech.
        """
        # load API key
        with open(api_key_path, 'r') as f:
            openai.api_key = f.read().strip()
        if not openai.api_key:
            raise ValueError("OpenAI API key not found.")

        self.model            = model
        self.samplerate       = samplerate
        self.threshold        = threshold
        self.silence_duration = silence_duration
        self.max_record_time  = max_record_time

    def record_and_transcribe(self) -> str:
        print("⏳ Waiting for speech…")
        frames        = []
        in_speech     = False
        silence_start = None
        stop_recording= False
        start_time    = time.time()

        def callback(indata, _frames, _time, _status):
            nonlocal in_speech, silence_start, stop_recording, start_time
            rms = np.sqrt(np.mean(indata**2))
            now = time.time()

            # overall timeout guard
            if self.max_record_time and now - start_time > self.max_record_time:
                stop_recording = True
                raise sd.CallbackStop()

            if rms > self.threshold:
                if not in_speech:
                    in_speech = True
                    print("🎤 Speech detected, recording…")
                silence_start = None
                frames.append(indata.copy())

            else:
                if in_speech:
                    # start silence timer
                    if silence_start is None:
                        silence_start = now
                    elif now - silence_start >= self.silence_duration:
                        print("🤫 Silence detected, stopping.")
                        stop_recording = True
                        raise sd.CallbackStop()
                    frames.append(indata.copy())

        # open stream, then spin until callback sets stop_recording
        with sd.InputStream(
            channels=1,
            samplerate=self.samplerate,
            dtype='float32',
            callback=callback
        ):
            while not stop_recording:
                time.sleep(0.05)

        if not frames:
            print("⚠️ No speech detected.")
            return ""

        # concatenate and write WAV
        audio = np.concatenate(frames, axis=0)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            wav.write(tmp.name, self.samplerate, audio)
            tmp_path = tmp.name

        try:
            print("⏳ Transcribing via Whisper…")
            with open(tmp_path, "rb") as f:
                resp = openai.Audio.transcriptions.create(
                    model=self.model,
                    file=f
                )
            text = resp.get("text", "").strip()
            print("📝 Transcription:", text)
            return text

        finally:
            try: os.remove(tmp_path)
            except: pass