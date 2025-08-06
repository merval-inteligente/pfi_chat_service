"""
Servicio de autenticación y validación JWT
"""
from typing import Optional
from jose import JWTError, jwt
from datetime import datetime, timedelta
from loguru import logger

from ..simple_config import get_simple_settings
from ..models.user import TokenPayload


class AuthService:
    """Servicio de autenticación"""
    
    def __init__(self):
        self.settings = get_simple_settings()
    
    def verify_token(self, token: str) -> Optional[TokenPayload]:
        """
        Verifica y decodifica un JWT token
        
        Args:
            token: Token JWT a verificar
            
        Returns:
            Payload del token o None si es inválido
        """
        try:
            # Decodificar token
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm]
            )
            
            # Verificar expiración
            exp = payload.get("exp")
            if exp is None:
                logger.warning("Token sin fecha de expiración")
                return None
            
            if datetime.utcnow() > datetime.fromtimestamp(exp):
                logger.warning("Token expirado")
                return None
            
            # Verificar que tenga user_id
            user_id = payload.get("sub")
            if user_id is None:
                logger.warning("Token sin user_id")
                return None
            
            return TokenPayload(
                sub=user_id,
                exp=exp,
                iat=payload.get("iat"),
                iss=payload.get("iss")
            )
            
        except JWTError as e:
            logger.warning(f"Error al decodificar JWT: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado al verificar token: {str(e)}")
            return None
    
    def extract_token_from_header(self, authorization: Optional[str]) -> Optional[str]:
        """
        Extrae el token del header Authorization
        
        Args:
            authorization: Header Authorization
            
        Returns:
            Token extraído o None
        """
        if not authorization:
            return None
        
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                return None
            return token
        except ValueError:
            return None
    
    def create_access_token(self, user_id: str, expires_delta: Optional[timedelta] = None) -> str:
        """
        Crea un nuevo access token (para testing o casos especiales)
        
        Args:
            user_id: ID del usuario
            expires_delta: Tiempo de expiración personalizado
            
        Returns:
            Token JWT generado
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.settings.jwt_access_token_expire_minutes
            )
        
        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "iss": self.settings.app_name
        }
        
        encoded_jwt = jwt.encode(
            payload,
            self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm
        )
        
        return encoded_jwt
    
    def validate_user_access(self, token_payload: TokenPayload, required_user_id: str) -> bool:
        """
        Valida que el token pertenezca al usuario requerido
        
        Args:
            token_payload: Payload del token
            required_user_id: ID del usuario requerido
            
        Returns:
            True si el acceso es válido
        """
        return token_payload.sub == required_user_id


# Singleton instance
auth_service = AuthService()
