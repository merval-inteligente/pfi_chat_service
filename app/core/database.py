"""
Conexiones a base de datos
"""
from typing import Optional
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from loguru import logger

from ..config import get_settings


# Base para modelos SQLAlchemy
Base = declarative_base()


class DatabaseManager:
    """Manejador de conexiones a base de datos"""
    
    def __init__(self):
        self.settings = get_settings()
        self.engine = None
        self.session_factory = None
        
    async def initialize(self):
        """Inicializa la conexión a la base de datos"""
        if not self.settings.database_url:
            logger.warning("No se configuró URL de base de datos")
            return
            
        try:
            # Crear engine asíncrono
            self.engine = create_async_engine(
                self.settings.database_url,
                echo=self.settings.debug,
                pool_pre_ping=True,
                pool_recycle=3600,
            )
            
            # Crear factory de sesiones
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            logger.info("Conexión a base de datos inicializada")
            
        except Exception as e:
            logger.error(f"Error al inicializar base de datos: {str(e)}")
            
    async def get_session(self) -> Optional[AsyncSession]:
        """
        Obtiene una sesión de base de datos
        
        Returns:
            Sesión de base de datos o None si no está inicializada
        """
        if not self.session_factory:
            return None
            
        return self.session_factory()
    
    async def close(self):
        """Cierra las conexiones a la base de datos"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Conexiones a base de datos cerradas")


# Singleton instance
db_manager = DatabaseManager()


async def get_db_session() -> Optional[AsyncSession]:
    """
    Dependency para obtener sesión de base de datos
    
    Returns:
        Sesión de base de datos
    """
    session = await db_manager.get_session()
    if not session:
        return None
        
    try:
        yield session
    finally:
        await session.close()


# Modelos de base de datos (si se necesitan)
class ChatMessageDB(Base):
    """Modelo de mensaje de chat en base de datos"""
    __tablename__ = "chat_messages"
    
    # Aquí irían las columnas si decidimos usar DB en lugar de solo Redis
    pass


class UserSessionDB(Base):
    """Modelo de sesión de usuario en base de datos"""
    __tablename__ = "user_sessions"
    
    # Aquí irían las columnas si decidimos persistir sesiones
    pass
