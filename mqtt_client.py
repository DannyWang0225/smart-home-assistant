"""
MQTT客户端模块
用于发送智能家居指令到MQTT broker
"""
import json
import paho.mqtt.client as mqtt
from datetime import datetime
from typing import Dict, Optional
import os

# 尝试使用本地broker模拟器（默认启用，因为大多数情况下没有外部broker）
USE_LOCAL_BROKER = os.getenv('USE_LOCAL_BROKER', 'true').lower() == 'true'
if USE_LOCAL_BROKER:
    try:
        from local_mqtt_broker import get_broker
        LOCAL_BROKER_AVAILABLE = True
    except ImportError:
        LOCAL_BROKER_AVAILABLE = False
else:
    LOCAL_BROKER_AVAILABLE = False


class MQTTClient:
    """MQTT客户端，用于发送智能家居指令"""
    
    def __init__(self, broker: str = "localhost", port: int = 1883, topic: str = "smart_home/command"):
        """
        初始化MQTT客户端
        
        Args:
            broker: MQTT broker地址，默认localhost
            port: MQTT broker端口，默认1883
            topic: 发布主题，默认smart_home/command
        """
        self.broker = broker
        self.port = port
        self.topic = topic
        self.client = None
        self.connected = False
    
    def connect(self) -> bool:
        """
        连接到MQTT broker
        
        Returns:
            连接是否成功
        """
        # 如果使用本地broker，直接返回成功
        if LOCAL_BROKER_AVAILABLE and USE_LOCAL_BROKER:
            self.connected = True
            print(f"✓ 使用本地MQTT Broker模拟器")
            return True
        
        try:
            self.client = mqtt.Client()
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            
            # 等待连接建立
            import time
            timeout = 5
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            return self.connected
        except Exception as e:
            print(f"MQTT连接错误: {e}")
            # 如果连接失败，尝试使用本地broker
            if not USE_LOCAL_BROKER and LOCAL_BROKER_AVAILABLE:
                print("尝试使用本地MQTT Broker模拟器...")
                self.connected = True
                print(f"✓ 已切换到本地MQTT Broker模拟器")
                return True
            return False
    
    def _on_connect(self, client, userdata, flags, rc):
        """连接回调函数"""
        if rc == 0:
            self.connected = True
            print(f"✓ MQTT已连接到 {self.broker}:{self.port}")
        else:
            print(f"✗ MQTT连接失败，错误代码: {rc}")
            self.connected = False
    
    def _on_disconnect(self, client, userdata, rc):
        """断开连接回调函数"""
        self.connected = False
        if rc != 0:
            print("MQTT意外断开连接")
    
    def send_command(self, command: Dict) -> bool:
        """
        发送智能家居指令
        
        Args:
            command: 指令字典，包含type、device、action等字段
            
        Returns:
            发送是否成功
        """
        if not self.connected:
            print("MQTT未连接，尝试连接...")
            if not self.connect():
                return False
        
        # 构建消息
        message = {
            "type": command.get("type"),
            "device": command.get("device", ""),
            "action": command.get("action", ""),
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # 转换为JSON并发送
            payload = json.dumps(message, ensure_ascii=False)
            
            # 如果使用本地broker
            if LOCAL_BROKER_AVAILABLE and (USE_LOCAL_BROKER or not self.client):
                broker = get_broker()
                broker.publish(self.topic, payload)
                print(f"✓ MQTT消息已发送到主题: {self.topic} (本地模拟器)")
                print(f"  消息内容: {payload}")
                return True
            
            # 使用真实MQTT broker
            result = self.client.publish(self.topic, payload, qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"✓ MQTT消息已发送到主题: {self.topic}")
                print(f"  消息内容: {payload}")
                return True
            else:
                print(f"✗ MQTT消息发送失败，错误代码: {result.rc}")
                return False
                
        except Exception as e:
            print(f"发送MQTT消息时出错: {e}")
            return False
    
    def disconnect(self):
        """断开MQTT连接"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            print("MQTT连接已断开")
