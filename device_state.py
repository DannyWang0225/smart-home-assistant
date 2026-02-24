"""
设备状态跟踪模块
跟踪智能家居设备的状态
"""
from datetime import datetime
from typing import Dict, Optional


class DeviceState:
    """跟踪智能家居设备状态"""
    
    def __init__(self):
        """初始化设备状态跟踪器"""
        self.devices = {
            "light": {"state": "off", "last_action": None, "last_update": None},
            "ac": {"state": "off", "last_action": None, "last_update": None},
            "window": {"state": "closed", "last_action": None, "last_update": None},
            "temperature": {"last_check": None, "last_value": None}
        }
    
    def update_state(self, command: Dict):
        """
        更新设备状态
        
        Args:
            command: 指令字典，包含type、action等字段
        """
        device_type = command.get("type")
        action = command.get("action")
        
        if device_type not in self.devices:
            return
        
        current_time = datetime.now().isoformat()
        
        if device_type == "temperature":
            # 温度检测不改变状态，只记录最后检查时间
            self.devices[device_type]["last_check"] = current_time
        else:
            # 更新开关状态
            if action == "开":
                if device_type == "window":
                    self.devices[device_type]["state"] = "open"
                else:
                    self.devices[device_type]["state"] = "on"
            elif action == "关":
                if device_type == "window":
                    self.devices[device_type]["state"] = "closed"
                else:
                    self.devices[device_type]["state"] = "off"
            
            self.devices[device_type]["last_action"] = action
            self.devices[device_type]["last_update"] = current_time
    
    def get_state(self, device_type: str) -> Optional[Dict]:
        """
        获取指定设备的状态
        
        Args:
            device_type: 设备类型（light/ac/window/temperature）
            
        Returns:
            设备状态字典，如果设备不存在返回None
        """
        return self.devices.get(device_type)
    
    def get_all_states(self) -> Dict:
        """
        获取所有设备状态
        
        Returns:
            所有设备状态的字典
        """
        return self.devices.copy()
    
    def get_state_summary(self) -> str:
        """
        获取状态摘要（用于模型推理）
        
        Returns:
            格式化的状态摘要字符串
        """
        summary_lines = []
        device_names = {
            "light": "灯",
            "ac": "空调",
            "window": "窗户",
            "temperature": "温度"
        }
        
        for device_type, info in self.devices.items():
            device_name = device_names.get(device_type, device_type)
            if device_type == "temperature":
                if info["last_check"]:
                    value = info["last_value"] if info["last_value"] else "未知"
                    summary_lines.append(f"{device_name}：最后检查时间 {info['last_check']}，值 {value}")
            else:
                state_cn = {
                    "on": "开启",
                    "off": "关闭",
                    "open": "打开",
                    "closed": "关闭"
                }.get(info["state"], info["state"])
                
                last_action = info.get("last_action", "无")
                summary_lines.append(f"{device_name}：{state_cn}（最后操作：{last_action}）")
        
        return "\n".join(summary_lines) if summary_lines else "暂无设备状态信息"
    
    def get_recently_operated_device(self) -> Optional[str]:
        """
        获取最近操作的设备类型
        
        Returns:
            设备类型或None
        """
        most_recent = None
        most_recent_time = None
        
        for device_type, info in self.devices.items():
            if device_type == "temperature":
                check_time = info.get("last_check")
                if check_time and (most_recent_time is None or check_time > most_recent_time):
                    most_recent_time = check_time
                    most_recent = device_type
            else:
                update_time = info.get("last_update")
                if update_time and (most_recent_time is None or update_time > most_recent_time):
                    most_recent_time = update_time
                    most_recent = device_type
        
        return most_recent
