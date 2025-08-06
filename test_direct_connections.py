"""
Test rápido de las bases de datos usando las URLs directas
"""

import asyncio
import motor.motor_asyncio
import redis.asyncio as redis

# URLs directas desde el .env verificado
MONGODB_URI = "mongodb+srv://admin:tRVIi8NhbKbzDj0q@cluster0.dad6cgj.mongodb.net/MervalDB?retryWrites=true&w=majority"
REDIS_URL = "redis://default:ASRBAAIjcDE4YjM3YmZiYWY0MTA0ZjUwYTJjOGZiMTJmZmIyYzljNXAxMA@stable-hog-9281.upstash.io:6379"

async def test_connections():
    print("🧪 PRUEBA RÁPIDA DE CONEXIONES")
    print("=" * 40)
    
    # Test MongoDB
    print("📊 Probando MongoDB Atlas...")
    try:
        mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        await mongo_client.admin.command('ping')
        print("✅ MongoDB: Conectado exitosamente")
        
        # Test de escritura
        db = mongo_client.MervalDB
        collection = db.test_quick
        result = await collection.insert_one({"test": "quick_test", "timestamp": "now"})
        await collection.delete_one({"_id": result.inserted_id})
        print("✅ MongoDB: Escritura/lectura OK")
        
        mongo_client.close()
        
    except Exception as e:
        print(f"❌ MongoDB error: {e}")
    
    # Test Redis
    print("\n⚡ Probando Redis Cloud (Upstash)...")
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        await asyncio.wait_for(redis_client.ping(), timeout=5.0)
        print("✅ Redis: Conectado exitosamente")
        
        # Test de escritura
        await redis_client.set("test_quick", "OK", ex=10)
        value = await redis_client.get("test_quick")
        if value == "OK":
            print("✅ Redis: Escritura/lectura OK")
        await redis_client.delete("test_quick")
        
        await redis_client.close()
        
    except Exception as e:
        print(f"❌ Redis error: {e}")
    
    print("\n🎉 Prueba completada")

if __name__ == "__main__":
    asyncio.run(test_connections())
