from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import asyncio
import json
import random

app = FastAPI(title="Chat Microservice", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos de datos
class ChatMessage(BaseModel):
    message: str
    user_id: str = "demo_user"

class ChatResponse(BaseModel):
    success: bool
    message_id: str
    user_message: str
    assistant_response: str
    timestamp: str
    personalized: bool = True
    hasContext: bool = True

class AuthRequest(BaseModel):
    user_id: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str

# Almacenamiento en memoria para la demo
chat_history = []
authenticated_users = set()

# Respuestas predefinidas para demo
DEMO_RESPONSES = [
    "El MERVAL está mostrando una tendencia interesante. Basándome en tu perfil de inversor conservador, te recomiendo considerar GGAL e YPF para diversificar tu portfolio.",
    "Según tu historial de inversiones en el sector financiero, BPAT y SUPV están presentando oportunidades de compra en este momento.",
    "Tu estrategia de inversión a largo plazo se alinea bien con ALUA y TXAR. Ambas acciones han mostrado fundamentos sólidos.",
    "Considerando tu tolerancia al riesgo medio, PAM y TECO podrían ser buenas adiciones a tu portfolio actual.",
    "El análisis técnico de MIRG y VALO sugiere una posible entrada en el corto plazo, acorde a tu perfil de trading.",
]

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )

@app.post("/auth/authenticate")
async def authenticate_user(auth_req: AuthRequest):
    """Simular autenticación del usuario"""
    authenticated_users.add(auth_req.user_id)
    return {
        "success": True,
        "user_id": auth_req.user_id,
        "message": "Usuario autenticado exitosamente"
    }

@app.get("/auth/verify")
async def verify_token():
    """Simular verificación de token"""
    return {
        "success": True,
        "user_id": "demo_user",
        "valid": True
    }

@app.get("/user/context")
async def get_user_context():
    """Simular obtención de contexto del usuario"""
    return {
        "success": True,
        "hasProfile": True,
        "context": {
            "risk_tolerance": "medio",
            "investment_style": "conservador",
            "preferred_sectors": ["financiero", "energia"],
            "current_portfolio": ["GGAL", "YPF", "ALUA"]
        }
    }

@app.post("/chat/send", response_model=ChatResponse)
async def send_message(message: ChatMessage):
    """Procesar mensaje de chat y generar respuesta"""
    try:
        # Simular tiempo de procesamiento
        await asyncio.sleep(0.5)
        
        # Generar respuesta personalizada
        response_text = random.choice(DEMO_RESPONSES)
        
        # Personalizar respuesta basada en el mensaje
        user_msg = message.message.lower()
        if "precio" in user_msg or "cotiza" in user_msg:
            response_text = "Según tu perfil, te sugiero revisar GGAL que cotiza en $850 y YPF en $920. Ambas están dentro de tu rango de inversión preferido."
        elif "comprar" in user_msg or "invertir" in user_msg:
            response_text = "Basándome en tu portfolio actual y estrategia conservadora, recomiendo evaluar SUPV como próxima inversión. Ha mostrado estabilidad consistente."
        elif "merval" in user_msg:
            response_text = "El MERVAL cerró en 2,180,450 puntos (+1.2%). Considerando tu perfil, las acciones líderes que más contribuyeron fueron GGAL (+2.1%) y ALUA (+1.8%)."
        
        message_id = f"msg_{datetime.now().timestamp()}"
        
        # Almacenar en historial
        chat_entry = {
            "message_id": message_id,
            "user_message": message.message,
            "assistant_response": response_text,
            "timestamp": datetime.now().isoformat(),
            "user_id": message.user_id,
            "personalized": True,
            "has_context": True
        }
        chat_history.append(chat_entry)
        
        return ChatResponse(
            success=True,
            message_id=message_id,
            user_message=message.message,
            assistant_response=response_text,
            timestamp=datetime.now().isoformat(),
            personalized=True,
            hasContext=True
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/history")
async def get_chat_history(limit: int = 20):
    """Obtener historial de chat"""
    try:
        recent_messages = chat_history[-limit:] if chat_history else []
        return {
            "success": True,
            "messages": recent_messages,
            "total": len(chat_history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "service": "Chat Microservice",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "chat": "/chat/send",
            "history": "/chat/history",
            "auth": "/auth/authenticate"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8084)
