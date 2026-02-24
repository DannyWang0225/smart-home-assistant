"""
音频接口模块
负责麦克风录音和简单的能量门控（Energy-based VAD）
"""
import pyaudio
import numpy as np
import time
import math
from typing import Generator, Optional
import wave
import os

class AudioInterface:
    def __init__(self, 
                 rate: int = 16000, 
                 chunk: int = 1024, 
                 channels: int = 1,
                 energy_threshold: int = 1000,  # 能量阈值，根据麦克风调整
                 silence_limit: float = 0.8):   # 静音多少秒后认为说话结束 (调小一点以加快响应，但不能太小)
        self.rate = rate
        self.chunk = chunk
        self.channels = channels
        self.format = pyaudio.paInt16
        self.energy_threshold = energy_threshold
        self.silence_limit = silence_limit
        self.p = pyaudio.PyAudio()
        self.stream = None
        self._paused = False

    def pause(self):
        """暂停监听（但不关闭流，仅丢弃数据）"""
        self._paused = True

    def resume(self):
        """恢复监听"""
        self._paused = False

    def start_stream(self):
        """启动音频流"""
        if self.stream is None:
            self.stream = self.p.open(format=self.format,
                                      channels=self.channels,
                                      rate=self.rate,
                                      input=True,
                                      frames_per_buffer=self.chunk)
        self._paused = False
        return self

    def stop_stream(self):
        """停止音频流"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

    def close(self):
        """关闭PyAudio"""
        self.stop_stream()
        self.p.terminate()

    def _calculate_energy(self, data) -> float:
        """计算音频块的能量 (RMS)"""
        # 将字节转换为numpy数组
        audio_data = np.frombuffer(data, dtype=np.int16)
        if len(audio_data) == 0:
            return 0
        # 计算RMS
        mean_sq = np.mean(audio_data**2)
        if mean_sq < 0 or np.isnan(mean_sq):
            return 0
        rms = np.sqrt(mean_sq)
        return rms

    def listen_for_speech(self) -> Generator[bytes, None, None]:
        """
        监听并返回语音片段
        逻辑：
        1. 等待能量超过阈值（开始说话）
        2. 持续录制
        3. 当能量低于阈值持续 silence_limit 秒（说话结束）
        4. yield 完整的音频数据
        """
        print(f"[*] 正在监听... (阈值: {self.energy_threshold})")
        
        frames = []
        silence_start = None
        is_speaking = False
        
        while True:
            try:
                data = self.stream.read(self.chunk, exception_on_overflow=False)
                
                # 如果处于暂停状态，直接丢弃数据并继续
                if self._paused:
                    # 如果之前正在说话，强制结束
                    if is_speaking:
                         is_speaking = False
                         frames = []
                         silence_start = None
                         print("[*] 系统发声中，中断当前录音")
                    continue

                energy = self._calculate_energy(data)
                
                if not is_speaking:
                    # 等待说话开始
                    if energy > self.energy_threshold:
                        print("[!] 检测到语音，开始录制...")
                        is_speaking = True
                        frames = [data] # 保留这一帧
                        silence_start = None
                    else:
                        # 可以在这里保存一点预缓冲，避免切掉开头的音
                        pass
                else:
                    # 正在录制
                    frames.append(data)
                    
                    if energy > self.energy_threshold:
                        silence_start = None # 重置静音计时
                    else:
                        if silence_start is None:
                            silence_start = time.time()
                        elif time.time() - silence_start > self.silence_limit:
                            # 静音超时，认为说话结束
                            print(f"[*] 语音结束，捕获 {len(frames)} 帧")
                            full_audio = b''.join(frames)
                            yield full_audio
                            
                            # 重置状态
                            frames = []
                            is_speaking = False
                            silence_start = None
                            print("[*] 继续监听...")
            except IOError as e:
                print(f"[!] 录音错误: {e}")
                continue
            except KeyboardInterrupt:
                break

    def play_audio(self, file_path: str):
        """播放音频文件"""
        wf = wave.open(file_path, 'rb')
        
        stream = self.p.open(format=self.p.get_format_from_width(wf.getsampwidth()),
                             channels=wf.getnchannels(),
                             rate=wf.getframerate(),
                             output=True)
        
        data = wf.readframes(self.chunk)
        
        while data:
            stream.write(data)
            data = wf.readframes(self.chunk)
            
        stream.stop_stream()
        stream.close()
        wf.close()

if __name__ == "__main__":
    # 测试代码
    audio = AudioInterface()
    try:
        audio.start_stream()
        for speech_audio in audio.listen_for_speech():
            print(f"收到语音片段，大小: {len(speech_audio)} bytes")
            # 这里可以保存为wav测试
            with wave.open("test_capture.wav", "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(audio.p.get_sample_size(pyaudio.paInt16))
                wf.setframerate(16000)
                wf.writeframes(speech_audio)
            print("已保存到 test_capture.wav")
            break
    except KeyboardInterrupt:
        pass
    finally:
        audio.close()
