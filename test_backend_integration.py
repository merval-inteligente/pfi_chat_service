"""
Test del servicio de chat integrado con backend principal
"""
import asyncio
import aiohttp
import json
from datetime import datetime


async def test_backend_integration():
    """Probar integración completa con el backend"""
    base_url = "http://localhost:8085"
    
    print("🔗 Testing Chat Service con Integración de Backend")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. Health Check
            print("\n1️⃣ Health Check del servicio integrado...")
            async with session.get(f"{base_url}/health") as response:
                health_data = await response.json()
                print(f"   Status: {health_data.get('status')}")
                print(f"   Backend principal: {health_data.get('services', {}).get('main_backend')}")
                print(f"   Redis: {health_data.get('services', {}).get('redis')}")
                print(f"   MongoDB: {health_data.get('services', {}).get('mongodb')}")
                print(f"   Backend URL: {health_data.get('backend_url')}")
            
            # 2. Crear token
            print("\n2️⃣ Creando token de usuario...")
            async with session.post(f"{base_url}/auth/token?user_id=user_financiero_123") as response:
                token_data = await response.json()
                access_token = token_data.get("access_token")
                print(f"   Usuario: {token_data.get('user_id')}")
                print(f"   Token válido por: {token_data.get('expires_in')} segundos")
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # 3. Verificar contexto del usuario
            print("\n3️⃣ Verificando contexto del usuario...")
            async with session.get(
                f"{base_url}/chat/context/user_financiero_123", 
                headers=headers
            ) as response:
                if response.status == 200:
                    context_data = await response.json()
                    print(f"   Tiene perfil: {context_data.get('has_profile')}")
                    print(f"   Tiene preferencias: {context_data.get('has_preferences')}")
                    print(f"   Tiene portfolio: {context_data.get('has_portfolio')}")
                    print(f"   Backend conectado: {context_data.get('backend_connected')}")
                else:
                    print(f"   ⚠️ No se pudo obtener contexto: {response.status}")
            
            # 4. Mensajes de prueba con diferentes contextos
            test_messages = [
                "Hola! ¿Cómo estás?",
                "¿Cómo está YPF hoy?", 
                "¿Qué opinas del MERVAL?",
                "Información sobre MercadoLibre",
                "¿Conviene comprar bonos ahora?",
                "¿Cómo está el dólar blue?"
            ]
            
            print("\n4️⃣ Enviando mensajes de prueba...")
            for i, message in enumerate(test_messages, 1):
                print(f"\n   📤 Mensaje {i}: {message}")
                
                payload = {"message": message}
                async with session.post(
                    f"{base_url}/chat/message", 
                    json=payload, 
                    headers=headers
                ) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        print(f"   🤖 Respuesta: {response_data.get('assistant_response')[:100]}...")
                        print(f"   📊 Personalizada: {response_data.get('personalized')}")
                        print(f"   🔗 Contexto usado: {response_data.get('user_context') is not None}")
                    else:
                        error_text = await response.text()
                        print(f"   ❌ Error {response.status}: {error_text}")
                
                # Pequeña pausa entre mensajes
                await asyncio.sleep(0.5)
            
            # 5. Obtener historial
            print("\n5️⃣ Obteniendo historial de conversación...")
            async with session.get(
                f"{base_url}/chat/history/user_financiero_123", 
                headers=headers
            ) as response:
                if response.status == 200:
                    history_data = await response.json()
                    total = history_data.get('total', 0)
                    personalized = history_data.get('personalized_count', 0)
                    print(f"   📋 Total mensajes: {total}")
                    print(f"   🎯 Respuestas personalizadas: {personalized}/{total//2}")
                    print(f"   📈 Tasa personalización: {(personalized/(total//2)*100):.1f}%" if total > 0 else "N/A")
                else:
                    print(f"   ❌ Error obteniendo historial: {response.status}")
            
            print("\n✅ Pruebas de integración completadas!")
            
        except Exception as e:
            print(f"\n❌ Error durante las pruebas: {e}")


async def test_multiple_users_with_context():
    """Probar múltiples usuarios con diferentes contextos"""
    base_url = "http://localhost:8085"
    
    print("\n" + "=" * 60)
    print("🧪 Testing múltiples usuarios con contexto")
    print("=" * 60)
    
    # Simular diferentes tipos de usuarios
    users = [
        {"id": "trader_pro", "type": "Trader profesional"},
        {"id": "inversor_conservador", "type": "Inversor conservador"},
        {"id": "principiante", "type": "Principiante"}
    ]
    
    async with aiohttp.ClientSession() as session:
        for user in users:
            user_id = user["id"]
            user_type = user["type"]
            
            print(f"\n👤 Probando usuario: {user_type} ({user_id})")
            
            # Crear token
            async with session.post(f"{base_url}/auth/token?user_id={user_id}") as response:
                token_data = await response.json()
                token = token_data.get("access_token")
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Enviar mensaje específico para cada tipo de usuario
            messages = {
                "trader_pro": "¿Cuáles son las mejores oportunidades de trading hoy en el MERVAL?",
                "inversor_conservador": "¿Qué inversiones seguras recomiendas para largo plazo?",
                "principiante": "Soy nuevo en inversiones, ¿por dónde empiezo?"
            }
            
            message = messages.get(user_id, "Hola")
            print(f"   📤 Enviando: {message}")
            
            async with session.post(
                f"{base_url}/chat/message", 
                json={"message": message}, 
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   🤖 Respuesta: {data.get('assistant_response')[:80]}...")
                    print(f"   🎯 Personalizada: {data.get('personalized')}")
                else:
                    print(f"   ❌ Error: {response.status}")


async def test_backend_connectivity():
    """Probar conectividad específica con el backend principal"""
    print("\n" + "=" * 60)
    print("🔌 Testing conectividad con backend principal")
    print("=" * 60)
    
    # Importar y probar directamente el cliente
    from backend_integration import MainBackendClient
    
    async with MainBackendClient() as client:
        print(f"\n🎯 Probando conexión a: {client.base_url}")
        
        # Test de health check
        health_ok = await client.health_check()
        print(f"   Health check: {'✅ OK' if health_ok else '❌ FAIL'}")
        
        # Test de endpoints (sin token real)
        print("\n🔍 Probando endpoints del backend...")
        endpoints_to_test = [
            "/health",
            "/api/auth/verify",
            "/api/users/demo"
        ]
        
        for endpoint in endpoints_to_test:
            result = await client._make_request("GET", endpoint)
            status = "✅ Responde" if result is not None else "❌ No responde"
            print(f"   {endpoint}: {status}")


if __name__ == "__main__":
    print("🚀 Iniciando pruebas del Chat Service Integrado con Backend...")
    print("⚠️  Asegúrate de que los servicios estén ejecutándose:")
    print("   1. Chat Service Integrado: python chat_integrated_backend.py (puerto 8085)")
    print("   2. Backend Principal: http://192.168.0.17:8080")
    
    # Ejecutar todas las pruebas
    asyncio.run(test_backend_integration())
    asyncio.run(test_multiple_users_with_context())
    asyncio.run(test_backend_connectivity())
