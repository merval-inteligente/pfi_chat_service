# 🤖 PFI Chat Service - Asistente Financiero Argentino

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-brightgreen.svg)](https://mongodb.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Servicio de chat inteligente especializado en mercados financieros argentinos**. Proporciona análisis en tiempo real del MERVAL, cotizaciones de divisas, información sobre inversiones y asesoramiento financiero contextualizado para el mercado local.

## ✨ Características Principales

### 🎯 **Especialización Financiera Argentina**
- 📈 **Análisis de mercados**: MERVAL, acciones principales (YPF, Galicia, Macro)
- 💵 **Cotizaciones en tiempo real**: Dólar blue, MEP, CCL, Bitcoin
- 💰 **Guía de inversiones**: Bonos soberanos, FCIs, UVAs, CEDEARs
- 🏦 **Sectores específicos**: Banca, energía, commodities, tecnología
- 📊 **Análisis macroeconómico**: Inflación, riesgo país, contexto local

### 🔐 **Autenticación y Seguridad**
- ✅ **Autenticación JWT obligatoria** - Identidad verificada del usuario
- ✅ **Validación contra backend principal** - Tokens verificados en tiempo real
- ✅ **Historial personalizado** - Conversaciones almacenadas por usuario autenticado
- ✅ **Protección de datos** - Sin acceso anónimo a funcionalidades

### 🏗️ **Arquitectura Profesional**
- ✅ **Modular y escalable** - Separación clara de responsabilidades
- ✅ **Clean Architecture** - Capas bien definidas (API, Core, Services, Models)
- ✅ **Async/Await** - Performance optimizada para alta concurrencia
- ✅ **Error handling** - Manejo robusto de errores y timeouts

## 🚀 Inicio Rápido

### 📋 Prerrequisitos

```bash
# Requerimientos del sistema
Python 3.8+ 
MongoDB Atlas (cuenta configurada)
Backend principal ejecutándose (puerto 8080)
```

### 📦 Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/nicopetcoff/pfi_chat_service.git
cd pfi_chat_service

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones
```

### ⚙️ Configuración

Crear archivo `.env` con las siguientes variables:

```env
# MongoDB Atlas
MONGODB_URL=mongodb+srv://user:password@cluster.mongodb.net/
MONGODB_DB_NAME=MervalDB

# Backend Integration
BACKEND_URL=http://localhost:8080

# Server Configuration
PORT=8084
HOST=0.0.0.0
```

### 🔥 Ejecutar

```bash
# Modo desarrollo
python main.py

# Con uvicorn (recomendado para producción)
uvicorn main:app --host 0.0.0.0 --port 8084 --reload

# Docker (próximamente)
# docker-compose up -d
```

## 📡 API Endpoints

### 🔐 **Autenticación Requerida**
Todos los endpoints requieren header de autorización:
```http
Authorization: Bearer <jwt_token>
```

### 🛤️ **Rutas Principales**

| Método | Endpoint | Descripción | Autenticación |
|--------|----------|-------------|---------------|
| `POST` | `/api/chat/message` | Enviar mensaje al asistente | ✅ Requerida |
| `GET` | `/api/chat/history` | Obtener historial personal | ✅ Requerida |
| `GET` | `/health` | Estado del servicio | ❌ Pública |
| `GET` | `/api/storage/status` | Estado de MongoDB | ❌ Pública |
| `GET` | `/docs` | Documentación Swagger | ❌ Pública |

### 💬 **Ejemplo de Uso**

```bash
# Enviar mensaje al asistente
curl -X POST "http://localhost:8084/api/chat/message" \
  -H "Authorization: Bearer <tu_token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "¿Cómo está el MERVAL?"}'

# Obtener historial
curl -X GET "http://localhost:8084/api/chat/history?limit=10" \
  -H "Authorization: Bearer <tu_token>"
```

## 🎯 Temas y Consultas Soportadas

### 📈 **Mercados y Acciones**
```
"MERVAL", "bolsa", "YPF", "Galicia", "Macro", "Pampa Energía"
```

### 💰 **Inversiones**
```
"plazo fijo", "UVA", "bonos", "FCIs", "CEDEARs", "AL30", "GD30"
```

### 💵 **Divisas y Crypto**
```
"dólar blue", "MEP", "CCL", "Bitcoin", "Ethereum", "crypto"
```

### 📊 **Análisis Económico**
```
"inflación", "riesgo país", "commodities", "soja", "agro"
```

### 🆘 **Comandos de Ayuda**
```
"ayuda", "help", "no entiendo", "inversión", "guía"
```

## 🏗️ Arquitectura del Sistema

```
chat-service/
├── 🚀 main.py                     # Punto de entrada principal
├── 📂 app/                        # Aplicación modular
│   ├── 🛤️  api/routes/             # Endpoints REST
│   │   ├── chat.py                # Rutas de chat (/api/chat/*)
│   │   └── system.py              # Health checks (/health, /status)
│   ├── 🔧 core/                   # Configuración y utilities
│   │   ├── config.py              # Variables de entorno
│   │   └── auth.py                # Middleware de autenticación
│   ├── 📝 models/                 # Modelos Pydantic
│   │   └── chat.py                # ChatMessage, ChatResponse
│   └── 🔨 services/               # Lógica de negocio
│       ├── memory_service.py      # Persistencia MongoDB
│       └── ai_service.py          # Motor de respuestas financieras
├── 📦 requirements.txt            # Dependencias Python
├── 🔐 .env                        # Variables de entorno
└── 📖 README.md                   # Esta documentación
```

### 🔄 **Flujo de Datos**

```mermaid
graph LR
    A[Cliente] -->|JWT Token| B[FastAPI Router]
    B --> C[Auth Middleware]
    C --> D[Chat Service]
    D --> E[AI Service]
    D --> F[Memory Service]
    F --> G[MongoDB Atlas]
    E --> H[Response Generator]
    H --> A
```

## 🔧 Stack Tecnológico

### 🐍 **Backend**
- **[FastAPI](https://fastapi.tiangolo.com/)** `0.115+` - Framework web moderno y rápido
- **[Uvicorn](https://www.uvicorn.org/)** `0.34+` - Servidor ASGI de alto rendimiento
- **[Pydantic](https://pydantic-docs.helpmanual.io/)** `2.11+` - Validación de datos y settings

### 💾 **Base de Datos**
- **[MongoDB Atlas](https://www.mongodb.com/atlas)** - Base de datos NoSQL en la nube
- **[Motor](https://motor.readthedocs.io/)** `3.7+` - Driver async para MongoDB

### 🔐 **Autenticación**
- **[JWT](https://jwt.io/)** - Tokens de autenticación
- **[Requests](https://requests.readthedocs.io/)** `2.32+` - Cliente HTTP para validación

### 🛠️ **Desarrollo**
- **[Python](https://python.org)** `3.8+` - Lenguaje principal
- **[Git](https://git-scm.com/)** - Control de versiones

## 🚦 Estados del Servicio

### ✅ **Healthy State**
```json
{
  "status": "healthy",
  "service": "PFI Chat Service",
  "mongodb": true,
  "timestamp": "2025-08-31T10:30:00Z"
}
```

### ❌ **Error States**
- `401 Unauthorized` - Token JWT inválido o expirado
- `503 Service Unavailable` - MongoDB no disponible
- `500 Internal Server Error` - Error interno del servidor

## 🧪 Testing y Desarrollo

### 🔍 **Comandos de Verificación**

```bash
# Verificar importaciones
python -c "from app.core.auth import verify_auth_token; print('✅ Auth OK')"
python -c "from app.services.ai_service import generate_ai_response; print('✅ AI OK')"

# Test de conectividad
curl http://localhost:8084/health

# Verificar documentación
open http://localhost:8084/docs
```

### 🐛 **Debug Mode**

```bash
# Ejecutar con logs detallados
uvicorn main:app --host 0.0.0.0 --port 8084 --reload --log-level debug
```

## 🔗 Integración con Otros Servicios

### 🔌 **Backend Principal** (Puerto 8080)
- **Autenticación**: Validación de tokens JWT
- **Perfiles de usuario**: Información personal y preferencias
- **Logs centralizados**: Auditoría de operaciones

### 📱 **Frontend React Native** (Puerto 8081)
- **Chat interface**: UI/UX para conversaciones
- **Authentication flow**: Login y gestión de sesiones
- **Real-time updates**: WebSocket para notificaciones

## 📊 Métricas y Monitoreo

### 📈 **KPIs del Servicio**
- **Tiempo de respuesta**: < 200ms promedio
- **Disponibilidad**: 99.9% uptime objetivo
- **Precisión**: Respuestas financieras actualizadas
- **Usuarios activos**: Tracking por día/semana/mes

### 🔍 **Logging**
```python
# Logs estructurados
{
  "timestamp": "2025-08-31T10:30:00Z",
  "level": "INFO",
  "user_id": "user123",
  "action": "chat_message",
  "topic": "merval",
  "response_time": "150ms"
}
```

## 🛡️ Seguridad

### 🔐 **Medidas Implementadas**
- ✅ **Autenticación obligatoria** - Sin acceso anónimo
- ✅ **Validación de tokens** - JWT verificados contra backend
- ✅ **Rate limiting** - Protección contra abuse
- ✅ **Input sanitization** - Validación con Pydantic
- ✅ **CORS configurado** - Acceso controlado desde frontend

### � **Consideraciones de Seguridad**
- Los tokens JWT deben renovarse periódicamente
- MongoDB Atlas tiene autenticación propia
- Variables sensibles en `.env` (no commitear)
- Logs no deben contener información personal

## 📚 Documentación Adicional

### 🔗 **Enlaces Útiles**
- [Documentación API (Swagger)](http://localhost:8084/docs)
- [Redoc Documentation](http://localhost:8084/redoc)
- [FastAPI Official Docs](https://fastapi.tiangolo.com/)
- [MongoDB Motor Docs](https://motor.readthedocs.io/)

### 📖 **Guías de Desarrollo**
- [Contribución](CONTRIBUTING.md) - Cómo contribuir al proyecto
- [Deployment](DEPLOYMENT.md) - Guía de despliegue
- [Troubleshooting](TROUBLESHOOTING.md) - Solución de problemas

## 🤝 Contribución

1. **Fork** el repositorio
2. **Crear** rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. **Commit** los cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. **Push** a la rama (`git push origin feature/nueva-funcionalidad`)
5. **Crear** Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver [LICENSE](LICENSE) para detalles.

## 👥 Equipo

- **Desarrollador Principal**: [Nicolás Petcoff](https://github.com/nicopetcoff)
- **Repositorio**: [pfi_chat_service](https://github.com/nicopetcoff/pfi_chat_service)

---

## 🚀 **¿Listo para empezar?**

```bash
git clone https://github.com/nicopetcoff/pfi_chat_service.git
cd pfi_chat_service
pip install -r requirements.txt
python main.py
```

**🎯 ¡Tu asistente financiero argentino está listo para ayudarte!**
