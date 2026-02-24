"""
模型指令识别模块
使用Ollama API识别智能家居指令
"""
import json
import requests
import sys
import time
from typing import Optional, Dict


class ModelHandler:
    """处理Ollama模型调用和指令识别"""
    
    def __init__(self, model_name: str = "qwen2.5:7b", base_url: str = "http://127.0.0.1:11434"):
        """
        初始化模型处理器
        
        Args:
            model_name: Ollama模型名称，默认为qwen2.5:7b
            base_url: Ollama服务地址，默认为http://127.0.0.1:11434
        """
        self.model_name = model_name
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
    
    def analyze_intent(self, user_input: str, conversation_history: str = "") -> Dict:
        """
        分析用户意图：指令、闲聊还是忽略
        """
        prompt = f"""你是一个智能语音助手。请分析用户的语音转文字内容，判断其意图。
注意：用户的输入是通过语音识别（ASR）生成的，可能存在同音字错误或不完整。
例如：“沙巴工程师”可能是“设吧（设为）...”，“非下如往”可能是“飞向...”或完全错误的识别。

请先尝试结合上下文修正语音识别错误，还原用户本意，然后再判断意图。

上下文：
{conversation_history}

原始语音文本："{user_input}"

请执行以下步骤：
1. 【纠错】：
   - 尝试修正语音文本中的错误。
   - **重要**：如果原始文本完全不通顺、逻辑混乱、或者是无意义的随机字符（如“说明前还会说话，你没有没有在北”），请不要强行纠错，直接保留原文本，并在下一步判断为 ignore。
   - 只有在非常有把握还原用户本意时（例如同音字清晰），才进行纠错。

2. 【判断】：基于修正后的文本判断意图。
   - command: 包含智能家居控制指令（如开灯、关空调、查温度）。
   - chat: 针对你的闲聊或提问（如你好、讲个笑话）。
   - ignore: 背景噪音、自言自语、逻辑不通的乱码、或者明显不是对助手说的话。

请严格按照JSON格式返回：
{{ 
  "corrected_text": "修正后的文本（如果无需修正或无法修正则填原文本）",
  "intent": "command" | "chat" | "ignore", 
  "reason": "判断理由" 
}}
"""
        try:
            data = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False
            }
            # sys.stdout.write("正在分析意图")
            # sys.stdout.flush()
            response = requests.post(self.api_url, json=data, stream=False, timeout=30)
            response.raise_for_status()
            # sys.stdout.write("\r" + " " * 20 + "\r")
            
            result_json = response.json()
            content = result_json.get('response', '').strip()
            
            if '```' in content:
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start != -1:
                    content = content[json_start:json_end]
            
            return json.loads(content)
        except Exception as e:
            print(f"意图分析失败: {e}")
            # 默认保守策略：如果是短语则忽略，长语可能是闲聊
            if len(user_input) < 2:
                return {"intent": "ignore", "corrected_text": user_input}
            return {"intent": "chat", "corrected_text": user_input}

    def generate_chat_response(self, user_input: str, conversation_history: str = "") -> str:
        """生成闲聊回复"""
        prompt = f"""你是一个智能语音助手，名字叫“小爱”。请以亲切、自然的口语风格回复用户。
避免长篇大论，因为你的回复将转为语音播放。回复要简短有力。

对话历史：
{conversation_history}

用户：{user_input}
助手："""
        
        try:
            data = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False
            }
            response = requests.post(self.api_url, json=data, stream=False, timeout=60)
            content = response.json().get('response', '').strip()
            return content
        except Exception as e:
            return "抱歉，我没听清，请再说一遍。"

    def _build_prompt(self, user_input: str, conversation_history: str = "", device_states: str = "") -> str:
        """
        构建识别指令的prompt
        
        Args:
            user_input: 用户输入的文本
            conversation_history: 对话历史（可选）
            device_states: 设备状态（可选）
            
        Returns:
            完整的prompt字符串
        """
        context_parts = []
        
        # 添加对话历史
        if conversation_history:
            context_parts.append(f"最近对话历史：\n{conversation_history}")
        
        # 添加设备状态
        if device_states:
            context_parts.append(f"当前设备状态：\n{device_states}")
        
        context_section = "\n\n".join(context_parts)
        if context_section:
            context_section = f"{context_section}\n\n"
        
        prompt = f"""你是一个智能家居指令识别系统。你的任务是从用户的自然语言输入中提取明确的控制指令。

请注意：用户可能会使用口语化、礼貌性的表达（如"帮我..."、"请..."、"有点热"、"太暗了"），你需要忽略这些修饰语，提取核心的控制意图。
同时，请注意用户的否定指令或修正指令（如"不要打开空调"、"不对，是关灯"），这通常意味着撤销之前的操作或确保设备处于特定状态。

支持的指令类型：
1. 开关灯（light）：开、关
2. 开关空调（ac）：开、关
3. 开关窗户（window）：开、关
4. 温度检测（temperature）：检测

示例：
- "帮我把空调打开" -> {{"commands": [{{"type": "ac", "device": "空调", "action": "开"}}], "potential": []}}
- "有点热" -> {{"commands": [], "potential": [{{"type": "ac", "action": "开", "suggestion": "为您打开空调？"}}]}}
- "不要打开空调 开窗透气" -> {{"commands": [{{"type": "ac", "device": "空调", "action": "关"}}, {{"type": "window", "device": "窗户", "action": "开"}}], "potential": []}}
- "太暗了" -> {{"commands": [{{"type": "light", "device": "灯", "action": "开"}}], "potential": []}}
- "查看当前温度" -> {{"commands": [{{"type": "temperature", "device": "", "action": "检测"}}], "potential": []}}

{context_section}用户输入：{user_input}

请严格按照JSON格式返回结果：
- 如果包含明确指令，返回：{{"commands": [指令对象列表], "potential": []}}
- 如果不包含明确指令，但可能有潜在意图，返回：{{"commands": [], "potential": [潜在指令数组]}}
- 如果完全不相关，返回：{{"commands": [], "potential": []}}

只返回JSON，不要其他文字说明。"""
        return prompt
    
    def _build_question_prompt(self, user_input: str, potential_commands: list) -> str:
        """
        构建生成询问的prompt
        
        Args:
            user_input: 用户原始输入
            potential_commands: 潜在指令列表
            
        Returns:
            询问用户的文本
        """
        # 构建选项描述
        options = []
        for idx, cmd in enumerate(potential_commands, 1):
            suggestion = cmd.get('suggestion', '')
            if suggestion:
                options.append(f"{idx}. {suggestion}")
            else:
                formatted = self.format_command_message(cmd)
                options.append(f"{idx}. {formatted}")
        
        options_text = "\n".join(options)
        
        prompt = f"""用户说："{user_input}"
可能的操作：
{options_text}

请生成一个自然的询问，询问用户想要执行哪个操作。不要列出选项，而是用自然语言询问。
只返回询问文本，不要其他说明。"""
        return prompt
    
    def generate_question(self, user_input: str, potential_commands: list) -> str:
        """
        生成询问用户的文本
        
        Args:
            user_input: 用户原始输入
            potential_commands: 潜在指令列表
            
        Returns:
            询问文本
        """
        prompt = self._build_question_prompt(user_input, potential_commands)
        
        try:
            data = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False
            }
            
            # 显示加载提示
            sys.stdout.write("正在生成询问")
            sys.stdout.flush()
            
            response = requests.post(self.api_url, json=data, stream=False, timeout=180)
            response.raise_for_status()
            
            # 清除加载提示
            sys.stdout.write("\r" + " " * 20 + "\r")
            sys.stdout.flush()
            
            result_json = response.json()
            question = result_json.get('response', '').strip()
            
            if not question:
                # 如果没有生成问题，使用默认询问
                return "您想要执行什么操作？"
            
            return question
            
        except Exception as e:
            print(f"⚠ 生成询问失败: {e}")
            return "您想要执行什么操作？"
    
    def parse_user_response(self, user_response: str, potential_commands: list, conversation_history: str = "") -> Optional[Dict]:
        """
        解析用户的自然语言回答，识别要执行的指令
        
        Args:
            user_response: 用户的回答
            potential_commands: 潜在指令列表
            conversation_history: 对话历史（可选，用于上下文理解）
            
        Returns:
            识别到的指令字典，如果没有识别到则返回None
        """
        # 构建选项描述
        options_desc = []
        for cmd in potential_commands:
            cmd_desc = f"- {self.format_command_message(cmd)} (type: {cmd.get('type')}, action: {cmd.get('action')})"
            options_desc.append(cmd_desc)
        
        options_text = "\n".join(options_desc)
        
        context_section = ""
        if conversation_history:
            context_section = f"\n对话历史：\n{conversation_history}\n\n"
        
        prompt = f"""用户回答："{user_response}"
{context_section}可选的操作：
{options_text}

请分析用户的回答，判断用户想要执行哪些操作。
- 如果用户的回答包含多个操作（如"开空调顺便测量室温"、"开空调和检测温度"等），返回所有操作的数组
- 如果用户的回答明确指向单个操作（如"开空调"、"检测温度"等），返回该操作的完整信息
- 如果用户的回答是模糊的肯定回答（如"好的"、"可以"、"行"、"嗯"等），优先选择第一个操作
- 如果用户的回答完全无法确定，返回：{{"type": "none"}}

请严格按照JSON格式返回结果：
- 单个操作：{{"type": "ac", "device": "空调", "action": "开"}}
- 多个操作：{{"commands": [{{"type": "ac", "device": "空调", "action": "开"}}, {{"type": "temperature", "device": "", "action": "检测"}}]}}
- 无法确定：{{"type": "none"}}

只返回JSON，不要其他文字说明。"""
        
        try:
            data = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False
            }
            
            # 显示加载提示
            sys.stdout.write("正在解析回答")
            sys.stdout.flush()
            
            response = requests.post(self.api_url, json=data, stream=False, timeout=180)
            response.raise_for_status()
            
            # 清除加载提示
            sys.stdout.write("\r" + " " * 20 + "\r")
            sys.stdout.flush()
            
            result_json = response.json()
            content = result_json.get('response', '').strip()
            
            # 提取JSON
            if '```' in content:
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    content = content[json_start:json_end]
            
            result = json.loads(content)
            
            # 检查是否识别到指令
            if result.get('type') == 'none':
                return None
            
            # 检查是否有多个指令
            if 'commands' in result and isinstance(result['commands'], list):
                # 多个指令，返回列表
                commands = []
                valid_types = ['light', 'ac', 'window', 'temperature']
                for cmd in result['commands']:
                    if cmd.get('type') in valid_types:
                        # 补充缺失的字段
                        if 'device' not in cmd:
                            cmd['device'] = ''
                        if 'action' not in cmd:
                            # 从potential_commands中找到匹配的action
                            for potential_cmd in potential_commands:
                                if potential_cmd.get('type') == cmd.get('type'):
                                    cmd['action'] = potential_cmd.get('action', '')
                                    break
                        commands.append(cmd)
                return commands if commands else None
            
            # 单个指令
            valid_types = ['light', 'ac', 'window', 'temperature']
            if result.get('type') not in valid_types:
                return None
            
            # 补充缺失的字段
            if 'device' not in result:
                result['device'] = ''
            if 'action' not in result:
                # 从potential_commands中找到匹配的action
                for cmd in potential_commands:
                    if cmd.get('type') == result.get('type'):
                        result['action'] = cmd.get('action', '')
                        break
            
            return result
            
        except Exception as e:
            print(f"⚠ 解析用户回答失败: {e}")
            return None
    
    def recognize_command(self, user_input: str, conversation_history: str = "", device_states: str = "") -> Dict:
        """
        识别用户输入中的智能家居指令（包括潜在意图）
        
        Args:
            user_input: 用户输入的文本
            conversation_history: 对话历史（可选，用于上下文理解）
            device_states: 设备状态（可选，用于上下文理解）
            
        Returns:
            返回字典，包含：
            - commands: 指令列表
            - potential: 潜在指令列表（如果有）
        """
        prompt = self._build_prompt(user_input, conversation_history, device_states)
        
        try:
            # 调用Ollama API (使用generate端点，参考llm_test.py)
            data = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False  # 非流式输出
            }
            
            # 显示加载提示
            sys.stdout.write("正在处理")
            sys.stdout.flush()
            
            # 使用较长的超时时间（180秒），因为模型首次加载或处理可能需要较长时间
            response = requests.post(self.api_url, json=data, stream=False, timeout=180)
            response.raise_for_status()  # 检查HTTP错误
            
            # 清除加载提示
            sys.stdout.write("\r" + " " * 20 + "\r")  # 清除提示行
            sys.stdout.flush()
            
            # 解析响应
            result_json = response.json()
            content = result_json.get('response', '').strip()
            
            if not content:
                print("⚠ 警告: 模型返回内容为空")
                return {'commands': [], 'potential': []}
            
            # 尝试解析JSON
            # 如果返回的内容包含代码块，提取JSON部分
            if '```' in content:
                # 提取代码块中的JSON
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    content = content[json_start:json_end]
            
            result = json.loads(content)
            
            # 确保有potential字段
            if 'potential' not in result:
                result['potential'] = []
            
            # 确保有commands字段
            if 'commands' not in result:
                result['commands'] = []
                # 兼容旧格式：如果返回了单指令格式
                if result.get('type') and result.get('type') != 'none':
                    result['commands'] = [{
                        'type': result.get('type'),
                        'device': result.get('device', ''),
                        'action': result.get('action', '')
                    }]
            
            # 验证指令类型
            valid_types = ['light', 'ac', 'window', 'temperature']
            valid_commands = []
            for cmd in result['commands']:
                if cmd.get('type') in valid_types:
                    valid_commands.append(cmd)
            
            result['commands'] = valid_commands
            
            return result
            
        except requests.exceptions.Timeout as e:
            sys.stdout.write("\r" + " " * 20 + "\r")  # 清除加载提示
            print(f"✗ 请求超时: 模型响应时间过长（超过180秒）")
            # ... (log details)
            return {'commands': [], 'potential': []}
        except requests.exceptions.ConnectionError as e:
            print(f"✗ 连接错误: 无法连接到Ollama服务")
            # ... (log details)
            return {'commands': [], 'potential': []}
        except requests.exceptions.HTTPError as e:
            # ... (log details)
            return {'commands': [], 'potential': []}
        except json.JSONDecodeError as e:
            print(f"⚠ JSON解析错误: {e}")
            print(f"模型返回内容: {content}")
            print("提示：模型返回的内容可能不是有效的JSON格式\n")
            return {'commands': [], 'potential': []}
        except Exception as e:
            error_msg = str(e)
            print(f"✗ 模型调用错误: {error_msg}")
            
            # ... (log details)
            
            print()
            return {'commands': [], 'potential': []}
    
    def format_command_message(self, command: Dict) -> str:
        """
        格式化指令为可读的中文消息
        
        Args:
            command: 指令字典
            
        Returns:
            格式化的中文消息
        """
        type_map = {
            'light': '灯',
            'ac': '空调',
            'window': '窗户',
            'temperature': '温度检测'
        }
        
        device = command.get('device', '')
        action = command.get('action', '')
        cmd_type = type_map.get(command.get('type', ''), '未知设备')
        
        if command.get('type') == 'temperature':
            return f"执行{cmd_type}"
        else:
            return f"{action}{device or cmd_type}"
