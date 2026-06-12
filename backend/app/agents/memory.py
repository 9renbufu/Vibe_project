"""
Design Memory Agent - 设计记忆系统
支持短期记忆、长期记忆、设计历史、版本管理、Prompt注入
"""

import json
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from .base import BaseAgent, AgentResult
from .state import AgentState


@dataclass
class ShortTermMemory:
    """短期记忆 - 当前会话"""
    session_id: str = ""
    current_style: str = ""
    current_mood: str = ""
    current_industry: str = ""
    current_elements: List[str] = field(default_factory=list)
    current_colors: List[str] = field(default_factory=list)
    conversation_context: List[Dict[str, str]] = field(default_factory=list)
    recent_plans: List[Dict[str, Any]] = field(default_factory=list)
    user_feedback: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class LongTermMemory:
    """长期记忆 - 跨会话持久化"""
    favorite_style: str = ""
    favorite_styles: List[str] = field(default_factory=list)
    favorite_colors: List[str] = field(default_factory=list)
    industry: str = ""
    brand_name: str = ""
    brand_keywords: List[str] = field(default_factory=list)
    target_audience: str = ""
    design_preferences: Dict[str, Any] = field(default_factory=dict)
    successful_designs: List[Dict[str, Any]] = field(default_factory=list)
    rejected_designs: List[Dict[str, Any]] = field(default_factory=list)
    total_designs: int = 0
    average_score: float = 0.0
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class DesignHistory:
    """设计历史记录"""
    id: str = ""
    session_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    user_input: str = ""
    style: str = ""
    elements: List[str] = field(default_factory=list)
    prompt: str = ""
    image_url: str = ""
    evaluation_score: float = 0.0
    evaluation_feedback: str = ""
    version: int = 1
    is_favorite: bool = False
    tags: List[str] = field(default_factory=list)


@dataclass
class DesignVersion:
    """设计版本"""
    id: str = ""
    design_id: str = ""
    version: int = 1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    prompt: str = ""
    image_base64: str = ""
    changes: List[str] = field(default_factory=list)
    evaluation: Optional[Dict[str, Any]] = None


class DesignMemoryAgent(BaseAgent):
    """设计记忆 Agent - 管理用户设计偏好和历史"""

    MEMORY_DIR = Path(__file__).parent.parent.parent / "data" / "memory"

    def __init__(self, llm_client=None):
        super().__init__(llm_client)
        self.MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory()
        self.history: List[DesignHistory] = []
        self.versions: Dict[str, List[DesignVersion]] = {}
        self._load_long_term_memory()

    def _load_long_term_memory(self):
        """加载长期记忆"""
        memory_file = self.MEMORY_DIR / "long_term_memory.json"
        if memory_file.exists():
            try:
                with open(memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.long_term = LongTermMemory(**data)
            except Exception as e:
                print(f"[MemoryAgent] Load error: {e}")

    def _save_long_term_memory(self):
        """保存长期记忆"""
        memory_file = self.MEMORY_DIR / "long_term_memory.json"
        try:
            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.long_term), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[MemoryAgent] Save error: {e}")

    def _load_history(self, session_id: str = None) -> List[Dict]:
        """加载设计历史"""
        history_file = self.MEMORY_DIR / "design_history.json"
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if session_id:
                        return [h for h in data if h.get('session_id') == session_id]
                    return data[-100:]  # 返回最近100条
            except Exception as e:
                print(f"[MemoryAgent] Load history error: {e}")
        return []

    def _save_history(self, record: Dict):
        """保存设计历史"""
        history_file = self.MEMORY_DIR / "design_history.json"
        try:
            history = []
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            history.append(record)
            # 只保留最近500条
            history = history[-500:]
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[MemoryAgent] Save history error: {e}")

    async def execute(self, state: AgentState, action: str = "update", **kwargs) -> AgentResult:
        """
        执行记忆操作

        action: update | query | inject | analyze
        """
        try:
            if action == "update":
                return await self._update_memory(state, **kwargs)
            elif action == "query":
                return await self._query_memory(**kwargs)
            elif action == "inject":
                return await self._inject_memory(state, **kwargs)
            elif action == "analyze":
                return await self._analyze_preferences(state, **kwargs)
            else:
                return AgentResult(
                    success=False,
                    data={},
                    message=f"Unknown action: {action}",
                )
        except Exception as e:
            return AgentResult(
                success=False,
                data={},
                message=self._format_error(e),
            )

    async def _update_memory(self, state: AgentState, **kwargs) -> AgentResult:
        """更新记忆"""
        # 更新短期记忆
        self.short_term.session_id = state.session_id
        self.short_term.current_style = state.requirement.style
        self.short_term.current_mood = state.requirement.mood
        self.short_term.current_industry = state.requirement.industry
        self.short_term.current_elements = state.requirement.elements
        self.short_term.current_colors = state.requirement.colors

        # 添加对话上下文
        if state.conversation_history:
            self.short_term.conversation_context = state.conversation_history[-5:]

        # 如果有评估结果，更新长期记忆
        if state.evaluation:
            score = state.evaluation.overall
            if score >= 70:
                # 成功的设计
                design_record = {
                    "style": state.requirement.style,
                    "elements": state.requirement.elements,
                    "colors": state.requirement.colors,
                    "score": score,
                    "timestamp": datetime.now().isoformat(),
                }
                self.long_term.successful_designs.append(design_record)
                self.long_term.successful_designs = self.long_term.successful_designs[-20:]

                # 更新偏好
                self._update_preferences(state)
            else:
                # 被拒绝的设计
                design_record = {
                    "style": state.requirement.style,
                    "score": score,
                    "feedback": state.evaluation.feedback,
                    "timestamp": datetime.now().isoformat(),
                }
                self.long_term.rejected_designs.append(design_record)
                self.long_term.rejected_designs = self.long_term.rejected_designs[-10:]

        # 更新统计
        self.long_term.total_designs += 1
        if state.evaluation:
            total = self.long_term.total_designs
            current_avg = self.long_term.average_score
            self.long_term.average_score = (
                (current_avg * (total - 1) + state.evaluation.overall) / total
            )

        self.long_term.last_updated = datetime.now().isoformat()
        self._save_long_term_memory()

        # 保存设计历史
        if state.current_version:
            history_record = {
                "id": state.current_version.id,
                "session_id": state.session_id,
                "timestamp": datetime.now().isoformat(),
                "user_input": state.requirement.original_text,
                "style": state.requirement.style,
                "elements": state.requirement.elements,
                "prompt": state.current_version.prompt,
                "evaluation_score": state.evaluation.overall if state.evaluation else 0,
                "evaluation_feedback": state.evaluation.feedback if state.evaluation else "",
                "version": state.current_version.version,
            }
            self._save_history(history_record)

        return AgentResult(
            success=True,
            data={
                "short_term": asdict(self.short_term),
                "long_term_summary": {
                    "favorite_style": self.long_term.favorite_style,
                    "favorite_colors": self.long_term.favorite_colors,
                    "industry": self.long_term.industry,
                    "total_designs": self.long_term.total_designs,
                    "average_score": round(self.long_term.average_score, 1),
                },
            },
            message="Memory updated successfully",
        )

    def _update_preferences(self, state: AgentState):
        """更新用户偏好"""
        style = state.requirement.style
        colors = state.requirement.colors
        industry = state.requirement.industry

        # 更新风格偏好
        if style:
            if style not in self.long_term.favorite_styles:
                self.long_term.favorite_styles.append(style)
            self.long_term.favorite_style = style

        # 更新颜色偏好
        for color in colors:
            if color not in self.long_term.favorite_colors:
                self.long_term.favorite_colors.append(color)
        # 只保留前10个颜色
        self.long_term.favorite_colors = self.long_term.favorite_colors[:10]

        # 更新行业
        if industry:
            self.long_term.industry = industry

    async def _query_memory(self, query_type: str = "all", **kwargs) -> AgentResult:
        """查询记忆"""
        result = {}

        if query_type in ("all", "short_term"):
            result["short_term"] = asdict(self.short_term)

        if query_type in ("all", "long_term"):
            result["long_term"] = asdict(self.long_term)

        if query_type in ("all", "history"):
            session_id = kwargs.get("session_id")
            result["history"] = self._load_history(session_id)

        if query_type == "preferences":
            result["preferences"] = {
                "favorite_style": self.long_term.favorite_style,
                "favorite_styles": self.long_term.favorite_styles,
                "favorite_colors": self.long_term.favorite_colors,
                "industry": self.long_term.industry,
                "brand_name": self.long_term.brand_name,
                "target_audience": self.long_term.target_audience,
                "design_preferences": self.long_term.design_preferences,
            }

        return AgentResult(
            success=True,
            data=result,
            message=f"Query {query_type} completed",
        )

    async def _inject_memory(self, state: AgentState, prompt_type: str = "full", **kwargs) -> AgentResult:
        """
        注入记忆到提示词

        prompt_type: full | style | colors | history
        """
        injection = self._build_memory_injection(prompt_type)

        return AgentResult(
            success=True,
            data={"injection": injection},
            message="Memory injection prepared",
        )

    def _build_memory_injection(self, prompt_type: str = "full") -> str:
        """构建记忆注入文本"""
        parts = []

        if prompt_type in ("full", "style"):
            if self.long_term.favorite_style:
                parts.append(f"用户偏好风格: {self.long_term.favorite_style}")
            if self.long_term.favorite_styles:
                parts.append(f"历史喜欢的风格: {', '.join(self.long_term.favorite_styles)}")

        if prompt_type in ("full", "colors"):
            if self.long_term.favorite_colors:
                parts.append(f"偏好颜色: {', '.join(self.long_term.favorite_colors)}")

        if prompt_type in ("full", "industry"):
            if self.long_term.industry:
                parts.append(f"行业领域: {self.long_term.industry}")
            if self.long_term.brand_name:
                parts.append(f"品牌名称: {self.long_term.brand_name}")
            if self.long_term.target_audience:
                parts.append(f"目标受众: {self.long_term.target_audience}")

        if prompt_type in ("full", "history"):
            if self.long_term.successful_designs:
                recent_success = self.long_term.successful_designs[-3:]
                styles = [d.get("style", "") for d in recent_success if d.get("style")]
                if styles:
                    parts.append(f"最近成功的设计风格: {', '.join(styles)}")

            if self.long_term.average_score > 0:
                parts.append(f"历史平均评分: {self.long_term.average_score:.1f}/100")

        # 短期记忆
        if prompt_type == "full":
            if self.short_term.current_style:
                parts.append(f"当前会话风格: {self.short_term.current_style}")
            if self.short_term.user_feedback:
                parts.append(f"用户反馈: {self.short_term.user_feedback[-1]}")

        if not parts:
            return ""

        return "\n用户设计偏好参考:\n" + "\n".join(f"- {p}" for p in parts)

    async def _analyze_preferences(self, state: AgentState, **kwargs) -> AgentResult:
        """分析用户偏好"""
        analysis = {
            "style_preference": self._analyze_style_preference(),
            "color_preference": self._analyze_color_preference(),
            "industry_focus": self.long_term.industry or "未指定",
            "design_quality": {
                "total_designs": self.long_term.total_designs,
                "average_score": round(self.long_term.average_score, 1),
                "success_rate": self._calculate_success_rate(),
            },
            "recommendations": self._generate_recommendations(),
        }

        return AgentResult(
            success=True,
            data=analysis,
            message="Preference analysis completed",
        )

    def _analyze_style_preference(self) -> Dict[str, Any]:
        """分析风格偏好"""
        if not self.long_term.successful_designs:
            return {"primary": "unknown", "confidence": 0}

        # 统计风格出现次数
        style_count = {}
        for design in self.long_term.successful_designs:
            style = design.get("style", "")
            if style:
                style_count[style] = style_count.get(style, 0) + 1

        if not style_count:
            return {"primary": "unknown", "confidence": 0}

        # 找出最常用的风格
        primary_style = max(style_count, key=style_count.get)
        total = sum(style_count.values())
        confidence = style_count[primary_style] / total if total > 0 else 0

        return {
            "primary": primary_style,
            "secondary": [s for s, _ in sorted(style_count.items(), key=lambda x: x[1], reverse=True)[1:3]],
            "confidence": round(confidence, 2),
            "distribution": style_count,
        }

    def _analyze_color_preference(self) -> Dict[str, Any]:
        """分析颜色偏好"""
        if not self.long_term.favorite_colors:
            return {"primary": [], "confidence": 0}

        return {
            "primary": self.long_term.favorite_colors[:3],
            "all": self.long_term.favorite_colors,
            "count": len(self.long_term.favorite_colors),
        }

    def _calculate_success_rate(self) -> float:
        """计算成功率"""
        if self.long_term.total_designs == 0:
            return 0.0
        success_count = len(self.long_term.successful_designs)
        return round(success_count / self.long_term.total_designs, 2)

    def _generate_recommendations(self) -> List[str]:
        """生成推荐"""
        recommendations = []

        # 基于风格偏好推荐
        if self.long_term.favorite_style:
            recommendations.append(f"继续使用 {self.long_term.favorite_style} 风格")

        # 基于成功率推荐
        success_rate = self._calculate_success_rate()
        if success_rate < 0.5:
            recommendations.append("尝试更明确的设计需求描述")
        elif success_rate > 0.8:
            recommendations.append("可以尝试更多创新风格")

        # 基于评分推荐
        if self.long_term.average_score < 70:
            recommendations.append("提供更多设计细节有助于提高质量")

        return recommendations

    def get_prompt_injection(self) -> str:
        """获取用于提示词注入的记忆文本"""
        return self._build_memory_injection("full")

    def start_new_session(self, session_id: str):
        """开始新会话"""
        self.short_term = ShortTermMemory(session_id=session_id)

    def add_user_feedback(self, feedback: str):
        """添加用户反馈"""
        self.short_term.user_feedback.append(feedback)
        self.short_term.user_feedback = self.short_term.user_feedback[-10:]
