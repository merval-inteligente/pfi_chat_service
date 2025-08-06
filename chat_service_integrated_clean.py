"""
Servicio integrado de chat con autenticación JWT
Versión autónoma simplificada
"""
import asyncio
import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum

import uvicorn
import jwt
from loguru import logger
from pydantic import BaseModel, Field
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager

# Intentar importar bases de datos (opcional)
try:
    import motor.motor_asyncio
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    logger.warning("MongoDB no disponible")

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis no disponible")

# Cargar variables de entorno
try:
    import dotenv
    dotenv.load_dotenv()
except ImportError:
    pass

# Configuración
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "demo-secret-key-for-testing-12345")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
MONGODB_URI = os.getenv("MONGODB_URI")


# Modelos Pydantic
class MessageType(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class User(BaseModel):
    user_id: str
    email: Optional[str] = None
    username: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen: Optional[datetime] = None


class TokenPayload(BaseModel):
    sub: str  # user_id
    exp: Optional[int] = None
    iat: Optional[int] = None


class ChatMessageCreate(BaseModel):
    message: str = Field(..., max_length=2000)
    user_context: Optional[Dict[str, Any]] = None


class ChatMessageResponse(BaseModel):
    message_id: str
    user_message: str
    assistant_response: str
    timestamp: datetime
    context_used: Optional[Dict[str, Any]] = None
    model_info: Optional[Dict[str, str]] = None


# Servicio de memoria simplificado
class SimpleMemoryService:
    def __init__(self):
        self.memory_store = {}
        self.redis_client = None
        self.mongo_client = None
        self.mongo_db = None
    
    async def initialize(self):
        """Inicializar conexiones"""
        logger.info("🔧 Inicializando servicios de memoria...")
        
        # Intentar Redis
        if REDIS_AVAILABLE and REDIS_URL:
            try:
                self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
                await self.redis_client.ping()
                logger.info("✅ Redis conectado")
            except Exception as e:
                logger.warning(f"⚠️ Redis no disponible: {e}")
                self.redis_client = None
        
        # Intentar MongoDB
        if MONGODB_AVAILABLE and MONGODB_URI:
            try:
                self.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
                self.mongo_db = self.mongo_client.MervalDB
                await self.mongo_client.admin.command('ping')
                logger.info("✅ MongoDB conectado")
            except Exception as e:
                logger.warning(f"⚠️ MongoDB no disponible: {e}")
                self.mongo_client = None
        
        logger.info("✅ Memoria local disponible como fallback")
    
    async def save_message(self, user_id: str, message: dict):
        """Guardar mensaje"""
        try:
            # Siempre guardar en memoria local
            if user_id not in self.memory_store:
                self.memory_store[user_id] = []
            self.memory_store[user_id].append(message)
            
            # Intentar Redis
            if self.redis_client:
                try:
                    key = f"chat:{user_id}"
                    await self.redis_client.lpush(key, json.dumps(message, default=str))
                    await self.redis_client.expire(key, 86400)
                except Exception as e:
                    logger.warning(f"Error guardando en Redis: {e}")
            
            # Intentar MongoDB
            if self.mongo_db:
                try:
                    await self.mongo_db.conversations.insert_one({
                        "user_id": user_id,
                        "message": message,
                        "timestamp": datetime.utcnow()
                    })
                except Exception as e:
                    logger.warning(f"Error guardando en MongoDB: {e}")
                    
        except Exception as e:
            logger.error(f"Error guardando mensaje: {e}")
    
    async def get_conversation_history(self, user_id: str, limit: int = 50) -> List[dict]:
        """Obtener historial"""
        try:
            # Intentar Redis primero
            if self.redis_client:
                try:
                    key = f"chat:{user_id}"
                    messages = await self.redis_client.lrange(key, 0, limit - 1)
                    if messages:
                        return [json.loads(msg) for msg in reversed(messages)]
                except Exception as e:
                    logger.warning(f"Error leyendo Redis: {e}")
            
            # Fallback a MongoDB
            if self.mongo_db:
                try:
                    cursor = self.mongo_db.conversations.find(
                        {"user_id": user_id}
                    ).sort("timestamp", -1).limit(limit)
                    
                    messages = []
                    async for doc in cursor:
                        messages.append(doc["message"])
                    if messages:
                        return list(reversed(messages))
                except Exception as e:
                    logger.warning(f"Error leyendo MongoDB: {e}")
            
            # Fallback a memoria local
            return self.memory_store.get(user_id, [])[-limit:]
            
        except Exception as e:
            logger.error(f"Error obteniendo historial: {e}")
            return []
    
    async def clear_conversation_history(self, user_id: str):
        """Limpiar historial"""
        try:
            # Limpiar memoria local
            if user_id in self.memory_store:
                del self.memory_store[user_id]
            
            # Limpiar Redis
            if self.redis_client:
                try:
                    await self.redis_client.delete(f"chat:{user_id}")
                except Exception as e:
                    logger.warning(f"Error limpiando Redis: {e}")
            
            # Limpiar MongoDB
            if self.mongo_db:
                try:
                    await self.mongo_db.conversations.delete_many({"user_id": user_id})
                except Exception as e:
                    logger.warning(f"Error limpiando MongoDB: {e}")
                    
        except Exception as e:
            logger.error(f"Error limpiando historial: {e}")
    
    async def cleanup(self):
        """Cerrar conexiones"""
        try:
            if self.redis_client:
                await self.redis_client.close()
            if self.mongo_client:
                self.mongo_client.close()
        except Exception as e:
            logger.error(f"Error cerrando conexiones: {e}")
    
    async def get_status(self) -> dict:
        """Obtener estado de las conexiones"""
        redis_status = "disconnected"
        mongo_status = "disconnected"
        
        if self.redis_client:
            try:
                await self.redis_client.ping()
                redis_status = "connected"
            except:
                redis_status = "error"
        
        if self.mongo_client:
            try:
                await self.mongo_client.admin.command('ping')
                mongo_status = "connected"
            except:
                mongo_status = "error"
        
        return {
            "redis": redis_status,
            "mongodb": mongo_status,
            "memory": "available"
        }


# Servicio de IA
async def create_ai_response(user_message: str, history: List[dict]) -> str:
    """Crear respuesta de IA especializada en mercado argentino"""
    
    # Respuestas especializadas
    responses = {
        "saludo": [
            "¡Hola! Soy tu asistente financiero especializado en el mercado argentino. ¿En qué puedo ayudarte?",
            "¡Bienvenido! Estoy aquí para ayudarte con información sobre el MERVAL, bonos, dólar y criptomonedas."
        ],
        "ypf": [
            "YPF (Yacimientos Petrolíferos Fiscales) es una de las empresas más importantes del MERVAL.",
            "Las acciones de YPF son muy volátiles y dependen del precio del petróleo y las políticas energéticas."
        ],
        "merval": [
            "El MERVAL es el principal índice de la Bolsa de Buenos Aires con las 25 empresas más líquidas.",
            "El MERVAL tiene alta correlación con el dólar blue y los bonos soberanos argentinos."
        ],
        "dolar": [
            "El dólar blue es el tipo de cambio paralelo con brecha significativa respecto al oficial.",
            "Los inversores siguen la brecha cambiaria como indicador de estabilidad económica."
        ],
        "bonos": [
            "Los bonos argentinos han mostrado alta volatilidad. Los más seguidos son AL30, GD30 y Bonar 2030.",
            "El riesgo país se mide principalmente a través del spread de estos bonos soberanos."
        ],
        "meli": [
            "MercadoLibre (MELI) cotiza en NASDAQ y MERVAL, siendo un refugio de valor en dólares.",
            "MELI ha sido muy popular entre inversores argentinos por su exposición al dólar."
        ]
    }
    
    # Analizar mensaje
    import random
    message_lower = user_message.lower()
    
    if any(word in message_lower for word in ["hola", "buenos", "saludos"]):
        return random.choice(responses["saludo"])
    elif "ypf" in message_lower:
        return random.choice(responses["ypf"])
    elif "merval" in message_lower:
        return random.choice(responses["merval"])
    elif any(word in message_lower for word in ["dolar", "dólar", "blue"]):
        return random.choice(responses["dolar"])
    elif any(word in message_lower for word in ["bono", "bonos"]):
        return random.choice(responses["bonos"])
    elif any(word in message_lower for word in ["meli", "mercadolibre"]):
        return random.choice(responses["meli"])
    else:
        return f"Interesante pregunta sobre '{user_message}'. En el mercado argentino es importante considerar la volatilidad de nuestros activos. ¿Te interesa algún instrumento específico del MERVAL, bonos o dólar?"


# Autenticación JWT
security = HTTPBearer()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crear token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> TokenPayload:
    """Verificar token JWT"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        token_data = TokenPayload(**payload)
        
        if token_data.exp and datetime.utcfromtimestamp(token_data.exp) < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return token_data
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Obtener usuario actual"""
    token_data = verify_token(credentials.credentials)
    return User(
        user_id=token_data.sub,
        is_active=True,
        last_seen=datetime.utcnow()
    )

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Obtener usuario activo"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )
    return current_user

def create_demo_token(user_id: str = "demo_user") -> str:
    """Crear token de demo"""
    return create_access_token(data={"sub": user_id})


# Aplicación FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida"""
    logger.info("🚀 Iniciando Chat Service Integrado...")
    
    global memory_service
    memory_service = SimpleMemoryService()
    await memory_service.initialize()
    
    logger.info("✅ Servicios inicializados")
    yield
    
    logger.info("🔄 Cerrando servicios...")
    await memory_service.cleanup()
    logger.info("✅ Servicios cerrados")


app = FastAPI(
    title="Chat Service Integrado",
    description="Servicio de chat con autenticación JWT",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

memory_service = None


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "Chat Service Integrado",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.utcnow(),
        "endpoints": [
            "/health",
            "/auth/demo-token",
            "/chat/message",
            "/chat/history/{user_id}",
            "/docs"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check"""
    try:
        services = await memory_service.get_status() if memory_service else {"error": "not_initialized"}
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "services": services
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }


@app.post("/auth/demo-token")
async def create_demo_token_endpoint(user_id: str = "demo_user"):
    """Crear token de demo"""
    try:
        token = create_demo_token(user_id)
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_id": user_id,
            "expires_in": JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creando token: {str(e)}"
        )


@app.post("/chat/message", response_model=ChatMessageResponse)
async def send_message(
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Enviar mensaje al chat"""
    try:
        logger.info(f"Usuario {current_user.user_id}: {message_data.message[:50]}...")
        
        # Guardar mensaje del usuario
        message_id = str(uuid.uuid4())
        user_message = {
            "id": message_id,
            "user_id": current_user.user_id,
            "message": message_data.message,
            "message_type": MessageType.USER,
            "timestamp": datetime.utcnow()
        }
        
        await memory_service.save_message(current_user.user_id, user_message)
        
        # Obtener historial para contexto
        history = await memory_service.get_conversation_history(current_user.user_id, limit=10)
        
        # Generar respuesta
        assistant_response = await create_ai_response(message_data.message, history)
        
        # Guardar respuesta
        response_id = str(uuid.uuid4())
        assistant_message = {
            "id": response_id,
            "user_id": current_user.user_id,
            "message": assistant_response,
            "message_type": MessageType.ASSISTANT,
            "timestamp": datetime.utcnow()
        }
        
        await memory_service.save_message(current_user.user_id, assistant_message)
        
        return ChatMessageResponse(
            message_id=response_id,
            user_message=message_data.message,
            assistant_response=assistant_response,
            timestamp=datetime.utcnow(),
            model_info={"model": "financial-ai", "provider": "custom"}
        )
        
    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )


@app.get("/chat/history/{user_id}")
async def get_chat_history(
    user_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user)
):
    """Obtener historial de chat"""
    try:
        if current_user.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puedes acceder a tu propio historial"
            )
        
        history = await memory_service.get_conversation_history(user_id, limit=limit)
        
        return {
            "user_id": user_id,
            "messages": history,
            "total_messages": len(history),
            "timestamp": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )


@app.delete("/chat/history/{user_id}")
async def clear_chat_history(
    user_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Limpiar historial"""
    try:
        if current_user.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puedes limpiar tu propio historial"
            )
        
        await memory_service.clear_conversation_history(user_id)
        
        return {
            "message": "Historial limpiado exitosamente",
            "user_id": user_id,
            "timestamp": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(
        "chat_service_integrated_clean:app",
        host="127.0.0.1",
        port=8083,
        reload=True,
        log_level="info"
    )
