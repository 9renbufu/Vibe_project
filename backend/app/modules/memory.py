"""
多轮对话记忆管理模块
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque


@dataclass
class MemoryEntry:
    """记忆条目"""
    timestamp: str
    role: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConversationMemory:
    """对话记忆管理器"""

    def __init__(self, max_short_term: int = 10, max_long_term: int = 50):
        self.short_term: deque[MemoryEntry] = deque(maxlen=max_short_term)
        self.long_term: List[MemoryEntry] = []
        self.max_long_term = max_long_term
        self.entity_memory: Dict[str, Any] = {}  # 实体记忆

    def add(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """添加记忆"""
        entry = MemoryEntry(
            timestamp=datetime.now().isoformat(),
            role=role,
            content=content,
            metadata=metadata or {},
        )
        self.short_term.append(entry)

        # 重要信息存入长期记忆
        if self._is_important(content):
            self.long_term.append(entry)
            if len(self.long_term) > self.max_long_term:
                self.long_term.pop(0)

        # 提取实体信息
        self._extract_entities(content)

    def get_short_term(self, n: int = None) -> List[Dict[str, str]]:
        """获取短期记忆"""
        entries = list(self.short_term)
        if n:
            entries = entries[-n:]
        return [{"role": e.role, "content": e.content} for e in entries]

    def get_long_term_summary(self) -> str:
        """获取长期记忆摘要"""
        if not self.long_term:
            return "暂无历史记忆"

        summaries = []
        for entry in self.long_term[-5:]:
            summaries.append(f"[{entry.role}] {entry.content[:50]}...")
        return "\n".join(summaries)

    def get_entity(self, key: str) -> Any:
        """获取实体信息"""
        return self.entity_memory.get(key)

    def set_entity(self, key: str, value: Any):
        """设置实体信息"""
        self.entity_memory[key] = value

    def _is_important(self, content: str) -> bool:
        """判断是否重要信息"""
        important_keywords = [
            "风格", "颜色", "要求", "设计", "元素",
            "背景", "主题", "品牌", "目标", "用户",
        ]
        return any(keyword in content for keyword in important_keywords)

    def _extract_entities(self, content: str):
        """提取实体信息"""
        # 简单的实体提取
        if "风格" in content:
            self.entity_memory["last_style_mention"] = content
        if "颜色" in content or "色" in content:
            self.entity_memory["last_color_mention"] = content

    def clear(self):
        """清空记忆"""
        self.short_term.clear()
        self.long_term.clear()
        self.entity_memory.clear()

    def to_dict(self) -> Dict[str, Any]:
        """导出为字典"""
        return {
            "short_term": [
                {
                    "timestamp": e.timestamp,
                    "role": e.role,
                    "content": e.content,
                }
                for e in self.short_term
            ],
            "long_term_count": len(self.long_term),
            "entities": self.entity_memory,
        }


class DesignMemory:
    """设计专用记忆管理"""

    def __init__(self):
        self.conversation = ConversationMemory()
        self.design_history: List[Dict[str, Any]] = []
        self.user_preferences: Dict[str, Any] = {}

    def add_design_iteration(self, iteration: Dict[str, Any]):
        """添加设计迭代"""
        iteration["timestamp"] = datetime.now().isoformat()
        self.design_history.append(iteration)

    def get_latest_design(self) -> Optional[Dict[str, Any]]:
        """获取最新设计"""
        return self.design_history[-1] if self.design_history else None

    def update_preferences(self, preferences: Dict[str, Any]):
        """更新用户偏好"""
        self.user_preferences.update(preferences)

    def get_preferences(self) -> Dict[str, Any]:
        """获取用户偏好"""
        return self.user_preferences

    def get_context_for_llm(self) -> str:
        """获取 LLM 上下文"""
        context_parts = []

        # 用户偏好
        if self.user_preferences:
            context_parts.append(f"用户偏好: {json.dumps(self.user_preferences, ensure_ascii=False)}")

        # 最近的设计历史
        if self.design_history:
            latest = self.design_history[-1]
            context_parts.append(f"最近设计: {json.dumps(latest, ensure_ascii=False)[:200]}")

        # 对话摘要
        context_parts.append(f"对话摘要: {self.conversation.get_long_term_summary()}")

        return "\n\n".join(context_parts)

    def clear(self):
        """清空所有记忆"""
        self.conversation.clear()
        self.design_history.clear()
        self.user_preferences.clear()

    def to_dict(self) -> Dict[str, Any]:
        """导出状态"""
        return {
            "conversation": self.conversation.to_dict(),
            "design_history_count": len(self.design_history),
            "preferences": self.user_preferences,
        }
