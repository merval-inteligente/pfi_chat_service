"""
Test del servicio de chat integrado con autenticación JWT
"""
import asyncio
import aiohttp
import json
from datetime import datetime


async def test_integrated_chat_service():
    """Prueba completa del servicio integrado"""
    base_url = "http://localhost:8084"
    
    print("🧪 Testing Chat Service Integrado con JWT")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. Health Check
            print("\n1️⃣ Health Check...")
            async with session.get(f"{base_url}/health") as response:
                health_data = await response.json()
                print(f"   Status: {health_data.get('status')}")
                print(f"   Services: {health_data.get('services')}")
            
            # 2. Crear token de demostración
            print("\n2️⃣ Creando token de demostración...")
            async with session.post(f"{base_url}/auth/token?user_id=test_user_123") as response:
                token_data = await response.json()
                access_token = token_data.get("access_token")
                print(f"   Token creado para usuario: {token_data.get('user_id')}")
                print(f"   Token type: {token_data.get('token_type')}")
            
            # Headers con autenticación
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # 3. Enviar primer mensaje
            print("\n3️⃣ Enviando primer mensaje...")
            message_1 = {
                "message": "Hola! ¿Cómo están las acciones de YPF hoy?"
            }
            
            async with session.post(
                f"{base_url}/chat/message", 
                json=message_1, 
                headers=headers
            ) as response:
                if response.status == 200:
                    response_data = await response.json()
                    print(f"   Usuario: {response_data.get('user_message')}")
                    print(f"   Asistente: {response_data.get('assistant_response')}")
                    print(f"   Modelo: {response_data.get('model_info')}")
                else:
                    error_text = await response.text()
                    print(f"   ❌ Error {response.status}: {error_text}")
            
            # 4. Enviar segundo mensaje
            print("\n4️⃣ Enviando segundo mensaje...")
            message_2 = {
                "message": "¿Y qué tal los bonos argentinos?"
            }
            
            async with session.post(
                f"{base_url}/chat/message", 
                json=message_2, 
                headers=headers
            ) as response:
                if response.status == 200:
                    response_data = await response.json()
                    print(f"   Usuario: {response_data.get('user_message')}")
                    print(f"   Asistente: {response_data.get('assistant_response')[:100]}...")
                else:
                    error_text = await response.text()
                    print(f"   ❌ Error {response.status}: {error_text}")
            
            # 5. Obtener historial
            print("\n5️⃣ Obteniendo historial de chat...")
            async with session.get(
                f"{base_url}/chat/history/test_user_123", 
                headers=headers
            ) as response:
                if response.status == 200:
                    history_data = await response.json()
                    messages = history_data.get('messages', [])
                    print(f"   Total de mensajes: {history_data.get('total_messages')}")
                    for i, msg in enumerate(messages[-4:], 1):  # Últimos 4 mensajes
                        print(f"   {i}. [{msg.get('message_type')}] {msg.get('message')[:50]}...")
                else:
                    error_text = await response.text()
                    print(f"   ❌ Error {response.status}: {error_text}")
            
            # 6. Probar acceso no autorizado
            print("\n6️⃣ Probando acceso no autorizado...")
            async with session.get(f"{base_url}/chat/history/otro_usuario", headers=headers) as response:
                if response.status == 403:
                    print("   ✅ Acceso denegado correctamente (403)")
                else:
                    print(f"   ⚠️ Status inesperado: {response.status}")
            
            # 7. Probar sin token
            print("\n7️⃣ Probando acceso sin token...")
            async with session.get(f"{base_url}/chat/history/test_user_123") as response:
                if response.status == 403:
                    print("   ✅ Acceso denegado sin token (403)")
                else:
                    print(f"   ⚠️ Status inesperado: {response.status}")
            
            # 8. Limpiar historial
            print("\n8️⃣ Limpiando historial...")
            async with session.delete(
                f"{base_url}/chat/history/test_user_123", 
                headers=headers
            ) as response:
                if response.status == 200:
                    cleanup_data = await response.json()
                    print(f"   ✅ {cleanup_data.get('message')}")
                else:
                    error_text = await response.text()
                    print(f"   ❌ Error {response.status}: {error_text}")
            
            print("\n✅ Pruebas completadas!")
            
        except Exception as e:
            print(f"\n❌ Error durante las pruebas: {e}")


async def test_multiple_users():
    """Probar con múltiples usuarios"""
    base_url = "http://localhost:8084"
    
    print("\n" + "=" * 50)
    print("🧪 Testing con múltiples usuarios")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # Crear tokens para 3 usuarios diferentes
        users = ["user_a", "user_b", "user_c"]
        tokens = {}
        
        for user in users:
            async with session.post(f"{base_url}/auth/token?user_id={user}") as response:
                token_data = await response.json()
                tokens[user] = token_data.get("access_token")
                print(f"   Token creado para {user}")
        
        # Cada usuario envía un mensaje
        messages = {
            "user_a": "¿Cuál es el precio del dólar blue?",
            "user_b": "Información sobre Mercado Libre (MELI)",
            "user_c": "¿Cómo va el MERVAL hoy?"
        }
        
        print("\n📤 Enviando mensajes de cada usuario...")
        for user, message in messages.items():
            headers = {
                "Authorization": f"Bearer {tokens[user]}",
                "Content-Type": "application/json"
            }
            
            async with session.post(
                f"{base_url}/chat/message", 
                json={"message": message}, 
                headers=headers
            ) as response:
                if response.status == 200:
                    print(f"   ✅ {user}: Mensaje enviado")
                else:
                    print(f"   ❌ {user}: Error {response.status}")
        
        # Verificar que cada usuario solo ve su historial
        print("\n📋 Verificando historiales separados...")
        for user in users:
            headers = {"Authorization": f"Bearer {tokens[user]}"}
            
            async with session.get(f"{base_url}/chat/history/{user}", headers=headers) as response:
                if response.status == 200:
                    history_data = await response.json()
                    count = history_data.get('total_messages', 0)
                    print(f"   ✅ {user}: {count} mensajes en su historial")
                else:
                    print(f"   ❌ {user}: Error obteniendo historial")


if __name__ == "__main__":
    print("🚀 Iniciando pruebas del Chat Service Integrado...")
    print("⚠️  Asegúrate de que el servicio esté ejecutándose en puerto 8082")
    print("   Comando: python chat_service_integrated.py")
    
    # Ejecutar pruebas
    asyncio.run(test_integrated_chat_service())
    asyncio.run(test_multiple_users())
