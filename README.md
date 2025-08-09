# 🤖 PFI Chat Service

Chat service optimizado para el sistema PFI (Proyecto Final Integrador).

## 🚀 Inicio Rápido

### Prerrequisitos
- Python 3.8+
- MongoDB Atlas (configurado)
- Redis Cloud (Upstash)

### Instalación
```bash
pip install -r requirements.txt
```

### Configuración
1. Copiar `.env.example` a `.env`
2. Configurar variables de entorno en `.env`

### Ejecutar
```bash
uvicorn chat_service_real:app --host 0.0.0.0 --port 8084 --reload
```

## 📡 Endpoints

- `GET /health` - Estado del servicio
- `POST /chat` - Enviar mensaje
- `GET /docs` - Documentación API

## 🏗️ Arquitectura

- **Framework**: FastAPI
- **Base de datos**: MongoDB (compartida con backend principal)
- **Cache**: Redis Cloud (Upstash)
- **Puerto**: 8084

## 📦 Dependencias Principales

- `fastapi` - Framework web
- `motor` - Driver async de MongoDB
- `redis` - Cliente Redis
- `uvicorn` - Servidor ASGI

## 🔗 Integración

Se conecta con:
- Backend Principal (puerto 8080)
- Frontend React Native (puerto 8081)
