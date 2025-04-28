import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import openai
import json
import pyttsx3
from pathlib import Path
from channel import Channel, Waveform, Envelope, Filter, Reverb
import sounddevice as sd
import numpy as np

# ✅ 设置 OpenAI API Key
client = openai.OpenAI(api_key="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")

# 创建保存目录
output_dir = Path("LLM_action/generated_sounds")
output_dir.mkdir(exist_ok=True)

# 五个 prompt
user_prompts = [
    "Create a 2-second square wave at 330Hz with fast attack and strong reverb. It should feel punchy.",
    "Make a 3-second dreamy sine wave layered with a soft triangle wave. Both should be ambient.",
    "Generate a 1.5-second saw wave at 440Hz and a square wave at 220Hz, with the saw wave louder.",
    "Compose a 4-second rich sound with three layers: sine, square, and saw. Each should have distinct filter settings.",
    "Create a 2.5-second energetic loop with two square waves at 330Hz and 660Hz. Use quick envelopes and echo."
]

# 系统提示词
system_prompt = """
You are an audio assistant. Based on the user request, generate a JSON object that defines a polyphonic Sound.
Each channel should contain waveform, envelope, filter, reverb, and volume.
Add a short English description in the top-level "description" field.
Add a top-level "playback_duration" field indicating how many seconds the sound should last.

Structure:
{
  "description": "short summary of the generated sound",
  "playback_duration": float,
  "channels": [
    {
      "waveform": { "name": "saw | sine | square | triangle", "frequency": float, "duration": float, "sample_rate": 44100 },
      "envelope": { "attack_time": float, "decay_time": float, "sustain_level": float, "release_time": float },
      "filter": { "low": float, "mid": float, "high": float },
      "reverb": { "decay": float, "delay": float, "reflections": int },
      "volume": float
    }
  ]
}
Only output valid JSON. Do not add any explanation.
"""

# 初始化语音播报
tts = pyttsx3.init()
voices = tts.getProperty('voices')
if len(voices) > 1:
    tts.setProperty('voice', voices[1].id)

# 主循环
for i, prompt in enumerate(user_prompts):
    try:
        print(f"\n🎤 Generating sound for prompt {i+1}...")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        content = response.choices[0].message.content
        result = json.loads(content)

        # 🔊 语音播报
        description = result.get("description", "Here is your generated sound.")
        print("🔣 DJ says:", description)
        tts.say("Yo! Here's what I cooked up. " + description)
        tts.runAndWait()

        # 🎶 直接生成numpy数组
        playback_duration = result.get("playback_duration", 2.0)  # 默认2秒
        frames = int(44100 * playback_duration)
        final_signal = np.zeros(frames, dtype=np.float32)

        for ch in result["channels"]:
            waveform_name = ch["waveform"]["name"]
            if waveform_name == "square":
                waveform_name = "sqr"
            if waveform_name == "sine":
                waveform_name = "sin"

            # 生成波形
            sr = ch["waveform"]["sample_rate"]
            freq = ch["waveform"]["frequency"]
            length = int(sr / freq)
            t = np.arange(length) / sr
            if waveform_name == 'saw':
                wave = (2 * (t * freq - np.floor(t * freq + 0.5))).astype('float32')
            elif waveform_name == 'sin':
                wave = np.sin(2 * np.pi * freq * t).astype('float32')
            elif waveform_name == 'sqr':
                wave = np.sign(np.sin(2 * np.pi * freq * t)).astype('float32')
            else:
                wave = np.zeros(length, dtype='float32')

            # 重复到frames大小
            repeats = int(np.ceil(frames / length))
            full_wave = np.tile(wave, repeats)[:frames]

            final_signal += full_wave * ch.get("volume", 1.0)

        final_signal = np.clip(final_signal, -1, 1)
        print("🎧 Playing generated numpy array...")
        sd.play(final_signal, samplerate=44100)
        sd.wait()

        print("✅ Done.")

        # 💾 保存 JSON
        file_path = output_dir / f"sound_{i+1}.json"
        with open(file_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"💾 Saved JSON to {file_path}")

    except Exception as e:
        print(f"❌ Failed on prompt {i+1}: {e}")
