# 🤖 Chat Service - Merval Inteligente

FastAPI backend para chat con asistente especializado en el mercado financiero argentino (MERVAL).

## 🚀 Características

- **Asistente Personalizado**: Integración con asistente OpenAI "Merval Inteligente"
- **Información MERVAL**: Datos sobre activos del mercado argentino
- **Sin Recomendaciones**: Solo información educativa, no asesoramiento
- **Fallback Inteligente**: Sistema de respaldo multinivel
- **MongoDB**: Almacenamiento de historial de conversaciones
- **Autenticación JWT**: Integración con backend principal

## 📁 Estructura del Proyecto

```
chat-service/
├── main.py                    # FastAPI app principal
├── requirements.txt           # Dependencias
├── .env                      # Variables de entorno
├── app/
│   ├── api/routes/           # Endpoints
│   │   ├── chat.py          # Rutas de chat
│   │   └── system.py        # Rutas de sistema
│   ├── core/                # Configuración
│   │   ├── config.py        # Variables de entorno
│   │   └── auth.py          # Autenticación
│   ├── models/              # Modelos Pydantic
│   │   └── chat.py          # Modelos de chat
│   └── services/            # Lógica de negocio
│       ├── chat_service.py  # Servicio consolidado de IA
│       └── memory_service.py # Gestión de MongoDB
```

## 🔧 Instalación

1. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

2. **Configurar variables de entorno (.env):**
```env
# OpenAI
OPENAI_API_KEY=sk-proj-tu-api-key-aqui

# MongoDB
MONGODB_URL=mongodb+srv://user:password@cluster.mongodb.net/database

# Backend principal
BACKEND_URL=http://localhost:8080

# Servidor
HOST=0.0.0.0
PORT=8084
```

## 🎯 Uso

### Iniciar servidor:
```bash
python main.py
```

### Endpoints disponibles:

#### 1. **Chat con autenticación** 
```http
POST /api/chat/message
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "message": "¿Cómo está YPF hoy?"
}
```

#### 2. **Chat de prueba (sin autenticación)**
```http
POST /api/chat/test
Content-Type: application/json

{
  "message": "¿Qué es el MERVAL?"
}
```

#### 3. **Historial de chat**
```http
GET /api/chat/history?limit=20
Authorization: Bearer <jwt_token>
```

#### 4. **Health check**
```http
GET /health
```

### 📊 Documentación automática:
- **Swagger UI**: http://localhost:8084/docs
- **ReDoc**: http://localhost:8084/redoc

## 🤖 Funcionalidades del Asistente

### ✅ **Información que proporciona:**
- Precios y variaciones de acciones del MERVAL
- Información sobre empresas argentinas
- Datos de volumen de operaciones
- Contexto del mercado financiero argentino
- Análisis técnico y fundamental básico

### ❌ **Lo que NO hace:**
- No da recomendaciones de inversión
- No sugiere timing de compra/venta
- No realiza asesoramiento financiero personalizado

### 🔄 **Sistema de Fallback:**
1. **Asistente OpenAI personalizado** (primera opción)
2. **Chat Completion básico** (si el asistente falla)
3. **Respuestas predefinidas** (último recurso)

## 🛠️ Configuración del Asistente

El asistente personalizado "Merval Inteligente" está configurado con:
- **ID**: `asst_XTeMOZNGajadI4NxfFO3s5jF`
- **Modelo**: GPT-4
- **Especialización**: Mercado financiero argentino
- **Tono**: Educativo, no asesor

## 📈 Estado del Sistema

Verificar en `/health`:
```json
{
  "status": "healthy",
  "services": {
    "mongodb": true,
    "openai": {
      "configured": true,
      "available": true,
      "assistant_available": true
    }
  }
}
```

## 🔐 Autenticación

El servicio requiere JWT token del backend principal para endpoints protegidos. El token debe incluir:
- `user_id`: ID único del usuario
- `name`: Nombre del usuario
- `email`: Email del usuario

## 💾 Almacenamiento

Las conversaciones se almacenan en MongoDB con:
- Historial por usuario
- Timestamp de mensajes
- Metadatos de storage

## 🚨 Disclaimers

Todas las respuestas incluyen automáticamente:
> "📊 Información solo con fines informativos. No constituye recomendación de inversión."

---

**Versión**: 3.0.0 - Limpia y Consolidada
**Autor**: Nicolas Petcoff
**Fecha**: Octubre 2025