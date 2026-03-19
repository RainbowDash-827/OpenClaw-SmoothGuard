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

### Step2: 配置本地大模型



### Step2: 启动 vllm
```python
python3 -m vllm.entrypoints.openai.api_server --model "/media/glenn/新加卷/lz/models/Qwen3-1.7B" --served-model-name local_vllm_Qwen3-1.7B --host 0.0.0.0 --port 8001 --enable-auto-tool-choice --tool-call-parser qwen3_xml
```

### Step3: 启动 smooth
```python
cd
python
```

### Step4: 启动 OpenClaw
```powershell
openclaw gateway
openclaw tui
```

