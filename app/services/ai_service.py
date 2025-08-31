"""
Servicio de AI y respuestas del chat
Extraído de chat_service_real.py
"""

import requests
from typing import Dict
from app.core.config import env_config

async def get_user_info(user_id: str, auth_header: str = None) -> Dict[str, str]:
    """Obtener información del usuario desde el backend"""
    try:
        # Obtener backend URL desde configuración
        backend_url = env_config.get('BACKEND_URL', 'http://localhost:8080')
        
        if auth_header and auth_header.startswith('Bearer '):
            # Intentar obtener info del usuario desde el backend
            headers = {'Authorization': auth_header}
            response = requests.get(f"{backend_url}/api/auth/profile", headers=headers, timeout=5)
            
            if response.status_code == 200:
                user_data = response.json()
                return {
                    'name': user_data.get('data', {}).get('user', {}).get('name', 'Usuario'),
                    'email': user_data.get('data', {}).get('user', {}).get('email', '')
                }
        
        # Fallback genérico - usar ID abreviado como nombre
        return {'name': f'Usuario {user_id[:8]}', 'email': ''}
        
    except Exception as e:
        print(f"Error obteniendo info del usuario: {e}")
        # Fallback genérico en caso de error
        return {'name': f'Usuario {user_id[:8]}', 'email': ''}

async def generate_ai_response(message: str, user_id: str, user_name: str) -> str:
    """Generar respuesta del asistente financiero AI con usuario validado"""
    message_lower = message.lower()
    
    responses = {
        "merval": """📈 **MERVAL - Análisis en Tiempo Real**
        
🔹 **Situación actual**: El índice está en 1.245.789 puntos (+0.8%)
🔹 **Volumen**: $2.1M ARS en operaciones
🔹 **Líderes**: YPF (+2.1%), Galicia (+1.5%), Pampa Energía (+3.2%)
🔹 **Rezagados**: Telecom (-1.2%), Aluar (-0.8%)

💡 **Análisis**: El mercado muestra optimismo moderado. Considera diversificar en energía y bancos, pero mantente atento a la volatilidad del dólar.
        
⚠️ *No es asesoramiento financiero profesional*""",

        "ypf": """🛢️ **YPF - Análisis Detallado**
        
📊 **Datos técnicos**:
• Precio actual: $4.150 ARS (+1.8%)
• Volumen: 580k acciones
• Resistencia: $4.300 | Soporte: $3.950

⚡ **Catalizadores clave**:
• Precio del Brent: $82/barril
• Producción Vaca Muerta: +15% YoY  
• Plan de inversiones 2024: U$S 3.8B

💭 **Outlook**: Fundamentales sólidos, dependiente del precio internacional del crudo. Horizonte recomendado: 6-12 meses.

⚠️ *Análisis basado en información pública*""",

        "dolar": """💵 **Dólares en Argentina - Panorama Actual**
        
💹 **Cotizaciones estimadas**:
• Oficial: $365 ARS
• Blue: $485 ARS (brecha: 33%)
• MEP: $422 ARS  
• CCL: $428 ARS

📊 **Para inversores**:
• **MEP**: Ideal para comprar acciones en USD
• **CCL**: Para transferir al exterior
• **Blue**: Ahorro en efectivo

⚠️ **Importante**: Verificá cotizaciones en tiempo real. La brecha indica presión cambiaria.""",

        "bitcoin": """₿ **Bitcoin en Argentina - Contexto Local**
        
💎 **Situación actual**:
• Precio global: ~$43,500 USD
• Premium argentino: +1.6%
• Volumen P2P: $12M USD diarios

🔄 **Casos de uso locales**:
• Refugio ante inflación (84% anual)
• Transferencias internacionales
• Trading vs. dólar blue

⚡ **Plataformas**: Ripio, SatoshiTango, Buenbit, Binance P2P

⚠️ *Invertí solo lo que podés permitirte perder*""",

        "bonos": """🏛️ **Bonos Soberanos Argentinos**
        
📊 **Principales instrumentos**:
• AL30 (2030 USD): TIR ~15.2%
• GD30 (2030 USD): TIR ~15.8%
• AE38 (2038 USD): TIR ~16.5%

💡 **Contexto**:
• Riesgo país: ~1,850 puntos
• Restructuración 2020: cumpliendo pagos
• Próximo vencimiento: diciembre 2024

⚠️ **Perfil**: Solo para inversores con tolerancia al riesgo soberano alto.""",

        "cedears": """🌎 **CEDEARs - Acciones Globales en Pesos**
        
🚀 **Top performers**:
• AAPL (Apple): $45,500 ARS (+2.3%)
• MSFT (Microsoft): $38,200 ARS (+1.8%)
• NVDA (Nvidia): $142,800 ARS (+5.2%)
• KO (Coca-Cola): $18,900 ARS (+0.9%)

💡 **Ventajas**:
✅ Exposición al mercado global en pesos
✅ Dividendos en dólares (convertidos)
✅ Liquidez inmediata en horario local

⚡ **Estrategia**: Ideal para diversificar fuera de Argentina sin cambiar divisas.

⚠️ *Precios ilustrativos - verificar cotizaciones reales*""",

        "crypto": """🔄 **Criptomonedas - Ecosistema Argentino**
        
💰 **Top cryptos locales**:
• Bitcoin (BTC): $43,500 USD
• Ethereum (ETH): $2,680 USD  
• USDT: $1.02 USD (premium 2%)
• DAI: $1.01 USD

🏦 **Exchanges locales**:
• Ripio: Más regulado, spreads menores
• SatoshiTango: Mayor volumen BTC
• Buenbit: DeFi y staking
• Binance P2P: Mejores precios

💡 **Casos de uso**:
🔸 Ahorro en moneda dura
🔸 Pagos internacionales
🔸 Trading especulativo
🔸 DeFi y yield farming

⚠️ *Extrema volatilidad - riesgo total de pérdida*""",

        "plazo_fijo": """🏦 **Plazos Fijos - Análisis de Rendimiento**
        
📊 **Tasas actuales** (30 días):
• Banco Nación: 75% TNA
• Banco Galicia: 78% TNA  
• Banco Macro: 79% TNA
• Brubank: 82% TNA

💭 **Rendimiento real**:
• Inflación estimada: 84% anual
• **Resultado**: Pérdida real del 5-9%

🔄 **Alternativas**:
• UVA: Ajuste por inflación + spread
• Fondos Money Market: Mayor flexibilidad
• Bonos CER: Protección inflacionaria

⚠️ *El plazo fijo tradicional no protege del poder adquisitivo*""",

        "inflacion": """📈 **Inflación Argentina - Impacto Financiero**
        
🔥 **Datos actuales**:
• Mensual: 7.4% (estimado)
• Anual: 84.2%
• Core: 6.8% mensual
• Alimentos: 8.1% mensual

💸 **Efecto en inversiones**:
• Plazo fijo: Pierde 5-9% real
• UVA: Empata inflación + spread
• Acciones: Históricamente ganan a inflación
• USD: Protección tradicional

📊 **Sectores ganadores**:
🔸 Utilities (servicios públicos)
🔸 Bancos (benefician de alta tasa)
🔸 Consumo esencial
🔸 Exportadoras (agro, minería)

⚠️ *Datos estimados - verificar fuentes oficiales*""",

        "fci": """📊 **Fondos Comunes de Inversión**
        
🏆 **Categorías principales**:
• **Money Market**: 78-85% TNA (liquidez diaria)
• **Renta Fija**: 65-75% TNA (bonos CER)
• **Renta Variable**: Tracking MERVAL ±15%
• **Balanceados**: 40% acciones, 60% bonos

💡 **Recomendados por perfil**:
• **Conservador**: FCI Money Market + UVA
• **Moderado**: 70% Money Market + 30% Acciones
• **Agresivo**: 60% Acciones + 40% Bonos USD

🔍 **Métricas clave**:
• TIR histórica vs. inflación
• Volatilidad (desvío estándar)
• Máxima pérdida (drawdown)

⚠️ *Rentabilidad pasada no garantiza futura*""",

        "uva": """💰 **UVA - Inversiones Ajustadas por Inflación**
        
📊 **Instrumentos UVA disponibles**:
• Plazo Fijo UVA: Inflación + 1-4% spread
• Bonos TX24/TX26: TIR real ~4-6%
• FCI UVA: Diversificación + liquidez
• Préstamos UVA: Hipotecarios y personales

⚡ **Mecánica**:
• Capital se ajusta por CER (inflación)
• Interés se cobra sobre capital ajustado
• **Resultado**: Preservación poder adquisitivo

💭 **Pros vs. Contras**:
✅ Protección real contra inflación
✅ Menor riesgo que acciones
❌ Rendimiento real modesto (1-4%)
❌ Iliquidez en algunos instrumentos

⚠️ *Ideal para objetivos de mediano/largo plazo*""",

        "bancos": """🏦 **Sector Bancario - Análisis Sectorial**
        
📊 **Principales bancos (MERVAL)**:
• Banco Galicia (GGAL): $520 (+1.2%)
• Grupo Financiero Valores (BVLS): $340 (+2.1%)  
• Banco Macro (BMA): $1,850 (+0.8%)
• Banco Supervielle (SUPV): $280 (-0.5%)

⚡ **Catalizadores positivos**:
🔸 Spreads altos por inflación
🔸 Expansión del crédito
🔸 Digitalización acelerada
🔸 Normalización monetaria gradual

⚠️ **Riesgos**:
🔸 Regulación estricta del BCRA
🔸 Presión sobre márgenes
🔸 Morosidad en alza
🔸 Contexto macroeconómico

💡 **Outlook**: Beneficiarios del carry trade local, pero sensibles a estabilidad macro.

⚠️ *Análisis basado en información pública*""",

        "commodities": """🌾 **Commodities - Argentina Exportadora**
        
📊 **Precios internacionales**:
• Soja: $485/tn (+1.8% sem)
• Trigo: $220/tn (-0.5% sem)
• Maíz: $195/tn (+2.1% sem)
• Carne: $4,200/tn (+0.8% sem)

🇦🇷 **Impacto local**:
• 60% de exportaciones son agropecuarias
• Generación de divisas crítica
• Efecto en tipo de cambio
• Recaudación por retenciones

📈 **Empresas expuestas**:
• Cresud (CRES): Agricultura y ganadería
• Grupo Los Grobo: Trading agrícola
• Molinos Río de la Plata (MOLI)
• SanCor: Lácteos y derivados

🌦️ **Factores clave**:
• Clima y precipitaciones
• Demanda china e india
• Políticas de retenciones
• Logística y transporte

⚠️ *Sector altamente cíclico y climático*"""
    }
    
    # Lógica expandida de detección de temas financieros
    if any(word in message_lower for word in ["merval", "mercado", "índice", "bolsa"]):
        return responses["merval"]
    elif any(word in message_lower for word in ["ypf", "petróleo", "energía", "oil", "vaca muerta"]):
        return responses["ypf"]
    elif any(word in message_lower for word in ["dólar", "blue", "mep", "ccl", "divisa", "cambio"]):
        return responses["dolar"]
    elif any(word in message_lower for word in ["bitcoin", "crypto", "btc", "ethereum", "eth", "criptomoneda"]):
        return responses["bitcoin"]
    elif any(word in message_lower for word in ["bonos", "al30", "gd30", "ae38", "soberano", "riesgo país"]):
        return responses["bonos"]
    elif any(word in message_lower for word in ["cedears", "cedear", "apple", "microsoft", "nvidia", "aapl", "msft", "acciones extranjeras"]):
        return responses["cedears"]
    elif any(word in message_lower for word in ["crypto", "criptomonedas", "ripio", "satoshitango", "buenbit", "binance"]):
        return responses["crypto"]
    elif any(word in message_lower for word in ["plazo fijo", "pf", "banco", "tasa", "depósito"]):
        return responses["plazo_fijo"]
    elif any(word in message_lower for word in ["inflación", "inflacion", "ipc", "precios", "carestía"]):
        return responses["inflacion"]
    elif any(word in message_lower for word in ["fci", "fondo", "fondos", "money market", "balanceado"]):
        return responses["fci"]
    elif any(word in message_lower for word in ["uva", "cer", "ajuste", "unidad de valor", "inflacionario"]):
        return responses["uva"]
    elif any(word in message_lower for word in ["bancos", "galicia", "macro", "supervielle", "ggal", "bma", "supv"]):
        return responses["bancos"]
    elif any(word in message_lower for word in ["commodities", "soja", "trigo", "maíz", "carne", "agro", "campo"]):
        return responses["commodities"]
    
    # Mensajes de ayuda contextuales para preguntas no reconocidas
    elif any(word in message_lower for word in ["ayuda", "help", "qué puedes hacer", "que puedes hacer", "opciones"]):
        return f"""🤖 **¡Hola {user_name}! Te ayudo con temas financieros argentinos**

🎯 **Mis especialidades principales**:

📈 **MERCADOS Y ACCIONES**:
• Escribe: "MERVAL", "bolsa", "mercado"
• Escribe: "YPF", "energía", "petróleo"
• Escribe: "bancos", "Galicia", "Macro"

💰 **INVERSIONES**:
• Escribe: "plazo fijo", "UVA", "bonos"
• Escribe: "FCIs", "fondos", "money market"
• Escribe: "CEDEARs", "Apple", "acciones extranjeras"

💵 **DIVISAS Y CRYPTO**:
• Escribe: "dólar blue", "MEP", "CCL"
• Escribe: "Bitcoin", "crypto", "Ethereum"

� **ANÁLISIS ECONÓMICO**:
• Escribe: "inflación", "precios"
• Escribe: "commodities", "soja", "agro"

💡 **Ejemplos de preguntas**:
• "¿Cómo está el MERVAL hoy?"
• "¿Conviene plazo fijo o UVA?"
• "¿Qué son los CEDEARs?"
• "Análisis de YPF"

**¡Simplemente escribe el tema que te interesa!**"""

    elif any(word in message_lower for word in ["hola", "buenas", "buenos días", "buenas tardes", "hi", "hello"]):
        return f"""¡Hola {user_name}! 👋 

Soy tu **asistente financiero especializado en el mercado argentino**.

🚀 **¿Por dónde empezamos?**

Podés preguntarme sobre:
• 📈 **Mercados**: "MERVAL", "YPF", "bancos"
• 💰 **Inversiones**: "plazo fijo", "UVA", "FCIs"
• 💵 **Divisas**: "dólar blue", "MEP"
• ₿ **Crypto**: "Bitcoin", "Ethereum"
• 📊 **Economía**: "inflación", "commodities"

**Escribe cualquier tema financiero que te interese, por ejemplo:**
• "¿Cómo está el dólar?"
• "Análisis de YPF" 
• "¿Qué son los CEDEARs?"

**¡Estoy aquí para ayudarte con tus consultas financieras!**"""

    elif any(word in message_lower for word in ["no entiendo", "no comprendo", "confuso", "explicar", "no sé", "no se"]):
        return f"""😊 **¡No te preocupes {user_name}!** Te explico mejor.

🎯 **Soy un asistente financiero argentino**. Mi trabajo es darte información sobre:

� **TEMAS PRINCIPALES**:
1. **Mercado de valores** (MERVAL, acciones argentinas)
2. **Divisas** (dólar blue, MEP, CCL)
3. **Inversiones** (plazo fijo, UVA, bonos, FCIs)
4. **Criptomonedas** (Bitcoin, exchanges argentinos)
5. **Economía argentina** (inflación, commodities)

💡 **¿Cómo usarme?**
• Escribí palabras clave como: "dólar", "MERVAL", "YPF"
• Hacé preguntas específicas: "¿Conviene plazo fijo?"
• Pedí análisis: "Análisis del sector bancario"

� **Ejemplos súper fáciles**:
• Escribí "dólar" → Te doy cotizaciones
• Escribí "YPF" → Te doy análisis de la acción
• Escribí "inflación" → Te explico el impacto

**¿Hay algún tema financiero específico que te interese?**"""

    elif any(word in message_lower for word in ["gracias", "thank you", "thanks", "perfecto", "excelente", "muy bien"]):
        return f"""¡De nada {user_name}! 😊

Me alegra haberte ayudado con información financiera.

🔄 **¿Querés consultar algo más?**

Recordá que podés preguntarme sobre:
• 📈 Mercados y acciones
• 💰 Inversiones y ahorros  
• 💵 Tipos de cambio
• ₿ Criptomonedas
• 📊 Análisis económico

**¡Estoy aquí cuando necesites información financiera actualizada!**"""

    elif any(word in message_lower for word in ["inversión", "inversion", "invertir", "dónde invertir", "donde invertir", "qué comprar"]):
        return f"""💰 **Guía de Inversiones Argentina - {user_name}**

🎯 **Por perfil de riesgo**:

🛡️ **CONSERVADOR** (preservar capital):
• Plazo fijo UVA: Inflación + 1-4%
• FCIs Money Market: 78-85% TNA
• Bonos CER: Protección inflacionaria

⚖️ **MODERADO** (balance riesgo/retorno):
• 60% FCIs + 40% acciones MERVAL
• CEDEARs diversificados (Apple, Microsoft)
• Bonos soberanos (AL30, GD30)

🚀 **AGRESIVO** (buscar rentabilidad):
• Acciones MERVAL (YPF, bancos)
• CEDEARs tecnológicos (Nvidia, Tesla)
• Crypto (Bitcoin, Ethereum)

💡 **Para empezar, contame**:
• ¿Cuánto podés invertir?
• ¿Sos conservador o arriesgado?
• ¿Necesitás la plata pronto?

**Escribe "plazo fijo", "acciones" o "crypto" para profundizar en cada tema.**"""

    elif len(message_lower) < 3:
        return f"""🤔 **Mensaje muy corto, {user_name}**

Para ayudarte mejor, escribí palabras clave o preguntas sobre:

📈 **Mercados**: "MERVAL", "YPF", "acciones"
💰 **Inversiones**: "plazo fijo", "UVA", "bonos"  
💵 **Divisas**: "dólar", "euro", "bitcoin"
📊 **Economía**: "inflación", "riesgo país"

**Ejemplos**:
• "¿Cómo está el dólar?"
• "Análisis de YPF"
• "¿Conviene plazo fijo?"

**¡Escribí tu consulta financiera!**"""

    else:
        return f"""❓ **No reconocí tu consulta, {user_name}**

🔍 **¿Tal vez quisiste preguntar sobre?**:

📈 **Si te interesa el mercado**:
• Escribe: "MERVAL", "bolsa", "acciones"
• Escribe: "YPF", "Galicia", "bancos"

💰 **Si querés invertir**:
• Escribe: "plazo fijo", "UVA", "bonos"
• Escribe: "FCIs", "CEDEARs"

💵 **Si necesitás divisas**:
• Escribe: "dólar blue", "MEP", "bitcoin"

📊 **Si te interesa la economía**:
• Escribe: "inflación", "commodities", "riesgo país"

💡 **También podés escribir**:
• "ayuda" → Para ver todas mis funciones
• "inversión" → Para guía de inversiones
• Una pregunta específica como "¿Conviene comprar dólares?"

**¿Cuál de estos temas te interesa?**"""
