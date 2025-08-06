"""
Modelos Pydantic para Chat
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    """Tipos de mensaje"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageRole(str, Enum):
    """Roles del mensaje para OpenAI"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Modelo de mensaje de chat"""
    id: Optional[str] = None
    user_id: str
    message: str = Field(..., max_length=2000)
    message_type: MessageType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('message')
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError('El mensaje no puede estar vacío')
        return v.strip()


class ChatMessageCreate(BaseModel):
    """Modelo para crear mensaje de chat"""
    message: str = Field(..., max_length=2000)
    user_context: Optional[Dict[str, Any]] = None
    
    @validator('message')
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError('El mensaje no puede estar vacío')
        return v.strip()


class ChatMessageResponse(BaseModel):
    """Respuesta del asistente"""
    message_id: str
    user_message: str
    assistant_response: str
    timestamp: datetime
    context_used: Optional[Dict[str, Any]] = None
    model_info: Optional[Dict[str, str]] = None


class ChatHistory(BaseModel):
    """Historial de chat"""
    user_id: str
    messages: List[ChatMessage]
    total_messages: int
    last_activity: datetime


class ChatSession(BaseModel):
    """Sesión de chat"""
    session_id: str
    user_id: str
    created_at: datetime
    last_activity: datetime
    messages_count: int = 0
    is_active: bool = True


class OpenAIMessage(BaseModel):
    """Modelo para mensaje de OpenAI"""
    role: MessageRole
    content: str
    
    
class OpenAIResponse(BaseModel):
    """Respuesta de OpenAI"""
    id: str
    object: str
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]


class UserContext(BaseModel):
    """Contexto del usuario obtenido del backend principal"""
    user_id: str
    preferences: Optional[Dict[str, Any]] = None
    favorite_stocks: Optional[List[str]] = None
    risk_profile: Optional[str] = None
    investment_goals: Optional[List[str]] = None
    portfolio_value: Optional[float] = None
    last_login: Optional[datetime] = None


class WebSocketMessage(BaseModel):
    """Mensaje de WebSocket"""
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, str]
