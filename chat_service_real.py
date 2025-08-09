"""
Chat Service funcional con MongoDB (y Redis opcional)
Versión que funciona perfectamente con tu base de datos
"""

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import motor.motor_asyncio
import redis.asyncio as redis
import json
import asyncio
import jwt
import requests
from typing import List, Dict, Optional
from datetime import datetime, timezone
from pydantic import BaseModel

# Configuración
def load_env():
    env_vars = {}
    try:
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value
    except FileNotFoundError:
        pass
    return env_vars

env_config = load_env()
REDIS_URL = env_config.get('REDIS_URL', 'rediss://default:ASRBAAIjcDE4YjM3YmZiYWY0MTA0ZjUwYTJjOGZiMTJmZmIyYzljNXAxMA@stable-hog-9281.upstash.io:6379')
MONGODB_URL = env_config.get('MONGODB_URL', 'mongodb+srv://admin:tRVIi8NhbKbzDj0q@cluster0.dad6cgj.mongodb.net/MervalDB?retryWrites=true&w=majority')
MONGODB_DATABASE = env_config.get('MONGODB_DATABASE', 'MervalDB')
MONGODB_URI = env_config.get('MONGODB_URL', 'mongodb+srv://admin:tRVIi8NhbKbzDj0q@cluster0.dad6cgj.mongodb.net/MervalDB?retryWrites=true&w=majority')
MONGODB_DB_NAME = env_config.get('MONGODB_DB_NAME', 'MervalDB')

print(f"🔍 Config loaded - MongoDB: {MONGODB_URI[:50]}...")
print(f"🔍 Config loaded - Redis: {REDIS_URL[:50]}...")

# Modelos
class ChatMessage(BaseModel):
    message: str
    user_id: str

class ChatResponse(BaseModel):
    response: str
    user_id: str
    message_id: str
    timestamp: str
    storage_info: Dict[str, bool]

# Servicio de memoria híbrido
class MemoryService:
    def __init__(self):
        self.redis_client = None
        self.mongo_client = None
        self.db = None
        self.chat_collection = None
        self.memory_fallback = {}
        self.redis_connected = False
        self.mongo_connected = False
        
    async def connect(self):
        """Conectar a ambas bases de datos"""
        # MongoDB (prioritario)
        try:
            self.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(
                MONGODB_URI,
                serverSelectionTimeoutMS=5000
            )
            await self.mongo_client.admin.command('ping')
            self.db = self.mongo_client[MONGODB_DB_NAME]
            self.chat_collection = self.db.chat_conversations
            self.mongo_connected = True
            print(f"✅ MongoDB conectado a {MONGODB_DB_NAME}")
        except Exception as e:
            print(f"❌ MongoDB error: {e}")
            self.mongo_connected = False
            
        # Redis (opcional)
        try:
            if "upstash" in REDIS_URL:
                self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
                await asyncio.wait_for(self.redis_client.ping(), timeout=3.0)
                self.redis_connected = True
                print(f"✅ Redis Cloud conectado")
        except Exception as e:
            print(f"⚠️ Redis no disponible: {e}")
            self.redis_connected = False
            
        return {
            "mongodb": self.mongo_connected,
            "redis": self.redis_connected
        }
    
    async def store_conversation(self, user_id: str, message: str, response: str) -> Dict[str, bool]:
        """Guardar conversación"""
        timestamp = datetime.now(timezone.utc)
        message_id = f"msg_{int(timestamp.timestamp())}_{user_id[:8]}"
        
        storage_info = {"mongodb": False, "redis": False, "memory": False}
        
        # MongoDB (principal)
        if self.mongo_connected:
            try:
                doc = {
                    "user_id": user_id,
                    "message": message,
                    "response": response,
                    "timestamp": timestamp,
                    "message_id": message_id
                }
                await self.chat_collection.insert_one(doc)
                storage_info["mongodb"] = True
            except Exception as e:
                print(f"Error MongoDB: {e}")
                self.mongo_connected = False
        
        # Redis (cache)
        if self.redis_connected:
            try:
                cache_data = {
                    "message": message,
                    "response": response,
                    "timestamp": timestamp.isoformat(),
                    "message_id": message_id
                }
                key = f"chat_history:{user_id}"
                await self.redis_client.lpush(key, json.dumps(cache_data))
                await self.redis_client.ltrim(key, 0, 49)
                await self.redis_client.expire(key, 86400 * 7)
                storage_info["redis"] = True
            except Exception as e:
                print(f"Error Redis: {e}")
                self.redis_connected = False
        
        # Memoria (fallback)
        if not storage_info["mongodb"] and not storage_info["redis"]:
            if user_id not in self.memory_fallback:
                self.memory_fallback[user_id] = []
            self.memory_fallback[user_id].append({
                "message": message,
                "response": response,
                "timestamp": timestamp.isoformat(),
                "message_id": message_id
            })
            self.memory_fallback[user_id] = self.memory_fallback[user_id][-50:]
            storage_info["memory"] = True
        
        return storage_info, message_id
    
    async def get_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Obtener historial"""
        # Intentar Redis primero (más rápido)
        if self.redis_connected:
            try:
                key = f"chat_history:{user_id}"
                conversations_raw = await self.redis_client.lrange(key, 0, limit - 1)
                if conversations_raw:
                    conversations = [json.loads(conv) for conv in conversations_raw]
                    return list(reversed(conversations))
            except Exception as e:
                print(f"Error leyendo Redis: {e}")
                self.redis_connected = False
        
        # Fallback a MongoDB
        if self.mongo_connected:
            try:
                cursor = self.chat_collection.find(
                    {"user_id": user_id}
                ).sort("timestamp", -1).limit(limit)
                
                conversations = []
                async for doc in cursor:
                    conversations.append({
                        "message": doc["message"],
                        "response": doc["response"],
                        "timestamp": doc["timestamp"].isoformat() if isinstance(doc["timestamp"], datetime) else doc["timestamp"],
                        "message_id": doc.get("message_id", "unknown")
                    })
                
                return list(reversed(conversations))
            except Exception as e:
                print(f"Error leyendo MongoDB: {e}")
                self.mongo_connected = False
        
        # Fallback a memoria
        conversations = self.memory_fallback.get(user_id, [])[-limit:]
        return list(reversed(conversations))
    
    async def get_status(self):
        """Estado de las conexiones"""
        return {
            "mongodb": {
                "connected": self.mongo_connected,
                "database": MONGODB_DB_NAME if self.mongo_connected else None
            },
            "redis": {
                "connected": self.redis_connected,
                "type": "upstash_cloud" if self.redis_connected else None
            },
            "memory_fallback": {
                "users": len(self.memory_fallback)
            }
        }

# FastAPI App
app = FastAPI(title="Chat Service - Bases de Datos Reales", version="2.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar servicio
memory_service = MemoryService()

# Función para obtener información del usuario
async def get_user_info(user_id: str, auth_header: str = None) -> Dict[str, str]:
    """Obtener información del usuario desde el backend"""
    try:
        # Obtener backend URL desde configuración
        backend_url = env_config.get('BACKEND_URL', 'http://localhost:8080')
        
        if auth_header and auth_header.startswith('Bearer '):
            # Intentar obtener info del usuario desde el backend
            headers = {'Authorization': auth_header}
            response = requests.get(f"{backend_url}/api/auth/profile", headers=headers, timeout=5)
            
            if response.status_code == 200:
                user_data = response.json()
                return {
                    'name': user_data.get('data', {}).get('user', {}).get('name', 'Usuario'),
                    'email': user_data.get('data', {}).get('user', {}).get('email', '')
                }
        
        # Fallback para usuarios conocidos si no hay token válido
        known_users = {
            '688ac3765e7f9bb2d827766c': {'name': 'Nicolas', 'email': 'nicolas@example.com'}
        }
        
        if user_id in known_users:
            return known_users[user_id]
        
        # Fallback final: usar ID abreviado
        return {'name': f'Usuario {user_id[:8]}', 'email': ''}
        
    except Exception as e:
        print(f"Error obteniendo info del usuario: {e}")
        # Fallback para usuarios conocidos en caso de error
        known_users = {
            '688ac3765e7f9bb2d827766c': {'name': 'Nicolas', 'email': 'nicolas@example.com'}
        }
        return known_users.get(user_id, {'name': 'Usuario', 'email': ''})

# Respuestas demo
async def get_ai_response_demo(message: str, user_id: str, auth_header: str = None) -> str:
    """Respuestas demo mejoradas"""
    message_lower = message.lower()
    
    # Obtener información del usuario
    user_info = await get_user_info(user_id, auth_header)
    user_name = user_info['name']
    
    responses = {
        "merval": """📈 **MERVAL - Análisis en Tiempo Real**
        
🔹 **Situación actual**: El índice está en 1.245.789 puntos (+0.8%)
🔹 **Volumen**: $2.1M ARS en operaciones
🔹 **Líderes**: YPF (+2.1%), Galicia (+1.5%), Pampa Energía (+3.2%)
🔹 **Rezagados**: Telecom (-1.2%), Aluar (-0.8%)

💡 **Análisis**: El mercado muestra optimismo moderado. Considera diversificar en energía y bancos, pero mantente atento a la volatilidad del dólar.
        
⚠️ *No es asesoramiento financiero profesional*""",

        "ypf": """🛢️ **YPF - Análisis Detallado**
        
📊 **Datos técnicos**:
• Precio actual: $4.150 ARS (+1.8%)
• Volumen: 580k acciones
• Resistencia: $4.300 | Soporte: $3.950

⚡ **Catalizadores clave**:
• Precio del Brent: $82/barril
• Producción Vaca Muerta: +15% YoY  
• Plan de inversiones 2024: U$S 3.8B

💭 **Outlook**: Fundamentales sólidos, dependiente del precio internacional del crudo. Horizonte recomendado: 6-12 meses.

⚠️ *Análisis basado en información pública*""",

        "dolar": """💵 **Dólares en Argentina - Panorama Actual**
        
💹 **Cotizaciones estimadas**:
• Oficial: $365 ARS
• Blue: $485 ARS (brecha: 33%)
• MEP: $422 ARS  
• CCL: $428 ARS

📊 **Para inversores**:
• **MEP**: Ideal para comprar acciones en USD
• **CCL**: Para transferir al exterior
• **Blue**: Ahorro en efectivo

⚠️ **Importante**: Verificá cotizaciones en tiempo real. La brecha indica presión cambiaria.""",

        "bitcoin": """₿ **Bitcoin en Argentina - Contexto Local**
        
💎 **Situación actual**:
• Precio global: ~$43,500 USD
• Premium argentino: +1.6%
• Volumen P2P: $12M USD diarios

🔄 **Casos de uso locales**:
• Refugio ante inflación (84% anual)
• Transferencias internacionales
• Trading vs. dólar blue

⚡ **Plataformas**: Ripio, SatoshiTango, Buenbit, Binance P2P

⚠️ *Invertí solo lo que podés permitirte perder*""",

        "bonos": """🏛️ **Bonos Soberanos Argentinos**
        
📊 **Principales instrumentos**:
• AL30 (2030 USD): TIR ~15.2%
• GD30 (2030 USD): TIR ~15.8%
• AE38 (2038 USD): TIR ~16.5%

💡 **Contexto**:
• Riesgo país: ~1,850 puntos
• Restructuración 2020: cumpliendo pagos
• Próximo vencimiento: diciembre 2024

⚠️ **Perfil**: Solo para inversores con tolerancia al riesgo soberano alto."""
    }
    
    if any(word in message_lower for word in ["merval", "mercado", "índice"]):
        return responses["merval"]
    elif any(word in message_lower for word in ["ypf", "petróleo", "energía"]):
        return responses["ypf"]
    elif any(word in message_lower for word in ["dólar", "blue", "mep", "ccl"]):
        return responses["dolar"]
    elif any(word in message_lower for word in ["bitcoin", "crypto", "btc"]):
        return responses["bitcoin"]
    elif any(word in message_lower for word in ["bonos", "al30", "gd30"]):
        return responses["bonos"]
    else:
        return f"""¡Hola {user_name}! 👋 Soy tu **asistente financiero argentino**.

🎯 **Especialidades**:
📈 Análisis del MERVAL (YPF, Galicia, Pampa, etc.)
💰 Bonos soberanos (AL30, GD30, AE38)
💵 Situación cambiaria (Blue, MEP, CCL)
₿ Criptomonedas en contexto local
🌎 Mercados internacionales

**¿Sobre qué tema financiero te gustaría conversar?**"""

# Endpoints
@app.on_event("startup")
async def startup_event():
    """Conectar bases de datos al iniciar"""
    print("🚀 Iniciando Chat Service...")
    connections = await memory_service.connect()
    print(f"📊 Estado: MongoDB={connections['mongodb']}, Redis={connections['redis']}")

@app.get("/health")
async def health_check():
    """Health check con estado de bases de datos"""
    status = await memory_service.get_status()
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.1.0",
        "storage": status
    }

@app.post("/api/chat/message", response_model=ChatResponse)
async def send_message(chat_msg: ChatMessage, authorization: str = Header(None)):
    """Enviar mensaje de chat"""
    try:
        # Generar respuesta con información del usuario
        ai_response = await get_ai_response_demo(chat_msg.message, chat_msg.user_id, authorization)
        
        # Guardar conversación
        storage_info, message_id = await memory_service.store_conversation(
            chat_msg.user_id,
            chat_msg.message,
            ai_response
        )
        
        return ChatResponse(
            response=ai_response,
            user_id=chat_msg.user_id,
            message_id=message_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            storage_info=storage_info
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/api/chat/history/{user_id}")
async def get_chat_history(user_id: str, limit: int = 20):
    """Obtener historial de chat"""
    try:
        history = await memory_service.get_conversation_history(user_id, limit)
        status = await memory_service.get_status()
        
        return {
            "user_id": user_id,
            "total_messages": len(history),
            "history": history,
            "storage_status": status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/api/storage/status")
async def storage_status():
    """Estado detallado del almacenamiento"""
    return await memory_service.get_status()

if __name__ == "__main__":
    import uvicorn
    port = int(env_config.get('PORT', 8087))
    uvicorn.run(app, host="0.0.0.0", port=port)
