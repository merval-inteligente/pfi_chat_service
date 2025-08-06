"""
Dependencias de la API
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import asyncio

from ..core.auth import get_current_user, get_current_active_user
from ..models.user import User
from ..models.chat import UserContext
from ..services.context_service import context_service
from ..services.memory_service import memory_service
from ..config import get_settings


# Rate Limiter
settings = get_settings()
limiter = Limiter(key_func=get_remote_address)


async def get_rate_limiter():
    """Dependency para rate limiting"""
    return limiter


async def get_user_context(
    current_user: User = Depends(get_current_user),
    authorization: str = Depends()
) -> Optional[UserContext]:
    """
    Dependency para obtener contexto del usuario
    
    Args:
        current_user: Usuario actual del token
        authorization: Header de autorización
        
    Returns:
        Contexto del usuario o None
    """
    try:
        # Extraer token del header
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
            context = await context_service.get_user_context(current_user.user_id, token)
            return context
        return None
    except Exception:
        # Si falla obtener contexto, continuamos sin él
        return None


async def verify_chat_access(
    user_id: str,
    current_user: User = Depends(get_current_user)
) -> bool:
    """
    Verifica que el usuario tenga acceso al chat especificado
    
    Args:
        user_id: ID del usuario del chat
        current_user: Usuario actual del token
        
    Returns:
        True si tiene acceso
        
    Raises:
        HTTPException: Si no tiene acceso
    """
    if current_user.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para acceder a este chat"
        )
    return True


async def get_chat_session(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene o crea una sesión de chat para el usuario
    
    Args:
        user_id: ID del usuario
        current_user: Usuario actual del token
        
    Returns:
        Sesión de chat
    """
    # Verificar acceso
    await verify_chat_access(user_id, current_user)
    
    # Obtener o crear sesión
    session = await memory_service.get_session(user_id)
    if not session:
        session = await memory_service.create_session(user_id)
    
    return session


class RateLimitDep:
    """Dependency class para rate limiting personalizado"""
    
    def __init__(self, requests: int = None, window: int = None):
        self.requests = requests or settings.rate_limit_requests
        self.window = window or settings.rate_limit_window
        
    def __call__(self, request):
        return limiter.limit(f"{self.requests}/{self.window}seconds")(request)


# Rate limiting preconfigurado para diferentes endpoints
chat_rate_limit = RateLimitDep(requests=20, window=60)  # 20 mensajes por minuto
history_rate_limit = RateLimitDep(requests=10, window=60)  # 10 consultas por minuto
general_rate_limit = RateLimitDep(requests=100, window=60)  # 100 requests por minuto
