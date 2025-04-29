import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import tempfile
import openai
import json
import os
import time
import pyttsx3

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

class SpeechToText:
    def __init__(self, api_key, device_keyword="USB PnP Sound Device", samplerate=44100, duration=5):
        self.api_key = api_key
        self.device_keyword = device_keyword.lower()
        self.samplerate = samplerate
        self.duration = duration
        self.client = openai.OpenAI(api_key=self.api_key)
        self._select_input_device()

    def _select_input_device(self):
        device_found = False
        for idx, dev in enumerate(sd.query_devices()):
            if self.device_keyword in dev['name'].lower() and dev['max_input_channels'] > 0:
                print(f"✅ Using microphone: {dev['name']} (index {idx})")
                sd.default.device = (idx, None)
                device_found = True
                break
        if not device_found:
            raise RuntimeError("❌ No matching microphone device found.")

    def record_and_transcribe(self):
        print("🎤 Recording... please speak now.")
        recording = sd.rec(int(self.duration * self.samplerate),
                           samplerate=self.samplerate,
                           channels=1,
                           dtype='int16')
        sd.wait()

        with tempfile.NamedTemporaryFile(suffix=".wav") as f:
            wav.write(f.name, self.samplerate, recording)
            with open(f.name, "rb") as audio_file:
                print("📤 Sending audio to Whisper API...")
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
                text = transcript.text.strip()
                print("📝 Transcription:", text)
                return text

class TextToSpeech:
    def __init__(self):
        self.engine = pyttsx3.init()
        # optionally adjust voice properties:
        # self.engine.setProperty('rate', 150)
        # self.engine.setProperty('volume', 1.0)

    def speak(self, text):
        self.engine.say(text)
        self.engine.runAndWait()

# ------------ Main Logic ------------

def main():
    api_key_path = ".openai_api_key"
    llm = LLMClient(api_key_path=api_key_path)
    with open(api_key_path) as f:
        api_key = f.read().strip()
    stt = SpeechToText(api_key=api_key)
    tts = TextToSpeech()

    tts.speak("Hello! Please describe the sound you would like to create.")

    while True:
        user_prompt = stt.record_and_transcribe()
        if not user_prompt:
            tts.speak("I did not catch that. Please try speaking again.")
            continue

        tts.speak("Got it. Generating your sound preset. Please wait.")
        response = llm.gen_resp(user_prompt)

        tts.speak("Here is what I created for you.")
        tts.speak(response["description"])

        tts.speak("Would you like to modify it? Please say yes or no.")
        user_reply = stt.record_and_transcribe().lower()

        if "no" in user_reply or user_reply.strip() == "":
            filename = f"llmgen_preset.json"
            with open(filename, "w") as f:
                json.dump(response, f, indent=2)
            tts.speak("Your preset has been saved. Thank you!")
            print(f"✅ Preset saved as {filename}")
            break
        else:
            tts.speak("Okay, let's try again. Please describe your sound.")

if __name__ == "__main__":
    main()