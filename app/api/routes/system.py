"""
Rutas de utilidad y sistema
Extraído de chat_service_real.py
"""

from fastapi import APIRouter
from datetime import datetime, timezone

from app.services.memory_service import memory_service

router = APIRouter(tags=["system"])

@router.get("/health")
async def health_check():
    """Health check con estado de bases de datos"""
    status = await memory_service.get_status()
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.1.0",
        "storage": status
    }

@router.get("/api/storage/status")
async def storage_status():
    """Estado detallado del almacenamiento"""
    return await memory_service.get_status()
