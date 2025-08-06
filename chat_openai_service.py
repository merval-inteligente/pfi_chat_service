"""
Chat Service con OpenAI Real - Versión de Producción
Integra OpenAI GPT-4 para respuestas reales especializadas en mercado financiero argentino
"""

import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import logging
import json
import asyncio
from dataclasses import dataclass, asdict

# Imports principales
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from loguru import logger
import uvicorn

# OpenAI
import openai
from openai import AsyncOpenAI

# =============================================================================
# CONFIGURACIÓN Y MODELOS
# =============================================================================

# Configuración desde .env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-demo-key-for-testing")
SERVICE_MODE = os.getenv("SERVICE_MODE", "demo")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8083"))
SERVICE_HOST = os.getenv("SERVICE_HOST", "0.0.0.0")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# Cliente OpenAI
if OPENAI_API_KEY.startswith("sk-") and OPENAI_API_KEY != "sk-demo-key-for-testing":
    openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    AI_MODE = "production"
    logger.info("🤖 OpenAI configurado en modo PRODUCCIÓN")
else:
    openai_client = None
    AI_MODE = "demo"
    logger.warning("⚠️  OpenAI en modo DEMO - configurar OPENAI_API_KEY para producción")

# Modelos Pydantic
class ChatMessage(BaseModel):
    message: str = Field(..., description="Mensaje del usuario")
    user_id: Optional[str] = Field(None, description="ID del usuario")
    session_id: Optional[str] = Field(None, description="ID de sesión")

class ChatResponse(BaseModel):
    message: str
    message_id: str
    timestamp: str
    ai_mode: str
    usage: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    services: Dict[str, str]
    ai_mode: str

class ServiceInfoResponse(BaseModel):
    service_name: str
    version: str
    ai_mode: str
    features: List[str]
    openai_model: str

@dataclass
class MessageData:
    role: str
    content: str
    timestamp: datetime
    message_id: str

# =============================================================================
# STORAGE EN MEMORIA
# =============================================================================

class MemoryStorage:
    def __init__(self):
        self.conversations: Dict[str, List[MessageData]] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def add_message(self, user_id: str, role: str, content: str) -> str:
        """Agregar mensaje a la conversación"""
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        message_id = f"msg_{len(self.conversations[user_id]) + 1}_{int(datetime.now().timestamp())}"
        message = MessageData(
            role=role,
            content=content,
            timestamp=datetime.now(timezone.utc),
            message_id=message_id
        )
        
        self.conversations[user_id].append(message)
        return message_id
    
    def get_conversation(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtener historial de conversación"""
        if user_id not in self.conversations:
            return []
        
        messages = self.conversations[user_id][-limit:]
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "message_id": msg.message_id
            }
            for msg in messages
        ]
    
    def get_context_for_ai(self, user_id: str, limit: int = 5) -> List[Dict[str, str]]:
        """Obtener contexto para enviar a OpenAI"""
        if user_id not in self.conversations:
            return []
        
        messages = self.conversations[user_id][-limit:]
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

# Instancia global de storage
memory_storage = MemoryStorage()

# =============================================================================
# SERVICIO OPENAI
# =============================================================================

class OpenAIService:
    def __init__(self):
        self.model = "gpt-4-turbo-preview"
        self.max_tokens = 2000
        self.temperature = 0.7
        
        # Sistema de prompts especializado en finanzas argentinas
        self.system_prompt = """Eres un asistente financiero especializado en el mercado argentino. Tu conocimiento incluye:

MERCADO ARGENTINO:
- MERVAL y acciones argentinas (GGAL, YPF, GGAL, BMA, SUPV, TECO2, etc.)
- Bonos soberanos (AL30, AL35, GD30, etc.)
- LELIQs, plazo fijo UVA, y instrumentos locales
- Impacto de políticas económicas y regulaciones AFIP
- Contexto de inflación y devaluación

CRIPTOMONEDAS EN ARGENTINA:
- Bitcoin y cryptos como cobertura inflacionaria
- Regulaciones AFIP para crypto
- Exchanges locales (SatoshiTango, Ripio, etc.)
- Dólar blue vs crypto como refugio de valor

ESTILO DE RESPUESTA:
- Conciso pero informativo
- Usa emojis relevantes (📈📉💰₿🏦)
- Menciona siempre los riesgos
- Contextualiza en la realidad argentina
- Máximo 200 palabras por respuesta

IMPORTANTE: Siempre aclarar que no es asesoramiento financiero profesional."""

    async def generate_response(self, user_message: str, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """Generar respuesta usando OpenAI GPT-4"""
        try:
            # Preparar mensajes para OpenAI
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Agregar historial (últimos 3 intercambios)
            messages.extend(conversation_history[-6:])  # user + assistant = 2 mensajes por intercambio
            
            # Agregar mensaje actual
            messages.append({"role": "user", "content": user_message})
            
            logger.info(f"🤖 Enviando {len(messages)} mensajes a OpenAI")
            
            # Llamada a OpenAI
            response = await openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            # Extraer respuesta
            ai_message = response.choices[0].message.content
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            logger.info(f"✅ OpenAI response: {usage['total_tokens']} tokens")
            
            return {
                "message": ai_message,
                "usage": usage,
                "model": self.model
            }
            
        except Exception as e:
            logger.error(f"❌ Error OpenAI: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error en OpenAI: {str(e)}"
            )

# Instancia del servicio OpenAI
openai_service = OpenAIService()

# =============================================================================
# RESPUESTAS DEMO (fallback)
# =============================================================================

DEMO_RESPONSES = {
    "saludo": "¡Hola! 👋 Soy tu asistente financiero especializado en el mercado argentino. ¿En qué puedo ayudarte?",
    "merval": """📈 **MERVAL HOY**
Principales acciones:
🏦 GGAL, BMA, SUPV (Bancos)
⚡ YPF, PAM (Energía)
📱 TECO2 (Telecom)
¿Te interesa algún sector en particular?""",
    "ypf": """⚡ **YPF - Análisis**
• Líder en energía argentina
• Exposición a Vaca Muerta
• Dependiente de precios del petróleo
• Riesgo: Regulación gubernamental
*No es asesoramiento financiero*""",
    "bitcoin": """₿ **Bitcoin en Argentina**
• Cobertura contra inflación
• Alternativa al dólar blue
• Considera volatilidad alta
• Aspectos impositivos AFIP
*Investiga antes de invertir*""",
    "bonos": """🏛️ **Bonos Argentinos**
• AL30, AL35 (USD)
• Riesgo país elevado
• Rendimientos atractivos pero riesgosos
• Historial de defaults
*Alto riesgo - diversifica*""",
    "default": "📊 Como asistente financiero argentino, puedo ayudarte con acciones, bonos, crypto y más. ¿Qué te interesa analizar?"
}

def get_demo_response(user_message: str) -> str:
    """Obtener respuesta demo basada en palabras clave"""
    message_lower = user_message.lower()
    
    if any(word in message_lower for word in ["hola", "buenos", "buenas", "hi", "hello"]):
        return DEMO_RESPONSES["saludo"]
    elif any(word in message_lower for word in ["merval", "bolsa", "acciones argentinas"]):
        return DEMO_RESPONSES["merval"]
    elif "ypf" in message_lower:
        return DEMO_RESPONSES["ypf"]
    elif any(word in message_lower for word in ["bitcoin", "btc", "crypto", "criptomoneda"]):
        return DEMO_RESPONSES["bitcoin"]
    elif any(word in message_lower for word in ["bonos", "al30", "al35", "gd30"]):
        return DEMO_RESPONSES["bonos"]
    else:
        return DEMO_RESPONSES["default"]

# =============================================================================
# FASTAPI APP
# =============================================================================

app = FastAPI(
    title="Chat Service - Financial AI Assistant",
    description="Asistente de chat especializado en mercado financiero argentino con OpenAI",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar Loguru
logger.remove()
logger.add(
    sink=lambda message: print(message, end=""),
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="INFO"
)

# =============================================================================
# ENDPOINTS
# =============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="2.0.0",
        services={
            "memory": "healthy",
            "ai": AI_MODE,
            "openai": "connected" if openai_client else "demo"
        },
        ai_mode=AI_MODE
    )

@app.get("/api/info", response_model=ServiceInfoResponse)
async def service_info():
    """Información del servicio"""
    return ServiceInfoResponse(
        service_name="Chat Service - Financial AI Assistant",
        version="2.0.0",
        ai_mode=AI_MODE,
        features=[
            "Chat con OpenAI GPT-4" if AI_MODE == "production" else "Chat con respuestas demo",
            "Especialización en mercado argentino",
            "Historial de conversaciones",
            "Análisis de acciones, bonos y crypto",
            "Contexto inflacionario argentino"
        ],
        openai_model="gpt-4-turbo-preview" if AI_MODE == "production" else "demo"
    )

@app.post("/api/chat/message", response_model=ChatResponse)
async def chat_message(data: ChatMessage):
    """Endpoint principal de chat"""
    try:
        # Generar user_id si no se proporciona
        user_id = data.user_id or f"user-{datetime.now().timestamp()}"
        
        logger.info(f"💬 Procesando mensaje de {user_id}: {data.message[:50]}...")
        
        # Guardar mensaje del usuario
        memory_storage.add_message(user_id, "user", data.message)
        
        # Generar respuesta
        if AI_MODE == "production" and openai_client:
            # Obtener contexto de conversación
            context = memory_storage.get_context_for_ai(user_id)
            
            # Generar respuesta con OpenAI
            ai_response = await openai_service.generate_response(data.message, context)
            response_text = ai_response["message"]
            usage = ai_response.get("usage")
        else:
            # Modo demo
            response_text = get_demo_response(data.message)
            usage = None
        
        # Guardar respuesta del asistente
        message_id = memory_storage.add_message(user_id, "assistant", response_text)
        
        logger.info(f"✅ Respuesta generada para {user_id}")
        
        return ChatResponse(
            message=response_text,
            message_id=message_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            ai_mode=AI_MODE,
            usage=usage
        )
        
    except Exception as e:
        logger.error(f"❌ Error en chat: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando mensaje: {str(e)}"
        )

@app.get("/api/chat/history/{user_id}")
async def get_chat_history(user_id: str, limit: int = 20):
    """Obtener historial de chat"""
    try:
        history = memory_storage.get_conversation(user_id, limit)
        return {
            "user_id": user_id,
            "total_messages": len(history),
            "messages": history,
            "ai_mode": AI_MODE
        }
    except Exception as e:
        logger.error(f"❌ Error obteniendo historial: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo historial: {str(e)}"
        )

# =============================================================================
# STARTUP & MAIN
# =============================================================================

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Iniciando Chat Service con OpenAI Real...")
    logger.info(f"📋 Modo AI: {AI_MODE}")
    logger.info(f"🔗 Docs: http://localhost:{SERVICE_PORT}/docs")
    logger.info(f"ℹ️  Info: http://localhost:{SERVICE_PORT}/api/info")
    
    if AI_MODE == "demo":
        logger.warning("⚠️  Para activar OpenAI real, configura OPENAI_API_KEY en .env")

if __name__ == "__main__":
    logger.info(f"🌟 Iniciando servidor en puerto {SERVICE_PORT}")
    uvicorn.run(
        "chat_openai_service:app",
        host=SERVICE_HOST,
        port=SERVICE_PORT,
        reload=DEBUG,
        log_level="info"
    )
