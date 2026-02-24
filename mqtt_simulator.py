"""
MQTT模拟接收器
用于模拟接收智能家居指令消息
"""
import json
import paho.mqtt.client as mqtt
from datetime import datetime
import queue
import threading
import os

# 尝试使用本地broker模拟器
USE_LOCAL_BROKER = os.getenv('USE_LOCAL_BROKER', 'true').lower() == 'true'
if USE_LOCAL_BROKER:
    try:
        from local_mqtt_broker import get_broker
        LOCAL_BROKER_AVAILABLE = True
    except ImportError:
        LOCAL_BROKER_AVAILABLE = False
else:
    LOCAL_BROKER_AVAILABLE = False


class MQTTSimulator:
    """MQTT模拟接收器，用于测试MQTT消息接收"""
    
    def __init__(self, broker: str = "localhost", port: int = 1883, topic: str = "smart_home/command"):
        """
        初始化MQTT模拟接收器
        
        Args:
            broker: MQTT broker地址，默认localhost
            port: MQTT broker端口，默认1883
            topic: 订阅主题，默认smart_home/command
        """
        self.broker = broker
        self.port = port
        self.topic = topic
        self.client = None
        self.message_queue = None
        self.running = False
    
    def _on_connect(self, client, userdata, flags, rc):
        """连接回调函数"""
        if rc == 0:
            print(f"✓ MQTT模拟接收器已连接到 {self.broker}:{self.port}")
            # 订阅主题
            client.subscribe(self.topic, qos=1)
            print(f"✓ 已订阅主题: {self.topic}")
            print("=" * 60)
            print("等待接收智能家居指令消息...")
            print("=" * 60)
        else:
            print(f"✗ MQTT连接失败，错误代码: {rc}")
    
    def _on_message(self, client, userdata, msg):
        """消息接收回调函数（真实MQTT broker）"""
        try:
            # 解析JSON消息
            payload = msg.payload.decode('utf-8')
            message = json.loads(payload)
            self._process_message({'topic': msg.topic, 'payload': payload})
        except json.JSONDecodeError as e:
            print(f"\n✗ JSON解析错误: {e}")
            print(f"原始消息: {msg.payload.decode('utf-8')}\n")
        except Exception as e:
            print(f"\n✗ 处理消息时出错: {e}\n")
    
    def _process_message(self, message_data: dict):
        """处理接收到的消息"""
        try:
            # 解析payload
            if isinstance(message_data.get('payload'), str):
                message = json.loads(message_data['payload'])
            else:
                message = message_data.get('payload', message_data)
            
            # 格式化显示
            print("\n" + "=" * 60)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 收到新消息")
            print("-" * 60)
            print(f"主题: {message_data.get('topic', self.topic)}")
            print(f"消息内容:")
            print(json.dumps(message, ensure_ascii=False, indent=2))
            
            # 解析指令类型
            cmd_type = message.get('type', '')
            device = message.get('device', '')
            action = message.get('action', '')
            
            type_map = {
                'light': '灯',
                'ac': '空调',
                'window': '窗户',
                'temperature': '温度检测'
            }
            
            device_name = type_map.get(cmd_type, '未知设备')
            if device:
                device_name = device
            
            print("-" * 60)
            print(f"指令解析: {action}{device_name}")
            
            # 生成执行反馈
            feedback = self._generate_feedback(cmd_type, action, device_name)
            print(f"💬 设备反馈: {feedback}")
            print("=" * 60 + "\n")
            
        except json.JSONDecodeError as e:
            print(f"\n✗ JSON解析错误: {e}")
            print(f"原始消息: {message_data}\n")
        except Exception as e:
            print(f"\n✗ 处理消息时出错: {e}\n")
    
    def _generate_feedback(self, cmd_type: str, action: str, device_name: str) -> str:
        """
        根据指令生成设备反馈
        
        Args:
            cmd_type: 指令类型
            action: 动作
            device_name: 设备名称
            
        Returns:
            反馈文本
        """
        if cmd_type == 'light':
            if action == '开':
                return "✅ 已经打开了灯"
            elif action == '关':
                return "✅ 已经关闭了灯"
        elif cmd_type == 'ac':
            if action == '开':
                return "✅ 已经打开了空调"
            elif action == '关':
                return "✅ 已经关闭了空调"
        elif cmd_type == 'window':
            if action == '开':
                return "✅ 已经打开了窗户"
            elif action == '关':
                return "✅ 已经关闭了窗户"
        elif cmd_type == 'temperature':
            if action == '检测':
                return f"✅ 当前温度：25°C（模拟数据）"
        
        return f"✅ 已执行：{action}{device_name}"
    
    def start(self):
        """启动模拟接收器"""
        # 如果使用本地broker
        if LOCAL_BROKER_AVAILABLE and USE_LOCAL_BROKER:
            try:
                self.message_queue = queue.Queue(maxsize=100)
                broker = get_broker()
                broker.subscribe(self.topic, self.message_queue)
                
                print("=" * 60)
                print("MQTT模拟接收器已启动 (使用本地Broker)")
                print(f"主题: {self.topic}")
                print("=" * 60)
                print("等待接收智能家居指令消息...")
                print("=" * 60)
                
                # 启动文件读取线程
                broker.running = True
                read_thread = threading.Thread(
                    target=broker.read_messages,
                    args=(self.message_queue, [self.topic]),
                    daemon=True
                )
                read_thread.start()
                
                self.running = True
                print("\n开始监听消息...\n")
                while self.running:
                    try:
                        # 使用较长的超时时间，避免频繁检查
                        message = self.message_queue.get(timeout=5)
                        self._process_message(message)
                    except queue.Empty:
                        # 超时是正常的，继续等待
                        continue
                    except KeyboardInterrupt:
                        break
                        
            except KeyboardInterrupt:
                print("\n\n正在停止MQTT模拟接收器...")
                self.running = False
                print("已停止")
            except Exception as e:
                print(f"启动MQTT模拟接收器时出错: {e}")
            return
        
        # 使用真实MQTT broker
        try:
            self.client = mqtt.Client()
            self.client.on_connect = self._on_connect
            self.client.on_message = self._on_message
            
            print("正在启动MQTT模拟接收器...")
            print(f"Broker: {self.broker}:{self.port}")
            print(f"主题: {self.topic}")
            
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_forever()
            
        except KeyboardInterrupt:
            print("\n\n正在停止MQTT模拟接收器...")
            if self.client:
                self.client.loop_stop()
                self.client.disconnect()
            print("已停止")
        except Exception as e:
            print(f"启动MQTT模拟接收器时出错: {e}")
            print("\n提示: 如果没有MQTT broker，可以使用本地模拟器：")
            print("      设置环境变量 USE_LOCAL_BROKER=true")


if __name__ == "__main__":
    simulator = MQTTSimulator()
    simulator.start()
