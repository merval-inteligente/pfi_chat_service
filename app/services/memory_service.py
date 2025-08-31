"""
Servicio de memoria y base de datos
Extraído de chat_service_real.py
"""

import motor.motor_asyncio
from datetime import datetime, timezone
from typing import Dict, List
from app.core.config import MONGODB_URI, MONGODB_DB_NAME

class MemoryService:
    def __init__(self):
        self.mongo_client = None
        self.db = None
        self.chat_collection = None
        self.memory_fallback = {}
        self.mongo_connected = False
        
    async def connect(self):
        """Conectar a MongoDB"""
        # MongoDB (prioritario)
        try:
            self.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(
                MONGODB_URI,
                serverSelectionTimeoutMS=5000
            )
            await self.mongo_client.admin.command('ping')
            self.db = self.mongo_client[MONGODB_DB_NAME]
            self.chat_collection = self.db.chat_conversations
            self.mongo_connected = True
            print(f"✅ MongoDB conectado a {MONGODB_DB_NAME}")
        except Exception as e:
            print(f"❌ MongoDB error: {e}")
            self.mongo_connected = False
            
        return {
            "mongodb": self.mongo_connected
        }
    
    async def store_conversation(self, user_id: str, message: str, response: str):
        """Guardar conversación"""
        timestamp = datetime.now(timezone.utc)
        message_id = f"msg_{int(timestamp.timestamp())}_{user_id[:8]}"
        
        storage_info = {"mongodb": False, "memory": False}
        
        # MongoDB (principal)
        if self.mongo_connected:
            try:
                doc = {
                    "user_id": user_id,
                    "message": message,
                    "response": response,
                    "timestamp": timestamp,
                    "message_id": message_id
                }
                await self.chat_collection.insert_one(doc)
                storage_info["mongodb"] = True
            except Exception as e:
                print(f"Error MongoDB: {e}")
                self.mongo_connected = False
        
        # Memoria (fallback)
        if not storage_info["mongodb"]:
            if user_id not in self.memory_fallback:
                self.memory_fallback[user_id] = []
            self.memory_fallback[user_id].append({
                "message": message,
                "response": response,
                "timestamp": timestamp.isoformat(),
                "message_id": message_id
            })
            self.memory_fallback[user_id] = self.memory_fallback[user_id][-50:]
            storage_info["memory"] = True
        
        return storage_info, message_id
    
    async def get_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Obtener historial"""
        # MongoDB (principal)
        if self.mongo_connected:
            try:
                cursor = self.chat_collection.find(
                    {"user_id": user_id}
                ).sort("timestamp", -1).limit(limit)
                
                conversations = []
                async for doc in cursor:
                    conversations.append({
                        "message": doc["message"],
                        "response": doc["response"],
                        "timestamp": doc["timestamp"].isoformat() if isinstance(doc["timestamp"], datetime) else doc["timestamp"],
                        "message_id": doc.get("message_id", "unknown")
                    })
                
                return list(reversed(conversations))
            except Exception as e:
                print(f"Error leyendo MongoDB: {e}")
                self.mongo_connected = False
        
        # Fallback a memoria
        conversations = self.memory_fallback.get(user_id, [])[-limit:]
        return list(reversed(conversations))
    
    async def get_status(self):
        """Estado de las conexiones"""
        return {
            "mongodb": {
                "connected": self.mongo_connected,
                "database": MONGODB_DB_NAME if self.mongo_connected else None
            },
            "memory_fallback": {
                "users": len(self.memory_fallback)
            }
        }

# Instancia global
memory_service = MemoryService()
