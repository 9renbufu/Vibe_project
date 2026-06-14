# Voice Designer Agent

AI 驱动的智能设计助手 - 基于多 Agent 协作的设计系统 + 纯语音控制绘图工具

## 项目简介

Voice Designer Agent 是一个 AI 设计平台，包含两个核心模式：

1. **AI Designer 模式**：用户通过语音描述设计需求，多 Agent 协作完成设计生成、评估、修改
2. **Voice Drawing 模式**：纯语音控制的程序化绘图工具，通过规则引擎解析中文指令，生成高质量艺术作品

## Voice Drawing 模式

纯语音控制的绘图工具，不依赖 LLM API 画图，通过 jieba 中文分词 + 正则意图解析 + 程序化算法生成绘图。

### 核心功能

- **多画布记录**：每个作品独立保存，支持切换和继续绘画
- **流式绘画效果**：逐个图形绘制，模拟真人作画过程
- **增量绘图**：在同一画布上逐步叠加、修饰
- **语音 + 文字输入**：支持语音识别和文字输入两种方式
- **用户偏好学习**：自动记录常用颜色、风格、形状
- **历史记录**：保存绘图历史，支持重放

### 支持的指令

| 类别 | 指令示例 |
|------|---------|
| 基础图形 | 画一个圆、画矩形、画三角形、画星形、画心形 |
| 程序化艺术 | 画流场、画分形树、画水彩、画曼陀罗、画螺线、画沃罗诺伊 |
| 风景场景 | 画日落、画海洋、画山脉、画星空、画森林、画雪景 |
| 颜色 | 红色、蓝色、暖色调、冷色调 |
| 编辑 | 撤销、重做、清空画布 |
| 位置 | 中间、左上角、右边 |

### 技术亮点

- **Perlin Noise 流场**：400+ 粒子沿噪声场运动，生成有机流动的线条艺术
- **分形树**：递归 L-system 算法，自然感的树木分支
- **水彩效果**：30+ 层半透明叠层渲染，模拟水彩晕染
- **曼陀罗**：径向对称图案，自动生成复杂几何
- **螺线**：外旋轮线参数方程生成精美曲线
- **沃罗诺伊**：随机种子点区域划分图案
- **风景场景**：天空渐变 + 山脉 + 海面 + 太阳/月亮的复合场景

### 绘图模式启动

```bash
# 后端
cd backend
python run_drawing.py

# 前端
cd frontend
npm run dev
```

访问 http://localhost:3000，点击顶部 "Voice Drawing" 按钮切换到绘图模式。

## AI Designer 模式

### Agent 系统架构

```
Agent Orchestrator (编排器)
├── RequirementAgent    - 需求分析 Agent
├── PlanningAgent       - 设计规划 Agent
├── PromptAgent         - 提示词生成 Agent
├── GenerationAgent     - 图像生成 Agent
├── CriticAgent         - 设计评估 Agent
├── RevisionAgent       - 设计修改 Agent
└── DesignMemoryAgent   - 设计记忆 Agent
```

### 功能模块

#### 1. 需求分析 (RequirementAgent)
- 自动识别用户意图 (创建/修改/导出/查询)
- 提取设计风格、情感氛围、行业领域
- 识别设计元素、颜色偏好、关键词
- 支持中文和英文输入

#### 2. 设计规划 (PlanningAgent)
- 自动生成 3 个差异化设计方案
- **艺术风格差异化**: 3 个方案各用不同艺术媒介风格
  - 方案 1：插画风格（digital illustration）
  - 方案 2：手绘/水彩风格（watercolor painting）
  - 方案 3：扁平/矢量风格（flat vector design）
- 每个方案包含: 名称、描述、风格、元素、配色、构图
- 方案评分和推荐
- 用户可选择方案进行生成

#### 3. 提示词生成 (PromptAgent)
- 根据设计方案生成高质量图像提示词
- 支持记忆注入 (自动融入用户偏好)
- 生成正面提示词和负面提示词
- 风格关键词和技术参数

#### 4. 图像生成 (GenerationAgent)
- 支持多种图像生成 API:
  - OpenAI DALL-E 3
  - 通义万相 (Qwen WanX)
  - 智谱 CogView
- 异步任务轮询
- 版本管理

#### 5. 设计评估 (CriticAgent)
- **四维度评估**:
  - `brand_consistency` - 品牌一致性
  - `creativity` - 创意性
  - `commercial_value` - 商业价值
  - `visual_impact` - 视觉冲击力
- **Vision 多模态评估**: 支持 GPT-4o 等视觉模型直接分析生成图片
- **具体优化建议** (如: 字体过细、色彩层级不足、品牌识别度不足)
- **自动优化**: 评分低于阈值时自动重新生成（最多 3 次）

#### 6. 设计修改 (RevisionAgent)
- 分析用户修改意见
- 生成修改方案 (minor/major/complete)
- 更新设计方案和提示词
- 重新生成和评估

#### 7. 设计记忆 (DesignMemoryAgent)
- **短期记忆**: 当前会话的风格、颜色、元素偏好
- **长期记忆**: 跨会话持久化的用户偏好
- **设计历史**: 保存最近 500 条设计记录
- **Prompt 注入**: 自动将用户偏好注入到提示词中
- **偏好分析**: 分析风格偏好、颜色偏好、成功率

### 前端界面

#### 三栏布局
- **左侧 - Conversation Panel**: 对话面板，支持语音和文本输入
  - **输入队列**: 生成过程中可以继续录音或打字，输入自动排队
  - **风格快捷标签**: 一键添加风格关键词（插画、水彩、手绘、扁平、像素、赛博）
- **中间 - Design Workspace**: 设计画布，展示生成的图像
- **右侧 - Agent Panel**: Agent 面板，展示思考过程和状态

#### Agent Panel 功能
- **Current Task**: 当前任务和步骤进度
- **Agent Thinking**: 实时展示 Agent 思考过程
- **Design Memory**: 显示长期偏好和当前会话记忆
- **Design Plan**: 设计方案选择
- **Version History**: 版本历史和回滚
- **AI Evaluation**: 四维度评估可视化

## 技术栈

### 前端
- React 18 + TypeScript
- Vite 构建工具
- Zustand 状态管理
- Web Speech API (语音识别)
- Canvas 2D API (程序化绘图)
- WebSocket 实时通信

### 后端
- FastAPI + WebSocket
- Pydantic 数据模型
- jieba 中文分词
- Perlin Noise 自实现
- 多 LLM 支持:
  - DeepSeek (推荐)
  - Claude
  - OpenAI
  - 通义千问
  - 智谱 GLM
  - Moonshot
  - Ollama (本地模型)
- 多图像生成 API:
  - OpenAI DALL-E 3
  - 通义万相
  - 智谱 CogView
- **Vision 多模态评估**: 支持 GPT-4o 等视觉模型进行图片评估

## 快速开始

### 前置要求

- Python 3.11+
- Node.js 18+
- Conda (推荐)
- 任一 LLM API Key（AI Designer 模式需要）
- 图像生成 API Key（AI Designer 模式需要）

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/9renbufu/Vibe_project.git
cd Vibe_project

# 2. 后端设置
conda create -n voicesketch python=3.11
conda activate voicesketch
cd backend
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 配置 API Key

# 3. 前端设置 (新终端)
cd frontend
npm install
```

### 配置 API

编辑 `backend/.env`:

```bash
# LLM 配置 (选择一个)
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_key

# 图像生成配置 (选择一个)
IMAGE_PROVIDER=qwen
DASHSCOPE_API_KEY=your_key

# Vision 模型配置 (可选，用于图片评估)
VISION_API_KEY=your_key
VISION_BASE_URL=https://api.openai.com/v1
VISION_MODEL=gpt-4o
```

### 启动服务

```bash
# AI Designer 模式
cd backend && python run.py
cd frontend && npm run dev

# Voice Drawing 模式
cd backend && python run_drawing.py
cd frontend && npm run dev
```

访问 http://localhost:3000

## 项目结构

```
Vibe_project/
├── backend/
│   ├── app/
│   │   ├── agents/              # AI Designer Agent 系统
│   │   │   ├── base.py          # Agent 基类
│   │   │   ├── state.py         # 状态管理
│   │   │   ├── orchestrator.py  # 编排器
│   │   │   ├── requirement.py   # 需求分析
│   │   │   ├── planning.py      # 设计规划
│   │   │   ├── prompt.py        # 提示词生成
│   │   │   ├── generation.py    # 图像生成
│   │   │   ├── critic.py        # 设计评估
│   │   │   ├── revision.py      # 设计修改
│   │   │   └── memory.py        # 设计记忆
│   │   ├── drawing/             # Voice Drawing 绘图引擎
│   │   │   ├── parser.py        # 指令解析 (jieba 分词 + 正则)
│   │   │   ├── engine.py        # 程序化绘图引擎 (Perlin/分形/水彩)
│   │   │   └── ws_handler.py    # WebSocket 处理器 (多画布记录)
│   │   ├── modules/             # 功能模块
│   │   │   ├── llm_client.py    # LLM 客户端
│   │   │   └── image_gen.py     # 图像生成器
│   │   ├── main_v4.py           # AI Designer 入口
│   │   ├── main_drawing.py      # Voice Drawing 入口
│   │   └── protocol.py          # 消息协议
│   ├── data/                    # 数据存储
│   │   └── memory/              # 记忆数据
│   ├── run.py                   # AI Designer 启动脚本
│   ├── run_drawing.py           # Voice Drawing 启动脚本
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AgentWorkspace/  # AI Designer 界面
│   │   │   │   ├── ConversationPanel.tsx
│   │   │   │   ├── DesignWorkspace.tsx
│   │   │   │   └── AgentPanel.tsx
│   │   │   └── DrawingWorkspace/ # Voice Drawing 界面
│   │   │       ├── VoicePanel.tsx
│   │   │       ├── StatusPanel.tsx
│   │   │       └── ProceduralCanvas.tsx
│   │   ├── store/
│   │   │   ├── agentStore.ts    # AI Designer 状态
│   │   │   ├── drawingStore.ts  # Voice Drawing 状态
│   │   │   └── wsManager.ts     # 共享 WebSocket 管理
│   │   ├── AppRouter.tsx        # 模式切换路由
│   │   ├── AppDrawing.tsx       # 绘图模式布局
│   │   └── main.tsx
│   └── package.json
└── README.md
```

## API 接口

### AI Designer WebSocket (`/ws`)

#### 客户端 -> 服务端
- `voice_input` - 语音输入
- `text_input` - 文本输入
- `select_plan` - 选择设计方案
- `get_state` - 获取状态
- `reset` - 重置

#### 服务端 -> 客户端
- `status` - 状态更新
- `thinking` - 思考过程
- `stage_update` - 阶段更新
- `agent_update` - Agent 执行结果
- `agent_response` - Agent 回复
- `plans_result` - 设计方案
- `evaluation_result` - 评估结果
- `image_result` - 图像结果
- `state_update` - 完整状态

### Voice Drawing WebSocket (`/ws/draw`)

#### 客户端 -> 服务端
- `voice_input` / `text_input` - 绘图指令
- `create_record` - 创建新画布记录
- `switch_record` - 切换画布记录
- `list_records` - 获取记录列表
- `undo` / `redo` - 撤销/重做
- `reset` - 重置画布

#### 服务端 -> 客户端
- `drawing_update` - 绘图更新 (指令 + 状态)
- `drawing_batch` - 流式批次指令
- `drawing_complete` - 绘制完成
- `record_created` - 新记录创建完成
- `record_switched` - 记录切换完成
- `records_list` - 记录列表

### REST API

- `GET /api/health` - AI Designer 健康检查
- `GET /api/drawing/health` - Voice Drawing 健康检查
- `GET /api/drawing/presets` - 获取预设列表
- `GET /api/memory/preferences` - 获取用户偏好
- `GET /api/memory/history` - 获取设计历史
- `GET /api/memory/stats` - 获取记忆统计

## 许可证

MIT License
