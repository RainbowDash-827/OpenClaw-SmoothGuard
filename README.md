# OpenClaw-SmoothGuard
在消息到达 AI 之前进行的检查判断

### Step1: 环境配置
```python
conda create -n smooth python=3.10 -y
conda activate smooth
```
```powershell
pip install vllm
```

### Step2: 修改 OpenClaw 配置文件
打开 OpenClaw.json，修改以下内容。

在 "models": "providers" 添加两项内容：
```json
"models":{
  "providers":{
    "vllm": {
      "baseUrl": "http://127.0.0.1:8001/v1",  // 后面 Qwen3-1.7B 是在 8001 端口，这里也写 8001
      "apiKey": "Not Use",  // 不需要 api
      "api": "openai-completions",  // 不需要 api
      "models": [
        {
          "id": "local_vllm_Qwen3-1.7B",  // 与后面 served-model-name 保持一致
          "name": "local_vllm_Qwen3-1.7B",  // 与后面 served-model-name 保持一致
          "reasoning": false,
          "input": [
            "text"
          ],
          "cost": {
            "input": 0,
            "output": 0,
            "cacheRead": 0,
            "cacheWrite": 0
          },
          "contextWindow": 128000,
          "maxTokens": 8192
        }
      ]
    },
  }
}
```
```json
"models":
  "providers":
    "smooth": {
      "baseUrl": "http://127.0.0.1:8002/v1",  // 后面 smooth 是在 8002 端口，这里也写 8002
      "apiKey": "Not Use",  // 不需要 api
      "api": "openai-completions",  // 不需要 api
      "models": [
        {
          "id": "local_vllm_Qwen3-1.7B",  // 与后面 served-model-name 保持一致
          "name": "local_vllm_Qwen3-1.7B",  // 与后面 served-model-name 保持一致
          "reasoning": true,
          "input": [
            "text"
          ],
          "contextWindow": 128000,
          "maxTokens": 8192
        }
      ]
    },
  }
}
```

### Step3: 配置本地大模型
在 HuggingFace 上下载模型到本地，这里选择的是 Qwne3-1.7B。

在终端 1 用 vllm 启动 Qwen，将 "your/path/for/Qwen3-1.7B" 替换为存放 Qwne3-1.7B 的路径。

```python
python3 -m vllm.entrypoints.openai.api_server --model "your/path/for/Qwen3-1.7B" --served-model-name local_vllm_Qwen3-1.7B --host 0.0.0.0 --port 8001 --enable-auto-tool-choice --tool-call-parser qwen3_xml
```

### Step4: 启动 smooth
```powershell
git clone
cd 
```
```python
python smooth_proxy.py
```

### Step5: 启动 OpenClaw
```powershell
openclaw gateway
```
在浏览器打开 localhost:18789 开始对话即可

