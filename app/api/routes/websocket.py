"""
Handlers de WebSocket para chat en tiempo real
"""
import json
import asyncio
from typing import Dict, Set
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
from loguru import logger

from ...models.chat import WebSocketMessage, ChatMessage, MessageType, OpenAIMessage, MessageRole
from ...models.user import TokenPayload
from ...services.auth_service import auth_service
from ...services.openai_service import openai_service
from ...services.memory_service import memory_service
from ...services.context_service import context_service


router = APIRouter()


class WebSocketManager:
    """Manejador de conexiones WebSocket"""
    
    def __init__(self):
        # Conexiones activas: {user_id: {websocket, last_activity}}
        self.active_connections: Dict[str, Dict] = {}
        # Usuarios escribiendo: {user_id: timestamp}
        self.typing_users: Dict[str, datetime] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str):
        """Conecta un usuario"""
        await websocket.accept()
        
        self.active_connections[user_id] = {
            "websocket": websocket,
            "last_activity": datetime.utcnow(),
            "connected_at": datetime.utcnow()
        }
        
        logger.info(f"Usuario {user_id} conectado via WebSocket")
        
        # Notificar conexión exitosa
        await self.send_personal_message({
            "type": "connection_established",
            "data": {
                "user_id": user_id,
                "message": "Conectado al chat inteligente",
                "timestamp": datetime.utcnow().isoformat()
            }
        }, user_id)
    
    def disconnect(self, user_id: str):
        """Desconecta un usuario"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            
        if user_id in self.typing_users:
            del self.typing_users[user_id]
            
        logger.info(f"Usuario {user_id} desconectado")
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Envía mensaje a un usuario específico"""
        if user_id in self.active_connections:
            try:
                websocket = self.active_connections[user_id]["websocket"]
                await websocket.send_text(json.dumps(message))
                
                # Actualizar actividad
                self.active_connections[user_id]["last_activity"] = datetime.utcnow()
                
            except Exception as e:
                logger.error(f"Error enviando mensaje a {user_id}: {str(e)}")
                # Remover conexión inválida
                self.disconnect(user_id)
    
    async def broadcast_typing(self, user_id: str, is_typing: bool):
        """Notifica que un usuario está escribiendo"""
        if is_typing:
            self.typing_users[user_id] = datetime.utcnow()
        else:
            self.typing_users.pop(user_id, None)
    
    def is_user_connected(self, user_id: str) -> bool:
        """Verifica si un usuario está conectado"""
        return user_id in self.active_connections
    
    def get_connected_users_count(self) -> int:
        """Obtiene cantidad de usuarios conectados"""
        return len(self.active_connections)


# Singleton manager
ws_manager = WebSocketManager()


async def get_websocket_user(websocket: WebSocket) -> TokenPayload:
    """
    Obtiene el usuario autenticado desde el WebSocket
    
    Args:
        websocket: Conexión WebSocket
        
    Returns:
        Usuario autenticado
    """
    try:
        # Obtener token del query parameter
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise Exception("Token requerido")
        
        # Verificar token
        token_payload = auth_service.verify_token(token)
        if not token_payload:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise Exception("Token inválido")
        
        return token_payload
        
    except Exception as e:
        logger.error(f"Error en autenticación WebSocket: {str(e)}")
        raise


@router.websocket("/chat/{user_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    user_id: str
):
    """
    Endpoint principal de WebSocket para chat
    
    Args:
        websocket: Conexión WebSocket
        user_id: ID del usuario
    """
    current_user = None
    
    try:
        # Autenticar usuario
        current_user = await get_websocket_user(websocket)
        
        # Verificar que el user_id coincida
        if current_user.sub != user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Conectar usuario
        await ws_manager.connect(websocket, user_id)
        
        # Loop principal de mensajes
        while True:
            try:
                # Recibir mensaje
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Procesar mensaje según tipo
                await handle_websocket_message(user_id, message_data, current_user)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await ws_manager.send_personal_message({
                    "type": "error",
                    "data": {"message": "Formato de mensaje inválido"}
                }, user_id)
            except Exception as e:
                logger.error(f"Error procesando mensaje WebSocket: {str(e)}")
                await ws_manager.send_personal_message({
                    "type": "error", 
                    "data": {"message": "Error procesando mensaje"}
                }, user_id)
                
    except Exception as e:
        logger.error(f"Error en conexión WebSocket: {str(e)}")
    finally:
        if current_user:
            ws_manager.disconnect(user_id)


async def handle_websocket_message(user_id: str, message_data: dict, current_user: TokenPayload):
    """
    Maneja mensajes recibidos via WebSocket
    
    Args:
        user_id: ID del usuario
        message_data: Datos del mensaje
        current_user: Usuario autenticado
    """
    message_type = message_data.get("type")
    data = message_data.get("data", {})
    
    try:
        if message_type == "send_message":
            await handle_chat_message(user_id, data, current_user)
            
        elif message_type == "typing_start":
            await handle_typing_indicator(user_id, True)
            
        elif message_type == "typing_stop":
            await handle_typing_indicator(user_id, False)
            
        elif message_type == "join_chat":
            await handle_join_chat(user_id, data)
            
        elif message_type == "ping":
            await handle_ping(user_id)
            
        else:
            await ws_manager.send_personal_message({
                "type": "error",
                "data": {"message": f"Tipo de mensaje no soportado: {message_type}"}
            }, user_id)
            
    except Exception as e:
        logger.error(f"Error manejando mensaje {message_type}: {str(e)}")
        await ws_manager.send_personal_message({
            "type": "error",
            "data": {"message": "Error procesando mensaje"}
        }, user_id)


async def handle_chat_message(user_id: str, data: dict, current_user: TokenPayload):
    """Maneja mensaje de chat"""
    message_text = data.get("message", "").strip()
    
    if not message_text:
        await ws_manager.send_personal_message({
            "type": "error",
            "data": {"message": "Mensaje vacío"}
        }, user_id)
        return
    
    try:
        import uuid
        
        # Crear mensaje del usuario
        user_message = ChatMessage(
            id=str(uuid.uuid4()),
            user_id=user_id,
            message=message_text,
            message_type=MessageType.USER
        )
        
        # Confirmar recepción del mensaje
        await ws_manager.send_personal_message({
            "type": "message_received",
            "data": {
                "message_id": user_message.id,
                "timestamp": user_message.timestamp.isoformat()
            }
        }, user_id)
        
        # Guardar mensaje del usuario
        await memory_service.save_message(user_id, user_message)
        
        # Indicar que la IA está escribiendo
        await ws_manager.send_personal_message({
            "type": "ai_typing_start",
            "data": {"message": "El asistente está escribiendo..."}
        }, user_id)
        
        # Obtener contexto del usuario
        try:
            # Aquí necesitaríamos el token para obtener contexto
            # Por ahora continuamos sin contexto
            user_context = None
        except:
            user_context = None
        
        # Obtener historial y generar respuesta
        conversation_history = await memory_service.get_conversation_history(user_id)
        conversation_history.append(OpenAIMessage(
            role=MessageRole.USER,
            content=message_text
        ))
        
        # Generar respuesta con IA
        ai_response = await openai_service.generate_response(
            messages=conversation_history,
            user_context=user_context
        )
        
        # Crear mensaje de respuesta
        assistant_message = ChatMessage(
            id=str(uuid.uuid4()),
            user_id=user_id,
            message=ai_response,
            message_type=MessageType.ASSISTANT
        )
        
        # Guardar respuesta
        await memory_service.save_message(user_id, assistant_message)
        
        # Enviar respuesta de la IA
        await ws_manager.send_personal_message({
            "type": "ai_response",
            "data": {
                "message_id": assistant_message.id,
                "message": ai_response,
                "timestamp": assistant_message.timestamp.isoformat(),
                "model": "gpt-4-turbo-preview"
            }
        }, user_id)
        
        # Detener indicador de escritura
        await ws_manager.send_personal_message({
            "type": "ai_typing_stop",
            "data": {}
        }, user_id)
        
    except Exception as e:
        logger.error(f"Error procesando mensaje de chat: {str(e)}")
        
        # Detener indicador de escritura en caso de error
        await ws_manager.send_personal_message({
            "type": "ai_typing_stop",
            "data": {}
        }, user_id)
        
        await ws_manager.send_personal_message({
            "type": "error",
            "data": {"message": "Error generando respuesta. Intenta nuevamente."}
        }, user_id)


async def handle_typing_indicator(user_id: str, is_typing: bool):
    """Maneja indicador de escritura"""
    await ws_manager.broadcast_typing(user_id, is_typing)


async def handle_join_chat(user_id: str, data: dict):
    """Maneja unión al chat"""
    await ws_manager.send_personal_message({
        "type": "chat_joined",
        "data": {
            "user_id": user_id,
            "message": "Te has unido al chat inteligente",
            "features": [
                "Chat en tiempo real",
                "Asistente de IA financiero", 
                "Análisis de mercado argentino",
                "Recomendaciones personalizadas"
            ]
        }
    }, user_id)


async def handle_ping(user_id: str):
    """Maneja ping para mantener conexión"""
    await ws_manager.send_personal_message({
        "type": "pong",
        "data": {"timestamp": datetime.utcnow().isoformat()}
    }, user_id)


@router.get("/stats")
async def get_websocket_stats():
    """Obtiene estadísticas de WebSocket"""
    return {
        "connected_users": ws_manager.get_connected_users_count(),
        "typing_users": len(ws_manager.typing_users),
        "timestamp": datetime.utcnow().isoformat()
    }
