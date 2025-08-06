"""
Servicio integrado de chat con autenticación JWT
"""
import asyncio
import os
import sys
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import uuid
import uvicorn
from loguru import logger
import jwt
from typing import Optional
from pydantic import BaseModel, Field

"""
Servicio integrado de chat con autenticación JWT
Versión autónoma con todas las dependencias incluidas
"""
import asyncio
import os
import sys
import json
import uuid
import motor.motor_asyncio
import redis.asyncio as redis
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import uvicorn
from loguru import logger
import jwt
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

# Configuración JWT
JWT_SECRET_KEY = "demo-secret-key-for-testing-12345"
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Configuración de base de datos desde .env
import dotenv
dotenv.load_dotenv()

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


# Servicio de memoria híbrida
class HybridMemoryService:
    def __init__(self):
        self.redis_client = None
        self.mongo_client = None
        self.mongo_db = None
        self.memory_store = {}
    
    async def initialize(self):
        """Inicializar conexiones"""
        try:
            # Redis
            if REDIS_URL:
                self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
                await self.redis_client.ping()
                logger.info("✅ Redis conectado")
            
            # MongoDB
            if MONGODB_URI:
                self.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
                self.mongo_db = self.mongo_client.MervalDB
                await self.mongo_client.admin.command('ping')
                logger.info("✅ MongoDB conectado")
                
        except Exception as e:
            logger.warning(f"⚠️ Error conexiones DB: {e}")
    
    async def save_message(self, user_id: str, message: dict):
        """Guardar mensaje en todas las bases disponibles"""
        try:
            # Memory store
            if user_id not in self.memory_store:
                self.memory_store[user_id] = []
            self.memory_store[user_id].append(message)
            
            # Redis
            if self.redis_client:
                key = f"chat:{user_id}"
                await self.redis_client.lpush(key, json.dumps(message, default=str))
                await self.redis_client.expire(key, 86400)  # 24 horas
            
            # MongoDB
            if self.mongo_db:
                await self.mongo_db.conversations.insert_one({
                    "user_id": user_id,
                    "message": message,
                    "timestamp": datetime.utcnow()
                })
                
        except Exception as e:
            logger.error(f"Error guardando mensaje: {e}")
    
    async def get_conversation_history(self, user_id: str, limit: int = 50) -> List[dict]:
        """Obtener historial de conversación"""
        try:
            # Intentar Redis primero
            if self.redis_client:
                key = f"chat:{user_id}"
                messages = await self.redis_client.lrange(key, 0, limit - 1)
                if messages:
                    return [json.loads(msg) for msg in reversed(messages)]
            
            # Fallback a MongoDB
            if self.mongo_db:
                cursor = self.mongo_db.conversations.find(
                    {"user_id": user_id}
                ).sort("timestamp", -1).limit(limit)
                
                messages = []
                async for doc in cursor:
                    messages.append(doc["message"])
                return list(reversed(messages))
            
            # Fallback a memoria
            return self.memory_store.get(user_id, [])[-limit:]
            
        except Exception as e:
            logger.error(f"Error obteniendo historial: {e}")
            return self.memory_store.get(user_id, [])
    
    async def clear_conversation_history(self, user_id: str):
        """Limpiar historial de conversación"""
        try:
            # Limpiar memory store
            if user_id in self.memory_store:
                del self.memory_store[user_id]
            
            # Limpiar Redis
            if self.redis_client:
                await self.redis_client.delete(f"chat:{user_id}")
            
            # Limpiar MongoDB
            if self.mongo_db:
                await self.mongo_db.conversations.delete_many({"user_id": user_id})
                
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
    
    async def _test_redis(self) -> bool:
        """Probar conexión Redis"""
        try:
            if self.redis_client:
                await self.redis_client.ping()
                return True
        except:
            pass
        return False
    
    async def _test_mongodb(self) -> bool:
        """Probar conexión MongoDB"""
        try:
            if self.mongo_client:
                await self.mongo_client.admin.command('ping')
                return True
        except:
            pass
        return False


# Servicio de IA
async def create_ai_response(user_message: str, history: List[dict]) -> str:
    """Crear respuesta de IA especializada en mercado argentino"""
    
    responses = {
        "saludo": [
            "¡Hola! Soy tu asistente financiero especializado en el mercado argentino. ¿En qué puedo ayudarte hoy?",
            "¡Bienvenido! Estoy aquí para ayudarte con información sobre el MERVAL, bonos, dólar y criptomonedas argentinas."
        ],
        "ypf": [
            "YPF (Yacimientos Petrolíferos Fiscales) es una de las empresas más importantes del MERVAL. Cotiza tanto en Buenos Aires como en NYSE.",
            "Las acciones de YPF son muy volátiles y dependen del precio del petróleo y las políticas energéticas del gobierno."
        ],
        "merval": [
            "El MERVAL es el principal índice de la Bolsa de Buenos Aires. Incluye las 25 empresas más líquidas del mercado argentino.",
            "El MERVAL tiene alta correlación con el precio del dólar blue y los bonos soberanos argentinos."
        ],
        "dolar": [
            "El dólar blue es el tipo de cambio paralelo en Argentina. Suele cotizar con una brecha significativa respecto al oficial.",
            "Los inversores siguen de cerca la brecha cambiaria como indicador de la estabilidad económica."
        ],
        "bonos": [
            "Los bonos argentinos han mostrado alta volatilidad. Los más seguidos son AL30, GD30 y el Bonar 2030.",
            "El riesgo país de Argentina se mide principalmente a través del spread de estos bonos soberanos."
        ],
        "meli": [
            "MercadoLibre (MELI) es una de las empresas argentinas más valiosas, cotiza en NASDAQ y también en el MERVAL.",
            "MELI ha sido un refugio de valor para muchos inversores argentinos debido a su exposición al dólar."
        ]
    }
    
    # Analizar el mensaje del usuario
    message_lower = user_message.lower()
    
    if any(word in message_lower for word in ["hola", "buenos", "saludos"]):
        import random
        return random.choice(responses["saludo"])
    elif "ypf" in message_lower:
        import random
        return random.choice(responses["ypf"])
    elif "merval" in message_lower:
        import random
        return random.choice(responses["merval"])
    elif any(word in message_lower for word in ["dolar", "dólar", "blue"]):
        import random
        return random.choice(responses["dolar"])
    elif any(word in message_lower for word in ["bono", "bonos"]):
        import random
        return random.choice(responses["bonos"])
    elif any(word in message_lower for word in ["meli", "mercadolibre", "mercado libre"]):
        import random
        return random.choice(responses["meli"])
    else:
        # Respuesta genérica financiera
        return f"Interesante pregunta sobre '{user_message}'. En el contexto del mercado argentino, es importante considerar la volatilidad característica de nuestros activos financieros. ¿Te interesa algún instrumento en particular como acciones del MERVAL, bonos o dólar?"


# Autenticación JWT
security = HTTPBearer()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crear token de acceso JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> TokenPayload:
    """Verificar y decodificar token JWT"""
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
    except (jwt.JWTError, Exception):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Obtener usuario actual desde token JWT"""
    try:
        token_data = verify_token(credentials.credentials)
        
        user = User(
            user_id=token_data.sub,
            is_active=True,
            last_seen=datetime.utcnow()
        )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se pudo validar el usuario",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Obtener usuario activo actual"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )
    return current_user

def create_demo_token(user_id: str = "demo_user") -> str:
    """Crear token de demostración para testing"""
    return create_access_token(data={"sub": user_id})


# Ciclo de vida de la aplicación
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida de la aplicación"""
    logger.info("🚀 Iniciando Chat Service Integrado...")
    
    # Inicializar servicios
    global memory_service
    memory_service = HybridMemoryService()
    await memory_service.initialize()
    
    logger.info("✅ Servicios inicializados correctamente")
    yield
    
    # Cleanup
    logger.info("🔄 Cerrando servicios...")
    await memory_service.cleanup()
    logger.info("✅ Servicios cerrados correctamente")


# Crear aplicación FastAPI
app = FastAPI(
    title="Chat Service Integrado",
    description="Servicio de chat con autenticación JWT y base de datos híbrida",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variable global para el servicio
memory_service = None


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "Chat Service Integrado",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.utcnow()
    }


@app.get("/health")
async def health_check():
    """Health check"""
    try:
        # Verificar conexiones de base de datos
        redis_status = "connected" if memory_service and await memory_service._test_redis() else "disconnected"
        mongo_status = "connected" if memory_service and await memory_service._test_mongodb() else "disconnected"
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "services": {
                "redis": redis_status,
                "mongodb": mongo_status,
                "memory": "available"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }


@app.post("/auth/demo-token")
async def create_demo_token_endpoint(user_id: str = "demo_user"):
    """Crear token de demostración para testing"""
    try:
        token = create_demo_token(user_id)
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_id": user_id
        }
    except Exception as e:
        logger.error(f"Error creating demo token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creando token de demostración"
        )


@app.post("/chat/message", response_model=ChatMessageResponse)
async def send_message(
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Enviar mensaje al chat con autenticación JWT
    """
    try:
        logger.info(f"Usuario {current_user.user_id} envió mensaje: {message_data.message[:50]}...")
        
        # Crear ID único para el mensaje
        message_id = str(uuid.uuid4())
        
        # Guardar mensaje del usuario
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
        
        # Generar respuesta de IA
        assistant_response = await create_ai_response(message_data.message, history)
        
        # Crear mensaje de respuesta
        response_id = str(uuid.uuid4())
        assistant_message = {
            "id": response_id,
            "user_id": current_user.user_id,
            "message": assistant_response,
            "message_type": MessageType.ASSISTANT,
            "timestamp": datetime.utcnow()
        }
        
        # Guardar respuesta
        await memory_service.save_message(current_user.user_id, assistant_message)
        
        logger.info(f"Respuesta generada para usuario {current_user.user_id}")
        
        return ChatMessageResponse(
            message_id=response_id,
            user_message=message_data.message,
            assistant_response=assistant_response,
            timestamp=datetime.utcnow(),
            model_info={"model": "custom-financial-ai", "provider": "internal"}
        )
        
    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando mensaje: {str(e)}"
        )


@app.get("/chat/history/{user_id}")
async def get_chat_history(
    user_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtener historial de chat (solo el propio usuario)
    """
    try:
        # Verificar que el usuario solo acceda a su propio historial
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
        logger.error(f"Error obteniendo historial: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo historial: {str(e)}"
        )


@app.delete("/chat/history/{user_id}")
async def clear_chat_history(
    user_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Limpiar historial de chat
    """
    try:
        # Verificar permisos
        if current_user.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puedes limpiar tu propio historial"
            )
        
        # Limpiar historial
        await memory_service.clear_conversation_history(user_id)
        
        logger.info(f"Historial limpiado para usuario {user_id}")
        
        return {
            "message": "Historial limpiado exitosamente",
            "user_id": user_id,
            "timestamp": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error limpiando historial: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error limpiando historial: {str(e)}"
        )


if __name__ == "__main__":
    # Configurar variables de entorno si no existen
    if not os.getenv("JWT_SECRET_KEY"):
        os.environ["JWT_SECRET_KEY"] = JWT_SECRET_KEY
    
    uvicorn.run(
        "chat_service_integrated:app",
        host="127.0.0.1",
        port=8083,
        reload=True,
        log_level="info"
    )

# Configuración
security = HTTPBearer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida de la aplicación"""
    logger.info("🚀 Iniciando Chat Service Integrado...")
    
    # Inicializar servicios
    global memory_service
    memory_service = HybridMemoryService()
    await memory_service.initialize()
    
    logger.info("✅ Servicios inicializados correctamente")
    yield
    
    # Cleanup
    logger.info("🔄 Cerrando servicios...")
    await memory_service.cleanup()
    logger.info("✅ Servicios cerrados correctamente")


# Crear aplicación FastAPI
app = FastAPI(
    title="Chat Service Integrado",
    description="Servicio de chat con autenticación JWT y base de datos híbrida",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variable global para el servicio
memory_service = None


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "Chat Service Integrado",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.utcnow()
    }


@app.get("/health")
async def health_check():
    """Health check"""
    try:
        # Verificar conexiones de base de datos
        redis_status = "connected" if memory_service and await memory_service._test_redis() else "disconnected"
        mongo_status = "connected" if memory_service and await memory_service._test_mongodb() else "disconnected"
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "services": {
                "redis": redis_status,
                "mongodb": mongo_status,
                "memory": "available"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }


@app.post("/auth/demo-token")
async def create_demo_token_endpoint(user_id: str = "demo_user"):
    """Crear token de demostración para testing"""
    try:
        token = create_demo_token(user_id)
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_id": user_id
        }
    except Exception as e:
        logger.error(f"Error creating demo token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creando token de demostración"
        )


@app.post("/chat/message", response_model=ChatMessageResponse)
async def send_message(
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Enviar mensaje al chat con autenticación JWT
    """
    try:
        logger.info(f"Usuario {current_user.user_id} envió mensaje: {message_data.message[:50]}...")
        
        # Crear ID único para el mensaje
        message_id = str(uuid.uuid4())
        
        # Guardar mensaje del usuario
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
        
        # Generar respuesta de IA
        assistant_response = await create_ai_response(message_data.message, history)
        
        # Crear mensaje de respuesta
        response_id = str(uuid.uuid4())
        assistant_message = {
            "id": response_id,
            "user_id": current_user.user_id,
            "message": assistant_response,
            "message_type": MessageType.ASSISTANT,
            "timestamp": datetime.utcnow()
        }
        
        # Guardar respuesta
        await memory_service.save_message(current_user.user_id, assistant_message)
        
        logger.info(f"Respuesta generada para usuario {current_user.user_id}")
        
        return ChatMessageResponse(
            message_id=response_id,
            user_message=message_data.message,
            assistant_response=assistant_response,
            timestamp=datetime.utcnow(),
            model_info={"model": "gpt-4", "provider": "openai"}
        )
        
    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando mensaje: {str(e)}"
        )


@app.get("/chat/history/{user_id}")
async def get_chat_history(
    user_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtener historial de chat (solo el propio usuario)
    """
    try:
        # Verificar que el usuario solo acceda a su propio historial
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
        logger.error(f"Error obteniendo historial: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo historial: {str(e)}"
        )


@app.delete("/chat/history/{user_id}")
async def clear_chat_history(
    user_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Limpiar historial de chat
    """
    try:
        # Verificar permisos
        if current_user.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puedes limpiar tu propio historial"
            )
        
        # Limpiar historial
        await memory_service.clear_conversation_history(user_id)
        
        logger.info(f"Historial limpiado para usuario {user_id}")
        
        return {
            "message": "Historial limpiado exitosamente",
            "user_id": user_id,
            "timestamp": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error limpiando historial: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error limpiando historial: {str(e)}"
        )


if __name__ == "__main__":
    # Configurar variables de entorno si no existen
    if not os.getenv("JWT_SECRET_KEY"):
        os.environ["JWT_SECRET_KEY"] = "demo-secret-key-for-testing-12345"
    
    uvicorn.run(
        "chat_service_integrated:app",
        host="0.0.0.0",
        port=8082,
        reload=True,
        log_level="info"
    )
