"""
Aplicación principal FastAPI - Chat Service (Versión de Testing)
"""
import uuid
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, status, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from loguru import logger
import sys

# Configurar logging simple
logger.remove()
logger.add(sys.stdout, level="INFO", format="{time} | {level} | {message}")

# Importaciones locales
from app.simple_config import get_simple_settings
from app.models.chat import (
    ChatMessageCreate, 
    ChatMessageResponse, 
    ChatMessage, 
    MessageType,
    HealthCheck
)
from app.models.user import TokenPayload
from app.services.simple_openai_service import simple_openai_service
from app.services.simple_memory_service import simple_memory_service
from app.services.auth_service import auth_service

# Configuración
settings = get_simple_settings()
security = HTTPBearer(auto_error=False)

# Crear aplicación FastAPI
app = FastAPI(
    title="Chat Service - Testing",
    description="Microservicio de Chat Inteligente - Versión de Testing",
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

# Helper para autenticación opcional (para testing)
async def get_optional_user(request: Request) -> Optional[TokenPayload]:
    """Obtiene usuario de forma opcional para testing"""
    try:
        auth = request.headers.get("authorization")
        if not auth:
            # Para testing, crear usuario demo
            return TokenPayload(sub="demo-user-123")
        
        token = auth.replace("Bearer ", "")
        
        # Para testing, aceptar tokens demo
        if token.startswith("demo-"):
            return TokenPayload(sub=token.replace("demo-", "user-"))
        
        # Intentar validar token real
        return auth_service.verify_token(token)
        
    except Exception:
        # En caso de error, usar usuario demo
        return TokenPayload(sub="demo-user-123")

# Middleware para logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware para logging de requests"""
    start_time = datetime.utcnow()
    
    response = await call_next(request)
    
    process_time = (datetime.utcnow() - start_time).total_seconds()
    
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    
    return response

# Health Check
@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0-testing",
        services={
            "memory": "healthy",
            "openai": "demo" if simple_openai_service.demo_mode else "healthy",
            "auth": "testing"
        }
    )

# Endpoint raíz
@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "service": "Chat Service - Testing",
        "version": "1.0.0-testing",
        "status": "running",
        "docs": "/docs",
        "timestamp": datetime.utcnow().isoformat(),
        "demo_mode": simple_openai_service.demo_mode
    }

# Endpoint de chat principal
@app.post("/api/chat/message", response_model=ChatMessageResponse)
async def send_chat_message(
    message_data: ChatMessageCreate,
    request: Request,
    current_user: Optional[TokenPayload] = Depends(get_optional_user)
):
    """
    Envía un mensaje al chat y recibe respuesta de IA
    """
    try:
        user_id = current_user.sub if current_user else "anonymous"
        message_id = str(uuid.uuid4())
        
        logger.info(f"Procesando mensaje de usuario {user_id}")
        
        # Crear mensaje del usuario
        user_message = ChatMessage(
            id=message_id,
            user_id=user_id,
            message=message_data.message,
            message_type=MessageType.USER,
            metadata=message_data.user_context
        )
        
        # Guardar mensaje del usuario
        await simple_memory_service.save_message(user_id, user_message)
        
        # Obtener historial de conversación
        conversation_history = await simple_memory_service.get_conversation_history(user_id)
        
        # Agregar mensaje actual al historial
        from app.models.chat import OpenAIMessage, MessageRole
        conversation_history.append(OpenAIMessage(
            role=MessageRole.USER,
            content=message_data.message
        ))
        
        # Generar respuesta con IA (o demo)
        ai_response = await simple_openai_service.generate_response(
            messages=conversation_history,
            user_context=None  # Sin contexto para testing
        )
        
        # Crear mensaje de respuesta
        response_id = str(uuid.uuid4())
        assistant_message = ChatMessage(
            id=response_id,
            user_id=user_id,
            message=ai_response,
            message_type=MessageType.ASSISTANT,
            metadata={
                "model": settings.openai_model,
                "demo_mode": simple_openai_service.demo_mode,
                "conversation_length": len(conversation_history)
            }
        )
        
        # Guardar respuesta del asistente
        await simple_memory_service.save_message(user_id, assistant_message)
        
        # Preparar respuesta
        response = ChatMessageResponse(
            message_id=response_id,
            user_message=message_data.message,
            assistant_response=ai_response,
            timestamp=datetime.utcnow(),
            context_used=None,
            model_info={
                "model": settings.openai_model,
                "provider": "openai" if not simple_openai_service.demo_mode else "demo",
                "demo_mode": simple_openai_service.demo_mode
            }
        )
        
        logger.info(f"Mensaje procesado exitosamente para usuario {user_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error al procesar mensaje: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar el mensaje: {str(e)}"
        )

# Obtener historial
@app.get("/api/chat/history/{user_id}")
async def get_chat_history(
    user_id: str,
    limit: int = 50,
    current_user: Optional[TokenPayload] = Depends(get_optional_user)
):
    """Obtiene el historial de chat del usuario"""
    try:
        # Para testing, permitir acceso a cualquier usuario
        messages = await simple_memory_service.get_chat_history(user_id, limit)
        
        return {
            "user_id": user_id,
            "messages": messages,
            "total_messages": len(messages),
            "last_activity": messages[0].timestamp if messages else datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error al obtener historial: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener el historial"
        )

# Limpiar historial
@app.delete("/api/chat/history/{user_id}")
async def clear_chat_history(
    user_id: str,
    current_user: Optional[TokenPayload] = Depends(get_optional_user)
):
    """Limpia el historial de chat del usuario"""
    try:
        success = await simple_memory_service.clear_conversation(user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al limpiar el historial"
            )
        
        logger.info(f"Historial limpiado para usuario {user_id}")
        return {"message": "Historial limpiado exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al limpiar historial: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al limpiar el historial"
        )

# Análisis de sentimiento
@app.post("/api/chat/analyze-sentiment")
async def analyze_sentiment(
    data: dict,
    current_user: Optional[TokenPayload] = Depends(get_optional_user)
):
    """Analiza el sentimiento de un mensaje"""
    try:
        text = data.get("text", "")
        if not text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Texto requerido para análisis"
            )
        
        sentiment_analysis = await simple_openai_service.analyze_sentiment(text)
        
        return sentiment_analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en análisis de sentimiento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al analizar sentimiento"
        )

# Información del servicio
@app.get("/api/info")
async def get_service_info():
    """Información del servicio"""
    return {
        "service": "Chat Service",
        "version": "1.0.0-testing",
        "demo_mode": simple_openai_service.demo_mode,
        "features": [
            "Chat con IA financiera",
            "Historial de conversaciones",
            "Análisis de sentimiento",
            "Especialización en mercado argentino"
        ],
        "endpoints": [
            "POST /api/chat/message - Enviar mensaje",
            "GET /api/chat/history/{user_id} - Obtener historial",
            "DELETE /api/chat/history/{user_id} - Limpiar historial",
            "POST /api/chat/analyze-sentiment - Análisis de sentimiento",
            "GET /health - Health check"
        ],
        "demo_instructions": {
            "message": "Para testing, puedes enviar mensajes sin autenticación",
            "sample_request": {
                "url": "/api/chat/message",
                "method": "POST",
                "body": {"message": "¿Cómo está el MERVAL hoy?"}
            }
        }
    }

# Manejadores de errores
@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception):
    """Manejador de errores internos del servidor"""
    logger.error(f"Error interno en {request.url}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Error interno del servidor",
            "message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main_simple:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info"
    )
