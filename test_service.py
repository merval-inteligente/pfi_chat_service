"""
Script de testing para el Chat Service
"""
import requests
import json
from datetime import datetime

# Base URL del servicio
BASE_URL = "http://localhost:8082"

def test_health_check():
    """Test del health check"""
    print("🔍 Testing Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Status: {response.status_code}")
        print(f"📄 Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_chat_message(message):
    """Test de envío de mensaje"""
    print(f"\n💬 Testing Chat Message: '{message}'")
    try:
        payload = {"message": message}
        response = requests.post(
            f"{BASE_URL}/api/chat/message",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"✅ Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"🤖 Assistant Response:")
            print(f"   {data['assistant_response'][:200]}...")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_service_info():
    """Test de información del servicio"""
    print(f"\n📋 Testing Service Info...")
    try:
        response = requests.get(f"{BASE_URL}/api/info")
        print(f"✅ Status: {response.status_code}")
        data = response.json()
        print(f"📊 Service: {data['service']}")
        print(f"🔧 Mode: {data['mode']}")
        print(f"📈 Features: {', '.join(data['features'])}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_chat_history():
    """Test de historial de chat"""
    print(f"\n📚 Testing Chat History...")
    try:
        user_id = "demo-127.0.0.1"  # ID de usuario demo típico
        response = requests.get(f"{BASE_URL}/api/chat/history/{user_id}")
        print(f"✅ Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"📝 Total messages: {data['total_messages']}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def run_full_test():
    """Ejecuta todos los tests"""
    print("🚀 Chat Service - Testing Suite")
    print("=" * 50)
    
    tests = [
        test_health_check,
        test_service_info,
        lambda: test_chat_message("Hola"),
        lambda: test_chat_message("¿Cómo está el MERVAL hoy?"),
        lambda: test_chat_message("Quiero información sobre YPF"),
        lambda: test_chat_message("¿Qué opinas sobre Bitcoin?"),
        lambda: test_chat_message("Análisis de bonos argentinos"),
        test_chat_history
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ¡Todos los tests pasaron! El servicio funciona correctamente.")
    else:
        print("⚠️  Algunos tests fallaron. Revisa los errores arriba.")

if __name__ == "__main__":
    run_full_test()
