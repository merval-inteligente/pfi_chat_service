"""
Modelos de Usuario
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class User(BaseModel):
    """Modelo de usuario básico"""
    user_id: str
    email: Optional[str] = None
    username: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen: Optional[datetime] = None


class UserProfile(BaseModel):
    """Perfil completo del usuario"""
    user_id: str
    email: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    is_premium: bool = False
    
    
class TokenPayload(BaseModel):
    """Payload del JWT token"""
    sub: str  # user_id
    exp: Optional[int] = None
    iat: Optional[int] = None
    iss: Optional[str] = None
