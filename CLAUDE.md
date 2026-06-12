# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Voice Designer Agent -- an AI-powered design assistant that accepts voice or text input, then runs a multi-agent pipeline: requirement analysis, design planning, prompt generation, image generation, evaluation, and optional revision. UI and comments are in Chinese; code identifiers are in English.

## Commands

### Backend (FastAPI + Python 3.11+)
```bash
cd backend
conda activate voicesketch
pip install -r requirements.txt
cp .env.example .env   # configure API keys in .env
python run.py          # uvicorn on port 8000 with --reload
```

### Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev       # dev server on port 3000
npm run build     # tsc && vite build -> frontend/dist/
npm run preview   # preview production build
```

### Docker
```bash
docker-compose up   # backend:8000 + frontend:80 (nginx)
```

### Windows Quick Start
`start.bat` launches both backend and frontend in separate cmd windows.

## Architecture

### Active Code vs Legacy

The current version is **v4**. Only these paths are actively used:
- `backend/app/main_v4.py` -- FastAPI app entry point (launched by `run.py`)
- `backend/app/agents/` -- the multi-agent system
- `backend/app/modules/` -- LLM client factory, image generation factory
- `frontend/src/App.tsx`, `frontend/src/components/AgentWorkspace/` -- current UI

Legacy files (`main.py`, `main_v2.py`, `main_v3.py`, `backend/app/agent/`, older frontend components) still exist but are not used by the active entry point.

### Backend Agent Pipeline

`AgentOrchestrator` (`agents/orchestrator.py`) coordinates a sequential pipeline:

```
User input
  -> RequirementAgent   (intent analysis, style/mood/industry extraction)
  -> PlanningAgent      (generates 3 differentiated design plans)
  -> PromptAgent        (converts selected plan into image-generation prompt)
  -> GenerationAgent    (calls image API, returns base64 image)
  -> CriticAgent        (4-dimension evaluation: brand consistency, creativity, commercial value, visual impact)
  -> [if score low: RevisionAgent -> re-Prompt -> re-Generate -> re-Critic]
  -> DesignMemoryAgent  (short-term + long-term memory, preference persistence)
  -> Complete
```

Each agent extends `BaseAgent` (`agents/base.py`) which provides `_call_llm()` and `_call_llm_json()` helpers. State flows through `AgentState` dataclass (`agents/state.py`) with stages: idle -> requirement -> planning -> generating -> evaluating -> (revising) -> completed.

### Multi-Provider Support

- **LLM providers** via `LLMClientFactory` (`modules/llm_client.py`): DeepSeek (recommended), Claude, OpenAI, Qwen, Zhipu GLM, Moonshot, Ollama. Controlled by `LLM_PROVIDER` env var.
- **Image providers** via `ImageGeneratorFactory` (`modules/image_gen.py`): DALL-E 3/GPT-Image, Qwen WanX, Zhipu CogView. Controlled by `IMAGE_PROVIDER` env var.

### Frontend Architecture

- **React 18 + TypeScript + Vite**
- **Single Zustand store** (`store/agentStore.ts`) manages all state: messages, pipeline steps, design memory, plans, versions, evaluation, thinking logs, preferences, connection state, image data.
- **WebSocket** at `/ws` is the primary communication channel (JSON messages defined in `backend/app/protocol.py`).
- **Voice recognition** via Web Speech API (`zh-CN`), handled in `ConversationPanel.tsx`.
- **Inline CSS** -- all styles are `Record<string, React.CSSProperties>` objects. No CSS framework.
- **Three-column layout**: ConversationPanel (340px) | DesignWorkspace (flex) | AgentPanel (280px).

### Key Environment Variables (backend/.env)

`LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL`, `LLM_BASE_URL` for LLM configuration.
`IMAGE_PROVIDER`, `IMAGE_API_KEY` for image generation.
See `.env.example` for the full list.

## Important Notes

- **No tests exist.** No test files, no test framework, no test scripts.
- **`backend/data/`** directory stores persistent memory (design history, user preferences) at runtime.
- **Dev proxy**: Vite proxies `/api` to `localhost:8000` and `/ws` to `ws://localhost:8000` during development.
