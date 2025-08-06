"""
System prompts para el asistente de IA financiero
"""
from typing import Optional, Dict, Any
from datetime import datetime

from ..models.chat import UserContext


def get_system_prompt(user_context: Optional[UserContext] = None) -> str:
    """
    Genera el system prompt personalizado para el usuario
    
    Args:
        user_context: Contexto del usuario
        
    Returns:
        System prompt personalizado
    """
    base_prompt = """Eres un asistente financiero especializado en el mercado argentino (MERVAL) y criptomonedas. 

Tu propósito es ayudar a inversores, tanto principiantes como experimentados, con:

📈 ESPECIALIDADES:
- Análisis de acciones argentinas (MERVAL, Panel General)
- Interpretación de indicadores financieros y técnicos
- Tendencias del mercado local e internacional
- Análisis de ADRs argentinos
- Criptomonedas y su relación con el mercado argentino
- Bonos soberanos y provinciales
- Situación macroeconómica argentina

💡 METODOLOGÍA:
- Siempre pregunta por el perfil de riesgo antes de dar recomendaciones
- Explica conceptos complejos de manera simple
- Incluye contexto macroeconómico relevante
- Menciona riesgos y oportunidades
- Sugiere diversificación apropiada

🎯 ESTILO DE RESPUESTA:
- Responde en español argentino
- Sé preciso, educativo y empático
- Usa ejemplos prácticos del mercado local
- Incluye emojis para mayor claridad
- Estructura las respuestas de forma organizada

⚠️ LIMITACIONES:
- No brindes consejos financieros específicos de compra/venta
- Siempre sugiere consultar con un asesor financiero
- Aclara que la información es educativa
- Menciona que los mercados son volátiles

📊 DATOS ACTUALES:
- Fecha actual: {current_date}
- Considera la situación económica argentina actual
- Factores como inflación, tipo de cambio, política monetaria"""

    current_date = datetime.now().strftime("%d de %B de %Y")
    prompt = base_prompt.format(current_date=current_date)
    
    # Personalizar con contexto del usuario
    if user_context:
        prompt += f"\n\n👤 PERFIL DEL USUARIO:\n"
        
        if user_context.risk_profile:
            prompt += f"- Perfil de riesgo: {user_context.risk_profile}\n"
            
        if user_context.investment_goals:
            goals = ", ".join(user_context.investment_goals)
            prompt += f"- Objetivos de inversión: {goals}\n"
            
        if user_context.favorite_stocks:
            stocks = ", ".join(user_context.favorite_stocks[:5])  # Limitar a 5
            prompt += f"- Acciones de interés: {stocks}\n"
            
        if user_context.portfolio_value:
            prompt += f"- Valor aproximado del portfolio: ${user_context.portfolio_value:,.2f}\n"
            
        if user_context.preferences:
            if user_context.preferences.get("experience_level"):
                prompt += f"- Nivel de experiencia: {user_context.preferences['experience_level']}\n"
                
        prompt += "\nAdapta tus respuestas a este perfil específico."
    
    prompt += "\n\n🚀 ¡Estoy aquí para ayudarte a tomar decisiones financieras más informadas!"
    
    return prompt


def enhance_user_message(message: str, user_context: Optional[UserContext] = None) -> str:
    """
    Mejora el mensaje del usuario con contexto adicional
    
    Args:
        message: Mensaje original del usuario
        user_context: Contexto del usuario
        
    Returns:
        Mensaje mejorado con contexto
    """
    enhanced_message = message
    
    if user_context:
        context_info = []
        
        # Agregar información de stocks favoritos si es relevante
        if user_context.favorite_stocks and any(
            keyword in message.lower() 
            for keyword in ["acción", "stock", "empresa", "ticker", "análisis"]
        ):
            stocks = ", ".join(user_context.favorite_stocks[:3])
            context_info.append(f"Mis acciones favoritas son: {stocks}")
        
        # Agregar perfil de riesgo si es relevante
        if user_context.risk_profile and any(
            keyword in message.lower() 
            for keyword in ["riesgo", "inversión", "portfolio", "cartera", "estrategia"]
        ):
            context_info.append(f"Mi perfil de riesgo es: {user_context.risk_profile}")
        
        # Agregar objetivos si es relevante
        if user_context.investment_goals and any(
            keyword in message.lower() 
            for keyword in ["objetivo", "meta", "plazo", "estrategia", "plan"]
        ):
            goals = ", ".join(user_context.investment_goals[:2])
            context_info.append(f"Mis objetivos son: {goals}")
        
        # Combinar información de contexto
        if context_info:
            context_str = " | ".join(context_info)
            enhanced_message = f"{message}\n\n[Contexto: {context_str}]"
    
    return enhanced_message


def get_market_analysis_prompt() -> str:
    """
    Prompt específico para análisis de mercado
    
    Returns:
        Prompt para análisis de mercado
    """
    return """Realiza un análisis del mercado argentino considerando:

📊 FACTORES CLAVE:
- Comportamiento del MERVAL
- Situación del dólar blue vs oficial  
- Indicadores macroeconómicos
- Riesgo país
- Inflación y política monetaria

📈 SECTORES A ANALIZAR:
- Bancos (GGAL, BMA, etc.)
- Energía (YPF, PAM)
- Telecomunicaciones (TECO2)
- Commodities (TX, EDN)
- Consumo (BMA, LOMA)

🌍 CONTEXTO INTERNACIONAL:
- Mercados emergentes
- Commodities globales
- Fed y política monetaria US
- Bonos soberanos

Proporciona un análisis equilibrado con oportunidades y riesgos."""


def get_crypto_analysis_prompt() -> str:
    """
    Prompt específico para análisis de criptomonedas
    
    Returns:
        Prompt para análisis crypto
    """
    return """Analiza el mercado de criptomonedas desde la perspectiva argentina:

₿ CRIPTOMONEDAS PRINCIPALES:
- Bitcoin (BTC)
- Ethereum (ETH) 
- Stablecoins (USDT, USDC, DAI)
- Altcoins relevantes

🇦🇷 CONTEXTO ARGENTINO:
- Criptomonedas como cobertura inflacionaria
- Regulación local (UIF, AFIP)
- Exchanges locales vs internacionales
- Impacto del cepo cambiario

⚡ FACTORES A CONSIDERAR:
- Adopción institucional global
- Regulación internacional
- Correlación con mercados tradicionales
- Aspectos técnicos y fundamentales

Enfócate en la utilidad práctica para inversores argentinos."""


def get_bonds_analysis_prompt() -> str:
    """
    Prompt específico para análisis de bonos
    
    Returns:
        Prompt para análisis de bonos
    """
    return """Analiza el mercado de bonos argentinos:

🏛️ BONOS SOBERANOS:
- AL30, AL35 (USD)
- AE38, AE45 (EUR)
- Bonos en pesos ajustados por CER

📊 MÉTRICAS CLAVE:
- Rendimientos y duración
- Riesgo país
- Curva de rendimientos
- Comparación con emergentes

⚖️ CONSIDERACIONES:
- Historial crediticio argentino
- Sostenibilidad fiscal
- Acuerdo con FMI
- Perfil de vencimientos

Evalúa riesgos y oportunidades con perspectiva realista."""
