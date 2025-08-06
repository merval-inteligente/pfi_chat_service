# 🤖 Chat Service - Microservicio de Chat Inteligente

Microservicio especializado en chat inteligente para aplicaciones financieras, con foco en el mercado argentino (MERVAL).

## 🚀 Características

- **🧠 IA Especializada**: Asistente financiero con conocimientos del mercado argentino
- **⚡ WebSocket**: Chat en tiempo real con indicadores de escritura
- **🔐 Autenticación**: Validación JWT compatible con backend principal
- **📊 Contexto Inteligente**: Integración con datos del usuario y mercado
- **🎯 Rate Limiting**: Protección contra abuso
- **📈 Análisis de Sentimiento**: Evaluación automática de mensajes
- **💾 Memoria Persistente**: Historial de conversaciones en Redis
- **🏥 Health Checks**: Monitoreo de estado del servicio

## 🛠️ Stack Tecnológico

- **Framework**: FastAPI
- **IA**: OpenAI GPT-4 Turbo
- **Cache/Sesiones**: Redis
- **Base de Datos**: PostgreSQL (alternativa: MongoDB)
- **WebSockets**: FastAPI WebSockets
- **Autenticación**: JWT con python-jose
- **Rate Limiting**: SlowAPI
- **Logging**: Loguru
- **Contenedores**: Docker & Docker Compose

## 📁 Estructura del Proyecto

```
chat-service/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app principal
│   ├── config.py              # Configuraciones
│   ├── models/
│   │   ├── __init__.py
│   │   ├── chat.py            # Modelos de chat
│   │   └── user.py            # Modelos de usuario
│   ├── services/
│   │   ├── __init__.py
│   │   ├── openai_service.py  # Integración OpenAI
│   │   ├── context_service.py # Contexto del usuario
│   │   ├── memory_service.py  # Gestión de memoria
│   │   └── auth_service.py    # Validación JWT
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py            # Dependencies
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── chat.py        # Endpoints REST
│   │       └── websocket.py   # WebSocket handlers
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py        # Seguridad JWT
│   │   └── database.py        # Conexiones DB
│   └── utils/
│       ├── __init__.py
│       └── prompts.py         # System prompts
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── nginx.conf
├── init.sql
└── README.md
```

## 🔧 Configuración e Instalación

### 1. Clonar y preparar el proyecto

```bash
cd chat-service
cp .env.example .env
```

### 2. Configurar variables de entorno

Edita el archivo `.env` con tus valores:

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here

# JWT Configuration (debe coincidir con tu backend principal)
JWT_SECRET_KEY=your-jwt-secret-key-here

# Main Backend URL
MAIN_BACKEND_URL=http://192.168.0.17:8080
```

### 3. Instalación Local (Desarrollo)

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Instalar Redis (requerido)
# Ubuntu/Debian: sudo apt install redis-server
# macOS: brew install redis
# Windows: usar Docker o WSL

# Ejecutar servicios
redis-server  # En otra terminal

# Ejecutar aplicación
python -m uvicorn app.main:app --reload --port 8081
```

### 4. Instalación con Docker (Recomendado)

```bash
# Ejecutar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f chat-service

# Detener servicios
docker-compose down
```

## 📚 API Endpoints

### REST API

#### Chat

```http
POST /api/chat/message
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "¿Cómo está el MERVAL hoy?",
  "user_context": {}
}
```

#### Historial

```http
GET /api/chat/history/{user_id}?limit=50
Authorization: Bearer <token>
```

#### Limpiar Historial

```http
DELETE /api/chat/history/{user_id}
Authorization: Bearer <token>
```

#### Resumen de Conversación

```http
GET /api/chat/summary/{user_id}
Authorization: Bearer <token>
```

#### Análisis de Sentimiento

```http
POST /api/chat/analyze-sentiment
Authorization: Bearer <token>
Content-Type: application/json

{
  "text": "Estoy preocupado por la caída del mercado"
}
```

### WebSocket

```javascript
// Conexión
const ws = new WebSocket('ws://localhost:8081/ws/chat/{user_id}?token={jwt_token}');

// Enviar mensaje
ws.send(JSON.stringify({
  type: 'send_message',
  data: {
    message: '¿Qué opinas sobre YPF?'
  }
}));

// Recibir respuesta
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

### Health Check

```http
GET /health
```

## 💡 Ejemplos de Uso

### Cliente JavaScript/React Native

```javascript
class ChatService {
  constructor(baseUrl, token) {
    this.baseUrl = baseUrl;
    this.token = token;
    this.ws = null;
  }

  // Conexión WebSocket
  connect(userId) {
    this.ws = new WebSocket(`${this.baseUrl}/ws/chat/${userId}?token=${this.token}`);
    
    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };
  }

  // Enviar mensaje
  sendMessage(text) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'send_message',
        data: { message: text }
      }));
    }
  }

  // API REST - Obtener historial
  async getHistory(userId) {
    const response = await fetch(`${this.baseUrl}/api/chat/history/${userId}`, {
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    return response.json();
  }
}

// Uso
const chat = new ChatService('http://localhost:8081', 'your-jwt-token');
chat.connect('user-123');
chat.sendMessage('¿Cómo está el mercado argentino hoy?');
```

### Cliente Python

```python
import asyncio
import websockets
import json
import requests

class ChatClient:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token
    
    async def connect_websocket(self, user_id):
        uri = f"ws://{self.base_url}/ws/chat/{user_id}?token={self.token}"
        
        async with websockets.connect(uri) as websocket:
            # Enviar mensaje
            await websocket.send(json.dumps({
                "type": "send_message",
                "data": {"message": "¿Qué acciones argentinas recomendás?"}
            }))
            
            # Recibir respuesta
            response = await websocket.recv()
            print(json.loads(response))
    
    def get_history(self, user_id):
        response = requests.get(
            f"{self.base_url}/api/chat/history/{user_id}",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        return response.json()

# Uso
client = ChatClient("localhost:8081", "your-jwt-token")
asyncio.run(client.connect_websocket("user-123"))
```

## 🔒 Seguridad

### Autenticación JWT

El servicio valida tokens JWT que deben incluir:

```json
{
  "sub": "user_id",
  "exp": 1234567890,
  "iat": 1234567890,
  "iss": "your-app"
}
```

### Rate Limiting

- **Chat**: 20 mensajes por minuto por usuario
- **Historial**: 10 consultas por minuto por usuario
- **General**: 100 requests por minuto por IP

### CORS

Configurado para permitir conexiones desde React Native y aplicaciones web.

## 🤖 Sistema de IA

### Prompts Especializados

El asistente está entrenado específicamente para:

- 📈 **Mercado Argentino**: MERVAL, Panel General, ADRs
- 💰 **Instrumentos Locales**: Acciones, bonos, LEBACs, FCI
- 🌍 **Contexto Macro**: Inflación, tipo de cambio, política monetaria
- ₿ **Criptomonedas**: Análisis desde perspectiva argentina
- ⚖️ **Gestión de Riesgo**: Perfiles y estrategias adaptadas

### Personalización

El asistente adapta sus respuestas según:

- Perfil de riesgo del usuario
- Acciones favoritas
- Objetivos de inversión
- Historial de conversación
- Valor del portfolio

## 📊 Monitoreo y Logs

### Logs Estructurados

```json
{
  "timestamp": "2024-08-04T12:00:00Z",
  "level": "INFO",
  "message": "POST /api/chat/message - 200 - 0.543s",
  "method": "POST",
  "url": "/api/chat/message",
  "status_code": 200,
  "process_time": 0.543,
  "client_ip": "192.168.1.100"
}
```

### Health Checks

```bash
# Verificar estado
curl http://localhost:8081/health

# Respuesta
{
  "status": "healthy",
  "timestamp": "2024-08-04T12:00:00Z",
  "version": "1.0.0",
  "services": {
    "redis": "healthy",
    "openai": "healthy",
    "main_backend": "healthy"
  }
}
```

### Métricas Docker

```bash
# Ver estado de contenedores
docker-compose ps

# Verificar logs
docker-compose logs -f chat-service

# Estadísticas de uso
docker stats chat-service
```

## 🚀 Deployment

### Desarrollo

```bash
docker-compose up -d
```

### Producción

1. **Actualizar variables de entorno**:
   ```env
   DEBUG=false
   ENVIRONMENT=production
   LOG_LEVEL=WARNING
   ```

2. **Usar secrets para credenciales**:
   ```bash
   docker secret create openai_key openai_key.txt
   docker secret create jwt_secret jwt_secret.txt
   ```

3. **Configurar reverse proxy**:
   - Nginx incluido en docker-compose
   - Configurar SSL/TLS
   - Optimizar rate limiting

4. **Monitoreo**:
   - Agregar Prometheus metrics
   - Configurar alertas
   - Logs centralizados

## 🔧 Troubleshooting

### Errores Comunes

1. **Error de conexión OpenAI**:
   ```bash
   # Verificar API key
   curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
   ```

2. **Error de Redis**:
   ```bash
   # Verificar conexión
   redis-cli ping
   docker-compose logs redis
   ```

3. **Error JWT**:
   ```bash
   # Verificar token
   echo "JWT_TOKEN" | base64 -d
   ```

4. **Error WebSocket**:
   ```bash
   # Verificar conexión
   wscat -c "ws://localhost:8081/ws/chat/test?token=TOKEN"
   ```

### Debug Mode

```bash
# Ejecutar con debug activado
DEBUG=true docker-compose up chat-service

# Ver logs detallados
docker-compose logs -f --tail=100 chat-service
```

## 🤝 Contribución

1. Fork el proyecto
2. Crear branch para feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push al branch (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver archivo [LICENSE](LICENSE) para detalles.

## 🆘 Soporte

Para reportar bugs o solicitar features:

1. **Issues**: [GitHub Issues](../../issues)
2. **Documentación**: Ver `/docs` en modo desarrollo
3. **Health Check**: `GET /health` para verificar estado

---

🇦🇷 **Hecho con ❤️ para el mercado argentino**
