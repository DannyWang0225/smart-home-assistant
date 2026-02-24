"""
对话管理模块
管理对话历史记录和上下文信息
"""
from datetime import datetime
from typing import List, Dict, Optional
from collections import deque


class ConversationManager:
    """管理对话历史记录"""
    
    def __init__(self, max_history: int = 10):
        """
        初始化对话管理器
        
        Args:
            max_history: 最大历史记录数，默认10轮
        """
        self.max_history = max_history
        self.conversation_history: deque = deque(maxlen=max_history)
    
    def add_message(self, role: str, content: str, command: Optional[Dict] = None):
        """
        添加对话消息
        
        Args:
            role: 角色，'user' 或 'assistant'
            content: 消息内容
            command: 关联的指令（如果有）
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "command": command
        }
        self.conversation_history.append(message)
    
    def get_recent_history(self, n: int = 5) -> List[Dict]:
        """
        获取最近N轮对话
        
        Args:
            n: 要获取的对话轮数，默认5轮
            
        Returns:
            最近的对话历史列表
        """
        return list(self.conversation_history)[-n:]
    
    def get_full_context(self) -> str:
        """
        获取完整对话上下文（用于模型推理）
        
        Returns:
            格式化的对话历史字符串
        """
        if not self.conversation_history:
            return ""
        
        context_lines = []
        for msg in self.conversation_history:
            role_name = "用户" if msg["role"] == "user" else "系统"
            context_lines.append(f"{role_name}：{msg['content']}")
        
        return "\n".join(context_lines)
    
    def get_recent_commands(self) -> List[Dict]:
        """
        获取最近执行的指令
        
        Returns:
            最近执行的指令列表
        """
        commands = []
        for msg in self.conversation_history:
            if msg.get("command"):
                cmd_data = msg["command"]
                if isinstance(cmd_data, dict) and "commands" in cmd_data and isinstance(cmd_data["commands"], list):
                    commands.extend(cmd_data["commands"])
                else:
                    commands.append(cmd_data)
        return commands
    
    def get_last_device_mentioned(self) -> Optional[str]:
        """
        获取最近提到的设备
        
        Returns:
            设备类型（light/ac/window/temperature）或None
        """
        # 从最近的对话中查找提到的设备
        for msg in reversed(self.conversation_history):
            if msg.get("command"):
                cmd_data = msg["command"]
                if isinstance(cmd_data, dict) and "commands" in cmd_data and isinstance(cmd_data["commands"], list):
                    if cmd_data["commands"]:
                        return cmd_data["commands"][-1].get("type")
                else:
                    return cmd_data.get("type")
        return None
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history.clear()
