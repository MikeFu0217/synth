#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import locale

# —— 强制在脚本里把 locale 设成 UTF-8 —— 
os.environ.setdefault('LC_ALL', 'en_US.UTF-8')
os.environ.setdefault('LANG',   'en_US.UTF-8')
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

# —— 强制 stdout/stderr 用 UTF-8 —— 
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
else:
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


import json
from pathlib import Path

import openai
import pyttsx3
import numpy as np
import sounddevice as sd

# —— 配置区（保持之前的简化版） —— 
API_KEY     = "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"
MODEL       = "gpt-4"
SAMPLE_RATE = 44100
OUTPUT_DIR  = Path("LLM_action/generated_sounds")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

client = openai.OpenAI(api_key=API_KEY)

tts = pyttsx3.init()
tts.setProperty('rate', 150)
voices = tts.getProperty('voices')
if len(voices) > 1:
    tts.setProperty('voice', voices[1].id)

SYSTEM_PROMPT = """\
You are an audio assistant. Based on the user request, generate a JSON object that defines a polyphonic Sound.
Each channel should contain waveform, envelope, filter, reverb, and volume.
Add a short English description in the top-level "description" field.
Add a top-level "playback_duration" field indicating how many seconds the sound should last.

Structure:
{
  "description": "short summary",
  "playback_duration": float,
  "channels": [ ... ]
}
Only output valid JSON. Do not add any explanation.
"""

USER_PROMPTS = [
    "Create a 2-second square wave at 330Hz with fast attack and strong reverb. It should feel punchy.",
    "Make a 3-second dreamy sine wave layered with a soft triangle wave. Both should be ambient.",
    # … 其余 prompts
]

def generate_wave(name, freq, frames):
    length = int(SAMPLE_RATE / freq)
    t = np.arange(length) / SAMPLE_RATE
    if name == 'saw':
        base = 2 * (t * freq - np.floor(t * freq + 0.5))
    elif name == 'sin':
        base = np.sin(2 * np.pi * freq * t)
    elif name == 'sqr':
        base = np.sign(np.sin(2 * np.pi * freq * t))
    else:
        base = np.zeros(length, dtype='float32')
    reps = int(np.ceil(frames / length))
    return np.tile(base.astype('float32'), reps)[:frames]

def process_prompt(idx, prompt):
    print(f"\n>>> Generating #{idx+1}: {prompt}")
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role":"system", "content":SYSTEM_PROMPT},
            {"role":"user",   "content":prompt}
        ]
    )
    data = json.loads(resp.choices[0].message.content)

    # TTS 播报
    desc = data.get("description", "")
    tts.say(desc)
    tts.runAndWait()

    # 合成器播放
    dur = data.get("playback_duration", 2.0)
    frames = int(SAMPLE_RATE * dur)
    sig = np.zeros(frames, dtype='float32')
    for ch in data["channels"]:
        w  = ch["waveform"]["name"][:3]  # saw/sin/sqr/tri
        fr = ch["waveform"]["frequency"]
        sig += generate_wave(w, fr, frames) * ch.get("volume", 1.0)
    sig = np.clip(sig, -1, 1)
    sd.play(sig, SAMPLE_RATE)
    sd.wait()

    # 保存 JSON
    out = OUTPUT_DIR / f"sound_{idx+1}.json"
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved → {out}")

if __name__ == "__main__":
    for i, p in enumerate(USER_PROMPTS):
        try:
            process_prompt(i, p)
        except Exception as e:
            print("Error:", e)