"""
Servicio OpenAI simplificado para testing
"""
from typing import List, Dict, Any, Optional
from loguru import logger

from ..simple_config import get_simple_settings
from ..models.chat import OpenAIMessage, MessageRole, UserContext
from ..utils.prompts import get_system_prompt, enhance_user_message


class SimpleOpenAIService:
    """Servicio OpenAI simplificado para testing sin API key real"""
    
    def __init__(self):
        self.settings = get_simple_settings()
        self.demo_mode = self.settings.openai_api_key.startswith("sk-demo")
        
    async def generate_response(
        self, 
        messages: List[OpenAIMessage],
        user_context: Optional[UserContext] = None,
        temperature: float = 0.7
    ) -> str:
        """
        Genera respuesta usando OpenAI GPT o modo demo
        
        Args:
            messages: Lista de mensajes de la conversación
            user_context: Contexto del usuario
            temperature: Temperatura para la generación
            
        Returns:
            Respuesta generada por IA o demo
        """
        try:
            if self.demo_mode:
                return await self._generate_demo_response(messages, user_context)
            
            # Aquí iría la implementación real con OpenAI
            import openai
            
            # Preparar mensajes para OpenAI
            openai_messages = self._prepare_messages(messages, user_context)
            
            logger.info(f"Enviando {len(openai_messages)} mensajes a OpenAI")
            
            # Crear cliente OpenAI
            client = openai.AsyncOpenAI(api_key=self.settings.openai_api_key)
            
            # Llamada a OpenAI
            response = await client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[{"role": msg.role.value, "content": msg.content} for msg in openai_messages],
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
                
        except Exception as e:
            logger.error(f"Error al generar respuesta: {str(e)}")
            return await self._generate_demo_response(messages, user_context)
    
    async def _generate_demo_response(
        self, 
        messages: List[OpenAIMessage],
        user_context: Optional[UserContext] = None
    ) -> str:
        """
        Genera respuesta de demostración sin usar OpenAI
        
        Args:
            messages: Lista de mensajes
            user_context: Contexto del usuario
            
        Returns:
            Respuesta de demostración
        """
        try:
            # Obtener último mensaje del usuario
            user_message = ""
            for msg in reversed(messages):
                if msg.role == MessageRole.USER:
                    user_message = msg.content.lower()
                    break
            
            # Respuestas predefinidas basadas en palabras clave
            responses = self._get_demo_responses()
            
            # Buscar respuesta apropiada
            for keywords, response in responses.items():
                if any(keyword in user_message for keyword in keywords):
                    # Personalizar respuesta con contexto si está disponible
                    if user_context and user_context.favorite_stocks:
                        response += f"\n\n💡 Veo que tienes interés en: {', '.join(user_context.favorite_stocks[:3])}. ¿Te gustaría que analice alguna de estas acciones?"
                    
                    return response
            
            # Respuesta por defecto
            default_response = """¡Hola! 👋 Soy tu asistente financiero especializado en el mercado argentino.

🔴 **MODO DEMO** - Este es el Chat Service funcionando sin API key de OpenAI.

Puedo ayudarte con:
📈 Análisis del MERVAL y acciones argentinas
💰 Información sobre bonos y FCI
₿ Análisis de criptomonedas
📊 Indicadores macroeconómicos

Para obtener respuestas de IA reales, configura tu OPENAI_API_KEY en el archivo .env

¿En qué puedo ayudarte hoy?"""
            
            if user_context:
                default_response += f"\n\n👤 Usuario autenticado: {user_context.user_id}"
            
            return default_response
            
        except Exception as e:
            logger.error(f"Error en respuesta demo: {str(e)}")
            return "Error al generar respuesta de demostración."
    
    def _get_demo_responses(self) -> Dict[tuple, str]:
        """Obtiene respuestas de demostración"""
        return {
            ("hola", "hi", "hello", "buenos días", "buenas tardes"): """¡Hola! 👋 

Soy tu asistente financiero especializado en el mercado argentino. 

🔴 **MODO DEMO ACTIVO**

Puedo ayudarte con:
📈 Análisis del MERVAL
💰 Acciones argentinas  
₿ Criptomonedas
📊 Bonos y FCI

¿Qué te interesa analizar hoy?""",

            ("merval", "mercado", "acciones", "bolsa"): """📈 **Análisis del MERVAL - DEMO**

El MERVAL es el principal índice de la Bolsa de Buenos Aires. Actualmente incluye las acciones más líquidas del mercado argentino.

**Sectores principales:**
🏦 Bancos: GGAL, BMA, SUPV
⚡ Energía: YPF, PAM, EDN  
📱 Telecom: TECO2
🏗️ Materiales: TX, LOMA

**Factores clave a considerar:**
• Tipo de cambio oficial vs. blue
• Inflación y política monetaria
• Riesgo país 
• Contexto macroeconómico

¿Te interesa algún sector en particular?""",

            ("ypf", "pampa", "energía", "petróleo"): """⚡ **Sector Energético - DEMO**

**YPF (YPF Sociedad Anónima)**
• Principal empresa energética argentina
• Exploración, producción y refinación
• Expuesta a Vaca Muerta (shale oil)

**PAM (Pampa Energía)**  
• Generación eléctrica diversificada
• Renovables + tradicional
• Participación en petróleo

**Factores clave:**
• Precios internacionales del petróleo
• Políticas energéticas del gobierno
• Desarrollo de Vaca Muerta
• Tarifas eléctricas

⚠️ **Riesgo:** Alta volatilidad por contexto regulatorio""",

            ("bitcoin", "crypto", "btc", "ethereum", "cripto"): """₿ **Criptomonedas en Argentina - DEMO**

**Contexto argentino:**
• Cobertura contra inflación
• Alternativa al dólar
• Restricciones cambiarias (cepo)

**Principales cryptos:**
₿ Bitcoin (BTC) - Reserva de valor
⚡ Ethereum (ETH) - Contratos inteligentes  
💵 Stablecoins (USDT, USDC) - Estabilidad

**Consideraciones:**
• Regulación AFIP/UIF
• Exchanges locales vs. internacionales
• Volatilidad alta
• Aspectos impositivos

**Estrategia sugerida:** Diversificación y DCA (Dollar Cost Average)""",

            ("bonos", "al30", "riesgo país", "soberanos"): """🏛️ **Bonos Argentinos - DEMO**

**Bonos Soberanos principales:**
• AL30, AL35 (dólares)
• AE38, AE45 (euros)
• Bonos CER (ajuste inflación)

**Métricas clave:**
📊 Riesgo País: ~1000-2000 puntos básicos
💰 Rendimientos: Variables según vencimiento
⏱️ Duración: Riesgo de tasa de interés

**Factores de riesgo:**
• Historial de defaults
• Sostenibilidad fiscal
• Acuerdo con FMI
• Contexto político

⚠️ **Importante:** Alta volatilidad y riesgo crediticio""",

            ("dólar", "blue", "mep", "cambio"): """💵 **Dólar en Argentina - DEMO**

**Tipos de cambio:**
• Oficial: Controlado por BCRA
• Blue/Paralelo: Mercado informal
• MEP: Mercado de valores
• CCL: Contado con liquidación

**Brecha cambiaria:** Diferencia entre oficial y blue

**Impacto en inversiones:**
📈 Acciones: Benefician con devaluación
📉 Bonos pesos: Sufren con expectativas devaluatorias
₿ Crypto: Mayor demanda como refugio

**Recomendación:** Considerar cobertura cambiaria en portfolios""",

            ("inflación", "cer", "índices"): """📊 **Inflación Argentina - DEMO**

**Indicadores principales:**
• IPC: Índice de Precios al Consumidor
• CER: Coeficiente de Estabilización de Referencia
• UVA: Unidad de Valor Adquisitivo

**Instrumentos de cobertura:**
📈 Bonos CER/UVA
🏠 Real estate
₿ Criptomonedas
📊 Acciones (parcial)

**Estrategia anti-inflacionaria:**
• Diversificación de activos
• Instrumentos indexados
• Moneda fuerte (USD)
• Activos reales""",
        }
    
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
        Analiza el sentimiento de un texto (versión demo)
        """
        # Análisis básico de sentimiento para demo
        positive_words = ["bueno", "excelente", "positivo", "optimista", "subir", "ganar"]
        negative_words = ["malo", "pesimista", "negativo", "bajar", "perder", "preocupar"]
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            sentiment = "positive"
            confidence = min(0.8, 0.5 + (positive_count * 0.1))
        elif negative_count > positive_count:
            sentiment = "negative"
            confidence = min(0.8, 0.5 + (negative_count * 0.1))
        else:
            sentiment = "neutral"
            confidence = 0.5
        
        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "market_emotion": sentiment if sentiment != "neutral" else "cautious",
            "key_indicators": positive_words if sentiment == "positive" else negative_words if sentiment == "negative" else []
        }
    
    async def summarize_conversation(self, messages: List[OpenAIMessage]) -> str:
        """
        Genera un resumen de la conversación (versión demo)
        """
        if not messages:
            return "No hay conversación para resumir."
        
        user_messages = [msg.content for msg in messages if msg.role == MessageRole.USER]
        
        if len(user_messages) == 0:
            return "No hay mensajes del usuario para resumir."
        
        # Resumen básico para demo
        topics = []
        for msg in user_messages:
            msg_lower = msg.lower()
            if any(word in msg_lower for word in ["merval", "acciones", "bolsa"]):
                topics.append("Mercado de acciones")
            elif any(word in msg_lower for word in ["crypto", "bitcoin", "btc"]):
                topics.append("Criptomonedas")
            elif any(word in msg_lower for word in ["bonos", "riesgo país"]):
                topics.append("Bonos soberanos")
            elif any(word in msg_lower for word in ["dólar", "cambio"]):
                topics.append("Tipo de cambio")
        
        unique_topics = list(set(topics))
        
        if unique_topics:
            return f"Conversación sobre: {', '.join(unique_topics)}. Total de mensajes: {len(user_messages)}"
        else:
            return f"Conversación general sobre finanzas. Total de mensajes: {len(user_messages)}"


# Singleton instance para testing
simple_openai_service = SimpleOpenAIService()
