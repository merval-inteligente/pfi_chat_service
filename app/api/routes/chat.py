"""
Rutas para el sistema de chat
Extraído de chat_service_real.py
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone

from app.models.chat import ChatMessage, ChatResponse
from app.services.memory_service import memory_service
from app.services.ai_service import generate_ai_response
from app.core.auth import get_user_identity

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("/message", response_model=ChatResponse)
async def send_message(
    chat_msg: ChatMessage, 
    user_info: dict = Depends(get_user_identity)
):
    """Enviar mensaje de chat - usuario autenticado automáticamente"""
    try:
        user_id = user_info['user_id']
        user_name = user_info['name']
        
        # Generar respuesta con información del usuario validado
        ai_response = await generate_ai_response(chat_msg.message, user_id, user_name)
        
        # Guardar conversación con user_id validado
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

@router.get("/history")
async def get_my_chat_history(
    limit: int = 20,
    user_info: dict = Depends(get_user_identity)
):
    """Obtener historial de chat del usuario autenticado"""
    try:
        user_id = user_info['user_id']
        history = await memory_service.get_conversation_history(user_id, limit)
        status = await memory_service.get_status()
        
        return {
            "user_id": user_id,
            "user_name": user_info['name'],
            "total_messages": len(history),
            "history": history,
            "storage_status": status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/history/{user_id}")
async def get_user_chat_history(
    user_id: str,
    limit: int = 20,
    user_info: dict = Depends(get_user_identity)
):
    """Obtener historial de chat por user_id (compatibilidad - solo del usuario autenticado)"""
    try:
        # Por seguridad, solo permitir acceso al propio historial
        authenticated_user_id = user_info['user_id']
        
        if user_id != authenticated_user_id:
            raise HTTPException(
                status_code=403, 
                detail="Solo puedes acceder a tu propio historial"
            )
        
        history = await memory_service.get_conversation_history(user_id, limit)
        status = await memory_service.get_status()
        
        return {
            "user_id": user_id,
            "user_name": user_info['name'],
            "total_messages": len(history),
            "history": history,
            "storage_status": status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
