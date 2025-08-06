"""
Test Suite para Chat Service con OpenAI Real
Versión 2.0 - Testing completo de funcionalidades
"""

import requests
import json
import time
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:8083"

def print_header(title):
    print(f"\n{'='*50}")
    print(f"🧪 {title}")
    print('='*50)

def print_test_result(test_name, status_code, response_data=None):
    status_emoji = "✅" if status_code == 200 else "❌"
    print(f"{status_emoji} {test_name}")
    print(f"   Status: {status_code}")
    if response_data:
        if isinstance(response_data, dict):
            for key, value in response_data.items():
                if key == "message" and len(str(value)) > 100:
                    print(f"   {key}: {str(value)[:100]}...")
                else:
                    print(f"   {key}: {value}")
        else:
            print(f"   Response: {response_data}")
    print()

def test_health_check():
    """Test del health check"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print_test_result("Health Check", response.status_code, response.json())
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error en health check: {e}")
        return False

def test_service_info():
    """Test de información del servicio"""
    try:
        response = requests.get(f"{BASE_URL}/api/info")
        data = response.json()
        print_test_result("Service Info", response.status_code, data)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error en service info: {e}")
        return False

def test_chat_message(message, test_name):
    """Test de envío de mensaje de chat"""
    try:
        payload = {
            "message": message,
            "user_id": f"test-user-{int(time.time())}"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/chat/message",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {test_name}")
            print(f"   Status: {response.status_code}")
            print(f"   AI Mode: {data.get('ai_mode', 'unknown')}")
            print(f"   Message ID: {data.get('message_id', 'unknown')}")
            
            # Mostrar respuesta del asistente
            assistant_message = data.get('message', '')
            print(f"   🤖 Assistant Response:")
            # Dividir en líneas para mejor legibilidad
            lines = assistant_message.split('\n')
            for line in lines[:5]:  # Mostrar máximo 5 líneas
                print(f"      {line}")
            if len(lines) > 5:
                print("      ...")
            
            # Mostrar usage si está disponible
            if data.get('usage'):
                usage = data['usage']
                print(f"   📊 Tokens: {usage.get('total_tokens', 0)} (prompt: {usage.get('prompt_tokens', 0)}, completion: {usage.get('completion_tokens', 0)})")
            
            print()
            return True, data.get('user_id')
        else:
            print(f"❌ {test_name} - Status: {response.status_code}")
            print(f"   Error: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Error en {test_name}: {e}")
        return False, None

def test_chat_history(user_id):
    """Test de obtención de historial"""
    try:
        response = requests.get(f"{BASE_URL}/api/chat/history/{user_id}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Chat History")
            print(f"   Status: {response.status_code}")
            print(f"   User ID: {data.get('user_id')}")
            print(f"   Total messages: {data.get('total_messages')}")
            print(f"   AI Mode: {data.get('ai_mode')}")
            
            # Mostrar algunos mensajes del historial
            messages = data.get('messages', [])
            if messages:
                print(f"   📝 Últimos mensajes:")
                for i, msg in enumerate(messages[-4:]):  # Últimos 4 mensajes
                    role_emoji = "👤" if msg['role'] == 'user' else "🤖"
                    content = msg['content'][:50] + "..." if len(msg['content']) > 50 else msg['content']
                    print(f"      {role_emoji} {msg['role']}: {content}")
            
            print()
            return True
        else:
            print(f"❌ Chat History - Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error en chat history: {e}")
        return False

def test_api_docs():
    """Test de acceso a documentación"""
    try:
        response = requests.get(f"{BASE_URL}/docs")
        success = response.status_code == 200
        print_test_result("API Documentation", response.status_code)
        return success
    except Exception as e:
        print(f"❌ Error en API docs: {e}")
        return False

def main():
    print_header("🚀 Chat Service con OpenAI - Testing Suite v2.0")
    
    tests_passed = 0
    total_tests = 0
    user_id_for_history = None
    
    # Test 1: Health Check
    total_tests += 1
    if test_health_check():
        tests_passed += 1
    
    # Test 2: Service Info
    total_tests += 1
    if test_service_info():
        tests_passed += 1
    
    # Test 3: Chat Messages con diferentes tipos de consultas
    test_messages = [
        ("Hola, ¿cómo estás?", "Saludo General"),
        ("¿Cómo está el MERVAL hoy?", "Consulta MERVAL"),
        ("Quiero información sobre YPF", "Análisis YPF"),
        ("¿Qué opinas sobre Bitcoin en Argentina?", "Consulta Bitcoin"),
        ("Análisis de bonos argentinos AL30", "Bonos Argentinos"),
        ("¿Conviene invertir en plazo fijo UVA?", "Consulta Plazo Fijo UVA")
    ]
    
    for message, test_name in test_messages:
        total_tests += 1
        success, user_id = test_chat_message(message, test_name)
        if success:
            tests_passed += 1
            if user_id_for_history is None:
                user_id_for_history = user_id
    
    # Test 4: Chat History
    if user_id_for_history:
        total_tests += 1
        if test_chat_history(user_id_for_history):
            tests_passed += 1
    
    # Test 5: API Documentation
    total_tests += 1
    if test_api_docs():
        tests_passed += 1
    
    # Resultados finales
    print_header("🎯 Resultados Finales")
    print(f"Tests ejecutados: {total_tests}")
    print(f"Tests exitosos: {tests_passed}")
    print(f"Tests fallidos: {total_tests - tests_passed}")
    print(f"Tasa de éxito: {(tests_passed/total_tests)*100:.1f}%")
    
    if tests_passed == total_tests:
        print("\n🎉 ¡Todos los tests pasaron! El servicio OpenAI está funcionando correctamente.")
    else:
        print(f"\n⚠️  {total_tests - tests_passed} tests fallaron. Revisar configuración.")
    
    # Información adicional
    print(f"\n📋 URLs importantes:")
    print(f"   Health: {BASE_URL}/health")
    print(f"   Info: {BASE_URL}/api/info")
    print(f"   Docs: {BASE_URL}/docs")
    print(f"   Chat: {BASE_URL}/api/chat/message")

if __name__ == "__main__":
    main()
