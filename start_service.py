"""
Script de inicio automático para el Chat Service integrado
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def check_requirements():
    """Verificar que todas las dependencias estén instaladas"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'redis',
        'pymongo',
        'aiohttp',
        'python-jose',
        'python-multipart',
        'asyncio-timeout'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Faltan dependencias: {', '.join(missing)}")
        print(f"Instálalas con: pip install {' '.join(missing)}")
        return False
    
    print("✅ Todas las dependencias están instaladas")
    return True

def check_env_file():
    """Verificar archivo .env"""
    env_path = Path('.env')
    if not env_path.exists():
        print("⚠️  Archivo .env no encontrado")
        create_sample_env()
        return False
    
    required_vars = [
        'MAIN_BACKEND_URL',
        'JWT_SECRET_KEY',
        'REDIS_URL',
        'MONGODB_URL'
    ]
    
    with open(env_path) as f:
        content = f.read()
    
    missing_vars = []
    for var in required_vars:
        if var not in content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Variables faltantes en .env: {', '.join(missing_vars)}")
        return False
    
    print("✅ Archivo .env configurado correctamente")
    return True

def create_sample_env():
    """Crear archivo .env de ejemplo"""
    sample_env = """# Backend Principal
MAIN_BACKEND_URL=http://192.168.0.17:8080
MAIN_BACKEND_TIMEOUT=30

# Chat Service
CHAT_SERVICE_PORT=8084
CHAT_SERVICE_HOST=192.168.0.17

# JWT Configuration
JWT_SECRET_KEY=tu_clave_secreta_super_segura_aqui
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# Redis Cloud (Upstash)
REDIS_URL=redis://default:password@host:port

# MongoDB Atlas
MONGODB_URL=mongodb+srv://user:password@cluster.mongodb.net/
MONGODB_DB_NAME=chatbot_conversations

# CORS
ALLOWED_ORIGINS=["http://localhost:3000", "http://192.168.0.17:3000"]
"""
    
    with open('.env', 'w') as f:
        f.write(sample_env)
    
    print("📝 Archivo .env de ejemplo creado")
    print("⚠️  Edita el archivo .env con tus configuraciones reales")

def check_backend_connection():
    """Verificar conexión al backend principal"""
    backend_url = os.getenv('MAIN_BACKEND_URL', 'http://192.168.0.17:8080')
    
    try:
        response = requests.get(f"{backend_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend principal conectado")
            return True
        else:
            print(f"⚠️  Backend responde con código: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ No se puede conectar al backend principal: {e}")
        print(f"   Verifica que esté ejecutándose en: {backend_url}")
        return False

def start_service():
    """Iniciar el servicio de chat"""
    host = os.getenv('CHAT_SERVICE_HOST', '192.168.0.17')
    port = os.getenv('CHAT_SERVICE_PORT', '8084')
    
    print(f"🚀 Iniciando Chat Service en {host}:{port}")
    print("   Presiona Ctrl+C para detener")
    
    try:
        subprocess.run([
            sys.executable, '-m', 'uvicorn',
            'chat_integrated_backend:app',
            '--host', host,
            '--port', str(port),
            '--reload'
        ])
    except KeyboardInterrupt:
        print("\n⏹️  Servicio detenido")

def run_tests():
    """Ejecutar pruebas de integración"""
    print("🧪 Ejecutando pruebas de integración...")
    
    try:
        result = subprocess.run([sys.executable, 'test_backend_integration.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Todas las pruebas pasaron")
            print(result.stdout)
        else:
            print("❌ Algunas pruebas fallaron")
            print(result.stderr)
            
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error ejecutando pruebas: {e}")
        return False

def main():
    """Función principal"""
    print("=" * 50)
    print("🤖 CHAT SERVICE - INICIO AUTOMÁTICO")
    print("=" * 50)
    
    # Cargar variables de entorno
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("⚠️  python-dotenv no está instalado")
        print("   Instálalo con: pip install python-dotenv")
    
    # Verificaciones previas
    print("\n📋 Verificando requisitos...")
    
    if not check_requirements():
        return
    
    if not check_env_file():
        print("\n❌ Configuración incompleta. Completa el archivo .env y ejecuta nuevamente.")
        return
    
    # Verificar backend principal (opcional)
    print("\n🔗 Verificando conexión al backend principal...")
    backend_connected = check_backend_connection()
    
    if not backend_connected:
        response = input("\n¿Continuar sin backend principal? (y/N): ")
        if response.lower() != 'y':
            print("⏹️  Configuración cancelada")
            return
    
    # Opciones de inicio
    print("\n🎯 Opciones de inicio:")
    print("1. Iniciar servicio directamente")
    print("2. Ejecutar pruebas primero")
    print("3. Solo ejecutar pruebas")
    
    choice = input("\nSelecciona una opción (1-3): ").strip()
    
    if choice == "1":
        start_service()
    elif choice == "2":
        if run_tests():
            input("\nPresiona Enter para iniciar el servicio...")
            start_service()
        else:
            print("❌ Las pruebas fallaron. Revisa la configuración.")
    elif choice == "3":
        run_tests()
    else:
        print("❌ Opción inválida")

if __name__ == "__main__":
    main()
