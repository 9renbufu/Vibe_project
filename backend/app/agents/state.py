"""
Agent 状态管理
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid


class DesignStage(str, Enum):
    """设计阶段"""
    IDLE = "idle"
    REQUIREMENT = "requirement"
    PLANNING = "planning"
    GENERATING = "generating"
    EVALUATING = "evaluating"
    REVISING = "revising"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class DesignPlan:
    """设计方案"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    style: str = ""
    elements: List[str] = field(default_factory=list)
    color_palette: List[str] = field(default_factory=list)
    mood: str = ""
    composition: str = ""
    score: float = 0.0
    selected: bool = False


@dataclass
class DesignVersion:
    """设计版本"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    version: int = 1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    image_url: str = ""
    image_base64: str = ""
    prompt: str = ""
    plan_id: str = ""
    changes: List[str] = field(default_factory=list)
    evaluation: Optional[Dict[str, Any]] = None


@dataclass
class Evaluation:
    """设计评估"""
    brand_consistency: float = 0.0
    creativity: float = 0.0
    commercial_value: float = 0.0
    aesthetics: float = 0.0
    overall: float = 0.0
    feedback: str = ""
    suggestions: List[str] = field(default_factory=list)


@dataclass
class Requirement:
    """用户需求"""
    original_text: str = ""
    intent: str = ""
    style: str = ""
    mood: str = ""
    industry: str = ""
    target_users: str = ""
    elements: List[str] = field(default_factory=list)
    colors: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)


@dataclass
class AgentState:
    """Agent 状态"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    stage: DesignStage = DesignStage.IDLE
    requirement: Requirement = field(default_factory=Requirement)
    plans: List[DesignPlan] = field(default_factory=list)
    current_plan: Optional[DesignPlan] = None
    versions: List[DesignVersion] = field(default_factory=list)
    current_version: Optional[DesignVersion] = None
    evaluation: Optional[Evaluation] = None
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    memory: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def add_message(self, role: str, content: str):
        """添加对话历史"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })

    def add_plan(self, plan: DesignPlan):
        """添加设计方案"""
        self.plans.append(plan)

    def select_plan(self, plan_id: str):
        """选择设计方案"""
        for plan in self.plans:
            plan.selected = plan.id == plan_id
            if plan.selected:
                self.current_plan = plan

    def add_version(self, version: DesignVersion):
        """添加设计版本"""
        self.versions.append(version)
        self.current_version = version

    def get_latest_version(self) -> Optional[DesignVersion]:
        """获取最新版本"""
        return self.versions[-1] if self.versions else None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "stage": self.stage.value,
            "requirement": {
                "original_text": self.requirement.original_text,
                "intent": self.requirement.intent,
                "style": self.requirement.style,
                "mood": self.requirement.mood,
                "industry": self.requirement.industry,
                "elements": self.requirement.elements,
                "keywords": self.requirement.keywords,
            },
            "plans": [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "style": p.style,
                    "elements": p.elements,
                    "score": p.score,
                    "selected": p.selected,
                }
                for p in self.plans
            ],
            "current_plan": {
                "id": self.current_plan.id,
                "name": self.current_plan.name,
                "description": self.current_plan.description,
            } if self.current_plan else None,
            "versions": [
                {
                    "id": v.id,
                    "version": v.version,
                    "timestamp": v.timestamp,
                    "prompt": v.prompt,
                    "changes": v.changes,
                }
                for v in self.versions
            ],
            "evaluation": {
                "overall": self.evaluation.overall,
                "feedback": self.evaluation.feedback,
                "suggestions": self.evaluation.suggestions,
            } if self.evaluation else None,
            "memory": self.memory,
        }
