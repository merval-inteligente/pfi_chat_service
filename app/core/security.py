"""
Seguridad y autenticación
"""
from typing import Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..services.auth_service import auth_service
from ..models.user import TokenPayload


# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenPayload:
    """
    Dependency para obtener el usuario actual desde el JWT
    
    Args:
        credentials: Credenciales de autorización
        
    Returns:
        Payload del token
        
    Raises:
        HTTPException: Si el token es inválido
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autorización requerido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_payload = auth_service.verify_token(credentials.credentials)
    
    if not token_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_payload


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[TokenPayload]:
    """
    Dependency para obtener el usuario actual de forma opcional
    
    Args:
        credentials: Credenciales de autorización (opcional)
        
    Returns:
        Payload del token o None
    """
    if not credentials:
        return None
    
    return auth_service.verify_token(credentials.credentials)


def verify_user_access(current_user: TokenPayload, required_user_id: str) -> bool:
    """
    Verifica que el usuario actual tenga acceso al recurso del usuario requerido
    
    Args:
        current_user: Usuario actual del token
        required_user_id: ID del usuario requerido
        
    Returns:
        True si tiene acceso
        
    Raises:
        HTTPException: Si no tiene acceso
    """
    if not auth_service.validate_user_access(current_user, required_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para acceder a este recurso"
        )
    
    return True
