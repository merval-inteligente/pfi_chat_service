"""
Chat Service Consolidado - Servicio único de IA
Combina OpenAI Assistant + Chat Completion + Fallback
"""

import time
import os
from typing import List, Dict, Optional
from openai import OpenAI

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

# Configuración
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# Cliente OpenAI
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# ID del asistente personalizado "Merval Inteligente"
ASSISTANT_ID = "asst_XTeMOZNGajadI4NxfFO3s5jF"

async def generate_ai_response(message: str, user_id: str, user_name: str, conversation_history: List[Dict] = None) -> str:
    """
    Servicio consolidado de IA:
    1. Intenta usar Asistente Personalizado "Merval Inteligente"
    2. Fallback a Chat Completion básico
    3. Fallback a respuestas predefinidas
    """
    
    # Opción 1: Asistente Personalizado
    try:
        if client and OPENAI_API_KEY:
            assistant_response = await _get_assistant_response(message)
            if assistant_response and not assistant_response.startswith("❌"):
                return assistant_response
    except Exception as e:
        print(f"⚠️ Error con asistente personalizado: {e}")
    
    # Opción 2: Chat Completion básico  
    try:
        if client and OPENAI_API_KEY:
            chat_response = await _get_chat_completion(message, conversation_history)
            if chat_response and not chat_response.startswith("❌"):
                return chat_response
    except Exception as e:
        print(f"⚠️ Error con chat completion: {e}")
    
    # Opción 3: Respuestas predefinidas
    return _get_fallback_response(message)

async def _get_assistant_response(message: str) -> Optional[str]:
    """Usar el asistente personalizado Merval Inteligente"""
    try:
        # Crear thread
        thread = client.beta.threads.create()
        
        # Agregar mensaje
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=message
        )
        
        # Ejecutar asistente
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )
        
        # Esperar completación
        while run.status in ['queued', 'in_progress']:
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
        
        if run.status == 'completed':
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            response = messages.data[0].content[0].text.value
            
            # Limpiar thread
            client.beta.threads.delete(thread.id)
            return response
        else:
            return f"❌ Error en asistente: {run.status}"
            
    except Exception as e:
        return f"❌ Error: {str(e)}"

async def _get_chat_completion(message: str, conversation_history: List[Dict] = None) -> Optional[str]:
    """Fallback usando chat completion básico"""
    try:
        messages = [
            {"role": "system", "content": "Eres un informador financiero especializado en el MERVAL argentino. Proporciona información factual sobre activos del MERVAL, NUNCA des recomendaciones de inversión. Incluye precios, variaciones, información de empresas y datos del mercado. Máximo 250 palabras, tono neutral e informativo. Termina siempre con: 📊 Información solo con fines informativos. No constituye recomendación de inversión."}
        ]
        
        # Agregar historial reciente (últimos 2 mensajes)
        if conversation_history:
            for item in conversation_history[-2:]:
                messages.append({"role": "user", "content": item.get("message", "")})
                messages.append({"role": "assistant", "content": item.get("response", "")})
        
        # Mensaje actual
        messages.append({"role": "user", "content": message})
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=messages,
            max_tokens=300,
            temperature=0.3
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Asegurar disclaimer
        if "solo con fines informativos" not in ai_response:
            ai_response += "\n\n Información solo con fines informativos. No constituye recomendación de inversión."
        
        return ai_response
        
    except Exception as e:
        return f"❌ Error: {str(e)}"

def _get_fallback_response(message: str) -> str:
    """Respuestas predefinidas como último fallback"""
    message_lower = message.lower()
    
    # Acciones del MERVAL
    if any(word in message_lower for word in ['ypf', 'pampa', 'galicia', 'macro', 'merval']):
        return """ Activos principales del MERVAL incluyen YPF (energía), Banco Macro (financiero), 
Pampa Energía (eléctrica), Galicia (bancario), entre otros. Para datos actualizados de precios 
y volúmenes, consulta la página oficial de BYMA (Bolsas y Mercados Argentinos).

 Información solo con fines informativos. No constituye recomendación de inversión."""
    
    # Dólar
    elif any(word in message_lower for word in ['dolar', 'dólar', 'blue', 'mep', 'ccl']):
        return """ Tipos de cambio en Argentina: Dólar oficial, blue, MEP y CCL. 
Cada uno tiene diferentes valores y usos. El blue es informal, MEP y CCL son 
vías legales para acceder a divisas. Consulta fuentes oficiales para cotizaciones actuales.

 Información solo con fines informativos. No constituye recomendación de inversión."""
    
    # Default
    else:
        return """Soy un asistente especializado en información del mercado financiero argentino. 
Puedo ayudarte con datos sobre activos del MERVAL, tipos de cambio y contexto del mercado local.

 Información solo con fines informativos. No constituye recomendación de inversión."""

async def check_ai_status() -> Dict[str, bool]:
    """Verificar estado de todos los servicios de IA"""
    status = {
        "openai_configured": bool(OPENAI_API_KEY),
        "openai_available": False,
        "assistant_available": False
    }
    
    if not client or not OPENAI_API_KEY:
        return status
    
    try:
        # Test básico
        client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        status["openai_available"] = True
        
        # Test asistente
        try:
            client.beta.assistants.retrieve(ASSISTANT_ID)
            status["assistant_available"] = True
        except:
            pass
            
    except:
        pass
    
    return status