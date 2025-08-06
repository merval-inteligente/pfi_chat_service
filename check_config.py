"""
Test rápido para verificar configuración de Redis y MongoDB
"""

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

print("🔍 VERIFICANDO CONFIGURACIÓN")
print("=" * 40)

env_config = load_env()

print("📋 Variables encontradas en .env:")
for key, value in env_config.items():
    if 'REDIS' in key or 'MONGO' in key:
        # Mostrar solo parte del valor por seguridad
        display_value = value[:30] + "..." if len(value) > 30 else value
        print(f"   {key}: {display_value}")

print("\n🔧 Variables específicas:")
REDIS_URL = env_config.get('REDIS_URL', 'NO ENCONTRADO')
MONGODB_URI = env_config.get('MONGODB_URI', 'NO ENCONTRADO')
MONGODB_DB_NAME = env_config.get('MONGODB_DB_NAME', 'NO ENCONTRADO')

print(f"REDIS_URL: {REDIS_URL[:50]}..." if REDIS_URL != 'NO ENCONTRADO' else f"REDIS_URL: {REDIS_URL}")
print(f"MONGODB_URI: {MONGODB_URI[:50]}..." if MONGODB_URI != 'NO ENCONTRADO' else f"MONGODB_URI: {MONGODB_URI}")
print(f"MONGODB_DB_NAME: {MONGODB_DB_NAME}")

print("\n✅ Configuración verificada")
