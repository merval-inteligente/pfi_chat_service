"""
Servicio para obtener contexto del usuario desde el backend principal
"""
import httpx
from typing import Optional, Dict, Any
from loguru import logger

from ..config import get_settings
from ..models.chat import UserContext


class ContextService:
    """Servicio para obtener contexto del usuario"""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.main_backend_url
        self.timeout = self.settings.main_backend_timeout
        
    async def get_user_context(self, user_id: str, auth_token: str) -> Optional[UserContext]:
        """
        Obtiene el contexto del usuario desde el backend principal
        
        Args:
            user_id: ID del usuario
            auth_token: Token de autenticación
            
        Returns:
            Contexto del usuario o None si hay error
        """
        try:
            headers = {
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Obtener información básica del usuario
                user_response = await client.get(
                    f"{self.base_url}/api/users/{user_id}",
                    headers=headers
                )
                
                if user_response.status_code != 200:
                    logger.warning(f"No se pudo obtener info del usuario {user_id}")
                    return None
                
                user_data = user_response.json()
                
                # Obtener preferencias de inversión
                preferences_response = await client.get(
                    f"{self.base_url}/api/users/{user_id}/preferences",
                    headers=headers
                )
                
                preferences = preferences_response.json() if preferences_response.status_code == 200 else {}
                
                # Obtener stocks favoritos
                favorites_response = await client.get(
                    f"{self.base_url}/api/users/{user_id}/favorites",
                    headers=headers
                )
                
                favorites = favorites_response.json() if favorites_response.status_code == 200 else []
                
                # Obtener información del portfolio
                portfolio_response = await client.get(
                    f"{self.base_url}/api/users/{user_id}/portfolio",
                    headers=headers
                )
                
                portfolio = portfolio_response.json() if portfolio_response.status_code == 200 else {}
                
                # Construir contexto
                context = UserContext(
                    user_id=user_id,
                    preferences=preferences.get("data", {}),
                    favorite_stocks=favorites.get("stocks", []),
                    risk_profile=preferences.get("data", {}).get("risk_profile"),
                    investment_goals=preferences.get("data", {}).get("goals", []),
                    portfolio_value=portfolio.get("total_value"),
                    last_login=user_data.get("last_login")
                )
                
                logger.info(f"Contexto obtenido para usuario {user_id}")
                return context
                
        except httpx.TimeoutException:
            logger.error(f"Timeout al obtener contexto del usuario {user_id}")
            return None
            
        except httpx.RequestError as e:
            logger.error(f"Error de conexión al obtener contexto: {str(e)}")
            return None
            
        except Exception as e:
            logger.error(f"Error inesperado al obtener contexto: {str(e)}")
            return None
    
    async def get_market_data(self, symbols: Optional[list] = None) -> Dict[str, Any]:
        """
        Obtiene datos de mercado actuales
        
        Args:
            symbols: Lista de símbolos a consultar
            
        Returns:
            Datos de mercado
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.base_url}/api/market/current"
                if symbols:
                    url += f"?symbols={','.join(symbols)}"
                
                response = await client.get(url)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning("No se pudieron obtener datos de mercado")
                    return {}
                    
        except Exception as e:
            logger.error(f"Error al obtener datos de mercado: {str(e)}")
            return {}
    
    async def get_user_portfolio_summary(self, user_id: str, auth_token: str) -> Dict[str, Any]:
        """
        Obtiene resumen del portfolio del usuario
        
        Args:
            user_id: ID del usuario
            auth_token: Token de autenticación
            
        Returns:
            Resumen del portfolio
        """
        try:
            headers = {
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/users/{user_id}/portfolio/summary",
                    headers=headers
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {}
                    
        except Exception as e:
            logger.error(f"Error al obtener resumen del portfolio: {str(e)}")
            return {}
    
    async def get_news_sentiment(self) -> Dict[str, Any]:
        """
        Obtiene análisis de sentimiento de noticias financieras
        
        Returns:
            Análisis de sentimiento de noticias
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/market/news/sentiment"
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"sentiment": "neutral", "score": 0.5}
                    
        except Exception as e:
            logger.error(f"Error al obtener sentimiento de noticias: {str(e)}")
            return {"sentiment": "neutral", "score": 0.5}


# Singleton instance
context_service = ContextService()
