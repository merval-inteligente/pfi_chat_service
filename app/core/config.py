"""
Configuración del Chat Service
Extraído de chat_service_real.py
"""

def load_env():
    """Cargar variables de entorno desde archivo .env"""
    env_vars = {}
    try:
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value
    except FileNotFoundError:
        pass
    return env_vars

# Configuración global
env_config = load_env()

# MongoDB Configuration
MONGODB_URL = env_config.get('MONGODB_URL', 'mongodb+srv://admin:tRVIi8NhbKbzDj0q@cluster0.dad6cgj.mongodb.net/MervalDB?retryWrites=true&w=majority')
MONGODB_DATABASE = env_config.get('MONGODB_DATABASE', 'MervalDB')
MONGODB_URI = env_config.get('MONGODB_URL', 'mongodb+srv://admin:tRVIi8NhbKbzDj0q@cluster0.dad6cgj.mongodb.net/MervalDB?retryWrites=true&w=majority')
MONGODB_DB_NAME = env_config.get('MONGODB_DB_NAME', 'MervalDB')

# Server Configuration
PORT = int(env_config.get('PORT', 8084))
HOST = env_config.get('HOST', '0.0.0.0')

print(f"🔍 Config loaded - MongoDB: {MONGODB_URI[:50]}...")
