from pydantic import BaseModel
from typing import Dict

class ChatMessage(BaseModel):
    """Modelo para mensajes entrantes de chat - solo el mensaje, user_id se obtiene del token"""
    message: str

class ChatResponse(BaseModel):
    """Modelo para respuestas del chat"""
    response: str
    user_id: str
    user_name: str
    message_id: str
    timestamp: str
    storage_info: Dict[str, bool]
