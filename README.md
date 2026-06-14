# Voice Designer Agent

AI 驱动的智能设计助手 - 基于多 Agent 协作的设计系统

## 项目简介

Voice Designer Agent 是一个基于 AI Agent 架构的智能设计系统，包含两个核心模式：

1. **AI Designer 模式**（题目一）：用户通过语音描述设计需求，多 Agent 协作完成设计生成
2. **语音绘图工具**（题目二）：纯语音控制的绘图工具，通过程序化算法生成高质量艺术作品

## 语音绘图工具（题目二）

纯语音控制的绘图工具，不使用 LLM API 画图，通过规则引擎解析中文指令 + 程序化算法生成绘图。

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

- **Perlin Noise 流场**：400 个粒子沿噪声场运动，生成有机流动的线条艺术
- **分形树**：递归 L-system 算法，自然感的树木分支
- **水彩效果**：30+ 层半透明叠层渲染，模拟水彩晕染
- **曼陀罗**：径向对称图案，自动生成复杂几何
- **风景场景**：天空渐变 + 山脉 + 海面 + 太阳/月亮的复合场景

### 启动方式

```bash
# 后端
cd backend
python run_drawing.py

# 前端
cd frontend
npm run dev
```

访问 http://localhost:3000，点击顶部 "语音绘图" 按钮切换模式。

## 核心特性

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
- **Vision 多模态评估**: 支持 GPT-4o 等视觉模型直接分析生成图片，给出更准确的评估
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
  - **输入队列**: 生成过程中可以继续录音或打字，输入自动排队，生成完成后自动发送
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
- WebSocket 实时通信

### 后端
- FastAPI + WebSocket
- Pydantic 数据模型
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
- 任一 LLM API Key
- 图像生成 API Key

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
# 启动后端
cd backend
python run.py

# 启动前端 (新终端)
cd frontend
npm run dev
```

访问 http://localhost:3000

## 使用示例

### 基本使用

```
用户: 设计一个科技感的logo
Agent: [分析需求] 识别风格: 科技感, 意图: 创建设计
       [设计方案] 生成3个方案供选择
       [提示词] 生成图像提示词
       [图像生成] 调用API生成图像
       [设计评估] 评分: 85/100
       [结果] 设计已完成，版本 v1
```

### 修改设计

```
用户: 把颜色改成蓝色
Agent: [分析修改] 识别修改类型: 颜色调整
       [更新方案] 修改配色方案
       [重新生成] 生成新版本
       [评估] 重新评估设计质量
       [结果] 已完成修改，版本 v2
```

### 查询记忆

```
用户: 我之前用过什么风格？
Agent: [查询记忆] 返回历史设计偏好
       [结果] 您偏好 minimalist 风格，常用蓝色系配色
```

## 项目结构

```
Vibe_project/
├── backend/
│   ├── app/
│   │   ├── agents/              # Agent 系统
│   │   │   ├── __init__.py
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
│   │   ├── modules/             # 功能模块
│   │   │   ├── llm_client.py    # LLM 客户端
│   │   │   └── image_gen.py     # 图像生成器
│   │   ├── main_v4.py           # 主应用 (v4)
│   │   └── protocol.py          # 消息协议
│   ├── data/                    # 数据存储
│   │   └── memory/              # 记忆数据
│   ├── run.py                   # 启动脚本
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── AgentWorkspace/  # Agent 工作区
│   │   │       ├── ConversationPanel.tsx
│   │   │       ├── DesignWorkspace.tsx
│   │   │       └── AgentPanel.tsx
│   │   ├── store/
│   │   │   └── agentStore.ts    # Zustand 状态
│   │   ├── types/
│   │   │   └── agent.ts         # TypeScript 类型
│   │   ├── App.tsx
│   │   └── main.tsx
│   └── package.json
└── README.md
```

## API 接口

### WebSocket 消息

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

### REST API

- `GET /api/health` - 健康检查
- `GET /api/memory/preferences` - 获取用户偏好
- `GET /api/memory/history` - 获取设计历史
- `GET /api/memory/stats` - 获取记忆统计

## 许可证

MIT License
