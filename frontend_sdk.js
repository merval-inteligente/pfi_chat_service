// SDK para el frontend (React Native / Web)
// Chat Service Integration

const CHAT_SERVICE_CONFIG = {
    baseUrl: 'http://192.168.0.17:8085', // Cambiar por tu IP/dominio
    timeout: 30000,
    endpoints: {
        health: '/health',
        auth: '/auth/token',
        message: '/chat/message',
        history: '/chat/history',
        context: '/chat/context'
    }
};

class ChatServiceSDK {
    constructor(config = CHAT_SERVICE_CONFIG) {
        this.config = config;
        this.token = null;
        this.userId = null;
    }

    /**
     * Autenticar usuario y obtener token
     */
    async authenticate(userId, mainBackendToken = null) {
        try {
            const response = await fetch(`${this.config.baseUrl}${this.config.endpoints.auth}?user_id=${userId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(mainBackendToken && { 'X-Backend-Token': mainBackendToken })
                }
            });

            if (!response.ok) {
                throw new Error(`Auth failed: ${response.status}`);
            }

            const data = await response.json();
            this.token = data.access_token;
            this.userId = userId;

            return {
                success: true,
                token: this.token,
                expiresIn: data.expires_in
            };

        } catch (error) {
            console.error('Chat authentication error:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Verificar estado del servicio
     */
    async checkHealth() {
        try {
            const response = await fetch(`${this.config.baseUrl}${this.config.endpoints.health}`);
            
            if (!response.ok) {
                throw new Error(`Health check failed: ${response.status}`);
            }

            return await response.json();

        } catch (error) {
            console.error('Health check error:', error);
            return { status: 'error', error: error.message };
        }
    }

    /**
     * Obtener contexto del usuario
     */
    async getUserContext() {
        if (!this.token || !this.userId) {
            throw new Error('Not authenticated');
        }

        try {
            const response = await fetch(`${this.config.baseUrl}${this.config.endpoints.context}/${this.userId}`, {
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Context fetch failed: ${response.status}`);
            }

            return await response.json();

        } catch (error) {
            console.error('Get context error:', error);
            throw error;
        }
    }

    /**
     * Enviar mensaje al chat
     */
    async sendMessage(message) {
        if (!this.token) {
            throw new Error('Not authenticated');
        }

        try {
            const response = await fetch(`${this.config.baseUrl}${this.config.endpoints.message}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message })
            });

            if (!response.ok) {
                throw new Error(`Send message failed: ${response.status}`);
            }

            const data = await response.json();
            
            return {
                messageId: data.message_id,
                userMessage: data.user_message,
                assistantResponse: data.assistant_response,
                timestamp: data.timestamp,
                personalized: data.personalized,
                hasContext: data.user_context !== null
            };

        } catch (error) {
            console.error('Send message error:', error);
            throw error;
        }
    }

    /**
     * Obtener historial de chat
     */
    async getChatHistory(limit = 50) {
        if (!this.token || !this.userId) {
            throw new Error('Not authenticated');
        }

        try {
            const response = await fetch(`${this.config.baseUrl}${this.config.endpoints.history}/${this.userId}?limit=${limit}`, {
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Get history failed: ${response.status}`);
            }

            return await response.json();

        } catch (error) {
            console.error('Get history error:', error);
            throw error;
        }
    }

    /**
     * Limpiar token (logout)
     */
    logout() {
        this.token = null;
        this.userId = null;
    }

    /**
     * Verificar si está autenticado
     */
    isAuthenticated() {
        return this.token !== null;
    }
}

// Para React Native
export default ChatServiceSDK;

// Para uso en Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChatServiceSDK;
}

/* 
EJEMPLO DE USO EN REACT NATIVE:

import ChatServiceSDK from './chat_sdk';

const chatSDK = new ChatServiceSDK();

// En tu componente React
const ChatScreen = () => {
    const [messages, setMessages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);

    // Autenticar al iniciar
    useEffect(() => {
        const authenticate = async () => {
            const result = await chatSDK.authenticate('user_123');
            if (result.success) {
                console.log('Chat autenticado');
                // Cargar historial
                loadHistory();
            }
        };
        authenticate();
    }, []);

    // Cargar historial
    const loadHistory = async () => {
        try {
            const history = await chatSDK.getChatHistory();
            setMessages(history.messages);
        } catch (error) {
            console.error('Error cargando historial:', error);
        }
    };

    // Enviar mensaje
    const sendMessage = async (text) => {
        setIsLoading(true);
        try {
            const response = await chatSDK.sendMessage(text);
            
            // Agregar mensaje del usuario
            setMessages(prev => [...prev, {
                id: Date.now(),
                message: response.userMessage,
                type: 'user',
                timestamp: new Date()
            }]);

            // Agregar respuesta del asistente
            setMessages(prev => [...prev, {
                id: response.messageId,
                message: response.assistantResponse,
                type: 'assistant',
                timestamp: new Date(response.timestamp),
                personalized: response.personalized
            }]);

        } catch (error) {
            console.error('Error enviando mensaje:', error);
            // Mostrar error al usuario
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <View style={styles.container}>
            <FlatList 
                data={messages}
                renderItem={renderMessage}
                keyExtractor={item => item.id}
            />
            <TextInput 
                onSubmitEditing={(e) => sendMessage(e.nativeEvent.text)}
                placeholder="Escribe tu mensaje..."
            />
        </View>
    );
};

EJEMPLO PARA WEB (JavaScript vanilla):

const chatSDK = new ChatServiceSDK();

// Autenticar
chatSDK.authenticate('user_123').then(result => {
    if (result.success) {
        console.log('Autenticado en chat');
        loadChatInterface();
    }
});

// Enviar mensaje
async function sendChatMessage(message) {
    try {
        const response = await chatSDK.sendMessage(message);
        displayMessage('user', response.userMessage);
        displayMessage('assistant', response.assistantResponse, response.personalized);
    } catch (error) {
        console.error('Error:', error);
    }
}

*/
