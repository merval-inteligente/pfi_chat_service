"""
Servicio de gestión de memoria del chat
"""
import json
import redis.asyncio as redis
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from loguru import logger

from ..config import get_settings
from ..models.chat import ChatMessage, OpenAIMessage, MessageRole, ChatSession


class MemoryService:
    """Servicio para gestionar la memoria del chat usando Redis"""
    
    def __init__(self):
        self.settings = get_settings()
        self.redis_pool = None
        
    async def get_redis_client(self) -> redis.Redis:
        """Obtiene cliente Redis"""
        if not self.redis_pool:
            self.redis_pool = redis.ConnectionPool.from_url(
                self.settings.redis_url,
                max_connections=self.settings.redis_max_connections,
                socket_timeout=self.settings.redis_timeout,
                decode_responses=True
            )
        return redis.Redis(connection_pool=self.redis_pool)
    
    async def save_message(self, user_id: str, message: ChatMessage) -> bool:
        """
        Guarda un mensaje en la memoria
        
        Args:
            user_id: ID del usuario
            message: Mensaje a guardar
            
        Returns:
            True si se guardó exitosamente
        """
        try:
            client = await self.get_redis_client()
            
            # Clave para los mensajes del usuario
            messages_key = f"chat:messages:{user_id}"
            
            # Serializar mensaje
            message_data = {
                "id": message.id,
                "user_id": message.user_id,
                "message": message.message,
                "message_type": message.message_type.value,
                "timestamp": message.timestamp.isoformat(),
                "metadata": json.dumps(message.metadata) if message.metadata else None
            }
            
            # Guardar en lista de Redis (LPUSH para orden cronológico inverso)
            await client.lpush(messages_key, json.dumps(message_data))
            
            # Mantener solo los últimos N mensajes
            max_messages = self.settings.max_context_messages * 2  # User + Assistant
            await client.ltrim(messages_key, 0, max_messages - 1)
            
            # Establecer TTL para la clave
            await client.expire(messages_key, self.settings.session_timeout)
            
            # Actualizar actividad de la sesión
            await self._update_session_activity(user_id)
            
            logger.debug(f"Mensaje guardado para usuario {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error al guardar mensaje: {str(e)}")
            return False
    
    async def get_conversation_history(
        self, 
        user_id: str, 
        limit: Optional[int] = None
    ) -> List[OpenAIMessage]:
        """
        Obtiene el historial de conversación para OpenAI
        
        Args:
            user_id: ID del usuario
            limit: Límite de mensajes (None para usar configuración)
            
        Returns:
            Lista de mensajes para OpenAI
        """
        try:
            client = await self.get_redis_client()
            messages_key = f"chat:messages:{user_id}"
            
            # Obtener mensajes (más recientes primero)
            max_messages = limit or self.settings.max_context_messages
            raw_messages = await client.lrange(messages_key, 0, max_messages - 1)
            
            # Procesar mensajes
            openai_messages = []
            for raw_msg in reversed(raw_messages):  # Revertir para orden cronológico
                try:
                    msg_data = json.loads(raw_msg)
                    role = MessageRole.USER if msg_data["message_type"] == "user" else MessageRole.ASSISTANT
                    
                    openai_messages.append(OpenAIMessage(
                        role=role,
                        content=msg_data["message"]
                    ))
                except Exception as e:
                    logger.warning(f"Error al procesar mensaje: {str(e)}")
                    continue
            
            logger.debug(f"Recuperados {len(openai_messages)} mensajes para usuario {user_id}")
            return openai_messages
            
        except Exception as e:
            logger.error(f"Error al obtener historial: {str(e)}")
            return []
    
    async def get_chat_history(self, user_id: str, limit: int = 50) -> List[ChatMessage]:
        """
        Obtiene historial completo de chat
        
        Args:
            user_id: ID del usuario
            limit: Límite de mensajes
            
        Returns:
            Lista de mensajes de chat
        """
        try:
            client = await self.get_redis_client()
            messages_key = f"chat:messages:{user_id}"
            
            raw_messages = await client.lrange(messages_key, 0, limit - 1)
            
            messages = []
            for raw_msg in reversed(raw_messages):
                try:
                    msg_data = json.loads(raw_msg)
                    
                    message = ChatMessage(
                        id=msg_data["id"],
                        user_id=msg_data["user_id"],
                        message=msg_data["message"],
                        message_type=msg_data["message_type"],
                        timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                        metadata=json.loads(msg_data["metadata"]) if msg_data["metadata"] else None
                    )
                    messages.append(message)
                    
                except Exception as e:
                    logger.warning(f"Error al procesar mensaje: {str(e)}")
                    continue
            
            return messages
            
        except Exception as e:
            logger.error(f"Error al obtener historial de chat: {str(e)}")
            return []
    
    async def clear_conversation(self, user_id: str) -> bool:
        """
        Limpia la conversación del usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            True si se limpió exitosamente
        """
        try:
            client = await self.get_redis_client()
            
            # Eliminar mensajes
            messages_key = f"chat:messages:{user_id}"
            await client.delete(messages_key)
            
            # Eliminar sesión
            session_key = f"chat:session:{user_id}"
            await client.delete(session_key)
            
            logger.info(f"Conversación limpiada para usuario {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error al limpiar conversación: {str(e)}")
            return False
    
    async def create_session(self, user_id: str) -> ChatSession:
        """
        Crea una nueva sesión de chat
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Sesión de chat creada
        """
        try:
            client = await self.get_redis_client()
            
            session = ChatSession(
                session_id=f"{user_id}_{int(datetime.utcnow().timestamp())}",
                user_id=user_id,
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow()
            )
            
            # Guardar sesión
            session_key = f"chat:session:{user_id}"
            session_data = {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "messages_count": session.messages_count,
                "is_active": session.is_active
            }
            
            await client.hset(session_key, mapping=session_data)
            await client.expire(session_key, self.settings.session_timeout)
            
            logger.info(f"Sesión creada para usuario {user_id}")
            return session
            
        except Exception as e:
            logger.error(f"Error al crear sesión: {str(e)}")
            # Retornar sesión por defecto
            return ChatSession(
                session_id=f"{user_id}_default",
                user_id=user_id,
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow()
            )
    
    async def get_session(self, user_id: str) -> Optional[ChatSession]:
        """
        Obtiene la sesión activa del usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Sesión activa o None
        """
        try:
            client = await self.get_redis_client()
            session_key = f"chat:session:{user_id}"
            
            session_data = await client.hgetall(session_key)
            
            if not session_data:
                return None
            
            session = ChatSession(
                session_id=session_data["session_id"],
                user_id=session_data["user_id"],
                created_at=datetime.fromisoformat(session_data["created_at"]),
                last_activity=datetime.fromisoformat(session_data["last_activity"]),
                messages_count=int(session_data["messages_count"]),
                is_active=session_data["is_active"] == "True"
            )
            
            return session
            
        except Exception as e:
            logger.error(f"Error al obtener sesión: {str(e)}")
            return None
    
    async def _update_session_activity(self, user_id: str):
        """Actualiza la actividad de la sesión"""
        try:
            client = await self.get_redis_client()
            session_key = f"chat:session:{user_id}"
            
            # Verificar si existe la sesión
            if await client.exists(session_key):
                # Actualizar timestamp y contador
                await client.hset(session_key, "last_activity", datetime.utcnow().isoformat())
                await client.hincrby(session_key, "messages_count", 1)
                await client.expire(session_key, self.settings.session_timeout)
            else:
                # Crear nueva sesión
                await self.create_session(user_id)
                
        except Exception as e:
            logger.error(f"Error al actualizar actividad de sesión: {str(e)}")
    
    async def cleanup_expired_sessions(self):
        """Limpia sesiones expiradas (tarea de mantenimiento)"""
        try:
            client = await self.get_redis_client()
            
            # Esta función sería llamada por un scheduler
            # Redis se encarga automáticamente del TTL, pero podríamos hacer limpieza adicional
            
            logger.debug("Limpieza de sesiones completada")
            
        except Exception as e:
            logger.error(f"Error en limpieza de sesiones: {str(e)}")


# Singleton instance
memory_service = MemoryService()
