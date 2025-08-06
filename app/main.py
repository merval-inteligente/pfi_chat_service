"""
Aplicación principal FastAPI - Chat Service
"""
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn
from loguru import logger
import sys

from .config import get_settings
from .models.chat import HealthCheck
from .core.database import db_manager
from .api.routes.chat import router as chat_router
from .api.routes.websocket import router as websocket_router


# Configuración
settings = get_settings()

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)

# Configurar logging
logger.remove()
if settings.log_format.upper() == "JSON":
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        level=settings.log_level.upper(),
        serialize=True
    )
else:
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level.upper()
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manejador del ciclo de vida de la aplicación"""
    
    # Startup
    logger.info("🚀 Iniciando Chat Service...")
    
    # Inicializar base de datos
    await db_manager.initialize()
    
    # Aquí podrías agregar más inicializaciones
    # - Verificar conexión a Redis
    # - Validar API keys
    # - Cargar configuraciones adicionales
    
    logger.info("✅ Chat Service iniciado correctamente")
    
    yield
    
    # Shutdown
    logger.info("🛑 Deteniendo Chat Service...")
    
    # Cerrar conexiones
    await db_manager.close()
    
    logger.info("✅ Chat Service detenido correctamente")


# Crear aplicación FastAPI
app = FastAPI(
    title=settings.app_name,
    description="Microservicio de Chat Inteligente para aplicación financiera",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)


# Middleware personalizado para logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware para logging de requests"""
    start_time = datetime.utcnow()
    
    # Procesar request
    response = await call_next(request)
    
    # Calcular tiempo de procesamiento
    process_time = (datetime.utcnow() - start_time).total_seconds()
    
    # Log estructurado
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s",
        extra={
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "process_time": process_time,
            "client_ip": request.client.host if request.client else "unknown"
        }
    )
    
    return response


# Manejadores de errores
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Manejador de errores de validación"""
    logger.warning(f"Error de validación en {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Error de validación",
            "details": exc.errors(),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception):
    """Manejador de errores internos del servidor"""
    logger.error(f"Error interno en {request.url}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Error interno del servidor",
            "message": "Ocurrió un error inesperado. Por favor, intenta nuevamente.",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Health Check
@app.get("/health", response_model=HealthCheck)
@limiter.limit("10/minute")
async def health_check(request: Request):
    """
    Health check endpoint
    
    Returns:
        Estado de salud del servicio
    """
    try:
        # Verificar servicios
        services_status = {}
        
        # Verificar Redis (simulado)
        try:
            # Aquí harías una verificación real de Redis
            services_status["redis"] = "healthy"
        except:
            services_status["redis"] = "unhealthy"
        
        # Verificar OpenAI (simulado)
        try:
            # Aquí harías una verificación real de OpenAI
            services_status["openai"] = "healthy"
        except:
            services_status["openai"] = "unhealthy"
        
        # Verificar backend principal (simulado)
        try:
            # Aquí harías una verificación real del backend
            services_status["main_backend"] = "healthy"
        except:
            services_status["main_backend"] = "unhealthy"
        
        # Determinar estado general
        overall_status = "healthy" if all(
            status == "healthy" for status in services_status.values()
        ) else "degraded"
        
        return HealthCheck(
            status=overall_status,
            timestamp=datetime.utcnow(),
            version="1.0.0",
            services=services_status
        )
        
    except Exception as e:
        logger.error(f"Error en health check: {str(e)}")
        return HealthCheck(
            status="unhealthy",
            timestamp=datetime.utcnow(),
            version="1.0.0",
            services={"error": str(e)}
        )


# Incluir routers
app.include_router(
    chat_router,
    prefix="/api/chat",
    tags=["Chat"]
)

app.include_router(
    websocket_router,
    prefix="/ws",
    tags=["WebSocket"]
)


# Endpoint raíz
@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "service": settings.app_name,
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs" if settings.debug else "disabled",
        "timestamp": datetime.utcnow().isoformat()
    }


# Función para ejecutar el servidor
def run_server():
    """Ejecuta el servidor"""
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True
    )


if __name__ == "__main__":
    run_server()
