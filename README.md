# 💬 Chat Service - Merval Inteligente

FastAPI backend con asistente GPT especializado en el mercado financiero argentino (MERVAL), desplegable automáticamente en AWS con Terraform.

## 🚀 Características

- **Asistente Personalizado**: Integración con asistente OpenAI "Merval Inteligente" (ID: `asst_XTeMOZNGajadI4NxfFO3s5jF`)
- **Información MERVAL**: Datos sobre activos del mercado argentino
- **Sin Recomendaciones**: Solo información educativa, no asesoramiento financiero
- **Fallback Inteligente**: Sistema de respaldo multinivel (Assistant → ChatCompletion → Fallback)
- **MongoDB Atlas**: Almacenamiento persistente de conversaciones
- **Autenticación JWT**: Integración con backend principal (opcional)
- **Docker**: Containerización con Docker Compose
- **Infraestructura como Código**: Despliegue automatizado en AWS con Terraform

## 📁 Estructura del Proyecto

```
chat-service/
├── main.py                      # FastAPI app consolidada
├── requirements.txt             # Dependencias Python
├── docker-compose.yml           # Configuración Docker
├── .env                         # Variables de entorno (NO COMMITEAR)
├── .gitignore                   # Archivos ignorados por Git
│
├── app/
│   └── services/
│       ├── chat_service.py      # Servicio de IA (OpenAI GPT)
│       └── memory_service.py    # Persistencia MongoDB
│
└── chat-tf/                     # Infraestructura Terraform
    ├── main.tf                  # Configuración principal
    ├── variables.tf             # Variables de infraestructura
    ├── outputs.tf               # Outputs (DNS, IP, URL)
    ├── terraform.tfvars         # Valores no sensibles
    ├── secrets.auto.tfvars      # Credenciales (NO COMMITEAR)
    ├── .gitignore               # Protección de archivos sensibles
    ├── README.md                # Documentación de Terraform
    └── modules/
        └── service-ec2/         # Módulo reutilizable EC2
            ├── main.tf
            ├── variables.tf
            ├── provisioners.tf  # Provisioners automáticos
            └── user_data.tpl    # Bootstrap script
```

## 🔧 Instalación y Despliegue

### Opción 1: Despliegue Automatizado en AWS (Terraform)

**¡Un solo comando despliega todo en AWS!**

```powershell
# 1. Configurar credenciales en chat-tf/secrets.auto.tfvars
cd chat-tf

# 2. Desplegar automáticamente
terraform init
terraform apply -auto-approve
```

**Terraform hace automáticamente:**
- ✅ Crea EC2 t3.micro + Security Groups
- ✅ Instala Docker en la instancia
- ✅ Copia código de la aplicación
- ✅ Levanta servicio con Docker Compose
- ✅ API funcionando en ~2-3 minutos

**Ver documentación detallada**: [chat-tf/README.md](./chat-tf/README.md)

### Opción 2: Desarrollo Local con Docker

```bash
# 1. Configurar variables de entorno
cp .env.example .env  # Editar con tus credenciales

# 2. Levantar con Docker Compose
docker-compose up -d

# 3. Ver logs
docker-compose logs -f
```

### Opción 3: Desarrollo Local sin Docker

1. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

2. **Configurar variables de entorno (.env):**
```env
# OpenAI
OPENAI_API_KEY=sk-proj-tu-api-key-aqui

# MongoDB
MONGODB_URL=mongodb+srv://user:password@cluster.mongodb.net/MervalDB
MONGODB_DATABASE=MervalDB

# Backend principal
BACKEND_URL=http://localhost:8080

# Servidor
HOST=0.0.0.0
PORT=8084
```

3. **Ejecutar servidor:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8084 --reload
```

## 🎯 Uso

### Iniciar servidor:
```bash
python main.py
```

### Endpoints disponibles:

#### 1. **Chat con autenticación** 
```http
POST /api/chat/message
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "message": "¿Cómo está YPF hoy?"
}
```

#### 2. **Chat de prueba (sin autenticación)**
```http
POST /api/chat/test
Content-Type: application/json

{
  "message": "¿Qué es el MERVAL?"
}
```

#### 3. **Historial de chat**
```http
GET /api/chat/history?limit=20
Authorization: Bearer <jwt_token>
```

#### 4. **Health check**
```http
GET /health
```

### 📊 Documentación automática:
- **Swagger UI**: http://localhost:8084/docs
- **ReDoc**: http://localhost:8084/redoc

## 🤖 Funcionalidades del Asistente

### ✅ **Información que proporciona:**
- Precios y variaciones de acciones del MERVAL
- Información sobre empresas argentinas
- Datos de volumen de operaciones
- Contexto del mercado financiero argentino
- Análisis técnico y fundamental básico

### ❌ **Lo que NO hace:**
- No da recomendaciones de inversión
- No sugiere timing de compra/venta
- No realiza asesoramiento financiero personalizado

### 🔄 **Sistema de Fallback:**
1. **Asistente OpenAI personalizado** (primera opción)
2. **Chat Completion básico** (si el asistente falla)
3. **Respuestas predefinidas** (último recurso)

## 🛠️ Configuración del Asistente

El asistente personalizado "Merval Inteligente" está configurado con:
- **ID**: `asst_XTeMOZNGajadI4NxfFO3s5jF`
- **Modelo**: GPT-4
- **Especialización**: Mercado financiero argentino
- **Tono**: Educativo, no asesor

## 📈 Estado del Sistema

Verificar en `/health`:
```json
{
  "status": "healthy",
  "services": {
    "mongodb": true,
    "openai": {
      "configured": true,
      "available": true,
      "assistant_available": true
    }
  }
}
```

## 🔐 Autenticación

El servicio requiere JWT token del backend principal para endpoints protegidos. El token debe incluir:
- `user_id`: ID único del usuario
- `name`: Nombre del usuario
- `email`: Email del usuario

## 💾 Almacenamiento

Las conversaciones se almacenan en MongoDB con:
- Historial por usuario
- Timestamp de mensajes
- Metadatos de storage

## 🌐 Despliegue en Producción

### Arquitectura AWS (Terraform)

```
Internet → AWS VPC (alertas-vpc)
         → Subnet Pública
           → Security Groups (HTTP 80 + SSH)
             → EC2 t3.micro (Amazon Linux 2023)
               → Docker + Docker Compose
                 → chat-service (puerto 8084 → 80)
                   ├── FastAPI
                   ├── OpenAI GPT Client
                   └── MongoDB Client
```

### Endpoints en Producción

Una vez desplegado con Terraform:
- **Health**: `http://<DNS>/health`
- **Docs**: `http://<DNS>/docs`
- **Chat**: `POST http://<DNS>/api/chat/message`

### Gestión del Servicio en AWS

```powershell
# Ver logs
ssh -i ~/.ssh/millaveuade.pem ec2-user@<DNS> "cd /opt/app/src && docker-compose logs -f"

# Reiniciar servicio
ssh -i ~/.ssh/millaveuade.pem ec2-user@<DNS> "cd /opt/app/src && docker-compose restart"

# Estado de contenedores
ssh -i ~/.ssh/millaveuade.pem ec2-user@<DNS> "cd /opt/app/src && docker-compose ps"
```

### Destruir Infraestructura

```powershell
cd chat-tf
terraform destroy -auto-approve
```

## 🛠️ Tecnologías

- **Backend**: FastAPI 0.115+
- **IA**: OpenAI GPT-4 (Assistant API)
- **Base de Datos**: MongoDB Atlas
- **Containerización**: Docker + Docker Compose
- **Infraestructura**: Terraform + AWS (EC2, VPC, Security Groups)
- **OS**: Amazon Linux 2023
- **Python**: 3.11

## 🚨 Disclaimers

Todas las respuestas incluyen automáticamente:
> "📊 Información solo con fines informativos. No constituye recomendación de inversión."

---

**Versión**: 3.0.0 - Limpia y Consolidada
**Autor**: Nicolas Petcoff
**Fecha**: Octubre 2025