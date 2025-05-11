import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import tempfile
import openai

# ✅ 初始化 OpenAI 客户端（适用于 openai>=1.0.0）
client = openai.OpenAI(api_key="")
# 🎯 通过设备名称自动选择麦克风（不再硬编码 index）
target_name = "USB PnP Sound Device"
device_found = False
for idx, dev in enumerate(sd.query_devices()):
    if target_name.lower() in dev['name'].lower() and dev['max_input_channels'] > 0:
        print(f"✅ 使用麦克风: {dev['name']} (index {idx})")
        sd.default.device = (idx, None)  # 设置为默认输入设备
        device_found = True
        break

if not device_found:
    raise RuntimeError("❌ 没有找到匹配的麦克风设备，请检查设备名称或连接状态")

# 📦 参数设置
samplerate = 44100  # 你麦克风支持的采样率
channels = 1
duration = 5  # 每次录音 5 秒

while True:
    print("🎤 正在录音... 说话中")
    recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=channels, dtype='int16')
    sd.wait()

    with tempfile.NamedTemporaryFile(suffix=".wav") as f:
        wav.write(f.name, samplerate, recording)

        print("📤 正在上传音频到 OpenAI Whisper API ...")
        with open(f.name, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            print("📝 识别结果：", transcript.text)
        print("-" * 50)
