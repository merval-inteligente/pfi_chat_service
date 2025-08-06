"""
Rutas de Chat API
"""
import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from loguru import logger

from ...models.chat import (
    ChatMessageCreate, 
    ChatMessageResponse, 
    ChatMessage, 
    ChatHistory,
    MessageType,
    UserContext
)
from ...models.user import User
from ...core.auth import get_current_active_user
from ...services.openai_service import openai_service
from ...services.memory_service import memory_service
from ...services.context_service import context_service
from ...api.deps import get_user_context, verify_chat_access, chat_rate_limit, history_rate_limit


router = APIRouter()


@router.post("/message", response_model=ChatMessageResponse)
async def send_chat_message(
    request: Request,
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_active_user),
    user_context: Optional[UserContext] = Depends(get_user_context)
):
    """
    Envía un mensaje al chat y recibe respuesta de IA
    
    Args:
        request: Request object
        message_data: Datos del mensaje
        current_user: Usuario actual
        user_context: Contexto del usuario
        
    Returns:
        Respuesta del asistente de IA
    """
    try:
        # Aplicar rate limiting
        # await chat_rate_limit(request)
        
        user_id = current_user.sub
        message_id = str(uuid.uuid4())
        
        # Crear mensaje del usuario
        user_message = ChatMessage(
            id=message_id,
            user_id=user_id,
            message=message_data.message,
            message_type=MessageType.USER,
            metadata=message_data.user_context
        )
        
        # Guardar mensaje del usuario
        await memory_service.save_message(user_id, user_message)
        
        # Obtener historial de conversación
        conversation_history = await memory_service.get_conversation_history(user_id)
        
        # Agregar mensaje actual al historial
        from ...models.chat import OpenAIMessage, MessageRole
        conversation_history.append(OpenAIMessage(
            role=MessageRole.USER,
            content=message_data.message
        ))
        
        # Generar respuesta con IA
        ai_response = await openai_service.generate_response(
            messages=conversation_history,
            user_context=user_context
        )
        
        # Crear mensaje de respuesta
        response_id = str(uuid.uuid4())
        assistant_message = ChatMessage(
            id=response_id,
            user_id=user_id,
            message=ai_response,
            message_type=MessageType.ASSISTANT,
            metadata={
                "model": "gpt-4-turbo-preview",
                "context_used": bool(user_context),
                "conversation_length": len(conversation_history)
            }
        )
        
        # Guardar respuesta del asistente
        await memory_service.save_message(user_id, assistant_message)
        
        # Preparar respuesta
        response = ChatMessageResponse(
            message_id=response_id,
            user_message=message_data.message,
            assistant_response=ai_response,
            timestamp=datetime.utcnow(),
            context_used=user_context.dict() if user_context else None,
            model_info={
                "model": "gpt-4-turbo-preview",
                "provider": "openai"
            }
        )
        
        logger.info(f"Mensaje procesado para usuario {user_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error al procesar mensaje: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al procesar el mensaje. Por favor, intenta nuevamente."
        )


@router.get("/history/{user_id}", response_model=ChatHistory)
async def get_chat_history(
    request: Request,
    user_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(verify_chat_access)
):
    """
    Obtiene el historial de chat del usuario
    
    Args:
        request: Request object
        user_id: ID del usuario
        limit: Límite de mensajes
        current_user: Usuario actual
        
    Returns:
        Historial de chat
    """
    try:
        # Aplicar rate limiting
        # await history_rate_limit(request)
        
        # Obtener mensajes del historial
        messages = await memory_service.get_chat_history(user_id, limit)
        
        # Preparar respuesta
        history = ChatHistory(
            user_id=user_id,
            messages=messages,
            total_messages=len(messages),
            last_activity=messages[0].timestamp if messages else datetime.utcnow()
        )
        
        logger.info(f"Historial obtenido para usuario {user_id}: {len(messages)} mensajes")
        return history
        
    except Exception as e:
        logger.error(f"Error al obtener historial: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener el historial"
        )


@router.delete("/history/{user_id}")
async def clear_chat_history(
    request: Request,
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(verify_chat_access)
):
    """
    Limpia el historial de chat del usuario
    
    Args:
        request: Request object
        user_id: ID del usuario
        current_user: Usuario actual
        
    Returns:
        Confirmación de limpieza
    """
    try:
        # Aplicar rate limiting
        # await history_rate_limit(request)
        
        # Limpiar conversación
        success = await memory_service.clear_conversation(user_id)
        
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


@router.get("/summary/{user_id}")
async def get_conversation_summary(
    request: Request,
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(verify_chat_access)
):
    """
    Obtiene un resumen de la conversación
    
    Args:
        request: Request object
        user_id: ID del usuario
        current_user: Usuario actual
        
    Returns:
        Resumen de la conversación
    """
    try:
        # Aplicar rate limiting
        # await history_rate_limit(request)
        
        # Obtener historial para el resumen
        conversation_history = await memory_service.get_conversation_history(user_id)
        
        if not conversation_history:
            return {"summary": "No hay conversación para resumir"}
        
        # Generar resumen
        summary = await openai_service.summarize_conversation(conversation_history)
        
        logger.info(f"Resumen generado para usuario {user_id}")
        return {
            "summary": summary,
            "messages_count": len(conversation_history),
            "generated_at": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error al generar resumen: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al generar resumen de la conversación"
        )


@router.post("/analyze-sentiment")
async def analyze_message_sentiment(
    request: Request,
    message: dict,
    current_user: User = Depends(get_current_active_user)
):
    """
    Analiza el sentimiento de un mensaje
    
    Args:
        request: Request object
        message: Mensaje a analizar
        current_user: Usuario actual
        
    Returns:
        Análisis de sentimiento
    """
    try:
        text = message.get("text", "")
        if not text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Texto requerido para análisis"
            )
        
        # Analizar sentimiento
        sentiment_analysis = await openai_service.analyze_sentiment(text)
        
        logger.info(f"Análisis de sentimiento realizado para usuario {current_user.sub}")
        return sentiment_analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en análisis de sentimiento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al analizar sentimiento"
        )
