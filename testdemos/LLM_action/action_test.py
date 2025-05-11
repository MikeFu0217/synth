import openai
import json
import pyttsx3
from pathlib import Path
from channel import Channel, Waveform, Envelope, Filter, Reverb
from sound import Sound

# ✅ 设置 OpenAI API Key
client = openai.OpenAI(api_key="")

# 创建保存目录
output_dir = Path("generated_sounds")
output_dir.mkdir(exist_ok=True)

# 五个 prompt
user_prompts = [
    "Create a square wave at 330Hz with fast attack and strong reverb. It should feel punchy.",
    "Make a dreamy sine wave layered with a soft triangle wave. Both should be ambient.",
    "Generate a saw wave at 440Hz and a square wave at 220Hz, with the saw wave louder.",
    "Compose a rich sound with three layers: sine, square, and saw. Each should have distinct filter settings.",
    "Create an energetic loop with two square waves at 330Hz and 660Hz. Use quick envelopes and echo."
]

# 系统提示词
system_prompt = """
You are an audio assistant. Based on the user request, generate a JSON object that defines a polyphonic Sound.
Each channel should contain waveform, envelope, filter, reverb, and volume.
Add a short English description in the top-level "description" field.

Structure:
{
  "description": "short summary of the generated sound",
  "channels": [
    {
      "waveform": {
        "name": "saw | sine | square | triangle",
        "frequency": float,
        "duration": float,
        "sample_rate": 44100
      },
      "envelope": {
        "attack_time": float,
        "decay_time": float,
        "sustain_level": float,
        "release_time": float
      },
      "filter": {
        "low": float,
        "mid": float,
        "high": float
      },
      "reverb": {
        "decay": float,
        "delay": float,
        "reflections": int
      },
      "volume": float
    }
  ]
}
Only output valid JSON. Do not add any explanation.
"""

# 初始化语音引擎
tts = pyttsx3.init()
# 选用更有表现力的声音（可改 index）
voices = tts.getProperty('voices')
if len(voices) > 1:
    tts.setProperty('voice', voices[1].id)  # 尝试 Zira（更灵动）

# 主循环：生成、播报、播放、保存
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
        print("📣 DJ says:", description)
        tts.say("Yo! Here's what I cooked up. " + description)
        tts.runAndWait()

        # 🎶 构建并播放声音
        sound = Sound(sample_rate=44100)
        for ch in result["channels"]:
            wf = Waveform(**ch["waveform"])
            env = Envelope(**ch["envelope"])
            flt = Filter(**ch["filter"])
            rev = Reverb(**ch["reverb"])
            vol = ch.get("volume", 1.0)

            channel = Channel(duration=wf.duration, sample_rate=wf.sample_rate)
            channel.set_waveform(wf)
            channel.add_envelope(env)
            channel.add_filter(flt)
            channel.add_reverb(rev)
            sound.add_channel(channel, volume=vol)

        print("🎧 Playing sound...")
        sound.play()
        print("✅ Done.")

        # 💾 保存 JSON
        file_path = output_dir / f"sound_{i+1}.json"
        with open(file_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"💾 Saved JSON to {file_path}")

    except Exception as e:
        print(f"❌ Failed on prompt {i+1}: {e}")
