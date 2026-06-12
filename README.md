# VoiceSketch AI

语音驱动的 AI 绘图工具 - 使用自然语言创建艺术作品

## 功能特性

### 核心功能
- 🎤 **语音实时识别** - 使用 Web Speech API 进行中文语音识别
- 🎨 **自然语言绘图** - 说"画一个红色太阳"即可自动绘图
- 🌅 **复杂场景绘图** - 说"画一个海边日落场景"自动拆解为多个绘图动作
- 🔄 **上下文记忆** - 说"把太阳移到左边"能识别之前创建的太阳
- ✏️ **语音纠错** - 自动修复语音识别错误

### 增强功能
- ↩️ **撤销/重做** - 语音说"撤销"或"undo"回退操作
- ⏺️ **录制回放** - 记录绘图过程，可回放演示
- 🎯 **智能分层** - 自动处理图形层次关系
- 🌈 **渐变阴影** - Canvas 绘图支持渐变和阴影效果

## 技术栈

### 前端
- React 18 + TypeScript
- Canvas API (增强绘图)
- Web Speech API
- Vite

### 后端
- FastAPI + WebSocket
- 多 LLM 支持 (DeepSeek / Claude / OpenAI / 通义千问 / 智谱 / Ollama)
- Pydantic 数据模型

## 快速开始

### 前置要求

- Python 3.11+
- Node.js 18+
- Conda (推荐)
- 任一 LLM API Key

### 本地开发

```bash
# 1. 克隆项目
git clone <repository-url>
cd VoiceSketch_AI

# 2. 后端设置
conda create -n voicesketch python=3.11
conda activate voicesketch
cd backend
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 配置 API Key
uvicorn app.main:app --reload --port 8000

# 3. 前端设置 (新终端)
cd frontend
npm install
npm run dev
```

访问 http://localhost:3000

## 语音命令

### 绘图命令
- "画一个红色的圆"
- "画一座房子"
- "画一个海边日落场景"
- "帮我设计一个赛博朋克城市"

### 编辑命令
- "把太阳移到左边"
- "让太阳变大一点"
- "太阳变成蓝色"
- "删除房子"

### 控制命令
- "撤销" / "undo" - 撤销上一步
- "重做" / "redo" - 恢复操作
- "清空" / "clear" - 清空画布
- "开始录制" - 记录绘图过程
- "停止录制" - 停止记录
- "回放" - 播放录制过程

## LLM 配置

在 `backend/.env` 中配置:

```bash
# 选择 LLM 提供商
LLM_PROVIDER=deepseek  # 可选: claude, openai, deepseek, qwen, zhipu, moonshot, ollama

# DeepSeek (推荐国内用户)
DEEPSEEK_API_KEY=your_key

# 通义千问
DASHSCOPE_API_KEY=your_key

# 智谱 GLM
ZHIPU_API_KEY=your_key

# Ollama (本地模型)
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=qwen2.5:7b
```

## 项目结构

```
VoiceSketch_AI/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI 主应用
│   │   ├── models.py        # 数据模型
│   │   ├── llm_handler.py   # 多 LLM 支持
│   │   ├── image_generator.py # 图像生成 (可选)
│   │   ├── scene_manager.py # 场景管理
│   │   └── voice_processor.py # 语音处理
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── EnhancedCanvas.tsx  # 增强 Canvas
│   │   │   ├── VoiceControl.tsx    # 语音控制
│   │   │   └── ControlPanel.tsx    # 控制面板
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts
│   │   │   ├── useVoiceRecognition.ts
│   │   │   ├── useHistory.ts       # 撤销/重做
│   │   │   ├── useRecording.ts     # 录制回放
│   │   │   └── useVoiceCommands.ts # 语音命令
│   │   └── App.tsx
│   └── package.json
└── README.md
```

## 毕业设计亮点

1. **纯语音交互** - 无需鼠标键盘，完全语音控制
2. **智能指令理解** - LLM 解析自然语言，支持复杂场景描述
3. **实时响应** - WebSocket 通信，低延迟绘图
4. **容错处理** - 语音纠错、指令容错
5. **演示功能** - 录制回放，适合答辩演示
6. **多模型支持** - 灵活接入不同 LLM

## 许可证

MIT License
