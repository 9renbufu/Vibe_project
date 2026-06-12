# Voice Designer 系统架构设计

## 1. 项目概述

Voice Designer 是一个纯语音驱动的 AI 设计师系统，用户通过语音描述设计需求，AI 自动理解、规划并生成高质量设计作品。

## 2. 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                       │
├─────────────────────────────────────────────────────────────┤
│  VoiceInput  │  ChatPanel  │  DesignCanvas  │  DesignInfo  │
└─────────────────────────────────────────────────────────────┘
                              │
                         WebSocket
                              │
┌─────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                        │
├─────────────────────────────────────────────────────────────┤
│                      main_v2.py (入口)                      │
├─────────────────────────────────────────────────────────────┤
│                      Agent Layer                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              DesignerAgent (核心代理)                 │   │
│  │  - 需求理解    - 方案规划    - 多轮对话              │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                     Module Layer                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │ LLM 客户端│  │ 图像生成  │  │ 记忆管理  │                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
├─────────────────────────────────────────────────────────────┤
│                    Protocol Layer                           │
│              WebSocket 消息协议定义                          │
└─────────────────────────────────────────────────────────────┘
```

## 3. 核心模块

### 3.1 DesignerAgent (设计代理)

**职责：**
- 理解用户设计需求
- 维护设计上下文
- 规划设计方案
- 协调各模块工作

**设计阶段：**
```python
class DesignPhase(Enum):
    IDLE = "idle"                    # 等待指令
    REQUIREMENT = "requirement"      # 需求收集
    DISCUSSION = "discussion"        # 设计讨论
    PLANNING = "planning"            # 方案规划
    GENERATING = "generating"        # 图像生成
    REVIEWING = "reviewing"          # 方案评审
    REFINING = "refining"            # 修改优化
    EXPORTING = "exporting"          # 导出作品
```

### 3.2 记忆管理

**三层记忆结构：**
- **短期记忆**：最近 10 条对话
- **长期记忆**：重要信息摘要
- **实体记忆**：设计元素、风格、颜色等

### 3.3 图像生成模块

**支持的 API：**
- OpenAI DALL-E
- 通义万相（阿里云）
- 智谱 CogView

## 4. WebSocket 消息协议

### 客户端 → 服务端

```json
{
    "type": "voice_input",
    "data": {
        "text": "帮我设计一个科技感的海报"
    }
}
```

### 服务端 → 客户端

```json
{
    "type": "agent_response",
    "data": {
        "response": "好的，我来帮你设计科技感海报...",
        "action": "generate",
        "phase": "generating",
        "style": "cyberpunk",
        "elements": [...],
        "color_palette": ["#00d4ff", "#7b2ff7"]
    }
}
```

## 5. 目录结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main_v2.py          # 主应用入口
│   ├── protocol.py         # WebSocket 消息协议
│   ├── agent/
│   │   ├── __init__.py
│   │   └── designer_agent.py  # 核心设计代理
│   └── modules/
│       ├── __init__.py
│       ├── llm_client.py   # LLM 客户端
│       ├── image_gen.py    # 图像生成
│       └── memory.py       # 记忆管理
├── run.py                  # 启动脚本
└── requirements.txt

frontend/
├── src/
│   ├── AppV2.tsx           # 新版主应用
│   └── components/
│       ├── ChatPanel.tsx   # 对话面板
│       ├── DesignCanvas.tsx # 设计画布
│       ├── DesignInfo.tsx  # 设计信息
│       └── VoiceInput.tsx  # 语音输入
└── package.json
```

## 6. 48小时开发路线

### 第一阶段（12小时）：基础框架
- [x] FastAPI 项目结构
- [x] WebSocket 通信
- [x] 基础前端框架
- [x] 语音识别集成

### 第二阶段（12小时）：核心功能
- [x] LLM 集成
- [x] Agent 架构
- [x] 记忆管理
- [x] 多轮对话

### 第三阶段（12小时）：图像生成
- [x] 图像生成模块
- [x] Prompt 工程
- [x] 图像展示
- [x] 多轮修改

### 第四阶段（12小时）：完善优化
- [ ] UI/UX 优化
- [ ] 错误处理
- [ ] 性能优化
- [ ] 测试部署
