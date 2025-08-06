"""
Servicio de integración con OpenAI
"""
import asyncio
from typing import List, Dict, Any, Optional
import openai
from loguru import logger

from ..config import get_settings
from ..models.chat import OpenAIMessage, MessageRole, UserContext
from ..utils.prompts import get_system_prompt, enhance_user_message


class OpenAIService:
    """Servicio para interactuar con OpenAI"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = openai.AsyncOpenAI(
            api_key=self.settings.openai_api_key
        )
        
    async def generate_response(
        self, 
        messages: List[OpenAIMessage],
        user_context: Optional[UserContext] = None,
        temperature: float = 0.7
    ) -> str:
        """
        Genera respuesta usando OpenAI GPT
        
        Args:
            messages: Lista de mensajes de la conversación
            user_context: Contexto del usuario
            temperature: Temperatura para la generación
            
        Returns:
            Respuesta generada por IA
        """
        try:
            # Preparar mensajes para OpenAI
            openai_messages = self._prepare_messages(messages, user_context)
            
            logger.info(f"Enviando {len(openai_messages)} mensajes a OpenAI")
            
            # Llamada a OpenAI
            response = await self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[msg.dict() for msg in openai_messages],
                max_tokens=self.settings.openai_max_tokens,
                temperature=temperature,
                stream=False
            )
            
            # Extraer respuesta
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                logger.info("Respuesta generada exitosamente")
                return content.strip()
            else:
                logger.error("No se recibió respuesta de OpenAI")
                return "Lo siento, no pude generar una respuesta. Por favor, intenta nuevamente."
                
        except openai.RateLimitError:
            logger.error("Rate limit alcanzado en OpenAI")
            return "El servicio está temporalmente ocupado. Por favor, intenta en unos momentos."
            
        except openai.AuthenticationError:
            logger.error("Error de autenticación con OpenAI")
            return "Error de configuración del servicio. Contacta al soporte técnico."
            
        except Exception as e:
            logger.error(f"Error al generar respuesta: {str(e)}")
            return "Ocurrió un error inesperado. Por favor, intenta nuevamente."
    
    def _prepare_messages(
        self, 
        messages: List[OpenAIMessage],
        user_context: Optional[UserContext] = None
    ) -> List[OpenAIMessage]:
        """
        Prepara los mensajes para enviar a OpenAI
        
        Args:
            messages: Mensajes de la conversación
            user_context: Contexto del usuario
            
        Returns:
            Lista de mensajes preparados
        """
        prepared_messages = []
        
        # Agregar system prompt
        system_prompt = get_system_prompt(user_context)
        prepared_messages.append(OpenAIMessage(
            role=MessageRole.SYSTEM,
            content=system_prompt
        ))
        
        # Limitar contexto a los últimos N mensajes
        max_messages = self.settings.max_context_messages
        recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages
        
        # Procesar mensajes del usuario
        for msg in recent_messages:
            if msg.role == MessageRole.USER:
                # Mejorar mensaje del usuario con contexto
                enhanced_content = enhance_user_message(msg.content, user_context)
                prepared_messages.append(OpenAIMessage(
                    role=msg.role,
                    content=enhanced_content
                ))
            else:
                prepared_messages.append(msg)
        
        return prepared_messages
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analiza el sentimiento de un texto
        
        Args:
            text: Texto a analizar
            
        Returns:
            Análisis de sentimiento
        """
        try:
            prompt = f"""
            Analiza el sentimiento del siguiente texto relacionado con finanzas e inversiones.
            Devuelve una respuesta en formato JSON con:
            - sentiment: "positive", "negative", "neutral"
            - confidence: número entre 0 y 1
            - market_emotion: "optimistic", "pessimistic", "cautious", "neutral"
            - key_indicators: lista de palabras clave que indican el sentimiento
            
            Texto: {text}
            """
            
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3
            )
            
            if response.choices:
                import json
                result = json.loads(response.choices[0].message.content)
                return result
            else:
                return {
                    "sentiment": "neutral",
                    "confidence": 0.5,
                    "market_emotion": "neutral",
                    "key_indicators": []
                }
                
        except Exception as e:
            logger.error(f"Error en análisis de sentimiento: {str(e)}")
            return {
                "sentiment": "neutral",
                "confidence": 0.5,
                "market_emotion": "neutral",
                "key_indicators": []
            }
    
    async def summarize_conversation(self, messages: List[OpenAIMessage]) -> str:
        """
        Genera un resumen de la conversación
        
        Args:
            messages: Mensajes de la conversación
            
        Returns:
            Resumen de la conversación
        """
        try:
            conversation_text = "\n".join([
                f"{msg.role}: {msg.content}" for msg in messages 
                if msg.role != MessageRole.SYSTEM
            ])
            
            prompt = f"""
            Resume la siguiente conversación sobre finanzas en máximo 3 puntos clave:
            
            {conversation_text}
            
            Resumen:
            """
            
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.5
            )
            
            if response.choices:
                return response.choices[0].message.content.strip()
            else:
                return "No se pudo generar un resumen de la conversación."
                
        except Exception as e:
            logger.error(f"Error al resumir conversación: {str(e)}")
            return "Error al generar resumen."


# Singleton instance
openai_service = OpenAIService()
