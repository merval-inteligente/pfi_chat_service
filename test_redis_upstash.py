"""
Test específico para Redis Cloud (Upstash) con datos del dashboard
"""

import redis.asyncio as redis
import asyncio
import json
from datetime import datetime

# Datos exactos de tu dashboard Upstash
REDIS_ENDPOINT = "stable-hog-9281.upstash.io"
REDIS_PORT = 6379
REDIS_TOKEN = "ASRBAAIjcDE4YjM3YmZiYWY0MTA0ZjUwYTJjOGZiMTJmZmIyYzljNXAxMA"

# Diferentes formatos de URL para probar
redis_urls = [
    # Formato 1: Con username default
    f"redis://default:{REDIS_TOKEN}@{REDIS_ENDPOINT}:{REDIS_PORT}",
    
    # Formato 2: Sin username
    f"redis://:{REDIS_TOKEN}@{REDIS_ENDPOINT}:{REDIS_PORT}",
    
    # Formato 3: Con rediss (SSL)
    f"rediss://default:{REDIS_TOKEN}@{REDIS_ENDPOINT}:{REDIS_PORT}",
    
    # Formato 4: Solo token
    f"rediss://:{REDIS_TOKEN}@{REDIS_ENDPOINT}:{REDIS_PORT}"
]

async def test_redis_connection():
    print("🧪 TESTING REDIS CLOUD (UPSTASH)")
    print("=" * 50)
    print(f"📍 Endpoint: {REDIS_ENDPOINT}")
    print(f"📍 Port: {REDIS_PORT}")
    print(f"📍 Token: {REDIS_TOKEN[:20]}...")
    print("=" * 50)
    
    for i, url in enumerate(redis_urls, 1):
        print(f"\n🔗 Test {i}: {url[:40]}...")
        
        try:
            client = redis.from_url(
                url,
                decode_responses=True,
                socket_timeout=15.0,
                socket_connect_timeout=15.0,
                retry_on_timeout=True,
                health_check_interval=0  # Disable health check
            )
            
            # Test de ping
            print("   ⏳ Conectando...")
            await asyncio.wait_for(client.ping(), timeout=10.0)
            print("   ✅ PING exitoso")
            
            # Test de escritura
            test_key = f"test_connection_{int(datetime.now().timestamp())}"
            test_value = f"test_value_{i}"
            
            print("   ⏳ Probando escritura...")
            await client.set(test_key, test_value, ex=60)
            print("   ✅ SET exitoso")
            
            # Test de lectura
            print("   ⏳ Probando lectura...")
            retrieved_value = await client.get(test_key)
            
            if retrieved_value == test_value:
                print("   ✅ GET exitoso")
                print("   🎉 ¡CONEXIÓN EXITOSA!")
                
                # Test adicional: lista
                print("   ⏳ Probando operaciones de lista...")
                list_key = f"test_list_{i}"
                await client.lpush(list_key, "item1", "item2", "item3")
                list_items = await client.lrange(list_key, 0, -1)
                print(f"   ✅ Lista creada: {list_items}")
                
                # Limpiar
                await client.delete(test_key, list_key)
                print("   🧹 Limpieza completada")
                
                # Cerrar cliente
                await client.aclose()
                
                return url, True
                
            else:
                print(f"   ❌ Valor incorrecto: esperado {test_value}, obtenido {retrieved_value}")
                await client.aclose()
                
        except asyncio.TimeoutError:
            print("   ❌ TIMEOUT - Conexión muy lenta")
        except ConnectionError as e:
            print(f"   ❌ CONNECTION ERROR: {e}")
        except redis.ResponseError as e:
            print(f"   ❌ REDIS ERROR: {e}")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
        
        print("   " + "-" * 30)
    
    print("\n❌ Ninguna configuración funcionó")
    return None, False

async def test_upstash_rest_api():
    """Test usando REST API de Upstash como alternativa"""
    print("\n🌐 TESTING UPSTASH REST API")
    print("=" * 30)
    
    import aiohttp
    
    # URL del REST API según el dashboard
    rest_url = f"https://{REDIS_ENDPOINT}"
    headers = {
        "Authorization": f"Bearer {REDIS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test PING via REST
            ping_data = {"command": "PING"}
            
            async with session.post(
                rest_url, 
                headers=headers, 
                json=ping_data,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ REST API PING: {result}")
                    
                    # Test SET via REST
                    set_data = {
                        "command": "SET",
                        "args": ["test_rest_key", "test_rest_value", "EX", "60"]
                    }
                    
                    async with session.post(
                        rest_url,
                        headers=headers,
                        json=set_data,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as set_response:
                        
                        if set_response.status == 200:
                            set_result = await set_response.json()
                            print(f"✅ REST API SET: {set_result}")
                            return True
                        else:
                            print(f"❌ REST API SET failed: {set_response.status}")
                            return False
                else:
                    print(f"❌ REST API PING failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ REST API Error: {e}")
        return False

async def main():
    # Test conexión Redis nativa
    working_url, success = await test_redis_connection()
    
    if success:
        print(f"\n🎉 ¡ÉXITO! URL funcionando: {working_url}")
        
        # Crear archivo de configuración funcionando
        with open("redis_working_config.txt", "w") as f:
            f.write(f"# Configuración Redis funcionando\n")
            f.write(f"REDIS_URL={working_url}\n")
            f.write(f"# Fecha test: {datetime.now()}\n")
        
        print("📝 Configuración guardada en redis_working_config.txt")
        
    else:
        print("\n🔄 Probando REST API como alternativa...")
        rest_success = await test_upstash_rest_api()
        
        if rest_success:
            print("✅ REST API funciona - podemos usar HTTP en lugar de Redis nativo")
        else:
            print("❌ Tanto Redis nativo como REST API fallan")
            print("\n🔍 DIAGNÓSTICO:")
            print("1. Verifica que la instancia esté activa en Upstash")
            print("2. Verifica que no haya restricciones de IP")
            print("3. Verifica que el token no haya expirado")
            print("4. Considera usar el REST API en lugar de Redis nativo")

if __name__ == "__main__":
    asyncio.run(main())
