# 智能家居指令识别系统 - API接口文档

## 项目概述

智能家居指令识别系统是一个基于本地LLM模型的指令识别和MQTT通信系统。系统能够识别用户的自然语言输入，识别潜在的智能家居指令，并通过MQTT协议发送设备控制命令。

### 功能特性

- 支持4种智能家居指令类型：开关灯、开关空调、开关窗户、温度检测
- 基于Ollama本地模型进行指令识别
- 主动识别潜在意图并询问用户
- 支持多指令识别和执行
- MQTT消息通信（支持本地模拟器和真实MQTT broker）
- 设备反馈模拟

---

## 模块接口

### 1. ModelHandler - 模型处理器

负责调用Ollama API进行指令识别和自然语言处理。

#### 1.1 初始化

```python
ModelHandler(model_name: str = "qwen2.5:7b", base_url: str = "http://127.0.0.1:11434")
```

**参数说明：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| model_name | str | "qwen2.5:7b" | Ollama模型名称 |
| base_url | str | "http://127.0.0.1:11434" | Ollama服务地址 |

**示例：**
```python
from model_handler import ModelHandler

# 使用默认配置
handler = ModelHandler()

# 自定义模型
handler = ModelHandler(model_name="llama3.2", base_url="http://localhost:11434")
```

#### 1.2 recognize_command - 识别指令

识别用户输入中的智能家居指令（包括潜在意图）。

**方法签名：**
```python
def recognize_command(self, user_input: str) -> Dict
```

**参数说明：**

| 参数 | 类型 | 说明 |
|------|------|------|
| user_input | str | 用户输入的文本 |

**返回值：**

返回字典，包含以下字段：

```python
{
    "type": str,        # 指令类型：'light'|'ac'|'window'|'temperature'|'none'
    "device": str,      # 设备名称（可选）
    "action": str,      # 动作：'开'|'关'|'检测'
    "potential": list   # 潜在指令列表（如果有）
}
```

**潜在指令格式：**
```python
{
    "type": str,         # 指令类型
    "device": str,       # 设备名称
    "action": str,       # 动作
    "suggestion": str    # 询问建议文本
}
```

**示例：**
```python
result = handler.recognize_command("感觉屋子好热呀！")
# 返回：
# {
#     "type": "none",
#     "potential": [
#         {
#             "type": "ac",
#             "action": "开",
#             "suggestion": "您是想开空调吗？"
#         },
#         {
#             "type": "temperature",
#             "action": "检测",
#             "suggestion": "还是想检测一下温度？"
#         }
#     ]
# }
```

#### 1.3 generate_question - 生成询问

根据潜在意图生成询问用户的自然语言文本。

**方法签名：**
```python
def generate_question(self, user_input: str, potential_commands: list) -> str
```

**参数说明：**

| 参数 | 类型 | 说明 |
|------|------|------|
| user_input | str | 用户原始输入 |
| potential_commands | list | 潜在指令列表 |

**返回值：**

返回询问文本字符串。

**示例：**
```python
potential = [
    {"type": "ac", "action": "开", "suggestion": "您是想开空调吗？"},
    {"type": "temperature", "action": "检测", "suggestion": "还是想检测一下温度？"}
]
question = handler.generate_question("好热", potential)
# 返回：'您是想打开空调降低屋内温度呢，还是希望我帮您测量一下当前室温？'
```

#### 1.4 parse_user_response - 解析用户回答

解析用户的自然语言回答，识别要执行的指令。

**方法签名：**
```python
def parse_user_response(self, user_response: str, potential_commands: list) -> Optional[Dict] | List[Dict] | None
```

**参数说明：**

| 参数 | 类型 | 说明 |
|------|------|------|
| user_response | str | 用户的回答 |
| potential_commands | list | 潜在指令列表 |

**返回值：**

- 单个指令：返回字典
- 多个指令：返回字典列表
- 无法识别：返回 `None`

**示例：**
```python
# 单个指令
result = handler.parse_user_response("开空调", potential_commands)
# 返回：{"type": "ac", "device": "空调", "action": "开"}

# 多个指令
result = handler.parse_user_response("开空调顺便测量室温", potential_commands)
# 返回：[{"type": "ac", "device": "空调", "action": "开"}, 
#        {"type": "temperature", "device": "", "action": "检测"}]

# 无法识别
result = handler.parse_user_response("不知道", potential_commands)
# 返回：None
```

#### 1.5 format_command_message - 格式化指令

将指令字典格式化为可读的中文消息。

**方法签名：**
```python
def format_command_message(self, command: Dict) -> str
```

**参数说明：**

| 参数 | 类型 | 说明 |
|------|------|------|
| command | Dict | 指令字典 |

**返回值：**

返回格式化的中文消息字符串。

**示例：**
```python
command = {"type": "ac", "device": "空调", "action": "开"}
msg = handler.format_command_message(command)
# 返回：'开空调'
```

---

### 2. MQTTClient - MQTT客户端

负责发送智能家居指令到MQTT broker。

#### 2.1 初始化

```python
MQTTClient(broker: str = "localhost", port: int = 1883, topic: str = "smart_home/command")
```

**参数说明：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| broker | str | "localhost" | MQTT broker地址 |
| port | int | 1883 | MQTT broker端口 |
| topic | str | "smart_home/command" | 发布主题 |

**环境变量：**

- `USE_LOCAL_BROKER`：设置为 `'true'` 使用本地broker模拟器（默认）

#### 2.2 connect - 连接Broker

连接到MQTT broker。

**方法签名：**
```python
def connect(self) -> bool
```

**返回值：**

- `True`：连接成功
- `False`：连接失败

**示例：**
```python
client = MQTTClient()
success = client.connect()
if success:
    print("连接成功")
```

#### 2.3 send_command - 发送指令

发送智能家居指令到MQTT broker。

**方法签名：**
```python
def send_command(self, command: Dict) -> bool
```

**参数说明：**

| 参数 | 类型 | 说明 |
|------|------|------|
| command | Dict | 指令字典，包含 `type`、`device`、`action` 字段 |

**返回值：**

- `True`：发送成功
- `False`：发送失败

**消息格式：**

```json
{
    "type": "ac",
    "device": "空调",
    "action": "开",
    "timestamp": "2026-01-21T12:00:00.000000"
}
```

**示例：**
```python
command = {"type": "ac", "device": "空调", "action": "开"}
success = client.send_command(command)
```

#### 2.4 disconnect - 断开连接

断开MQTT连接。

**方法签名：**
```python
def disconnect(self) -> None
```

**示例：**
```python
client.disconnect()
```

---

### 3. MQTTSimulator - MQTT模拟接收器

模拟MQTT消息接收器，用于测试和演示。

#### 3.1 初始化

```python
MQTTSimulator(broker: str = "localhost", port: int = 1883, topic: str = "smart_home/command")
```

**参数说明：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| broker | str | "localhost" | MQTT broker地址 |
| port | int | 1883 | MQTT broker端口 |
| topic | str | "smart_home/command" | 订阅主题 |

#### 3.2 start - 启动接收器

启动模拟接收器，开始监听消息。

**方法签名：**
```python
def start(self) -> None
```

**示例：**
```python
simulator = MQTTSimulator()
simulator.start()  # 阻塞运行，直到收到中断信号
```

---

### 4. LocalMQTTBroker - 本地MQTT Broker模拟器

本地MQTT broker模拟器，使用文件进行进程间通信。

#### 4.1 get_broker - 获取Broker实例

获取全局broker实例（单例模式）。

**方法签名：**
```python
def get_broker() -> LocalMQTTBroker
```

**示例：**
```python
from local_mqtt_broker import get_broker

broker = get_broker()
```

#### 4.2 subscribe - 订阅主题

订阅指定主题。

**方法签名：**
```python
def subscribe(self, topic: str, callback_queue: queue.Queue) -> None
```

**参数说明：**

| 参数 | 类型 | 说明 |
|------|------|------|
| topic | str | 主题名称 |
| callback_queue | queue.Queue | 消息队列 |

#### 4.3 publish - 发布消息

发布消息到指定主题。

**方法签名：**
```python
def publish(self, topic: str, payload: str) -> bool
```

**参数说明：**

| 参数 | 类型 | 说明 |
|------|------|------|
| topic | str | 主题名称 |
| payload | str | 消息内容（JSON字符串） |

**返回值：**

- `True`：发布成功
- `False`：发布失败

---

## 数据格式

### 指令类型

| 类型值 | 说明 | 支持的动作 |
|--------|------|-----------|
| `light` | 灯 | 开、关 |
| `ac` | 空调 | 开、关 |
| `window` | 窗户 | 开、关 |
| `temperature` | 温度检测 | 检测 |

### MQTT消息格式

**主题：** `smart_home/command`

**消息体（JSON）：**
```json
{
    "type": "ac",
    "device": "空调",
    "action": "开",
    "timestamp": "2026-01-21T12:00:00.000000"
}
```

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 指令类型（light/ac/window/temperature） |
| device | string | 设备名称（可选） |
| action | string | 动作（开/关/检测） |
| timestamp | string | ISO格式时间戳 |

---

## 使用示例

### 示例1：基本指令识别

```python
from model_handler import ModelHandler
from mqtt_client import MQTTClient

# 初始化
handler = ModelHandler(model_name="qwen2.5:7b")
mqtt_client = MQTTClient()

# 连接MQTT
mqtt_client.connect()

# 识别指令
result = handler.recognize_command("请帮我开灯")

if result.get('type') != 'none':
    # 发送指令
    mqtt_client.send_command(result)
```

### 示例2：潜在意图处理

```python
# 识别潜在意图
result = handler.recognize_command("感觉屋子好热呀！")

if result.get('potential'):
    # 生成询问
    question = handler.generate_question("感觉屋子好热呀！", result['potential'])
    print(question)
    
    # 获取用户回答
    user_response = input("您的回答: ")
    
    # 解析回答
    command = handler.parse_user_response(user_response, result['potential'])
    
    if command:
        # 发送指令
        mqtt_client.send_command(command)
```

### 示例3：多指令处理

```python
# 识别多个指令
result = handler.parse_user_response("开空调顺便测量室温", potential_commands)

if isinstance(result, list):
    # 依次发送所有指令
    for cmd in result:
        mqtt_client.send_command(cmd)
```

### 示例4：完整流程

```python
from model_handler import ModelHandler
from mqtt_client import MQTTClient

def process_user_input(user_input: str):
    # 初始化
    handler = ModelHandler()
    mqtt_client = MQTTClient()
    mqtt_client.connect()
    
    # 识别指令
    result = handler.recognize_command(user_input)
    
    # 明确指令
    if result.get('type') != 'none':
        mqtt_client.send_command(result)
        return
    
    # 潜在意图
    if result.get('potential'):
        question = handler.generate_question(user_input, result['potential'])
        print(question)
        
        user_response = input("您的回答: ")
        commands = handler.parse_user_response(user_response, result['potential'])
        
        if commands:
            if isinstance(commands, list):
                for cmd in commands:
                    mqtt_client.send_command(cmd)
            else:
                mqtt_client.send_command(commands)
    
    mqtt_client.disconnect()

# 使用
process_user_input("天气好热，屋子里闷闷的")
```

---

## 错误处理

### ModelHandler 错误

| 错误类型 | 说明 | 处理方式 |
|---------|------|---------|
| `requests.exceptions.Timeout` | 请求超时（超过180秒） | 检查模型是否正在加载，等待后重试 |
| `requests.exceptions.ConnectionError` | 无法连接到Ollama服务 | 确保Ollama服务正在运行 |
| `requests.exceptions.HTTPError` | HTTP错误 | 根据状态码处理（502/404/503） |
| `json.JSONDecodeError` | JSON解析错误 | 检查模型返回内容 |

### MQTTClient 错误

| 错误类型 | 说明 | 处理方式 |
|---------|------|---------|
| 连接失败 | 无法连接到MQTT broker | 检查broker是否运行，或使用本地模拟器 |
| 消息发送失败 | 发送MQTT消息失败 | 检查连接状态和broker状态 |

---

## 环境配置

### 依赖安装

```bash
pip install -r requirements.txt
```

**依赖列表：**

- `requests>=2.31.0` - HTTP请求库
- `paho-mqtt>=2.0.0` - MQTT客户端库

### Ollama配置

1. **安装Ollama：**
   - 访问 https://ollama.ai 下载安装

2. **下载模型：**
   ```bash
   ollama pull qwen2.5:7b
   ```

3. **启动Ollama服务：**
   ```bash
   ollama serve
   ```

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `USE_LOCAL_BROKER` | `true` | 是否使用本地MQTT broker模拟器 |

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `main.py` | 主程序入口 |
| `model_handler.py` | 模型指令识别模块 |
| `mqtt_client.py` | MQTT客户端模块 |
| `mqtt_simulator.py` | MQTT模拟接收器 |
| `local_mqtt_broker.py` | 本地MQTT broker模拟器 |
| `requirements.txt` | Python依赖列表 |
| `.mqtt_messages.jsonl` | MQTT消息文件（自动创建） |

---

## 运行方式

### 1. 启动MQTT接收器（终端1）

```bash
python mqtt_simulator.py
```

### 2. 运行主程序（终端2）

```bash
python main.py
```

### 3. 交互使用

```
请输入指令: 感觉屋子好热呀！
💡 检测到潜在意图
您是想打开空调降低屋内温度呢，还是希望我帮您测量一下当前室温？
您的回答: 开空调顺便测量室温

✓ 识别到 2 个指令：
   - 开空调
   - 执行温度检测

✓ 所有指令已发送 (2/2)
```

---

## 注意事项

1. **首次调用延迟：** 模型首次加载可能需要30-120秒，建议程序启动时预热模型
2. **超时设置：** API调用超时时间设置为180秒，可根据实际情况调整
3. **消息文件：** 本地broker使用 `.mqtt_messages.jsonl` 文件进行进程间通信
4. **模型要求：** 需要确保Ollama服务正在运行，并且已下载相应模型

---

## 更新日志

- **v1.0** - 初始版本
  - 支持基本指令识别
  - 支持潜在意图识别和询问
  - 支持MQTT消息发送和接收
  - 支持本地broker模拟器

---

## 许可证

本项目仅用于学习和测试目的。
