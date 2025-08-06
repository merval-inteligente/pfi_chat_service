"""
Versión simplificada del servicio de memoria para testing
"""
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from loguru import logger

from ..simple_config import get_simple_settings
from ..models.chat import ChatMessage, OpenAIMessage, MessageRole, ChatSession


class SimpleMemoryService:
    """Servicio de memoria simplificado usando almacenamiento en memoria"""
    
    def __init__(self):
        self.settings = get_simple_settings()
        # Almacenamiento en memoria
        self._messages_store: Dict[str, List[Dict]] = {}
        self._sessions_store: Dict[str, Dict] = {}
        
    async def save_message(self, user_id: str, message: ChatMessage) -> bool:
        """
        Guarda un mensaje en memoria
        
        Args:
            user_id: ID del usuario
            message: Mensaje a guardar
            
        Returns:
            True si se guardó exitosamente
        """
        try:
            # Inicializar si no existe
            if user_id not in self._messages_store:
                self._messages_store[user_id] = []
            
            # Serializar mensaje
            message_data = {
                "id": message.id,
                "user_id": message.user_id,
                "message": message.message,
                "message_type": message.message_type.value,
                "timestamp": message.timestamp.isoformat(),
                "metadata": message.metadata
            }
            
            # Agregar al principio de la lista
            self._messages_store[user_id].insert(0, message_data)
            
            # Mantener solo los últimos N mensajes
            max_messages = self.settings.max_context_messages * 2
            if len(self._messages_store[user_id]) > max_messages:
                self._messages_store[user_id] = self._messages_store[user_id][:max_messages]
            
            # Actualizar actividad de la sesión
            await self._update_session_activity(user_id)
            
            logger.debug(f"Mensaje guardado en memoria para usuario {user_id}")
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
            limit: Límite de mensajes
            
        Returns:
            Lista de mensajes para OpenAI
        """
        try:
            # Obtener mensajes del usuario
            user_messages = self._messages_store.get(user_id, [])
            
            # Aplicar límite
            max_messages = limit or self.settings.max_context_messages
            recent_messages = user_messages[:max_messages]
            
            # Convertir a formato OpenAI (orden cronológico)
            openai_messages = []
            for msg_data in reversed(recent_messages):
                try:
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
            user_messages = self._messages_store.get(user_id, [])
            recent_messages = user_messages[:limit]
            
            messages = []
            for msg_data in reversed(recent_messages):
                try:
                    message = ChatMessage(
                        id=msg_data["id"],
                        user_id=msg_data["user_id"],
                        message=msg_data["message"],
                        message_type=msg_data["message_type"],
                        timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                        metadata=msg_data.get("metadata")
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
            # Limpiar mensajes
            if user_id in self._messages_store:
                del self._messages_store[user_id]
            
            # Limpiar sesión
            if user_id in self._sessions_store:
                del self._sessions_store[user_id]
            
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
            session = ChatSession(
                session_id=f"{user_id}_{int(datetime.utcnow().timestamp())}",
                user_id=user_id,
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow()
            )
            
            # Guardar sesión en memoria
            self._sessions_store[user_id] = {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "messages_count": session.messages_count,
                "is_active": session.is_active
            }
            
            logger.info(f"Sesión creada en memoria para usuario {user_id}")
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
            session_data = self._sessions_store.get(user_id)
            
            if not session_data:
                return None
            
            session = ChatSession(
                session_id=session_data["session_id"],
                user_id=session_data["user_id"],
                created_at=datetime.fromisoformat(session_data["created_at"]),
                last_activity=datetime.fromisoformat(session_data["last_activity"]),
                messages_count=int(session_data["messages_count"]),
                is_active=session_data["is_active"]
            )
            
            return session
            
        except Exception as e:
            logger.error(f"Error al obtener sesión: {str(e)}")
            return None
    
    async def _update_session_activity(self, user_id: str):
        """Actualiza la actividad de la sesión"""
        try:
            if user_id in self._sessions_store:
                # Actualizar timestamp y contador
                self._sessions_store[user_id]["last_activity"] = datetime.utcnow().isoformat()
                self._sessions_store[user_id]["messages_count"] += 1
            else:
                # Crear nueva sesión
                await self.create_session(user_id)
                
        except Exception as e:
            logger.error(f"Error al actualizar actividad de sesión: {str(e)}")


# Singleton instance para testing
simple_memory_service = SimpleMemoryService()
