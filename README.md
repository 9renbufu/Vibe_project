# VoiceSketch AI

语音驱动的 AI 绘图工具 - 使用自然语言创建艺术作品

## 功能特性

- 🎤 **语音实时识别** - 使用 Web Speech API 进行中文语音识别
- 🎨 **自然语言绘图** - 说"画一个红色太阳"即可自动绘图
- 🌅 **复杂场景绘图** - 说"画一个海边日落场景"自动拆解为多个绘图动作
- 🔄 **上下文记忆** - 说"把太阳移到左边"能识别之前创建的太阳
- ✏️ **语音纠错** - 自动修复语音识别错误
- 🚀 **创意模式** - 说"帮我设计一个赛博朋克城市"AI 自动规划并绘图

## 技术栈

### 前端
- React 18
- TypeScript
- Canvas API
- Web Speech API
- Vite

### 后端
- FastAPI
- WebSocket
- Pydantic
- 多 LLM 支持 (Claude / OpenAI / DeepSeek / 通义千问 / 智谱GLM / Moonshot / Ollama)

## 快速开始

### 前置要求

- Python 3.11+
- Node.js 18+
- Conda (推荐) 或 pip
- 任一 LLM API Key (可选，无 API 也能使用基础功能)

### 本地开发

#### 1. 克隆项目
```bash
git clone <repository-url>
cd VoiceSketch_AI
```

#### 2. 设置后端

```bash
# 创建 conda 环境
conda create -n voicesketch python=3.11
conda activate voicesketch

# 安装依赖
cd backend
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置 LLM API
# 支持: claude, openai, deepseek, qwen, zhipu, moonshot, ollama

# 启动后端
uvicorn app.main:app --reload --port 8000
```

#### 3. 设置前端

```bash
# 新开一个终端
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

#### 4. 访问应用

打开浏览器访问 http://localhost:3000

### Docker 部署

```bash
# 配置环境变量
export ANTHROPIC_API_KEY=your_api_key_here

# 启动所有服务
docker-compose up -d

# 访问应用
# 前端: http://localhost
# 后端 API: http://localhost:8000
```

## 项目结构

```
VoiceSketch_AI/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI 主应用
│   │   ├── models.py        # 数据模型
│   │   ├── llm_handler.py    # 多 LLM 支持
│   │   ├── scene_manager.py # 场景管理
│   │   └── voice_processor.py # 语音处理
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── DrawingCanvas.tsx  # Canvas 绘图组件
│   │   │   └── VoiceControl.tsx   # 语音控制组件
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts    # WebSocket 连接
│   │   │   └── useVoiceRecognition.ts # 语音识别
│   │   ├── types/
│   │   │   └── index.ts       # TypeScript 类型定义
│   │   ├── App.tsx            # 主应用组件
│   │   └── main.tsx           # 入口文件
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
└── README.md
```

## LLM 配置

在 `backend/.env` 文件中配置:

```bash
# 选择 LLM 提供商
LLM_PROVIDER=openai  # 可选: claude, openai, deepseek, qwen, zhipu, moonshot, ollama

# OpenAI (或兼容 API)
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o

# DeepSeek
DEEPSEEK_API_KEY=your_key

# 通义千问 (阿里云)
DASHSCOPE_API_KEY=your_key

# 智谱 GLM
ZHIPU_API_KEY=your_key

# Moonshot (月之暗面)
MOONSHOT_API_KEY=your_key

# Ollama (本地模型，无需 API Key)
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=qwen2.5:7b
```

**推荐选择:**
- 国内用户: DeepSeek / 通义千问 / 智谱 (速度快，价格低)
- 本地部署: Ollama (免费，隐私好)
- 海外用户: OpenAI / Claude (效果最好)

## API 端点

### REST API
- `GET /api/health` - 健康检查
- `GET /api/scene` - 获取当前场景状态
- `POST /api/scene/clear` - 清空场景

### WebSocket
- `/ws` - 实时通信端点

#### 消息格式

**发送语音命令:**
```json
{
  "type": "voice",
  "data": {
    "text": "画一个红色的太阳"
  }
}
```

**接收动作:**
```json
{
  "type": "action",
  "data": {
    "actions": [...],
    "explanation": "画了一个红色的太阳"
  }
}
```

**场景状态:**
```json
{
  "type": "state",
  "data": {
    "shapes": [...],
    "background": {"r": 255, "g": 255, "b": 255},
    "width": 800,
    "height": 600
  }
}
```

## 使用示例

1. **基础绘图**
   - "画一个红色的圆"
   - "画一个蓝色的矩形"
   - "画一条直线"

2. **命名和引用**
   - "画一个太阳" → 创建名为"太阳"的圆形
   - "把太阳移到左边" → 移动之前创建的太阳

3. **复杂场景**
   - "画一个海边日落场景" → 自动创建天空、太阳、海面、沙滩等
   - "画一座房子" → 创建房子主体和屋顶

4. **创意模式**
   - "帮我设计一个赛博朋克城市"
   - "画一个未来太空站"

## 注意事项

1. **浏览器要求**: 语音识别功能需要 Chrome 浏览器支持
2. **LLM API**: 配置任一 LLM API 可获得完整功能，无 API 也能使用基础绘图
3. **网络**: WebSocket 连接需要稳定的网络环境
4. **本地模型**: 使用 Ollama 可完全离线运行

## 故障排除

### 语音识别不工作
- 确保使用 Chrome 浏览器
- 检查麦克风权限是否已授予
- 确保网络连接正常

### WebSocket 连接失败
- 检查后端服务是否正在运行
- 确认端口 8000 未被占用
- 检查防火墙设置

### LLM API 错误
- 验证 API Key 是否正确
- 检查 API 额度是否充足
- 查看后端日志获取详细错误信息
- 确认 LLM_PROVIDER 设置正确

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
