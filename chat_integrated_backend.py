"""
Servicio de chat integrado con el backend principal
"""
import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

import uvicorn
import jwt
from loguru import logger
from pydantic import BaseModel, Field
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager

# Importar nuestros servicios
from backend_integration import backend_integration, MainBackendClient

# Configuración desde .env
try:
    import dotenv
    dotenv.load_dotenv()
except ImportError:
    pass

# Variables de entorno
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "demo-secret-key-for-testing-12345")
JWT_ALGORITHM = "HS256"
MAIN_BACKEND_URL = os.getenv("MAIN_BACKEND_URL", "http://192.168.0.17:8080")
REDIS_URL = os.getenv("REDIS_URL")
MONGODB_URI = os.getenv("MONGODB_URI")

# Importar servicios de base de datos
try:
    import motor.motor_asyncio
    import redis.asyncio as redis
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

# Modelos
class User(BaseModel):
    user_id: str
    email: Optional[str] = None
    username: Optional[str] = None
    is_active: bool = True

class TokenPayload(BaseModel):
    sub: str  # user_id
    exp: Optional[int] = None

class ChatMessage(BaseModel):
    message: str = Field(..., max_length=2000)

class ChatResponse(BaseModel):
    message_id: str
    user_message: str
    assistant_response: str
    timestamp: datetime
    user_context: Optional[Dict[str, Any]] = None
    personalized: bool = False

class UserContextResponse(BaseModel):
    user_id: str
    has_profile: bool
    has_preferences: bool
    has_portfolio: bool
    backend_connected: bool


# Servicio de memoria (simplificado)
class IntegratedMemoryService:
    def __init__(self):
        self.memory_store = {}
        self.redis_client = None
        self.mongo_client = None
    
    async def initialize(self):
        """Inicializar conexiones de base de datos"""
        if DB_AVAILABLE:
            # Redis
            if REDIS_URL:
                try:
                    self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
                    await self.redis_client.ping()
                    logger.info("✅ Redis conectado")
                except Exception as e:
                    logger.warning(f"⚠️ Redis no disponible: {e}")
            
            # MongoDB
            if MONGODB_URI:
                try:
                    self.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
                    await self.mongo_client.admin.command('ping')
                    logger.info("✅ MongoDB conectado")
                except Exception as e:
                    logger.warning(f"⚠️ MongoDB no disponible: {e}")
    
    async def save_message(self, user_id: str, message: dict):
        """Guardar mensaje"""
        # Memoria local siempre
        if user_id not in self.memory_store:
            self.memory_store[user_id] = []
        self.memory_store[user_id].append(message)
        
        # Redis si está disponible
        if self.redis_client:
            try:
                key = f"chat:{user_id}"
                await self.redis_client.lpush(key, json.dumps(message, default=str))
                await self.redis_client.expire(key, 86400)
            except Exception as e:
                logger.warning(f"Error guardando en Redis: {e}")
        
        # MongoDB si está disponible
        if self.mongo_client:
            try:
                db = self.mongo_client.MervalDB
                await db.chat_conversations.insert_one({
                    "user_id": user_id,
                    "message": message,
                    "timestamp": datetime.utcnow()
                })
            except Exception as e:
                logger.warning(f"Error guardando en MongoDB: {e}")
    
    async def get_history(self, user_id: str, limit: int = 10) -> List[dict]:
        """Obtener historial"""
        # Intentar Redis primero
        if self.redis_client:
            try:
                key = f"chat:{user_id}"
                messages = await self.redis_client.lrange(key, 0, limit - 1)
                if messages:
                    return [json.loads(msg) for msg in reversed(messages)]
            except Exception:
                pass
        
        # Fallback a memoria
        return self.memory_store.get(user_id, [])[-limit:]
    
    async def cleanup(self):
        """Cerrar conexiones"""
        if self.redis_client:
            await self.redis_client.close()
        if self.mongo_client:
            self.mongo_client.close()


# IA personalizada con contexto del usuario
class PersonalizedAI:
    @staticmethod
    async def generate_response(message: str, user_context: Dict = None, history: List = None) -> Dict[str, Any]:
        """Generar respuesta personalizada basada en el contexto del usuario"""
        message_lower = message.lower()
        
        # Información base del usuario
        user_name = ""
        portfolio_info = ""
        preferences_info = ""
        
        if user_context and user_context.get("profile"):
            profile = user_context["profile"]
            user_name = profile.get("name", profile.get("username", ""))
        
        if user_context and user_context.get("portfolio"):
            portfolio = user_context["portfolio"]
            if portfolio.get("holdings"):
                portfolio_info = f" Veo que tienes inversiones en {', '.join(portfolio['holdings'][:3])}."
        
        if user_context and user_context.get("preferences"):
            prefs = user_context["preferences"]
            if prefs.get("favorite_stocks"):
                preferences_info = f" Tus acciones favoritas son {', '.join(prefs['favorite_stocks'][:3])}."
        
        # Generar respuesta personalizada
        greeting = f"Hola{' ' + user_name if user_name else ''}! "
        
        if any(word in message_lower for word in ["hola", "buenos"]):
            response = f"{greeting}Soy tu asistente financiero especializado en el mercado argentino.{portfolio_info}{preferences_info} ¿En qué puedo ayudarte?"
            personalized = bool(user_name or portfolio_info or preferences_info)
            
        elif "ypf" in message_lower:
            base_response = "YPF es una de las empresas más importantes del MERVAL. Su cotización depende del precio del petróleo y las políticas energéticas."
            if portfolio_info and "ypf" in str(user_context.get("portfolio", {})).lower():
                response = f"{base_response} Veo que la tienes en tu portfolio, ¡excelente elección para diversificación energética!"
                personalized = True
            else:
                response = base_response
                personalized = False
                
        elif "merval" in message_lower:
            base_response = "El MERVAL es el índice principal de la Bolsa de Buenos Aires con las 25 empresas más líquidas."
            if portfolio_info:
                response = f"{base_response} Considerando tu portfolio actual, es importante seguir las tendencias del índice."
                personalized = True
            else:
                response = base_response
                personalized = False
                
        elif any(word in message_lower for word in ["dolar", "dólar", "blue"]):
            response = "El dólar blue cotiza con brecha respecto al oficial. Es un indicador clave para inversiones en Argentina."
            personalized = False
            
        elif any(word in message_lower for word in ["bono", "bonos"]):
            response = "Los bonos argentinos como AL30 y GD30 son referencia para medir el riesgo país. Importante para diversificación."
            personalized = False
            
        elif any(word in message_lower for word in ["meli", "mercadolibre"]):
            base_response = "MercadoLibre cotiza en NASDAQ y MERVAL. Es un refugio de valor en dólares."
            if preferences_info and "meli" in str(user_context.get("preferences", {})).lower():
                response = f"{base_response} Veo que está en tus favoritas, ¡muy buena para exposición al dólar!"
                personalized = True
            else:
                response = base_response
                personalized = False
                
        else:
            response = f"Interesante pregunta sobre '{message}'. En el mercado argentino la volatilidad es característica.{preferences_info} ¿Te interesa algún activo específico?"
            personalized = bool(preferences_info)
        
        return {
            "response": response,
            "personalized": personalized,
            "context_used": user_context is not None
        }


# Autenticación JWT integrada
security = HTTPBearer()

def verify_token(token: str) -> TokenPayload:
    """Verificar token JWT"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return TokenPayload(**payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Obtener usuario actual"""
    token_data = verify_token(credentials.credentials)
    return User(user_id=token_data.sub)

def create_demo_token(user_id: str) -> str:
    """Crear token de demo"""
    expire = datetime.utcnow() + timedelta(minutes=30)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


# Aplicación FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida de la aplicación"""
    logger.info("🚀 Iniciando Chat Service Integrado...")
    
    # Inicializar servicios
    global memory_service
    memory_service = IntegratedMemoryService()
    await memory_service.initialize()
    
    # Verificar conexión con backend principal
    backend_status = await backend_integration.verify_backend_connection()
    if backend_status:
        logger.info("✅ Backend principal conectado")
    else:
        logger.warning("⚠️ Backend principal no disponible")
    
    logger.info("✅ Servicios inicializados")
    yield
    
    logger.info("🔄 Cerrando servicios...")
    await memory_service.cleanup()
    logger.info("✅ Servicios cerrados")


app = FastAPI(
    title="Chat Service Integrado con Backend",
    description="Servicio de chat que se integra con el backend principal y personaliza respuestas",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

memory_service = None


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "service": "Chat Service Integrado",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "JWT Authentication",
            "Backend Integration", 
            "Personalized AI",
            "Multi-database storage"
        ],
        "backend_url": MAIN_BACKEND_URL,
        "endpoints": [
            "/health",
            "/auth/token", 
            "/chat/message",
            "/chat/context/{user_id}",
            "/chat/history/{user_id}"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check completo"""
    backend_status = await backend_integration.verify_backend_connection()
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "services": {
            "chat_service": "running",
            "main_backend": "connected" if backend_status else "disconnected",
            "redis": "connected" if memory_service and memory_service.redis_client else "disconnected",
            "mongodb": "connected" if memory_service and memory_service.mongo_client else "disconnected",
            "memory": "available"
        },
        "backend_url": MAIN_BACKEND_URL
    }


@app.post("/auth/token")
async def create_auth_token(user_id: str = "demo_user"):
    """Crear token de autenticación"""
    token = create_demo_token(user_id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user_id,
        "expires_in": 1800  # 30 minutos
    }


@app.get("/chat/context/{user_id}", response_model=UserContextResponse)
async def get_user_context(
    user_id: str,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """Obtener contexto del usuario desde el backend principal"""
    # Verificar permisos
    if current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    # Obtener token del header
    auth_header = request.headers.get("Authorization", "").replace("Bearer ", "")
    
    # Obtener contexto del backend
    context = await backend_integration.get_user_context(user_id, auth_header)
    
    return UserContextResponse(
        user_id=user_id,
        has_profile=context.get("profile") is not None,
        has_preferences=context.get("preferences") is not None,
        has_portfolio=context.get("portfolio") is not None,
        backend_connected=await backend_integration.verify_backend_connection()
    )


@app.post("/chat/message", response_model=ChatResponse)
async def send_message(
    message: ChatMessage,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """Enviar mensaje con personalización basada en el backend"""
    try:
        # Obtener token del header
        auth_header = request.headers.get("Authorization", "").replace("Bearer ", "")
        
        # Obtener contexto del usuario desde el backend principal
        user_context = None
        try:
            user_context = await backend_integration.get_user_context(current_user.user_id, auth_header)
        except Exception as e:
            logger.warning(f"No se pudo obtener contexto del usuario: {e}")
        
        # Obtener historial para contexto de conversación
        history = await memory_service.get_history(current_user.user_id, limit=5)
        
        # Guardar mensaje del usuario
        user_msg = {
            "id": str(uuid.uuid4()),
            "user_id": current_user.user_id,
            "message": message.message,
            "type": "user",
            "timestamp": datetime.utcnow()
        }
        await memory_service.save_message(current_user.user_id, user_msg)
        
        # Generar respuesta personalizada
        ai_result = await PersonalizedAI.generate_response(
            message.message, 
            user_context, 
            history
        )
        
        # Guardar respuesta
        response_id = str(uuid.uuid4())
        ai_msg = {
            "id": response_id,
            "user_id": current_user.user_id,
            "message": ai_result["response"],
            "type": "assistant",
            "timestamp": datetime.utcnow(),
            "personalized": ai_result["personalized"]
        }
        await memory_service.save_message(current_user.user_id, ai_msg)
        
        # Registrar actividad en el backend principal
        try:
            await backend_integration.log_chat_session(
                current_user.user_id,
                {
                    "message_count": len(history) + 2,
                    "personalized": ai_result["personalized"],
                    "context_available": user_context is not None
                },
                auth_header
            )
        except Exception as e:
            logger.warning(f"No se pudo registrar actividad: {e}")
        
        return ChatResponse(
            message_id=response_id,
            user_message=message.message,
            assistant_response=ai_result["response"],
            timestamp=datetime.utcnow(),
            user_context=user_context,
            personalized=ai_result["personalized"]
        )
        
    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/chat/history/{user_id}")
async def get_chat_history(
    user_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Obtener historial de chat"""
    if current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    history = await memory_service.get_history(user_id, limit=limit)
    
    return {
        "user_id": user_id,
        "messages": history,
        "total": len(history),
        "personalized_count": sum(1 for msg in history if msg.get("personalized", False))
    }


if __name__ == "__main__":
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=8085,
        reload=True,
        log_level="info"
    )
