from fastapi import HTTPException, Header, Depends
from typing import Dict
import requests
from app.core.config import env_config

async def verify_auth_token(authorization: str = Header(...)) -> Dict[str, str]:
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    
    if not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Formato de token inválido")
    
    try:
        backend_url = env_config.get('BACKEND_URL', 'http://localhost:8080')
        headers = {'Authorization': authorization}
        response = requests.get(f"{backend_url}/api/auth/profile", headers=headers, timeout=10)
        
        if response.status_code == 401:
            raise HTTPException(status_code=401, detail="Token inválido")
        elif response.status_code != 200:
            raise HTTPException(status_code=500, detail="Error validando token")
        
        user_data = response.json()
        user_info = user_data.get('data', {}).get('user', {})
        
        if not user_info.get('id'):
            raise HTTPException(status_code=400, detail="No se pudo obtener ID del usuario")
        
        return {
            'user_id': str(user_info.get('id')),
            'name': user_info.get('name', 'Usuario'),
            'email': user_info.get('email', ''),
            'username': user_info.get('username', '')
        }
        
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=503, detail="Backend no disponible")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

def get_user_identity(user_info: Dict[str, str] = Depends(verify_auth_token)) -> Dict[str, str]:
    return user_info
