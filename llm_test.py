import requests

url = "http://127.0.0.1:11434/api/generate"
data = {
    "model": "qwen2.5:7b",
    "prompt": "解释什么是无需唤醒词语音系统",
    "stream": True  # 流式输出
}

resp = requests.post(url, json=data, stream=True)

# 逐行读取输出
for line in resp.iter_lines():
    if line:
        print(line.decode("utf-8"))
