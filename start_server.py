"""
Script de arranque simple para el Chat Service
"""
import sys
import os
import uvicorn

# Agregar el directorio actual al path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Importar la aplicación
from app.main_simple import app

if __name__ == "__main__":
    print("🚀 Iniciando Chat Service en modo testing...")
    print("📍 Directorios en PATH:")
    for p in sys.path[:3]:
        print(f"   {p}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8081,
        reload=True,
        log_level="info"
    )
