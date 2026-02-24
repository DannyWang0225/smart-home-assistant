# AI 智能家居助手 (Smart Home AI Assistant)

这是一个基于本地大模型 (Ollama + Qwen2.5) 的智能家居语音助手项目。它包含一个 Python 后端服务、一个 React 前端界面以及一个 MQTT 设备模拟器。

## 📋 前置要求

在运行项目之前，请确保已安装以下软件：

1.  **Python 3.10+** (建议使用 Conda 管理环境)
2.  **Node.js & npm** (用于前端)
3.  **Ollama** (用于本地 LLM 推理)

## 🚀 快速开始

### 1. 环境准备

#### 启动 Ollama 模型服务
本项目默认使用 `qwen2.5:7b` 模型。请确保 Ollama 已安装并运行。

```bash
# 下载模型
ollama pull qwen2.5:7b

# 启动服务 (通常安装后会自动后台运行，如未运行请执行)
ollama serve
```

#### 后端环境设置
建议使用 Conda 创建独立的虚拟环境：

```bash
# 创建并激活环境
conda create -n ai_assistant python=3.10
conda activate ai_assistant

# 安装依赖
pip install -r requirements.txt
```

#### 前端环境设置

```bash
cd frontend
npm install
```

### 2. 启动项目

你需要打开 **3 个终端窗口** 分别运行以下服务：

#### 终端 1: 启动 MQTT 模拟器
该脚本模拟 MQTT Broker 和智能家居设备（灯、空调、窗户等）。

```bash
# 确保在项目根目录
conda activate ai_assistant
python mqtt_simulator.py
```

#### 终端 2: 启动后端 API 服务
后端服务负责处理语音识别、意图理解和设备控制逻辑。

```bash
# 确保在项目根目录
conda activate ai_assistant
python server.py
```
*后端服务将运行在: http://localhost:8000*

#### 终端 3: 启动前端界面

```bash
cd frontend
npm run dev
```
*前端界面将运行在: http://localhost:5173*

## 💡 使用说明

1.  打开浏览器访问前端页面 (http://localhost:5173)。
2.  在聊天框中输入或通过语音（如果实现了前端语音录制）发送指令。
3.  **支持的指令示例**：
    *   "帮我把空调打开"
    *   "房间有点暗" (会询问是否开灯或自动开灯)
    *   "不要打开空调，开窗透气" (复合指令)
    *   "查看当前温度"

## 🛠️ 项目结构

*   `server.py`: 后端 FastAPI 服务入口。
*   `mqtt_simulator.py`: 本地 MQTT Broker 和设备模拟器。
*   `model_handler.py`: 处理与 Ollama 的交互和意图识别。
*   `frontend/`: React + Vite 前端项目源码。
*   `requirements.txt`: Python 依赖列表。

## ⚠️ 注意事项

*   确保 Ollama 服务在后台运行且端口为默认的 `11434`。
*   如果 MQTT 连接失败，请检查 `mqtt_simulator.py` 是否正常运行。
