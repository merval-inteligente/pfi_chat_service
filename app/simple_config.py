"""
Configuración simplificada para testing
"""
from typing import List
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class SimpleSettings:
    """Configuración simplificada"""
    
    def __init__(self):
        # App Configuration
        self.app_name = os.getenv("APP_NAME", "Chat Service")
        self.debug = os.getenv("DEBUG", "true").lower() == "true"
        self.environment = os.getenv("ENVIRONMENT", "development")
        
        # Server Configuration
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "8081"))
        
        # OpenAI Configuration
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "sk-demo-key-for-testing")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        self.openai_max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))
        
        # JWT Configuration
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", "demo-secret-key-for-testing-12345")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        
        # Chat Configuration
        self.max_context_messages = int(os.getenv("MAX_CONTEXT_MESSAGES", "20"))
        self.max_message_length = int(os.getenv("MAX_MESSAGE_LENGTH", "2000"))
        
        # CORS Configuration (simplificado)
        self.cors_origins = ["*"]
        self.cors_credentials = True
        self.cors_methods = ["*"]
        self.cors_headers = ["*"]

# Singleton instance
simple_settings = SimpleSettings()

def get_simple_settings():
    """Obtiene configuración simplificada"""
    return simple_settings
