"""
智能家居指令识别测试程序主入口
"""
import sys
from model_handler import ModelHandler
from mqtt_client import MQTTClient
from conversation_manager import ConversationManager
from device_state import DeviceState
from context_manager import ContextManager


def main():
    """主程序入口"""
    print("=" * 60)
    print("智能家居指令识别测试程序")
    print("=" * 60)
    print("\n支持的指令类型：")
    print("  - 开关灯（开灯/关灯）")
    print("  - 开关空调（开空调/关空调）")
    print("  - 开关窗户（开窗/关窗）")
    print("  - 温度检测（查询温度/检测温度）")
    print("\n提示：输入 'quit' 或 'exit' 退出程序")
    print("=" * 60 + "\n")
    
    # 初始化对话管理、设备状态和语境管理
    conversation_manager = ConversationManager(max_history=10)
    device_state = DeviceState()
    context_manager = ContextManager(conversation_manager, device_state)
    
    # 初始化模型处理器（默认使用qwen2.5:7b，可根据实际情况修改）
    model_handler = ModelHandler(model_name="qwen2.5:7b")
    
    # 预热模型（首次调用可能需要加载时间）
    print("正在预热模型（首次加载可能需要一些时间）...")
    try:
        # 发送一个简单的测试请求来预热模型
        test_result = model_handler.recognize_command("测试")
        print("✓ 模型已准备就绪\n")
    except Exception as e:
        print(f"⚠ 模型预热失败，但可以继续使用: {e}\n")
    
    # 初始化MQTT客户端
    mqtt_client = MQTTClient()
    
    # 尝试连接MQTT（如果连接失败，程序仍可继续运行，只是无法发送消息）
    print("正在连接MQTT broker...")
    mqtt_available = mqtt_client.connect()
    if not mqtt_available:
        print("⚠ 警告: MQTT连接失败，消息将无法发送")
        print("   请确保MQTT broker正在运行，或先启动mqtt_simulator.py")
        print()
    
    try:
        while True:
            # 获取用户输入
            user_input = input("请输入指令: ").strip()
            
            # 检查退出命令
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("\n程序退出")
                break
            
            if not user_input:
                print("输入不能为空，请重新输入\n")
                continue
            
            # 添加用户消息到对话历史
            conversation_manager.add_message("user", user_input)
            
            # 处理代词指代（如"把它关了"）
            resolved_input = user_input
            resolved = context_manager.resolve_pronoun(user_input)
            if resolved:
                print(f"💡 识别到代词，已解析为: {resolved}")
                resolved_input = resolved
            
            # 获取对话历史和设备状态用于上下文
            conversation_history = conversation_manager.get_full_context()
            device_states = device_state.get_state_summary()
            
            # 使用模型识别指令（带上下文）
            print(f"\n正在识别指令: {resolved_input}")
            result = model_handler.recognize_command(resolved_input, conversation_history, device_states)
            
            # 检查是否有明确指令
            if result.get('type') != 'none':
                # 有明确指令，直接询问确认
                formatted_msg = model_handler.format_command_message(result)
                print(f"\n识别到指令: {formatted_msg}")
                print(f"详细信息: {result}")
                
                # 设置待确认指令
                context_manager.set_pending_confirmation(result)
                
                # 询问用户确认
                while True:
                    confirm = input("\n是否执行此指令？(y/n): ").strip().lower()
                    if confirm in ['y', 'yes', '是', '确认']:
                        # 发送MQTT消息
                        if mqtt_available:
                            success = mqtt_client.send_command(result)
                            if success:
                                # 更新设备状态
                                device_state.update_state(result)
                                # 添加系统响应到对话历史
                                response_text = f"已执行指令: {formatted_msg}"
                                conversation_manager.add_message("assistant", response_text, result)
                                print("✓ 指令已发送\n")
                            else:
                                print("✗ 指令发送失败\n")
                        else:
                            print("⚠ MQTT不可用，无法发送指令\n")
                        # 清除待确认指令
                        context_manager.set_pending_confirmation(None)
                        break
                    elif confirm in ['n', 'no', '否', '取消']:
                        print("已取消执行\n")
                        # 清除待确认指令
                        context_manager.set_pending_confirmation(None)
                        break
                    else:
                        print("请输入 y 或 n")
            
            # 检查是否有潜在指令
            elif result.get('potential') and len(result.get('potential', [])) > 0:
                # 有潜在指令，LLM主动询问用户
                potential_commands = result.get('potential', [])
                
                # 生成询问文本
                print(f"\n💡 检测到潜在意图")
                question = model_handler.generate_question(user_input, potential_commands)
                print(f"{question}")
                
                # 添加系统询问到对话历史
                conversation_manager.add_message("assistant", question)
                
                # 等待用户自然语言回答
                user_response = input("您的回答: ").strip()
                
                if not user_response:
                    print("已取消\n")
                    continue
                
                # 添加用户回答到对话历史
                conversation_manager.add_message("user", user_response)
                
                # 处理代词指代
                resolved_response = user_response
                resolved = context_manager.resolve_pronoun(user_response)
                if resolved:
                    print(f"💡 识别到代词，已解析为: {resolved}")
                    resolved_response = resolved
                
                # 获取更新的对话历史
                conversation_history = conversation_manager.get_full_context()
                
                # 解析用户回答，识别要执行的指令（带上下文）
                print(f"\n正在解析您的回答...")
                selected_commands = model_handler.parse_user_response(resolved_response, potential_commands, conversation_history)
                
                if selected_commands is None:
                    print("⚠ 无法识别您的意图")
                    print("💡 提示：请明确说明您想要执行的操作，例如：")
                    for idx, cmd in enumerate(potential_commands, 1):
                        suggestion = cmd.get('suggestion', '')
                        if suggestion:
                            print(f"   - {suggestion.replace('您是想', '').replace('吗？', '').replace('还是想', '').strip()}")
                    print("   或者直接说：开空调、检测温度、开窗等\n")
                    continue
                
                # 处理单个或多个指令
                if isinstance(selected_commands, list):
                    # 多个指令
                    print(f"\n✓ 识别到 {len(selected_commands)} 个指令：")
                    for cmd in selected_commands:
                        formatted_msg = model_handler.format_command_message(cmd)
                        print(f"   - {formatted_msg}")
                    
                    # 依次发送所有指令
                    if mqtt_available:
                        success_count = 0
                        response_texts = []
                        for cmd in selected_commands:
                            if mqtt_client.send_command(cmd):
                                # 更新设备状态
                                device_state.update_state(cmd)
                                success_count += 1
                                formatted = model_handler.format_command_message(cmd)
                                response_texts.append(formatted)
                        if success_count == len(selected_commands):
                            # 添加系统响应到对话历史
                            response_text = f"已执行 {len(selected_commands)} 个指令: {', '.join(response_texts)}"
                            for cmd in selected_commands:
                                conversation_manager.add_message("assistant", response_text, cmd)
                            print(f"\n✓ 所有指令已发送 ({success_count}/{len(selected_commands)})\n")
                        else:
                            print(f"\n⚠ 部分指令发送失败 ({success_count}/{len(selected_commands)})\n")
                    else:
                        print("⚠ MQTT不可用，无法发送指令\n")
                else:
                    # 单个指令
                    formatted_msg = model_handler.format_command_message(selected_commands)
                    print(f"\n✓ 识别到指令: {formatted_msg}")
                    
                    # 直接发送MQTT消息（不再确认）
                    if mqtt_available:
                        success = mqtt_client.send_command(selected_commands)
                        if success:
                            # 更新设备状态
                            device_state.update_state(selected_commands)
                            # 添加系统响应到对话历史
                            response_text = f"已执行指令: {formatted_msg}"
                            conversation_manager.add_message("assistant", response_text, selected_commands)
                            print("✓ 指令已发送\n")
                        else:
                            print("✗ 指令发送失败\n")
                    else:
                        print("⚠ MQTT不可用，无法发送指令\n")
            
            else:
                # 完全没有相关指令
                print("✓ 未识别到智能家居相关指令\n")
                # 仍然记录对话
                conversation_manager.add_message("assistant", "未识别到智能家居相关指令")
            
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n程序出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 断开MQTT连接
        if mqtt_available:
            mqtt_client.disconnect()


if __name__ == "__main__":
    main()
