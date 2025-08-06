// Ejemplo de implementación del Chat Service SDK
// Para React Native o React Web

import React, { useState, useEffect, useRef } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView, Alert } from 'react-native';
import ChatServiceSDK from './frontend_sdk.js';

const ChatScreen = () => {
    // Estado del chat
    const [messages, setMessages] = useState([]);
    const [inputText, setInputText] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [userContext, setUserContext] = useState(null);
    
    // Referencias
    const chatSDK = useRef(new ChatServiceSDK({
        baseUrl: 'http://192.168.0.17:8084' // Tu IP del chat service
    }));
    const scrollViewRef = useRef();

    // Inicialización
    useEffect(() => {
        initializeChat();
    }, []);

    const initializeChat = async () => {
        try {
            setIsLoading(true);
            
            // 1. Verificar salud del servicio
            const health = await chatSDK.current.checkHealth();
            console.log('Service health:', health);
            
            if (health.status !== 'healthy') {
                Alert.alert('Error', 'El servicio de chat no está disponible');
                return;
            }

            // 2. Autenticar usuario
            // En una app real, obtendrías el userId del estado de autenticación
            const userId = 'user123'; // Reemplaza con tu lógica de auth
            const authResult = await chatSDK.current.authenticate(userId);
            
            if (authResult.success) {
                setIsAuthenticated(true);
                console.log('Authentication successful');
                
                // 3. Obtener contexto del usuario
                try {
                    const context = await chatSDK.current.getUserContext();
                    setUserContext(context);
                    console.log('User context loaded:', context);
                } catch (error) {
                    console.log('User context not available:', error);
                }
                
                // 4. Cargar historial de chat
                await loadChatHistory();
                
            } else {
                Alert.alert('Error de Autenticación', authResult.error);
            }
            
        } catch (error) {
            console.error('Initialization error:', error);
            Alert.alert('Error', 'No se pudo inicializar el chat');
        } finally {
            setIsLoading(false);
        }
    };

    const loadChatHistory = async () => {
        try {
            const history = await chatSDK.current.getChatHistory(20);
            if (history.messages && history.messages.length > 0) {
                setMessages(history.messages);
                // Scroll al final después de un momento
                setTimeout(() => scrollToBottom(), 100);
            }
        } catch (error) {
            console.error('Error loading history:', error);
        }
    };

    const sendMessage = async () => {
        if (!inputText.trim() || isLoading) return;

        const messageText = inputText.trim();
        setInputText('');
        setIsLoading(true);

        // Agregar mensaje del usuario inmediatamente
        const userMessage = {
            id: Date.now(),
            type: 'user',
            text: messageText,
            timestamp: new Date().toISOString(),
            sending: true
        };
        
        setMessages(prev => [...prev, userMessage]);
        scrollToBottom();

        try {
            // Enviar mensaje al chat service
            const response = await chatSDK.current.sendMessage(messageText);
            
            // Reemplazar el mensaje temporal con la respuesta completa
            setMessages(prev => {
                const newMessages = prev.filter(msg => msg.id !== userMessage.id);
                return [
                    ...newMessages,
                    {
                        id: response.messageId,
                        type: 'user',
                        text: response.userMessage,
                        timestamp: response.timestamp
                    },
                    {
                        id: response.messageId + '_response',
                        type: 'assistant',
                        text: response.assistantResponse,
                        timestamp: response.timestamp,
                        personalized: response.personalized,
                        hasContext: response.hasContext
                    }
                ];
            });
            
            scrollToBottom();
            
        } catch (error) {
            console.error('Send message error:', error);
            
            // Marcar el mensaje como fallido
            setMessages(prev => prev.map(msg => 
                msg.id === userMessage.id 
                    ? { ...msg, error: true, sending: false }
                    : msg
            ));
            
            Alert.alert('Error', 'No se pudo enviar el mensaje');
        } finally {
            setIsLoading(false);
        }
    };

    const scrollToBottom = () => {
        if (scrollViewRef.current) {
            scrollViewRef.current.scrollToEnd({ animated: true });
        }
    };

    const renderMessage = (message, index) => {
        const isUser = message.type === 'user';
        
        return (
            <View key={message.id || index} style={{
                flexDirection: 'row',
                justifyContent: isUser ? 'flex-end' : 'flex-start',
                marginVertical: 4,
                marginHorizontal: 16
            }}>
                <View style={{
                    backgroundColor: isUser ? '#007AFF' : '#F0F0F0',
                    borderRadius: 12,
                    padding: 12,
                    maxWidth: '80%',
                    ...(message.error && { backgroundColor: '#FF3B30' }),
                    ...(message.sending && { opacity: 0.7 })
                }}>
                    <Text style={{
                        color: isUser ? 'white' : 'black',
                        fontSize: 16
                    }}>
                        {message.text}
                    </Text>
                    
                    {/* Indicadores especiales */}
                    <View style={{ flexDirection: 'row', marginTop: 4 }}>
                        {message.personalized && (
                            <Text style={{ color: '#FFD700', fontSize: 12 }}>✨ Personalizado</Text>
                        )}
                        {message.hasContext && (
                            <Text style={{ color: '#32D74B', fontSize: 12, marginLeft: 8 }}>📊 Con contexto</Text>
                        )}
                        {message.sending && (
                            <Text style={{ color: '#999', fontSize: 12 }}>⏳ Enviando...</Text>
                        )}
                        {message.error && (
                            <Text style={{ color: 'white', fontSize: 12 }}>❌ Error</Text>
                        )}
                    </View>
                    
                    {/* Timestamp */}
                    <Text style={{
                        fontSize: 11,
                        color: isUser ? 'rgba(255,255,255,0.7)' : '#666',
                        marginTop: 4
                    }}>
                        {new Date(message.timestamp).toLocaleTimeString()}
                    </Text>
                </View>
            </View>
        );
    };

    const renderContextInfo = () => {
        if (!userContext) return null;
        
        return (
            <View style={{
                backgroundColor: '#E3F2FD',
                padding: 12,
                margin: 16,
                borderRadius: 8,
                borderLeftWidth: 4,
                borderLeftColor: '#2196F3'
            }}>
                <Text style={{ fontWeight: 'bold', marginBottom: 4 }}>
                    🤖 Chat personalizado activo
                </Text>
                <Text style={{ fontSize: 12, color: '#666' }}>
                    Conectado con tu perfil y portafolio
                </Text>
            </View>
        );
    };

    if (!isAuthenticated && isLoading) {
        return (
            <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
                <Text>Conectando al chat...</Text>
            </View>
        );
    }

    if (!isAuthenticated) {
        return (
            <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20 }}>
                <Text style={{ textAlign: 'center', marginBottom: 20 }}>
                    No se pudo conectar al servicio de chat
                </Text>
                <TouchableOpacity 
                    onPress={initializeChat}
                    style={{
                        backgroundColor: '#007AFF',
                        padding: 12,
                        borderRadius: 8
                    }}
                >
                    <Text style={{ color: 'white' }}>Reintentar</Text>
                </TouchableOpacity>
            </View>
        );
    }

    return (
        <View style={{ flex: 1, backgroundColor: 'white' }}>
            {/* Header */}
            <View style={{
                backgroundColor: '#007AFF',
                padding: 16,
                paddingTop: 50
            }}>
                <Text style={{
                    color: 'white',
                    fontSize: 18,
                    fontWeight: 'bold'
                }}>
                    Chat Financiero IA
                </Text>
                <Text style={{
                    color: 'rgba(255,255,255,0.8)',
                    fontSize: 14
                }}>
                    {userContext ? 'Personalizado' : 'Modo general'}
                </Text>
            </View>

            {/* Context Info */}
            {renderContextInfo()}

            {/* Messages */}
            <ScrollView
                ref={scrollViewRef}
                style={{ flex: 1 }}
                showsVerticalScrollIndicator={false}
            >
                {messages.length === 0 ? (
                    <View style={{ padding: 20, alignItems: 'center' }}>
                        <Text style={{ color: '#666', textAlign: 'center' }}>
                            ¡Hola! Soy tu asistente financiero IA. 
                            Puedo ayudarte con consultas sobre inversiones, 
                            análisis de mercado y tu portafolio.
                        </Text>
                    </View>
                ) : (
                    messages.map((message, index) => renderMessage(message, index))
                )}
            </ScrollView>

            {/* Input Area */}
            <View style={{
                flexDirection: 'row',
                padding: 16,
                backgroundColor: '#F8F8F8',
                alignItems: 'flex-end'
            }}>
                <TextInput
                    style={{
                        flex: 1,
                        borderWidth: 1,
                        borderColor: '#DDD',
                        borderRadius: 20,
                        paddingHorizontal: 16,
                        paddingVertical: 12,
                        backgroundColor: 'white',
                        maxHeight: 100
                    }}
                    value={inputText}
                    onChangeText={setInputText}
                    placeholder="Escribe tu consulta financiera..."
                    multiline
                    onSubmitEditing={sendMessage}
                    editable={!isLoading}
                />
                <TouchableOpacity
                    onPress={sendMessage}
                    disabled={!inputText.trim() || isLoading}
                    style={{
                        backgroundColor: (!inputText.trim() || isLoading) ? '#CCC' : '#007AFF',
                        borderRadius: 20,
                        padding: 12,
                        marginLeft: 8
                    }}
                >
                    <Text style={{ color: 'white', fontWeight: 'bold' }}>
                        {isLoading ? '⏳' : '➤'}
                    </Text>
                </TouchableOpacity>
            </View>
        </View>
    );
};

export default ChatScreen;
