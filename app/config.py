"""
Configuración de la aplicación
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()


class Settings(BaseSettings):
    # App Configuration
    app_name: str = "Chat Service"
    debug: bool = False
    environment: str = "production"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8081
    
    # OpenAI Configuration
    openai_api_key: str = "sk-demo-key-for-testing"
    openai_model: str = "gpt-4-turbo-preview"
    openai_max_tokens: int = 2000
    
    # Main Backend Configuration
    main_backend_url: str = "http://192.168.0.17:8080"
    main_backend_timeout: int = 30
    
    # JWT Configuration
    jwt_secret_key: str = "demo-secret-key-for-testing-12345"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 10
    redis_timeout: int = 5
    
    # Database Configuration
    database_url: Optional[str] = None
    mongodb_url: Optional[str] = None
    mongodb_database: str = "chat_db"
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "JSON"
    
    # CORS Configuration
    cors_origins: List[str] = ["*"]
    cors_credentials: bool = True
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]
    
    # WebSocket Configuration
    ws_max_connections: int = 1000
    ws_heartbeat_interval: int = 30
    
    # Chat Configuration
    max_context_messages: int = 20
    max_message_length: int = 2000
    session_timeout: int = 3600

    class Config:
        env_file = ".env"
        case_sensitive = False


# Singleton instance
settings = Settings()


def get_settings() -> Settings:
    """Get settings instance"""
    return settings
