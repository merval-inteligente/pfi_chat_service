"""
Demo de OpenAI Real - Simulación de Modo Producción
Este script simula cómo funcionaría el servicio con OpenAI real configurado
"""

import asyncio
import os
from datetime import datetime
from typing import List, Dict

# Mock de OpenAI para demostración
class MockOpenAIResponse:
    def __init__(self, message, tokens):
        self.choices = [MockChoice(message)]
        self.usage = MockUsage(tokens)

class MockChoice:
    def __init__(self, message):
        self.message = MockMessage(message)

class MockMessage:
    def __init__(self, content):
        self.content = content

class MockUsage:
    def __init__(self, total_tokens):
        self.prompt_tokens = total_tokens // 2
        self.completion_tokens = total_tokens // 2
        self.total_tokens = total_tokens

class MockOpenAIClient:
    def __init__(self):
        self.chat = MockChat()

class MockChat:
    def __init__(self):
        self.completions = MockCompletions()

class MockCompletions:
    async def create(self, **kwargs):
        # Simular respuesta de GPT-4 especializada en finanzas argentinas
        user_message = kwargs.get('messages', [])[-1]['content'].lower()
        
        responses = {
            "merval": """📈 **MERVAL - Análisis en Tiempo Real**

**Situación Actual (Agosto 2025):**
• **GGAL** (Grupo Galicia): $2,850 (+2.1%) - Beneficiado por tasas altas
• **YPF**: $3,200 (-0.8%) - Presión por precio del petróleo WTI
• **BMA** (Banco Macro): $1,980 (+1.5%) - Expansión en créditos comerciales
• **SUPV** (Supervielle): $850 (+3.2%) - Recuperación post-restructuración
• **TECO2** (Telecom): $1,450 (-0.3%) - Competencia en telefonía móvil

**Contexto Macro:**
🔹 Inflación interanual: ~85% (desaceleración gradual)
🔹 Dólar oficial: $850 | Blue: $1,020
🔹 Riesgo país: 1,450 puntos básicos

**Sectores destacados:**
🏦 **Bancos**: Beneficiados por carry trade en pesos
⚡ **Energía**: Volatilidad por precios internacionales
🏗️ **Construcción**: Recuperación lenta pero sostenida

*Recordá: Siempre diversificá y considerá tu perfil de riesgo. No es asesoramiento financiero profesional.*""",

            "bitcoin": """₿ **Bitcoin en Argentina - Análisis Contextual**

**Situación Actual (Agosto 2025):**
• **Precio BTC**: ~$42,000 USD
• **En pesos argentinos**: ~$36M (aprox)
• **Gap vs. dólar blue**: BTC como refugio anti-inflación

**Contexto Argentino Específico:**
🔹 **Regulación AFIP**: Declaración obligatoria de tenencias crypto
🔹 **Exchanges locales**: SatoshiTango, Ripio, Belo siguen operativos
🔹 **Adopción**: Creciente uso como reserva de valor vs. inflación

**Ventajas en Argentina:**
✅ Cobertura contra devaluación del peso
✅ Alternativa al dólar blue (más líquida)
✅ Protección contra controles cambiarios
✅ Diversificación geográfica de activos

**Riesgos a considerar:**
⚠️ Alta volatilidad (±30% mensual posible)
⚠️ Aspectos regulatorios cambiantes
⚠️ Complejidad técnica para usuarios nuevos
⚠️ Riesgo de exchanges (not your keys, not your coins)

**Estrategia sugerida:**
• Máximo 5-10% del portfolio total
• Dollar-cost averaging (compras periódicas)
• Wallet propia para montos importantes
• Diversificar entre BTC y otras crypto

*No es asesoramiento financiero. Invertí solo lo que podés permitirte perder.*""",

            "ypf": """⚡ **YPF - Análisis Detallado (Agosto 2025)**

**Datos Fundamentales:**
• **Precio actual**: $3,200 por acción
• **Market Cap**: ~$1.26 billones
• **P/E Ratio**: 8.5x (relativamente atractivo)
• **Dividend Yield**: 4.2%

**Factores Clave:**
🔹 **Vaca Muerta**: Reservas de shale oil/gas de clase mundial
🔹 **Integración vertical**: Refinación + retail + exploración
🔹 **Posición dominante**: ~40% del mercado local

**Análisis Técnico:**
📊 **Resistencia**: $3,400-3,500
📊 **Soporte**: $2,800-2,900
📊 **Tendencia**: Lateral con sesgo bajista

**Catalizadores Positivos:**
✅ Aumento de precios del petróleo (+$70 WTI)
✅ Mayor producción en Vaca Muerta
✅ Posible reducción de retenciones por gobierno
✅ Acuerdos de exportación de GNL

**Riesgos:**
⚠️ **Regulación gubernamental**: Historial de intervención estatal
⚠️ **Precios commodities**: Dependencia del WTI y Henry Hub
⚠️ **Inversión requerida**: CAPEX alto para desarrollar Vaca Muerta
⚠️ **Contexto macro**: Recesión puede afectar demanda local

**Recomendación:**
• **Target price**: $3,600 (12 meses)
• **Peso en portfolio**: Máximo 3-5%
• **Perfil**: Inversor con tolerancia a volatilidad alta

*Análisis basado en información pública. No constituye asesoramiento financiero.*""",

            "bonos": """🏛️ **Bonos Argentinos - Panorama Actualizado**

**Principales Instrumentos (Agosto 2025):**

**BONOS EN USD:**
• **AL30**: Precio ~$32 (TIR: ~18%) - Vence 2030
• **AL35**: Precio ~$28 (TIR: ~19.5%) - Vence 2035
• **GD30**: Precio ~$35 (TIR: ~17%) - Ley extranjera

**BONOS EN PESOS:**
• **T2X5**: CER + 4.5% - Ajuste por inflación
• **TX26**: Tasa fija ~75% anual
• **DICP**: Dólar linked, alta volatilidad

**Contexto Macro:**
🔹 **Riesgo país**: 1,450 puntos básicos (alto pero estable)
🔹 **Historial**: Default 2001, 2014, 2020 (restructuración)
🔹 **Situación fiscal**: Déficit primario controlado

**Análisis por Riesgo/Retorno:**

**CONSERVADOR** (AL30):
✅ Menor duration, vencimiento 2030
✅ Liquidez aceptable en mercado secundario
⚠️ Riesgo soberano sigue presente

**AGRESIVO** (AL35):
✅ Mayor retorno potencial (+19.5% TIR)
⚠️ Mayor duration = más sensible a tasas
⚠️ Vencimiento más lejano (2035)

**COBERTURA INFLACIÓN** (CER):
✅ Protección contra inflación doméstica
✅ Menor riesgo cambiario
⚠️ Dependiente de metodología INDEC

**Estrategia Sugerida:**
• **Máximo 10-15%** del portfolio total
• **Diversificar**: Mix USD + CER
• **Timing**: Comprar en momentos de estrés (spreads altos)
• **Liquidez**: Mantener posiciones negociables

**Escenarios:**
📈 **Bull case**: Estabilidad política → spreads se comprimen → ganancias de capital
📉 **Bear case**: Nueva crisis → restructuración → pérdidas significativas

*Alta volatilidad esperada. Solo para inversores con experiencia en mercados emergentes.*"""
        }
        
        # Buscar respuesta apropiada
        response_text = None
        tokens = 0
        
        if any(word in user_message for word in ["merval", "bolsa", "acciones"]):
            response_text = responses["merval"]
            tokens = 320
        elif any(word in user_message for word in ["bitcoin", "btc", "crypto"]):
            response_text = responses["bitcoin"]
            tokens = 280
        elif "ypf" in user_message:
            response_text = responses["ypf"]
            tokens = 350
        elif any(word in user_message for word in ["bonos", "al30", "al35"]):
            response_text = responses["bonos"]
            tokens = 400
        else:
            response_text = """🤖 **Asistente Financiero Argentino**

Hola! Soy tu asistente especializado en el mercado financiero argentino. Puedo ayudarte con:

📊 **Análisis de mercado:**
• MERVAL y acciones argentinas
• Bonos soberanos (AL30, AL35, GD30)
• ADRs argentinos en NYSE

₿ **Criptomonedas:**
• Bitcoin y altcoins en contexto argentino
• Regulaciones AFIP
• Exchanges locales

🏦 **Instrumentos locales:**
• Plazo fijo UVA
• LELIQs y instrumentos del BCRA
• Fondos comunes de inversión

💱 **Contexto macro:**
• Inflación y devaluación
• Políticas monetarias
• Impacto de elecciones

¿En qué tema específico te gustaría que profundice?

*Recordá que esto no constituye asesoramiento financiero profesional.*"""
            tokens = 180
        
        return MockOpenAIResponse(response_text, tokens)

async def demo_openai_conversation():
    """Demostración de conversación con OpenAI simulado"""
    print("🚀 DEMO: Chat Service con OpenAI Real")
    print("="*60)
    print("💡 Esta es una simulación de cómo funcionaría con tu API key real")
    print("="*60)
    
    client = MockOpenAIClient()
    
    # Simulación de conversación
    questions = [
        "¿Cómo está el MERVAL hoy?",
        "¿Qué opinas sobre Bitcoin en Argentina?",
        "Dame un análisis de YPF",
        "¿Conviene comprar bonos argentinos?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n👤 Usuario: {question}")
        print("🔄 Procesando con GPT-4...")
        
        # Simular tiempo de respuesta de OpenAI
        await asyncio.sleep(1)
        
        # Simular llamada a OpenAI
        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "Eres un asistente financiero argentino"},
                {"role": "user", "content": question}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        
        print(f"🤖 GPT-4:")
        print(response.choices[0].message.content)
        print(f"\n📊 Tokens usados: {response.usage.total_tokens} (prompt: {response.usage.prompt_tokens}, completion: {response.usage.completion_tokens})")
        print("-" * 60)

def show_production_config():
    """Mostrar cómo configurar para producción"""
    print("\n🔧 CONFIGURACIÓN PARA PRODUCCIÓN:")
    print("="*50)
    print("1. Obtener API Key de OpenAI:")
    print("   https://platform.openai.com/api-keys")
    print()
    print("2. Editar archivo .env:")
    print("   OPENAI_API_KEY=sk-proj-tu-api-key-aqui...")
    print("   SERVICE_MODE=production")
    print()
    print("3. Reiniciar el servicio:")
    print("   El servicio detectará automáticamente la API key válida")
    print()
    print("4. Verificar logs:")
    print("   Debería mostrar '🤖 OpenAI configurado en modo PRODUCCIÓN'")
    print()
    print("💰 Costos estimados OpenAI (GPT-4 Turbo):")
    print("   • Input: $0.01 por 1K tokens")
    print("   • Output: $0.03 por 1K tokens")
    print("   • Conversación típica: ~500 tokens = $0.02 USD")
    print("   • 1000 consultas/mes ≈ $20 USD")

async def main():
    await demo_openai_conversation()
    show_production_config()

if __name__ == "__main__":
    asyncio.run(main())
