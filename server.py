
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from model_handler import ModelHandler
from mqtt_client import MQTTClient
from conversation_manager import ConversationManager
from device_state import DeviceState
from context_manager import ContextManager

app = FastAPI()

# Allow CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State
conversation_manager = ConversationManager(max_history=10)
device_state = DeviceState()
context_manager = ContextManager(conversation_manager, device_state)
model_handler = ModelHandler(model_name="qwen2.5:7b")
mqtt_client = MQTTClient()

# Initialize connection
print("Connecting to MQTT...")
mqtt_available = mqtt_client.connect()
if not mqtt_available:
    print("WARNING: MQTT connection failed. Messages will not be sent.")

class ChatRequest(BaseModel):
    message: str
    potential_commands: Optional[List[Dict[str, Any]]] = None

class ChatResponse(BaseModel):
    type: str  # 'success', 'question', 'none', 'error'
    text: str
    data: Optional[Any] = None  # potential commands or executed commands

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    user_input = request.message.strip()
    if not user_input:
        return ChatResponse(type="error", text="Input cannot be empty")

    conversation_manager.add_message("user", user_input)
    
    # Resolve pronouns
    resolved_input = user_input
    resolved = context_manager.resolve_pronoun(user_input)
    if resolved:
        resolved_input = resolved
        print(f"Resolved pronoun: {resolved}")

    conversation_history = conversation_manager.get_full_context()
    
    # Case 1: Handling potential command response
    if request.potential_commands:
        print(f"Processing response to potential commands: {user_input}")
        selected_commands = model_handler.parse_user_response(
            resolved_input, 
            request.potential_commands, 
            conversation_history
        )
        
        if not selected_commands:
             return ChatResponse(
                 type="question", 
                 text="抱歉，我没有理解您的意图。请明确说明您想要执行的操作。",
                 data=request.potential_commands # Keep the context
             )
        
        # Execute commands
        commands_to_execute = selected_commands if isinstance(selected_commands, list) else [selected_commands]
        response_texts = execute_commands(commands_to_execute)
        
        return ChatResponse(
            type="success",
            text=f"已执行: {', '.join(response_texts)}",
            data=commands_to_execute
        )

    # Case 2: New command recognition
    print(f"Recognizing command: {resolved_input}")
    device_states = device_state.get_state_summary()
    result = model_handler.recognize_command(resolved_input, conversation_history, device_states)

    # Direct command
    if result.get('commands'):
        commands = result['commands']
        # Execute directly (skipping confirmation for better UX in chat app, or could add confirmation step)
        response_texts = execute_commands(commands)
        if response_texts:
             msg_text = ", ".join(response_texts)
             # Store commands in history
             command_data = {"commands": commands}
             conversation_manager.add_message("assistant", f"已执行指令: {msg_text}", command_data)
             return ChatResponse(type="success", text=f"已执行: {msg_text}", data=commands)
        else:
             return ChatResponse(type="error", text="指令发送失败")

    # Potential intent
    if result.get('potential'):
        potential_commands = result.get('potential', [])
        question = model_handler.generate_question(user_input, potential_commands)
        conversation_manager.add_message("assistant", question)
        return ChatResponse(
            type="question",
            text=question,
            data=potential_commands
        )

    # No command
    conversation_manager.add_message("assistant", "未识别到智能家居相关指令")
    return ChatResponse(type="none", text="未识别到智能家居相关指令")

def execute_commands(commands: List[Dict]) -> List[str]:
    response_texts = []
    if not mqtt_available:
        return ["MQTT不可用 (模拟执行)"]
        
    for cmd in commands:
        if mqtt_client.send_command(cmd):
            device_state.update_state(cmd)
            formatted = model_handler.format_command_message(cmd)
            response_texts.append(formatted)
    return response_texts

@app.get("/api/state")
async def get_state():
    return device_state.get_all_states()

class ControlRequest(BaseModel):
    type: str
    action: str
    device: Optional[str] = None

@app.post("/api/control")
async def control_device(request: ControlRequest):
    command = {
        "type": request.type,
        "action": request.action,
        "device": request.device or request.type 
    }
    
    # Generate timestamp
    from datetime import datetime
    command["timestamp"] = datetime.now().isoformat()

    if mqtt_available:
        if mqtt_client.send_command(command):
            device_state.update_state(command)
            return {"status": "success", "message": f"已{request.action}{request.device or request.type}"}
        else:
            raise HTTPException(status_code=500, detail="MQTT发送失败")
    else:
        # Simulation mode
        device_state.update_state(command)
        return {"status": "success", "message": f"模拟执行: 已{request.action}{request.device or request.type}"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
