"""
本地MQTT Broker模拟器
使用文件进行进程间通信，支持跨进程消息传递
"""
import threading
import queue
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Optional


class LocalMQTTBroker:
    """本地MQTT Broker模拟器 - 使用文件进行进程间通信"""
    
    def __init__(self, message_file: str = ".mqtt_messages.jsonl"):
        """初始化broker"""
        self.message_file = message_file
        self.subscriptions = {}  # topic -> [callback_queue]
        self.running = False
        self._lock = threading.Lock()
        
        # 确保消息文件存在
        if not os.path.exists(self.message_file):
            with open(self.message_file, 'w', encoding='utf-8') as f:
                pass  # 创建空文件
        
        print("本地MQTT Broker已初始化")
    
    def subscribe(self, topic: str, callback_queue: queue.Queue):
        """订阅主题"""
        with self._lock:
            if topic not in self.subscriptions:
                self.subscriptions[topic] = []
            if callback_queue not in self.subscriptions[topic]:
                self.subscriptions[topic].append(callback_queue)
                print(f"✓ 订阅主题: {topic}")
    
    def publish(self, topic: str, payload: str):
        """发布消息到文件（跨进程通信）"""
        message = {
            'topic': topic,
            'payload': payload,
            'timestamp': datetime.now().isoformat()
        }
        
        # 写入文件（追加模式）
        try:
            with open(self.message_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(message, ensure_ascii=False) + '\n')
                f.flush()  # 立即刷新到磁盘
        except Exception as e:
            print(f"⚠ 写入消息文件失败: {e}")
            return False
        
        # 同时尝试通知本进程内的订阅者（如果存在）
        with self._lock:
            if topic in self.subscriptions:
                for callback_queue in self.subscriptions[topic]:
                    try:
                        callback_queue.put_nowait(message)
                    except queue.Full:
                        pass
        
        print(f"✓ 消息已发布到主题: {topic}")
        return True
    
    def read_messages(self, callback_queue: queue.Queue, topics: List[str]):
        """从文件读取消息并放入队列（用于订阅者）"""
        last_position = 0
        
        while self.running:
            try:
                # 检查文件是否有新内容
                if os.path.exists(self.message_file):
                    file_size = os.path.getsize(self.message_file)
                    
                    # 如果文件大小小于上次位置，说明文件被重置了
                    if file_size < last_position:
                        last_position = 0
                    
                    # 如果有新内容
                    if file_size > last_position:
                        with open(self.message_file, 'r', encoding='utf-8') as f:
                            # 移动到上次读取的位置
                            f.seek(last_position)
                            
                            # 读取新行
                            new_lines = []
                            for line in f:
                                if line.strip():
                                    new_lines.append(line.strip())
                            
                            # 处理新行
                            for line in new_lines:
                                try:
                                    message = json.loads(line)
                                    # 检查主题是否匹配
                                    if message.get('topic') in topics:
                                        try:
                                            callback_queue.put_nowait(message)
                                        except queue.Full:
                                            # 队列满，尝试清空旧消息
                                            try:
                                                while not callback_queue.empty():
                                                    callback_queue.get_nowait()
                                                callback_queue.put_nowait(message)
                                            except:
                                                pass
                                except json.JSONDecodeError:
                                    pass
                            
                            # 更新位置
                            last_position = f.tell()
                
                # 短暂休眠，避免CPU占用过高
                time.sleep(0.2)
                
            except Exception as e:
                print(f"⚠ 读取消息文件失败: {e}")
                time.sleep(0.5)


# 全局broker实例（每个进程一个）
_global_broker = None


def get_broker():
    """获取全局broker实例"""
    global _global_broker
    if _global_broker is None:
        _global_broker = LocalMQTTBroker()
    return _global_broker
