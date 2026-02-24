"""
语音处理模块
负责语音识别 (STT) 和 语音合成 (TTS)
"""
import os
import asyncio
import edge_tts
from funasr import AutoModel
from pydub import AudioSegment
import io
import wave
import sys
import contextlib

# 抑制 FunASR 的部分日志
os.environ["MODELSCOPE_LOG_LEVEL"] = "ERROR"

class SpeechHandler:
    def __init__(self, model_name: str = "paraformer-zh", tts_voice: str = "zh-CN-XiaoxiaoNeural"):
        self.model_name = model_name
        self.tts_voice = tts_voice
        self.asr_model = None
        
        print(f"[*] 正在加载语音识别模型: {model_name} ...")
        try:
            # 捕获标准输出以隐藏部分加载日志
            # with contextlib.redirect_stdout(io.StringIO()):
            # 定义热词：增强对智能家居指令的识别敏感度
            hotwords = "打开空调 关闭空调 开灯 关灯 检测温度 查询温度 多少度 你好 小爱 窗户 关窗 开窗"
            
            self.asr_model = AutoModel(model=model_name, 
                                     model_revision="v2.0.4",
                                     vad_model="fsmn-vad",
                                     vad_model_revision="v2.0.4",
                                     punc_model="ct-punc-c", 
                                     punc_model_revision="v2.0.4",
                                     disable_update=True,
                                     hotword=hotwords) # 注入热词
            print("[✓] 语音模型加载完成")
        except Exception as e:
            print(f"[!] 语音模型加载失败: {e}")
            print("请确保已安装 funasr, modelscope, torch 等依赖")

    def speech_to_text(self, audio_data: bytes) -> str:
        """
        将音频数据转换为文本
        Args:
            audio_data: 原始 PCM 音频数据 (16k, 16bit, mono)
        Returns:
            识别出的文本
        """
        if not self.asr_model:
            return ""
        
        try:
            # FunASR 接受音频路径或 numpy array 或 bytes
            # 这里我们先保存为临时wav文件传入，或者直接传bytes如果支持
            # AutoModel通常支持 input=audio_bytes
            
            # 为了稳健性，保存为临时文件
            temp_wav = "temp_speech.wav"
            with wave.open(temp_wav, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2) # 16 bit
                wf.setframerate(16000)
                wf.writeframes(audio_data)
            
            res = self.asr_model.generate(input=temp_wav, batch_size_s=300)
            
            # 清理
            if os.path.exists(temp_wav):
                os.remove(temp_wav)
                
            # res 格式通常为List[Dict]
            if res and isinstance(res, list):
                text = res[0].get("text", "")
                return text
            return ""
            
        except Exception as e:
            print(f"[!] 语音识别错误: {e}")
            return ""

    async def _text_to_speech_async(self, text: str, output_file: str):
        """异步 TTS 生成"""
        communicate = edge_tts.Communicate(text, self.tts_voice)
        await communicate.save(output_file)

    def text_to_speech(self, text: str, output_file: str = "response.mp3"):
        """
        文本转语音
        Args:
            text: 要朗读的文本
            output_file: 输出文件名
        """
        try:
            asyncio.run(self._text_to_speech_async(text, output_file))
            return output_file
        except Exception as e:
            print(f"[!] TTS 生成错误: {e}")
            return None

    def play_audio_file(self, file_path: str):
        """
        播放音频文件 (支持 mp3/wav)
        需要 ffmpeg 支持
        """
        try:
            if not os.path.exists(file_path):
                return
            
            # 使用 pydub 加载
            if file_path.endswith(".mp3"):
                audio = AudioSegment.from_mp3(file_path)
            elif file_path.endswith(".wav"):
                audio = AudioSegment.from_wav(file_path)
            else:
                print(f"[!] 不支持的音频格式: {file_path}")
                return
                
            # 播放 (使用 simpleaudio 或 pyaudio)
            # 这里我们手动通过 pyaudio 播放以获得更好的控制
            import pyaudio
            
            p = pyaudio.PyAudio()
            
            # 转换为 raw data
            # 确保是 16bit, 16k/24k/44.1k
            # 统一转换为 16k mono 以便统一处理? 不，播放可以随意
            
            stream = p.open(format=p.get_format_from_width(audio.sample_width),
                            channels=audio.channels,
                            rate=audio.frame_rate,
                            output=True)
            
            # 分块播放
            chunk_length = 1024
            raw_data = audio.raw_data
            
            for i in range(0, len(raw_data), chunk_length):
                stream.write(raw_data[i:i+chunk_length])
                
            stream.stop_stream()
            stream.close()
            p.terminate()
            
        except Exception as e:
            print(f"[!] 播放音频失败: {e}")
            print("提示: 请确保已安装 ffmpeg (conda install ffmpeg)")

if __name__ == "__main__":
    # 测试代码
    handler = SpeechHandler()
    
    # 测试 TTS
    print("测试 TTS...")
    handler.text_to_speech("你好，我是你的智能助手。")
    handler.play_audio_file("response.mp3")
    
    # 清理
    if os.path.exists("response.mp3"):
        os.remove("response.mp3")
