"""
Chat Service - Backend Organizado Principal
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importaciones desde estructura organizada
from app.core.config import env_config, PORT, HOST
from app.services.memory_service import memory_service
from app.api.routes.chat import router as chat_router
from app.api.routes.system import router as system_router
app = FastAPI(
    title="Chat Service - Backend Organizado", 
    description="Servicio de chat con estructura modular profesional",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# FastAPI App configurada

# Incluir rutas en la aplicación
app.include_router(chat_router)
app.include_router(system_router)

# Eventos de inicio
@app.on_event("startup")
async def startup_event():
    """Conectar bases de datos al iniciar"""
    print("🚀 Iniciando Chat Service...")
    connections = await memory_service.connect()
    print(f"📊 Estado: MongoDB={connections['mongodb']}")

if __name__ == "__main__":
    import uvicorn
    from app.core.config import PORT, HOST
    uvicorn.run(app, host=HOST, port=PORT)
