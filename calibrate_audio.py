"""
麦克风能量校准工具
用于检测环境噪音水平，帮助设置合理的 energy_threshold
"""
import pyaudio
import numpy as np
import time

def calibrate():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    
    p = pyaudio.PyAudio()
    
    try:
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)
        
        print("="*60)
        print("正在检测环境音量... (按 Ctrl+C 停止)")
        print("请保持安静查看'底噪'，然后尝试说话查看'语音能量'")
        print("="*60)
        
        max_energy = 0
        min_energy = 999999
        
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16)
            
            # 计算能量 (RMS)
            # 防止空数据或全0导致的计算错误
            if len(audio_data) == 0:
                continue
                
            mean_sq = np.mean(audio_data**2)
            if mean_sq < 0 or np.isnan(mean_sq):
                energy = 0
            else:
                energy = int(np.sqrt(mean_sq))
            
            max_energy = max(max_energy, energy)
            min_energy = min(min_energy, energy)
            
            # 简单的可视化条
            bar_len = int(energy / 100)
            bar = "#" * min(bar_len, 50)
            
            print(f"\r当前能量: {energy:5d} | Min: {min_energy:5d} | Max: {max_energy:5d} | {bar}", end="")
            
    except KeyboardInterrupt:
        print("\n\n" + "="*60)
        print("检测结束")
        print(f"建议设置:")
        print(f"环境底噪 (Min): {min_energy}")
        print(f"说话峰值 (Max): {max_energy}")
        recommended = max(min_energy * 2, 500) # 至少500，或者底噪的2倍
        if recommended > max_energy * 0.8:
             recommended = int(max_energy * 0.5)
        
        print(f"推荐阈值 (energy_threshold): {recommended}")
        print("="*60)
        
    except Exception as e:
        print(f"\n错误: {e}")
    finally:
        if 'stream' in locals():
            stream.stop_stream()
            stream.close()
        p.terminate()

if __name__ == "__main__":
    calibrate()
