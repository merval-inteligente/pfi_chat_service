# Guía de Integración del Chat Service

## Resumen de la Arquitectura

```
Frontend Apps          Chat Service          Backend Principal
     |                       |                      |
     |<--- SDK -------> FastAPI (8084/8085) <---> HTTP (8080)
     |                       |                      |
     |                 Bases de datos:             |
     |                 - Redis Cloud               |
     |                 - MongoDB Atlas             |
     |                 - Memory (fallback)         |
```

## Archivos Creados para la Integración

### 1. Backend Integration (`backend_integration.py`)
**Propósito**: Cliente HTTP para comunicarse con tu backend principal

**Funcionalidades**:
- Verificación de tokens JWT
- Obtención de perfil de usuario
- Acceso a preferencias del usuario
- Consulta de datos del portafolio
- Registro de actividad del usuario

### 2. Chat Service Integrado (`chat_integrated_backend.py`)
**Propósito**: Servicio de chat mejorado con personalización

**Funcionalidades**:
- Respuestas personalizadas basadas en el contexto del usuario
- Integración automática con el backend principal
- Almacenamiento inteligente de conversaciones
- IA simulada especializada en mercado financiero argentino

### 3. SDK Frontend (`frontend_sdk.js`)
**Propósito**: Cliente JavaScript para React Native y web

**Funcionalidades**:
- Autenticación automática
- Envío y recepción de mensajes
- Gestión del historial de chat
- Verificación de estado del servicio

### 4. Tests (`test_backend_integration.py`)
**Propósito**: Suite de pruebas para validar la integración

## Pasos de Implementación

### Paso 1: Configurar el Backend Principal

Tu backend en `http://192.168.0.17:8080` debe tener estos endpoints:

```python
# Endpoints necesarios en tu backend principal:

@app.post("/auth/verify")
async def verify_token(token: str):
    """Verificar si un token JWT es válido"""
    return {"valid": True, "user_id": "123", "expires_at": "..."}

@app.get("/users/{user_id}/profile")
async def get_user_profile(user_id: str):
    """Obtener perfil del usuario"""
    return {
        "user_id": user_id,
        "name": "Juan Pérez",
        "email": "juan@example.com",
        "created_at": "2024-01-01T00:00:00Z"
    }

@app.get("/users/{user_id}/preferences")
async def get_user_preferences(user_id: str):
    """Obtener preferencias del usuario"""
    return {
        "language": "es",
        "timezone": "America/Argentina/Buenos_Aires",
        "risk_tolerance": "medium",
        "investment_goals": ["retirement", "savings"]
    }

@app.get("/users/{user_id}/portfolio")
async def get_user_portfolio(user_id: str):
    """Obtener datos del portafolio"""
    return {
        "total_value": 150000.50,
        "positions": [
            {"symbol": "GGAL", "quantity": 100, "value": 15000},
            {"symbol": "YPF", "quantity": 50, "value": 8500}
        ],
        "performance": {
            "daily_change": 2.5,
            "total_return": 12.3
        }
    }

@app.post("/users/{user_id}/activity")
async def log_user_activity(user_id: str, activity_data: dict):
    """Registrar actividad del usuario"""
    return {"success": True, "logged_at": "2024-01-01T12:00:00Z"}
```

### Paso 2: Configurar Variables de Entorno

Crea un archivo `.env` en el directorio `chat-service`:

```env
# Backend Principal
MAIN_BACKEND_URL=http://192.168.0.17:8080
MAIN_BACKEND_TIMEOUT=30

# Chat Service
CHAT_SERVICE_PORT=8084
CHAT_SERVICE_HOST=192.168.0.17

# JWT Configuration
JWT_SECRET_KEY=tu_clave_secreta_aqui
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# Redis Cloud (Upstash)
REDIS_URL=tu_redis_url_aqui

# MongoDB Atlas
MONGODB_URL=tu_mongodb_url_aqui
MONGODB_DB_NAME=chatbot_conversations

# CORS
ALLOWED_ORIGINS=["http://localhost:3000", "http://192.168.0.17:3000"]
```

### Paso 3: Instalar Dependencias

```powershell
# En el directorio chat-service
pip install -r requirements.txt

# Si no tienes requirements.txt, instala las dependencias nuevas:
pip install aiohttp asyncio-timeout
```

### Paso 4: Ejecutar el Chat Service Integrado

```powershell
# Opción 1: Usar el servicio integrado
python chat_integrated_backend.py

# Opción 2: Usar uvicorn
uvicorn chat_integrated_backend:app --host 192.168.0.17 --port 8084 --reload
```

### Paso 5: Implementar en el Frontend

#### Para React Native:

```javascript
import ChatServiceSDK from './frontend_sdk.js';

// Inicializar el SDK
const chatSDK = new ChatServiceSDK({
    baseUrl: 'http://192.168.0.17:8084'
});

// En tu componente de chat
export default function ChatScreen() {
    const [messages, setMessages] = useState([]);
    const [isAuthenticated, setIsAuthenticated] = useState(false);

    useEffect(() => {
        // Autenticar al usuario
        authenticateUser();
    }, []);

    const authenticateUser = async () => {
        try {
            const result = await chatSDK.authenticate("user123");
            if (result.success) {
                setIsAuthenticated(true);
                loadChatHistory();
            }
        } catch (error) {
            console.error('Auth failed:', error);
        }
    };

    const sendMessage = async (text) => {
        try {
            const response = await chatSDK.sendMessage(text);
            setMessages(prev => [...prev, {
                user: response.userMessage,
                assistant: response.assistantResponse,
                timestamp: response.timestamp,
                personalized: response.personalized
            }]);
        } catch (error) {
            console.error('Send failed:', error);
        }
    };

    const loadChatHistory = async () => {
        try {
            const history = await chatSDK.getChatHistory();
            setMessages(history.messages || []);
        } catch (error) {
            console.error('History failed:', error);
        }
    };

    // Tu UI aquí...
}
```

#### Para Web (React):

```javascript
import ChatServiceSDK from './frontend_sdk.js';

function ChatComponent() {
    const [chatSDK] = useState(() => new ChatServiceSDK());
    const [messages, setMessages] = useState([]);
    const [inputText, setInputText] = useState('');

    useEffect(() => {
        initializeChat();
    }, []);

    const initializeChat = async () => {
        // Verificar salud del servicio
        const health = await chatSDK.checkHealth();
        if (health.status === 'healthy') {
            // Autenticar usuario
            await chatSDK.authenticate("user123");
        }
    };

    const handleSendMessage = async () => {
        if (!inputText.trim()) return;

        try {
            const response = await chatSDK.sendMessage(inputText);
            setMessages(prev => [...prev, response]);
            setInputText('');
        } catch (error) {
            console.error('Error sending message:', error);
        }
    };

    return (
        <div className="chat-container">
            <div className="messages">
                {messages.map((msg, index) => (
                    <div key={index} className="message-pair">
                        <div className="user-message">{msg.userMessage}</div>
                        <div className="assistant-message">
                            {msg.assistantResponse}
                            {msg.personalized && <span className="personalized-badge">✨</span>}
                        </div>
                    </div>
                ))}
            </div>
            <div className="input-area">
                <input
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                />
                <button onClick={handleSendMessage}>Enviar</button>
            </div>
        </div>
    );
}
```

### Paso 6: Ejecutar Pruebas

```powershell
# Ejecutar las pruebas de integración
python test_backend_integration.py
```

## Flujo de Datos Completo

1. **Usuario se autentica en tu app**: App frontend → Tu backend (8080)
2. **App obtiene token**: Tu backend devuelve JWT
3. **App inicializa chat**: Frontend → Chat Service (8084) con token opcional
4. **Chat Service verifica usuario**: Chat Service → Tu backend (8080) para verificar token
5. **Chat Service obtiene contexto**: Chat Service → Tu backend (8080) para perfil/preferencias/portafolio
6. **Usuario envía mensaje**: Frontend → Chat Service
7. **IA genera respuesta personalizada**: Chat Service usa contexto del usuario
8. **Respuesta se envía al frontend**: Chat Service → Frontend
9. **Actividad se registra**: Chat Service → Tu backend (8080) para logging

## Personalización de Respuestas

El sistema personaliza las respuestas basándose en:

- **Perfil del usuario**: Nombre, preferencias de comunicación
- **Datos del portafolio**: Posiciones actuales, rendimiento
- **Preferencias**: Tolerancia al riesgo, objetivos de inversión
- **Historial de conversación**: Contexto de mensajes anteriores

## Monitoreo y Logs

El sistema registra:
- Todas las interacciones del chat
- Errores de conexión con el backend
- Tiempos de respuesta
- Uso de personalización

Revisa los logs en:
- Console del chat service
- Logs de tu backend principal
- Dashboards de Redis Cloud y MongoDB Atlas

## Solución de Problemas

### Error de Conexión al Backend
```
Error: Connection refused to http://192.168.0.17:8080
```
**Solución**: Verificar que tu backend principal esté ejecutándose en el puerto 8080

### Token JWT Inválido
```
Error: Token verification failed
```
**Solución**: Verificar que el JWT_SECRET_KEY coincida entre servicios

### Sin Personalización
```
Warning: User context not available, using generic responses
```
**Solución**: Verificar que los endpoints del backend principal estén funcionando

¡La integración está completa! Tienes un sistema de chat totalmente funcional que se conecta con tu backend y ofrece respuestas personalizadas.
