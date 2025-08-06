"""
Servicio híbrido de memoria con Redis Cloud (Upstash) + MongoDB
Prueba de integración con bases de datos reales
"""

import redis.asyncio as redis
import motor.motor_asyncio
import json
import asyncio
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

# Configuración simple desde .env
def load_env():
    env_vars = {}
    try:
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value
    except FileNotFoundError:
        print("⚠️ Archivo .env no encontrado")
    return env_vars

# Cargar configuración
env_config = load_env()
REDIS_URL = env_config.get('REDIS_URL', 'redis://localhost:6379')
MONGODB_URI = env_config.get('MONGODB_URI', 'mongodb://localhost:27017')
MONGODB_DB_NAME = env_config.get('MONGODB_DB_NAME', 'MervalDB')

@dataclass
class ConversationStats:
    redis_stored: bool = False
    mongodb_stored: bool = False
    memory_fallback: bool = False
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class HybridMemoryService:
    def __init__(self):
        self.redis_client = None
        self.mongo_client = None
        self.db = None
        self.chat_collection = None
        self._memory_fallback = {}
        self._redis_connected = False
        self._mongo_connected = False
        
    async def connect(self):
        """Conectar a ambas bases de datos"""
        print("🔗 Iniciando conexiones a bases de datos...")
        print(f"📍 Redis URL: {REDIS_URL[:50]}...")
        print(f"📍 MongoDB: {MONGODB_DB_NAME}")
        
        # Conectar Redis
        await self._connect_redis()
        
        # Conectar MongoDB
        await self._connect_mongodb()
        
        # Mostrar resumen
        print("\n" + "="*50)
        print("📊 ESTADO DE CONEXIONES:")
        print(f"✅ Redis Cloud: {'Conectado' if self._redis_connected else '❌ Error'}")
        print(f"✅ MongoDB: {'Conectado' if self._mongo_connected else '❌ Error'}")
        print("="*50 + "\n")
        
        return {
            "redis": self._redis_connected,
            "mongodb": self._mongo_connected
        }
        
    async def _connect_redis(self):
        """Conectar a Redis Cloud (Upstash)"""
        try:
            print("🔗 Conectando a Redis Cloud (Upstash)...")
            
            if not REDIS_URL or "localhost" in REDIS_URL:
                raise Exception("URL de Redis no configurada correctamente")
                
            self.redis_client = redis.from_url(
                REDIS_URL,
                decode_responses=True,
                socket_timeout=10.0,
                socket_connect_timeout=10.0,
                retry_on_timeout=True
            )
            
            # Test de ping
            await asyncio.wait_for(self.redis_client.ping(), timeout=10.0)
            
            # Test de escritura/lectura
            test_key = f"test_connection_{int(datetime.now().timestamp())}"
            test_value = "OK_TEST"
            
            await self.redis_client.set(test_key, test_value, ex=60)
            retrieved_value = await self.redis_client.get(test_key)
            
            if retrieved_value == test_value:
                await self.redis_client.delete(test_key)
                self._redis_connected = True
                print("✅ Redis Cloud: Conexión exitosa y funcional")
            else:
                raise Exception("Test de escritura/lectura falló")
                
        except Exception as e:
            print(f"❌ Redis Cloud error: {e}")
            self._redis_connected = False
            
    async def _connect_mongodb(self):
        """Conectar a MongoDB compartida"""
        try:
            print("🔗 Conectando a MongoDB (MervalDB)...")
            
            if not MONGODB_URI or "localhost" in MONGODB_URI:
                if "localhost" in MONGODB_URI:
                    print("⚠️  Usando MongoDB local, asegúrate de que esté corriendo")
                else:
                    raise Exception("URL de MongoDB no configurada")
                    
            self.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(
                MONGODB_URI,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000
            )
            
            # Test de ping
            await asyncio.wait_for(
                self.mongo_client.admin.command('ping'), 
                timeout=10.0
            )
            
            self.db = self.mongo_client[MONGODB_DB_NAME]
            self.chat_collection = self.db.chat_conversations
            
            # Crear índices para optimizar queries
            await self.chat_collection.create_index([
                ("user_id", 1),
                ("timestamp", -1)
            ])
            
            # Test de escritura
            test_doc = {
                "test": True,
                "timestamp": datetime.utcnow(),
                "connection_test": "OK"
            }
            result = await self.chat_collection.insert_one(test_doc)
            
            if result.inserted_id:
                await self.chat_collection.delete_one({"_id": result.inserted_id})
                self._mongo_connected = True
                print("✅ MongoDB: Conexión exitosa y funcional")
            else:
                raise Exception("Test de escritura falló")
                
        except Exception as e:
            print(f"❌ MongoDB error: {e}")
            self._mongo_connected = False

    async def store_conversation_test(self, user_id: str, message: str, response: str) -> ConversationStats:
        """Prueba de almacenamiento con estadísticas detalladas"""
        stats = ConversationStats()
        
        conversation_data = {
            "user_id": user_id,
            "message": message,
            "response": response,
            "timestamp": datetime.utcnow(),
            "test_id": f"test_{int(datetime.now().timestamp())}"
        }
        
        print(f"💾 Guardando conversación para usuario: {user_id}")
        print(f"📝 Mensaje: {message[:50]}...")
        print(f"🤖 Respuesta: {response[:50]}...")
        
        # 1. Intentar guardar en Redis
        if self._redis_connected:
            try:
                print("📤 Guardando en Redis Cloud...")
                
                cache_data = {
                    "message": message,
                    "response": response,
                    "timestamp": conversation_data["timestamp"].isoformat(),
                    "test_id": conversation_data["test_id"]
                }
                
                # Guardar en lista de historial
                history_key = f"chat_history:{user_id}"
                await self.redis_client.lpush(history_key, json.dumps(cache_data))
                await self.redis_client.ltrim(history_key, 0, 49)  # Últimas 50
                await self.redis_client.expire(history_key, 86400 * 7)  # 7 días
                
                # Contador de mensajes
                count_key = f"chat_count:{user_id}"
                new_count = await self.redis_client.incr(count_key)
                await self.redis_client.expire(count_key, 86400 * 30)  # 30 días
                
                # Última actividad
                activity_key = f"last_activity:{user_id}"
                await self.redis_client.set(
                    activity_key, 
                    conversation_data["timestamp"].isoformat(), 
                    ex=86400 * 7
                )
                
                stats.redis_stored = True
                print(f"✅ Redis: Guardado exitosamente (total mensajes: {new_count})")
                
            except Exception as e:
                stats.errors.append(f"Redis error: {e}")
                print(f"❌ Redis error: {e}")
                self._redis_connected = False
        
        # 2. Intentar guardar en MongoDB
        if self._mongo_connected:
            try:
                print("📤 Guardando en MongoDB...")
                
                # Preparar documento para MongoDB
                mongo_doc = conversation_data.copy()
                result = await self.chat_collection.insert_one(mongo_doc)
                
                if result.inserted_id:
                    stats.mongodb_stored = True
                    print(f"✅ MongoDB: Guardado exitosamente (ID: {result.inserted_id})")
                else:
                    raise Exception("No se pudo insertar el documento")
                    
            except Exception as e:
                stats.errors.append(f"MongoDB error: {e}")
                print(f"❌ MongoDB error: {e}")
                self._mongo_connected = False
        
        # 3. Fallback a memoria si ambas fallan
        if not stats.redis_stored and not stats.mongodb_stored:
            if user_id not in self._memory_fallback:
                self._memory_fallback[user_id] = []
            
            memory_data = {
                "message": message,
                "response": response,
                "timestamp": conversation_data["timestamp"].isoformat(),
                "test_id": conversation_data["test_id"]
            }
            self._memory_fallback[user_id].append(memory_data)
            self._memory_fallback[user_id] = self._memory_fallback[user_id][-50:]
            
            stats.memory_fallback = True
            print(f"💾 Memoria local: Guardado como fallback")
        
        return stats

    async def get_conversation_history_test(self, user_id: str, limit: int = 10) -> Dict:
        """Obtener historial con información de origen"""
        print(f"\n📖 Obteniendo historial para usuario: {user_id}")
        
        result = {
            "conversations": [],
            "source": "none",
            "total_found": 0,
            "sources_checked": []
        }
        
        # 1. Intentar desde Redis
        if self._redis_connected:
            try:
                print("🔍 Buscando en Redis Cloud...")
                result["sources_checked"].append("redis")
                
                history_key = f"chat_history:{user_id}"
                conversations_raw = await self.redis_client.lrange(history_key, 0, limit - 1)
                
                if conversations_raw:
                    conversations = [json.loads(conv) for conv in conversations_raw]
                    result["conversations"] = list(reversed(conversations))  # Cronológico
                    result["source"] = "redis_cloud"
                    result["total_found"] = len(conversations)
                    print(f"✅ Redis: Encontrados {len(conversations)} mensajes")
                    return result
                else:
                    print("📭 Redis: No hay historial para este usuario")
                    
            except Exception as e:
                print(f"❌ Error leyendo Redis: {e}")
                self._redis_connected = False
        
        # 2. Fallback a MongoDB
        if self._mongo_connected:
            try:
                print("🔍 Buscando en MongoDB...")
                result["sources_checked"].append("mongodb")
                
                cursor = self.chat_collection.find(
                    {"user_id": user_id}
                ).sort("timestamp", -1).limit(limit)
                
                conversations = []
                async for doc in cursor:
                    conversations.append({
                        "message": doc["message"],
                        "response": doc["response"],
                        "timestamp": doc["timestamp"].isoformat() if isinstance(doc["timestamp"], datetime) else doc["timestamp"],
                        "test_id": doc.get("test_id", "unknown")
                    })
                
                if conversations:
                    result["conversations"] = list(reversed(conversations))  # Cronológico
                    result["source"] = "mongodb"
                    result["total_found"] = len(conversations)
                    print(f"✅ MongoDB: Encontrados {len(conversations)} mensajes")
                    return result
                else:
                    print("📭 MongoDB: No hay historial para este usuario")
                    
            except Exception as e:
                print(f"❌ Error leyendo MongoDB: {e}")
                self._mongo_connected = False
        
        # 3. Fallback a memoria
        result["sources_checked"].append("memory")
        conversations = self._memory_fallback.get(user_id, [])[-limit:]
        
        if conversations:
            result["conversations"] = list(reversed(conversations))  # Cronológico
            result["source"] = "memory"
            result["total_found"] = len(conversations)
            print(f"💾 Memoria: Encontrados {len(conversations)} mensajes")
        else:
            print("📭 Memoria: No hay historial para este usuario")
        
        return result

    async def get_database_stats(self) -> Dict:
        """Estadísticas de las bases de datos"""
        stats = {
            "redis": {
                "connected": self._redis_connected,
                "total_users": 0,
                "total_conversations": 0
            },
            "mongodb": {
                "connected": self._mongo_connected,
                "total_documents": 0,
                "database_name": MONGODB_DB_NAME
            },
            "memory": {
                "users_in_fallback": len(self._memory_fallback)
            }
        }
        
        # Stats de Redis
        if self._redis_connected:
            try:
                # Buscar todas las keys de historial
                history_keys = await self.redis_client.keys("chat_history:*")
                stats["redis"]["total_users"] = len(history_keys)
                
                total_conversations = 0
                for key in history_keys:
                    count = await self.redis_client.llen(key)
                    total_conversations += count
                
                stats["redis"]["total_conversations"] = total_conversations
                
            except Exception as e:
                print(f"Error obteniendo stats de Redis: {e}")
        
        # Stats de MongoDB
        if self._mongo_connected:
            try:
                stats["mongodb"]["total_documents"] = await self.chat_collection.count_documents({})
            except Exception as e:
                print(f"Error obteniendo stats de MongoDB: {e}")
        
        return stats

    async def cleanup_test_data(self):
        """Limpiar datos de prueba"""
        print("\n🧹 Limpiando datos de prueba...")
        
        cleaned = {"redis": 0, "mongodb": 0}
        
        # Limpiar Redis
        if self._redis_connected:
            try:
                test_keys = await self.redis_client.keys("*test*")
                if test_keys:
                    cleaned["redis"] = await self.redis_client.delete(*test_keys)
                    print(f"🗑️ Redis: Eliminadas {cleaned['redis']} keys de prueba")
            except Exception as e:
                print(f"Error limpiando Redis: {e}")
        
        # Limpiar MongoDB
        if self._mongo_connected:
            try:
                result = await self.chat_collection.delete_many({
                    "$or": [
                        {"test_id": {"$regex": "test_"}},
                        {"user_id": {"$regex": "test_"}}
                    ]
                })
                cleaned["mongodb"] = result.deleted_count
                print(f"🗑️ MongoDB: Eliminados {cleaned['mongodb']} documentos de prueba")
            except Exception as e:
                print(f"Error limpiando MongoDB: {e}")
        
        return cleaned

    async def close(self):
        """Cerrar conexiones"""
        print("\n🔌 Cerrando conexiones...")
        
        if self.redis_client:
            await self.redis_client.close()
            print("✅ Redis: Conexión cerrada")
            
        if self.mongo_client:
            self.mongo_client.close()
            print("✅ MongoDB: Conexión cerrada")

# Test principal
async def test_database_integration():
    """Prueba completa de integración con bases de datos"""
    print("🧪 INICIANDO PRUEBA DE INTEGRACIÓN DE BASES DE DATOS")
    print("=" * 60)
    
    # Inicializar servicio
    service = HybridMemoryService()
    
    try:
        # Conectar
        connections = await service.connect()
        
        if not connections["redis"] and not connections["mongodb"]:
            print("❌ No se pudo conectar a ninguna base de datos")
            return
        
        # Datos de prueba
        test_user = "test_user_123"
        test_conversations = [
            ("¿Cómo está el MERVAL hoy?", "📈 El MERVAL está subiendo 2.1% hoy, liderado por YPF y Galicia..."),
            ("¿Qué opinas de YPF?", "🛢️ YPF es una acción interesante con exposición a Vaca Muerta..."),
            ("¿Conviene comprar dólares?", "💵 El dólar blue está en $485, considera MEP para inversiones...")
        ]
        
        print(f"\n📝 Probando con {len(test_conversations)} conversaciones...")
        
        # Guardar conversaciones
        all_stats = []
        for i, (message, response) in enumerate(test_conversations, 1):
            print(f"\n--- Conversación {i}/{len(test_conversations)} ---")
            stats = await service.store_conversation_test(test_user, message, response)
            all_stats.append(stats)
            await asyncio.sleep(1)  # Pequeña pausa entre guardados
        
        # Resumen de guardado
        print(f"\n📊 RESUMEN DE GUARDADO:")
        redis_count = sum(1 for s in all_stats if s.redis_stored)
        mongo_count = sum(1 for s in all_stats if s.mongodb_stored)
        memory_count = sum(1 for s in all_stats if s.memory_fallback)
        
        print(f"✅ Redis: {redis_count}/{len(test_conversations)}")
        print(f"✅ MongoDB: {mongo_count}/{len(test_conversations)}")
        print(f"💾 Memoria: {memory_count}/{len(test_conversations)}")
        
        # Obtener historial
        print(f"\n📖 OBTENIENDO HISTORIAL:")
        history_result = await service.get_conversation_history_test(test_user)
        
        print(f"🔍 Fuente: {history_result['source']}")
        print(f"📝 Total encontrado: {history_result['total_found']}")
        print(f"🔍 Fuentes verificadas: {', '.join(history_result['sources_checked'])}")
        
        # Mostrar algunas conversaciones
        if history_result["conversations"]:
            print(f"\n💬 Últimas conversaciones:")
            for i, conv in enumerate(history_result["conversations"][:2], 1):
                print(f"   {i}. 👤 {conv['message'][:40]}...")
                print(f"      🤖 {conv['response'][:40]}...")
        
        # Estadísticas de bases de datos
        print(f"\n📊 ESTADÍSTICAS DE BASES DE DATOS:")
        db_stats = await service.get_database_stats()
        
        for db_name, stats in db_stats.items():
            print(f"\n{db_name.upper()}:")
            for key, value in stats.items():
                print(f"   {key}: {value}")
        
        # Limpiar datos de prueba
        print(f"\n🧹 ¿Limpiar datos de prueba? (automático en 3 segundos)")
        await asyncio.sleep(3)
        
        cleaned = await service.cleanup_test_data()
        print(f"✅ Limpieza completada: {cleaned}")
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await service.close()
    
    print("\n🎉 PRUEBA COMPLETADA")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_database_integration())
