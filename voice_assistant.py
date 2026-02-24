"""
无唤醒词智能语音助手主程序
集成语音识别、意图理解、语音合成和设备控制
"""
import sys
import time
import traceback
import threading
import queue
from audio_interface import AudioInterface
from speech_handler import SpeechHandler
from model_handler import ModelHandler
from mqtt_client import MQTTClient
from conversation_manager import ConversationManager
from device_state import DeviceState
from context_manager import ContextManager

# 全局队列，用于存储捕获的音频片段
audio_queue = queue.Queue()

def listen_worker(audio_interface):
    """
    监听线程工作函数：持续监听并将音频放入队列
    """
    try:
        print("[*] 监听线程已启动")
        for audio_data in audio_interface.listen_for_speech():
            audio_queue.put(audio_data)
    except Exception as e:
        print(f"[!] 监听线程错误: {e}")

def main():
    print("=" * 60)
    print("智能语音助手 (全双工版)")
    print("=" * 60)
    print("初始化系统模块...")

    # 1. 初始化模块
    try:
        # 语音接口
        audio = AudioInterface(energy_threshold=30, silence_limit=1.0)
        
        # 语音处理 (STT/TTS)
        speech = SpeechHandler()
        
        # 对话管理
        conversation_manager = ConversationManager(max_history=10)
        
        # 设备状态
        device_state = DeviceState()
        
        # 上下文管理
        context_manager = ContextManager(conversation_manager, device_state)
        
        # 模型处理 (LLM)
        model = ModelHandler(model_name="qwen2.5:7b")
        
        # MQTT 客户端
        mqtt = MQTTClient()
        mqtt_available = mqtt.connect()
        if not mqtt_available:
            print("⚠ MQTT 连接失败，将无法控制设备")
            
    except Exception as e:
        print(f"系统初始化失败: {e}")
        traceback.print_exc()
        return

    print("\n✓ 系统初始化完成")
    print("正在启动监听... (请说话)")
    print("-" * 60)

    # 启动音频流
    audio.start_stream()
    
    # 启动监听线程
    listener_thread = threading.Thread(target=listen_worker, args=(audio,), daemon=True)
    listener_thread.start()
    
    # 活跃状态管理
    last_interaction_time = 0
    ACTIVE_WINDOW = 30 # 30秒内处于活跃状态，更容易触发
    
    try:
        # 主循环：处理队列中的音频
        while True:
            # 从队列获取音频数据（阻塞等待）
            try:
                # 设置超时，以便能够响应KeyboardInterrupt
                audio_data = audio_queue.get(timeout=1.0)
            except queue.Empty:
                continue
                
            # 1. 语音转文字
            print(">>> 正在识别...")
            text = speech.speech_to_text(audio_data)
            
            if not text or len(text.strip()) == 0:
                print("--- (未识别到有效语音)")
                continue
                
            print(f"用户说: {text}")
            
            # 2. 上下文增强与意图分析
            # 处理代词
            resolved_text = text
            resolved = context_manager.resolve_pronoun(text)
            if resolved:
                print(f"💡 指代消解: {text} -> {resolved}")
                resolved_text = resolved
            
            # 获取上下文
            context = conversation_manager.get_full_context()
            
            # 如果处于活跃窗口，提示模型更倾向于认为是对话
            is_active = (time.time() - last_interaction_time) < ACTIVE_WINDOW
            if is_active:
                print("[*] 处于活跃交互模式")
            
            print(">>> 分析意图(含纠错)...")
            # 使用解析后的文本进行意图分析
            analysis = model.analyze_intent(resolved_text, context)
            intent = analysis.get("intent", "ignore")
            corrected_text = analysis.get("corrected_text", resolved_text)
            
            # 如果发生了纠错
            if corrected_text != resolved_text:
                 print(f"💡 LLM纠错: {resolved_text} -> {corrected_text}")
                 resolved_text = corrected_text
            
            print(f"意图判别: {intent} (理由: {analysis.get('reason', '无')})")
            
            # 3. 根据意图处理
            response_text = ""
            should_reply = False
            
            if intent == "ignore":
                # 如果非常活跃且文本较长，可能误判，或者是闲聊
                if is_active and len(text) > 3:
                     # 二次确认，或者直接当做chat
                     # 此时我们可以假设是Chat，因为处于活跃对话中
                     intent = "chat"
                     print(">>> 活跃模式下忽略判断修正为 Chat")
                else:
                    print("--- 忽略此消息")
                    continue
            
            if intent == "command":
                # 处理指令
                print(">>> 识别指令详情...")
                # 结合设备状态
                states = device_state.get_state_summary()
                # 使用解析后的文本
                cmd_result = model.recognize_command(resolved_text, context, states)
                
                if cmd_result.get("type") != "none":
                    formatted_cmd = model.format_command_message(cmd_result)
                    print(f"执行指令: {formatted_cmd}")
                    
                    if mqtt_available:
                        success = mqtt.send_command(cmd_result)
                        if success:
                            device_state.update_state(cmd_result)
                            response_text = f"好的，{formatted_cmd}"
                        else:
                            response_text = f"抱歉，{formatted_cmd}失败了"
                    else:
                        response_text = f"我明白了，{formatted_cmd}，但是MQTT未连接。"
                    
                    should_reply = True
                    # 记录指令到历史
                    conversation_manager.add_message("user", resolved_text)
                    conversation_manager.add_message("assistant", response_text, cmd_result)
                else:
                    response_text = "抱歉，我没听懂具体的指令。"
                    should_reply = True
            
            elif intent == "chat":
                # 处理闲聊
                print(">>> 生成回复...")
                conversation_manager.add_message("user", resolved_text)
                response_text = model.generate_chat_response(resolved_text, context)
                conversation_manager.add_message("assistant", response_text)
                print(f"助手说: {response_text}")
                should_reply = True

            # 4. 语音回复
            if should_reply and response_text:
                # 更新活跃时间
                last_interaction_time = time.time()
                
                print(f">>> 正在播报: {response_text}")
                
                # 暂停监听（防止听到自己）
                audio.pause()
                
                tts_file = speech.text_to_speech(response_text)
                if tts_file:
                    speech.play_audio_file(tts_file)
                    try:
                        import os
                        os.remove(tts_file)
                    except:
                        pass
                
                # 恢复监听
                audio.resume()
                print(">>> 恢复监听")


    except KeyboardInterrupt:
        print("\n停止监听")
    except Exception as e:
        print(f"发生错误: {e}")
        traceback.print_exc()
    finally:
        audio.close()
        if mqtt_available:
            mqtt.disconnect()

if __name__ == "__main__":
    main()
