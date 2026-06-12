"""
WebSocket 消息协议定义
"""

from typing import Any, Optional, List, Dict
from pydantic import BaseModel
from enum import Enum


class MessageType(str, Enum):
    """消息类型"""
    # 客户端 -> 服务端
    VOICE_INPUT = "voice_input"          # 语音输入
    TEXT_INPUT = "text_input"            # 文本输入
    ACTION_REQUEST = "action_request"    # 操作请求
    GET_STATE = "get_state"              # 获取状态

    # 服务端 -> 客户端
    AGENT_RESPONSE = "agent_response"    # Agent 回复
    IMAGE_RESULT = "image_result"        # 图像生成结果
    STATE_UPDATE = "state_update"        # 状态更新
    ERROR = "error"                      # 错误信息
    STATUS = "status"                    # 状态信息


class VoiceInputMessage(BaseModel):
    """语音输入消息"""
    type: str = "voice_input"
    data: Dict[str, Any]


class AgentResponseMessage(BaseModel):
    """Agent 回复消息"""
    type: str = "agent_response"
    data: Dict[str, Any]


class ImageResultMessage(BaseModel):
    """图像结果消息"""
    type: str = "image_result"
    data: Dict[str, Any]


class StateUpdateMessage(BaseModel):
    """状态更新消息"""
    type: str = "state_update"
    data: Dict[str, Any]


class ErrorMessage(BaseModel):
    """错误消息"""
    type: str = "error"
    data: Dict[str, str]


class StatusMessage(BaseModel):
    """状态消息"""
    type: str = "status"
    data: Dict[str, Any]


# 消息构造辅助函数

def create_agent_response(
    response: str,
    action: str = "ask",
    phase: str = "discussion",
    elements: List[Dict] = None,
    style: str = None,
    color_palette: List[str] = None,
) -> Dict[str, Any]:
    """创建 Agent 回复消息"""
    return {
        "type": "agent_response",
        "data": {
            "response": response,
            "action": action,
            "phase": phase,
            "elements": elements or [],
            "style": style,
            "color_palette": color_palette or [],
        }
    }


def create_image_result(
    image_base64: str,
    prompt: str,
    design_context: Dict = None,
) -> Dict[str, Any]:
    """创建图像结果消息"""
    return {
        "type": "image_result",
        "data": {
            "image": image_base64,
            "prompt": prompt,
            "design_context": design_context or {},
        }
    }


def create_state_update(state: Dict[str, Any]) -> Dict[str, Any]:
    """创建状态更新消息"""
    return {
        "type": "state_update",
        "data": state,
    }


def create_error(message: str) -> Dict[str, Any]:
    """创建错误消息"""
    return {
        "type": "error",
        "data": {"message": message},
    }


def create_status(status: str, message: str = "") -> Dict[str, Any]:
    """创建状态消息"""
    return {
        "type": "status",
        "data": {
            "status": status,
            "message": message,
        },
    }
