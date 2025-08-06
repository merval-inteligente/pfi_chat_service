"""
Aplicación de chat ultra-simplificada para testing
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger
import sys

# Configurar logging simple
logger.remove()
logger.add(sys.stdout, level="INFO", format="{time} | {level} | {message}")

# Modelos básicos
class ChatMessageCreate(BaseModel):
    message: str
    user_context: Optional[Dict[str, Any]] = None

class ChatMessageResponse(BaseModel):
    message_id: str
    user_message: str
    assistant_response: str
    timestamp: datetime
    context_used: Optional[Dict[str, Any]] = None
    model_info: Optional[Dict[str, str]] = None

class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, str]

# Almacenamiento en memoria simple
chat_storage: Dict[str, List[Dict]] = {}

# Crear aplicación FastAPI
app = FastAPI(
    title="Chat Service - Ultra Simple",
    description="Microservicio de Chat Inteligente - Testing Ultra Simple",
    version="1.0.0-testing",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Respuestas demo predefinidas
DEMO_RESPONSES = {
    "hola": "¡Hola! 👋 Soy tu asistente financiero especializado en el mercado argentino. ¿En qué puedo ayudarte?",
    "merval": "📈 **MERVAL HOY**\n\nPrincipales acciones:\n🏦 GGAL, BMA, SUPV (Bancos)\n⚡ YPF, PAM (Energía)\n📱 TECO2 (Telecom)\n\n¿Te interesa algún sector en particular?",
    "ypf": "⚡ **YPF - Análisis**\n\n• Líder en energía argentina\n• Exposición a Vaca Muerta\n• Dependiente de precios del petróleo\n• Riesgo: Regulación gubernamental",
    "bitcoin": "₿ **Bitcoin en Argentina**\n\n• Cobertura contra inflación\n• Alternativa al dólar blue\n• Considera volatilidad alta\n• Aspectos impositivos AFIP",
    "bonos": "🏛️ **Bonos Argentinos**\n\n• AL30, AL35 (USD)\n• Riesgo país elevado\n• Rendimientos atractivos pero riesgosos\n• Historial de defaults",
    "dolar": "💵 **Dólar Argentina**\n\n• Oficial vs Blue (brecha cambiaria)\n• MEP y CCL para inversores\n• Impacto en acciones locales\n• Cobertura recomendada"
}

def get_demo_response(message: str) -> str:
    """Obtiene respuesta demo basada en palabras clave"""
    message_lower = message.lower()
    
    for keyword, response in DEMO_RESPONSES.items():
        if keyword in message_lower:
            return response
    
    # Respuesta por defecto
    return """🤖 **Chat Service - MODO DEMO**

Soy tu asistente financiero argentino. Puedo ayudarte con:

📈 **MERVAL** - Análisis de acciones argentinas
💰 **YPF** - Sector energético  
₿ **Bitcoin** - Criptomonedas en Argentina
🏛️ **Bonos** - Instrumentos de renta fija
💵 **Dólar** - Tipos de cambio

⚠️ **Nota**: Este es modo DEMO. Para IA real, configura OPENAI_API_KEY.

¿Qué te interesa analizar?"""

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "service": "Chat Service - Ultra Simple",
        "version": "1.0.0-testing",
        "status": "running",
        "mode": "demo",
        "docs": "/docs",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0-testing",
        services={
            "memory": "healthy",
            "ai": "demo",
            "auth": "testing"
        }
    )

@app.post("/api/chat/message", response_model=ChatMessageResponse)
async def send_chat_message(message_data: ChatMessageCreate, request: Request):
    """Envía un mensaje al chat y recibe respuesta demo"""
    try:
        # Obtener IP del cliente como user_id para demo
        client_ip = request.client.host if request.client else "unknown"
        user_id = f"demo-{client_ip}"
        
        message_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        logger.info(f"Procesando mensaje de {user_id}: {message_data.message[:50]}...")
        
        # Inicializar almacenamiento para usuario si no existe
        if user_id not in chat_storage:
            chat_storage[user_id] = []
        
        # Guardar mensaje del usuario
        user_message = {
            "id": message_id,
            "user_id": user_id,
            "message": message_data.message,
            "type": "user",
            "timestamp": timestamp.isoformat()
        }
        chat_storage[user_id].append(user_message)
        
        # Generar respuesta demo
        ai_response = get_demo_response(message_data.message)
        
        # Guardar respuesta del asistente
        response_id = str(uuid.uuid4())
        assistant_message = {
            "id": response_id,
            "user_id": user_id,
            "message": ai_response,
            "type": "assistant",
            "timestamp": datetime.utcnow().isoformat()
        }
        chat_storage[user_id].append(assistant_message)
        
        # Mantener solo los últimos 20 mensajes
        if len(chat_storage[user_id]) > 20:
            chat_storage[user_id] = chat_storage[user_id][-20:]
        
        # Preparar respuesta
        response = ChatMessageResponse(
            message_id=response_id,
            user_message=message_data.message,
            assistant_response=ai_response,
            timestamp=timestamp,
            context_used=message_data.user_context,
            model_info={
                "model": "demo-gpt",
                "provider": "demo",
                "mode": "testing"
            }
        )
        
        logger.info(f"Respuesta generada para {user_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error al procesar mensaje: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar el mensaje: {str(e)}"
        )

@app.get("/api/chat/history/{user_id}")
async def get_chat_history(user_id: str, limit: int = 50):
    """Obtiene el historial de chat del usuario"""
    try:
        messages = chat_storage.get(user_id, [])
        limited_messages = messages[-limit:] if len(messages) > limit else messages
        
        return {
            "user_id": user_id,
            "messages": limited_messages,
            "total_messages": len(limited_messages),
            "last_activity": limited_messages[-1]["timestamp"] if limited_messages else datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error al obtener historial: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener el historial"
        )

@app.delete("/api/chat/history/{user_id}")
async def clear_chat_history(user_id: str):
    """Limpia el historial de chat del usuario"""
    try:
        if user_id in chat_storage:
            del chat_storage[user_id]
        
        logger.info(f"Historial limpiado para usuario {user_id}")
        return {"message": "Historial limpiado exitosamente"}
        
    except Exception as e:
        logger.error(f"Error al limpiar historial: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al limpiar el historial"
        )

@app.get("/api/info")
async def get_service_info():
    """Información del servicio"""
    return {
        "service": "Chat Service Ultra Simple",
        "version": "1.0.0-testing",
        "mode": "demo",
        "description": "Versión de testing sin dependencias externas",
        "features": [
            "Chat con respuestas predefinidas",
            "Historial en memoria",
            "Especialización en mercado argentino",
            "Sin autenticación requerida"
        ],
        "endpoints": {
            "POST /api/chat/message": "Enviar mensaje",
            "GET /api/chat/history/{user_id}": "Obtener historial", 
            "DELETE /api/chat/history/{user_id}": "Limpiar historial",
            "GET /health": "Health check",
            "GET /api/info": "Información del servicio"
        },
        "demo_keywords": list(DEMO_RESPONSES.keys()),
        "sample_request": {
            "url": "POST /api/chat/message",
            "body": {"message": "Hola, ¿cómo está el MERVAL?"}
        },
        "storage": {
            "active_users": len(chat_storage),
            "total_messages": sum(len(messages) for messages in chat_storage.values())
        }
    }

@app.get("/api/stats")
async def get_stats():
    """Estadísticas del servicio"""
    total_messages = sum(len(messages) for messages in chat_storage.values())
    active_users = len(chat_storage)
    
    return {
        "active_users": active_users,
        "total_messages": total_messages,
        "average_messages_per_user": total_messages / active_users if active_users > 0 else 0,
        "timestamp": datetime.utcnow().isoformat()
    }

# Middleware para logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware para logging de requests"""
    start_time = datetime.utcnow()
    
    response = await call_next(request)
    
    process_time = (datetime.utcnow() - start_time).total_seconds()
    
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    
    return response

if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando Chat Service Ultra Simple...")
    print("📋 Modo: DEMO (sin OpenAI)")
    print("🔗 Docs: http://localhost:8082/docs")
    print("ℹ️  Info: http://localhost:8082/api/info")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8082,  # Cambiar a puerto 8082
        reload=False,
        log_level="info"
    )
