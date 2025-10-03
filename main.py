"""
FastAPI Chat Service
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional
import os
from datetime import datetime, timezone
import requests

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

# Configuración
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
MONGODB_URL = os.getenv('MONGODB_URL', '')
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8080')

# Importaciones de servicios
from app.services.chat_service import generate_ai_response, check_ai_status
from app.services.memory_service import memory_service

# Modelos
class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    user_id: str
    user_name: str
    message_id: str
    timestamp: str
    storage_info: Dict[str, bool]

# FastAPI App
app = FastAPI(
    title="Chat Service - Merval Inteligente",
    description="Servicio de chat con asistente especializado en MERVAL",
    version="3.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Autenticación simplificada
async def get_user_identity(authorization: str = Header(...)) -> Dict[str, str]:
    """Verificar token y obtener identidad del usuario"""
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Token requerido")
    
    try:
        headers = {'Authorization': authorization}
        response = requests.get(f"{BACKEND_URL}/api/auth/profile", headers=headers, timeout=10)
        
        if response.status_code == 401:
            raise HTTPException(status_code=401, detail="Token inválido")
        elif response.status_code != 200:
            raise HTTPException(status_code=503, detail="Backend no disponible")
        
        user_data = response.json()
        user_info = user_data.get('data', {}).get('user', {})
        
        return {
            'user_id': str(user_info.get('id', 'unknown')),
            'name': user_info.get('name', 'Usuario'),
            'email': user_info.get('email', '')
        }
        
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=503, detail="Backend no disponible")

# Endpoints principales

@app.post("/api/chat/message", response_model=ChatResponse)
async def send_message(
    chat_msg: ChatMessage, 
    user_info: dict = Depends(get_user_identity)
):
    """Enviar mensaje al chat con asistente Merval Inteligente"""
    try:
        user_id = user_info['user_id']
        user_name = user_info['name']
        
        # Obtener historial para contexto
        conversation_history = await memory_service.get_conversation_history(user_id, limit=3)
        
        # Generar respuesta con asistente personalizado
        ai_response = await generate_ai_response(
            chat_msg.message, 
            user_id, 
            user_name, 
            conversation_history
        )
        
        # Guardar conversación
        storage_info, message_id = await memory_service.store_conversation(
            user_id,
            chat_msg.message,
            ai_response
        )
        
        return ChatResponse(
            response=ai_response,
            user_id=user_id,
            user_name=user_name,
            message_id=message_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            storage_info=storage_info
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/api/chat/history")
async def get_chat_history(
    limit: int = 20,
    user_info: dict = Depends(get_user_identity)
):
    """Obtener historial de chat del usuario"""
    try:
        user_id = user_info['user_id']
        history = await memory_service.get_conversation_history(user_id, limit)
        
        return {
            "user_id": user_id,
            "user_name": user_info['name'],
            "total_messages": len(history),
            "history": history
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check con estado completo del sistema"""
    storage_status = await memory_service.get_status()
    ai_status = await check_ai_status()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "3.0.0",
        "services": {
            "mongodb": storage_status.get("mongodb", False),
            "openai": {
                "configured": ai_status.get("openai_configured", False),
                "available": ai_status.get("openai_available", False),
                "assistant_available": ai_status.get("assistant_available", False)
            }
        }
    }

# Endpoint de prueba sin autenticación (solo para desarrollo)
@app.post("/api/chat/test")
async def test_chat(chat_msg: ChatMessage):
    """Endpoint de prueba sin autenticación - solo para desarrollo"""
    try:
        ai_response = await generate_ai_response(
            chat_msg.message, 
            "test_user", 
            "Test User", 
            []
        )
        
        return {
            "response": ai_response,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Eventos de inicio
@app.on_event("startup")
async def startup_event():
    """Inicializar servicios"""
    print("Iniciando Chat Service - Merval Inteligente...")
    connections = await memory_service.connect()
    ai_status = await check_ai_status()
    
    print(f"MongoDB: {'✅' if connections['mongodb'] else '❌'}")
    print(f"OpenAI: {'✅' if ai_status['openai_available'] else '❌'}")
    print(f"Asistente: {'✅' if ai_status['assistant_available'] else '❌'}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('PORT', 8084))
    host = os.getenv('HOST', '0.0.0.0')
    uvicorn.run(app, host=host, port=port)