"""
Cliente para comunicarse con el backend principal
"""
import aiohttp
import asyncio
from typing import Optional, Dict, Any
from loguru import logger
from datetime import datetime


class MainBackendClient:
    """Cliente para comunicarse con el backend principal"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8080", timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _make_request(self, method: str, endpoint: str, headers: Dict = None, **kwargs) -> Optional[Dict]:
        """Realizar petición HTTP al backend principal Node.js"""
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
        
        url = f"{self.base_url}{endpoint}"
        default_headers = {
            "Content-Type": "application/json",
            "User-Agent": "ChatService-Microservice/1.0"
        }
        
        if headers:
            default_headers.update(headers)
        
        try:
            logger.debug(f"🔗 {method} {url}")
            async with self.session.request(method, url, headers=default_headers, **kwargs) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.debug(f"✅ Response: {response.status}")
                    return data
                else:
                    logger.warning(f"⚠️ Backend response: {response.status}")
                    return None
                    
        except asyncio.TimeoutError:
            logger.error(f"⏰ Timeout connecting to {url}")
            return None
        except Exception as e:
            logger.error(f"❌ Error connecting to backend: {e}")
            return None
    
    async def verify_token(self, token: str) -> Optional[Dict]:
        """Verificar token con el backend principal Node.js"""
        headers = {"Authorization": f"Bearer {token}"}
        return await self._make_request("GET", "/api/auth/verify", headers=headers)
    
    async def get_user_profile(self, user_id: str, token: str) -> Optional[Dict]:
        """Obtener perfil del usuario desde el backend principal"""
        headers = {"Authorization": f"Bearer {token}"}
        return await self._make_request("GET", "/api/auth/profile", headers=headers)
    
    async def get_user_preferences(self, user_id: str, token: str) -> Optional[Dict]:
        """Obtener preferencias del usuario (acciones favoritas, etc.)"""
        headers = {"Authorization": f"Bearer {token}"}
        return await self._make_request("GET", "/api/user/preferences", headers=headers)
    
    async def get_user_portfolio(self, user_id: str, token: str) -> Optional[Dict]:
        """Obtener información completa de stocks"""
        headers = {"Authorization": f"Bearer {token}"}
        return await self._make_request("GET", "/api/user/preferences/stocks/complete", headers=headers)
    
    async def log_chat_activity(self, user_id: str, activity_data: Dict, token: str) -> bool:
        """Registrar actividad del chat en el backend principal"""
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "userId": user_id,
            "activityType": "chat_interaction", 
            "data": activity_data,
            "timestamp": datetime.utcnow().isoformat(),
            "service": "chat_microservice"
        }
        
        # Nota: Necesitarás crear este endpoint en tu backend Node.js
        result = await self._make_request("POST", "/api/activity/log", headers=headers, json=payload)
        return result is not None
    
    async def health_check(self) -> bool:
        """Verificar si el backend principal está disponible"""
        result = await self._make_request("GET", "/api/base/health")
        return result is not None and result.get("status") == 200


# Instancia global
main_backend = MainBackendClient()


class BackendIntegrationService:
    """Servicio de integración con el backend principal Node.js"""
    
    @staticmethod
    async def get_user_context(user_id: str, token: str) -> Dict[str, Any]:
        """Obtener contexto completo del usuario para personalizar respuestas"""
        context = {
            "user_id": user_id,
            "profile": None,
            "preferences": None,
            "portfolio": None,
            "timestamp": datetime.utcnow().isoformat(),
            "backend_type": "nodejs_express"
        }
        
        async with MainBackendClient() as client:
            # Obtener perfil del usuario
            profile = await client.get_user_profile(user_id, token)
            if profile and profile.get("data"):
                context["profile"] = profile["data"]["user"]
            
            # Obtener preferencias (acciones favoritas)
            preferences = await client.get_user_preferences(user_id, token)
            if preferences and preferences.get("data"):
                context["preferences"] = preferences["data"]["preferences"]
            
            # Obtener información completa de stocks
            portfolio = await client.get_user_portfolio(user_id, token)
            if portfolio and portfolio.get("data"):
                context["portfolio"] = portfolio["data"]
        
        return context
    
    @staticmethod
    async def log_chat_session(user_id: str, session_data: Dict, token: str) -> bool:
        """Registrar sesión de chat en el backend principal"""
        async with MainBackendClient() as client:
            return await client.log_chat_activity(user_id, session_data, token)
    
    @staticmethod
    async def verify_backend_connection() -> bool:
        """Verificar conexión con el backend principal"""
        async with MainBackendClient() as client:
            return await client.health_check()


# Instancia del servicio
backend_integration = BackendIntegrationService()


# Instancia del servicio
backend_integration = BackendIntegrationService()
