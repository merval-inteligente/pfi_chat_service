"""
Servicio de chat simple con autenticación JWT
"""
import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict

import jwt
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

# Configuración
JWT_SECRET = "demo-secret-key-12345"
JWT_ALGORITHM = "HS256"

# Memoria simple
CONVERSATIONS = {}

# Modelos
class User(BaseModel):
    user_id: str
    is_active: bool = True

class TokenPayload(BaseModel):
    sub: str
    exp: Optional[int] = None

class ChatMessage(BaseModel):
    message: str = Field(..., max_length=2000)

class ChatResponse(BaseModel):
    message_id: str
    user_message: str
    assistant_response: str
    timestamp: datetime

# Autenticación
security = HTTPBearer()

def create_token(user_id: str) -> str:
    """Crear token JWT"""
    expire = datetime.utcnow() + timedelta(minutes=30)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> TokenPayload:
    """Verificar token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return TokenPayload(**payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Obtener usuario actual"""
    token_data = verify_token(credentials.credentials)
    return User(user_id=token_data.sub)

# IA simple
def generate_response(message: str) -> str:
    """Generar respuesta de IA"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ["hola", "buenos"]):
        return "¡Hola! Soy tu asistente financiero argentino. ¿En qué puedo ayudarte?"
    elif "ypf" in message_lower:
        return "YPF es una de las empresas más importantes del MERVAL. Su cotización depende del precio del petróleo."
    elif "merval" in message_lower:
        return "El MERVAL es el índice principal de la Bolsa de Buenos Aires con las 25 empresas más líquidas."
    elif "dolar" in message_lower or "dólar" in message_lower:
        return "El dólar blue cotiza con brecha respecto al oficial. Es un indicador clave del mercado."
    elif "bono" in message_lower:
        return "Los bonos argentinos como AL30 y GD30 son referencia para medir el riesgo país."
    elif "meli" in message_lower:
        return "MercadoLibre cotiza en NASDAQ y MERVAL. Es un refugio de valor en dólares para muchos argentinos."
    else:
        return f"Interesante pregunta sobre '{message}'. En el mercado argentino, la volatilidad es característica. ¿Te interesa algún activo específico del MERVAL?"

# Aplicación FastAPI
app = FastAPI(title="Chat Service Simple", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "service": "Chat Service Simple",
        "status": "running",
        "version": "1.0.0",
        "endpoints": ["/health", "/auth/token", "/chat/message", "/chat/history/{user_id}"]
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "conversations": len(CONVERSATIONS)
    }

@app.post("/auth/token")
async def create_auth_token(user_id: str = "demo_user"):
    """Crear token de autenticación"""
    token = create_token(user_id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user_id
    }

@app.post("/chat/message", response_model=ChatResponse)
async def send_message(
    message: ChatMessage,
    current_user: User = Depends(get_current_user)
):
    """Enviar mensaje"""
    # Guardar mensaje del usuario
    user_id = current_user.user_id
    if user_id not in CONVERSATIONS:
        CONVERSATIONS[user_id] = []
    
    user_msg = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "message": message.message,
        "type": "user",
        "timestamp": datetime.utcnow()
    }
    CONVERSATIONS[user_id].append(user_msg)
    
    # Generar respuesta
    response_text = generate_response(message.message)
    
    # Guardar respuesta
    response_id = str(uuid.uuid4())
    ai_msg = {
        "id": response_id,
        "user_id": user_id,
        "message": response_text,
        "type": "assistant",
        "timestamp": datetime.utcnow()
    }
    CONVERSATIONS[user_id].append(ai_msg)
    
    return ChatResponse(
        message_id=response_id,
        user_message=message.message,
        assistant_response=response_text,
        timestamp=datetime.utcnow()
    )

@app.get("/chat/history/{user_id}")
async def get_history(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Obtener historial"""
    if current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    history = CONVERSATIONS.get(user_id, [])
    return {
        "user_id": user_id,
        "messages": history,
        "total": len(history)
    }

@app.delete("/chat/history/{user_id}")
async def clear_history(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Limpiar historial"""
    if current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    if user_id in CONVERSATIONS:
        del CONVERSATIONS[user_id]
    
    return {"message": "Historial limpiado", "user_id": user_id}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8084)
