"""
语境管理模块
管理对话上下文和代词指代解析
"""
from typing import List, Dict, Optional
from conversation_manager import ConversationManager
from device_state import DeviceState


class ContextManager:
    """管理对话语境和上下文"""
    
    def __init__(self, conversation_manager: ConversationManager, device_state: DeviceState):
        """
        初始化语境管理器
        
        Args:
            conversation_manager: 对话管理器实例
            device_state: 设备状态实例
        """
        self.conversation_manager = conversation_manager
        self.device_state = device_state
        self.pending_confirmation: Optional[Dict] = None
    
    def resolve_pronoun(self, text: str) -> Optional[str]:
        """
        解析代词指代，将代词替换为具体设备
        
        Args:
            text: 包含代词的文本（如"把它关了"）
            
        Returns:
            替换后的文本（如"把灯关了"），如果无法解析返回None
        """
        # 代词关键词
        pronouns = ["它", "那个", "这个", "上面", "刚才", "之前", "刚才那个"]
        
        # 检查是否包含代词
        contains_pronoun = any(pronoun in text for pronoun in pronouns)
        
        if not contains_pronoun:
            return None
        
        # 从对话历史中查找最近提到的设备
        last_device = self.conversation_manager.get_last_device_mentioned()
        if last_device:
            device_names = {
                "light": "灯",
                "ac": "空调",
                "window": "窗户",
                "temperature": "温度"
            }
            device_name = device_names.get(last_device, last_device)
            
            # 替换代词
            for pronoun in pronouns:
                if pronoun in text:
                    # 根据上下文替换
                    if pronoun == "它":
                        text = text.replace("它", device_name)
                    elif pronoun in ["那个", "这个", "刚才那个"]:
                        text = text.replace(pronoun, device_name)
                    elif pronoun in ["上面", "刚才", "之前"]:
                        text = text.replace(pronoun, f"{device_name}的{pronoun}")
                    return text
        
        # 如果对话历史中没有，从设备状态中查找最近操作的设备
        recent_device = self.device_state.get_recently_operated_device()
        if recent_device:
            device_names = {
                "light": "灯",
                "ac": "空调",
                "window": "窗户",
                "temperature": "温度"
            }
            device_name = device_names.get(recent_device, recent_device)
            
            for pronoun in pronouns:
                if pronoun in text:
                    if pronoun == "它":
                        text = text.replace("它", device_name)
                    elif pronoun in ["那个", "这个", "刚才那个"]:
                        text = text.replace(pronoun, device_name)
                    return text
        
        return None
    
    def get_context_summary(self) -> str:
        """
        获取语境摘要（用于模型推理）
        
        Returns:
            格式化的语境摘要
        """
        parts = []
        
        # 对话历史摘要
        recent_history = self.conversation_manager.get_recent_history(3)
        if recent_history:
            history_text = []
            for msg in recent_history:
                role_name = "用户" if msg["role"] == "user" else "系统"
                history_text.append(f"{role_name}: {msg['content']}")
            parts.append(f"最近对话：\n{chr(10).join(history_text)}")
        
        # 设备状态摘要
        state_summary = self.device_state.get_state_summary()
        if state_summary:
            parts.append(f"\n设备状态：\n{state_summary}")
        
        # 待确认指令
        if self.pending_confirmation:
            parts.append(f"\n待确认指令：{self.pending_confirmation}")
        
        return "\n".join(parts)
    
    def get_recent_devices(self) -> List[str]:
        """
        获取最近操作的设备列表
        
        Returns:
            设备类型列表
        """
        recent_commands = self.conversation_manager.get_recent_commands()
        devices = []
        for cmd in recent_commands:
            device_type = cmd.get("type")
            if device_type and device_type not in devices:
                devices.append(device_type)
        return devices
    
    def set_pending_confirmation(self, command: Optional[Dict]):
        """
        设置待确认的指令
        
        Args:
            command: 待确认的指令，如果为None则清除
        """
        self.pending_confirmation = command
    
    def clear_context(self):
        """清空语境信息"""
        self.pending_confirmation = None
