import openai
import json
from channel import Channel, Waveform, Envelope, Filter, Reverb

# ✅ 设置你的 OpenAI API Key
client = openai.OpenAI(api_key="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")

# 🎤 用户输入控制描述
user_prompt = """
Use a square wave at 330 Hz for 2 seconds. Make the attack fast, sustain high, and reverb echo strong.
"""

# 🎯 引导系统生成合法结构的 JSON
system_prompt = """
You are an audio assistant helping configure a synthesizer. Based on user description, generate parameters for the following 4 classes in JSON format.
Make sure:
- filter values (low, mid, high) are float gains between 0.0 and 2.0
- reverb.delay is around 0.1–0.3 seconds, and reflections under 10

Output ONLY valid JSON:
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
  }
}
"""

# 💬 调用 GPT
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
)

# 📤 提取 JSON 内容
try:
    config = json.loads(response.choices[0].message.content)
    print("✅ 参数解析成功：\n", json.dumps(config, indent=2))

    # 🎶 构建对象
    waveform = Waveform(**config["waveform"])
    envelope = Envelope(**config["envelope"])
    filter_obj = Filter(**config["filter"])
    reverb = Reverb(**config["reverb"])

    # 🎛 应用到 Channel
    channel = Channel(duration=config["waveform"]["duration"], sample_rate=44100)
    channel.set_waveform(waveform)
    channel.add_envelope(envelope)
    channel.add_filter(filter_obj)
    channel.add_reverb(reverb)

    print("🎧 播放中...")
    channel.play()
    print("✅ 播放完成。")

except Exception as e:
    print("❌ JSON parse error:", e)
    print("Raw content:")
    print(response.choices[0].message.content)
