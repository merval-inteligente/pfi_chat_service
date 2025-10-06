# Chat Service - Terraform Infrastructure

Infraestructura como código (IaC) para desplegar el Chat Service con el asistente "Merval Inteligente" en AWS EC2.

## 📋 Requisitos

- Terraform >= 1.5.0
- AWS CLI configurado con credenciales válidas
- PowerShell 5.1+ (Windows)
- Par de claves SSH: `millaveuade` en AWS
- Archivo de clave SSH: `~/.ssh/millaveuade.pem`

## 🏗️ Arquitectura

```
VPC (alertas-vpc)
└── Subnet pública
    ├── EC2 t3.micro (Amazon Linux 2023)
    │   ├── Docker + Docker Compose
    │   ├── Python 3.11 (FastAPI + OpenAI + MongoDB)
    │   └── Puerto 80 → 8084
    │
    └── Security Groups
        ├── chat-chat-sg (HTTP 80 + SSH 22)
        └── alertas-internal-sg (comunicación intra-VPC)
```

## 📁 Estructura del Proyecto

```
chat-tf/
├── main.tf                    # Configuración principal
├── variables.tf               # Definición de variables
├── outputs.tf                 # Outputs de la infraestructura
├── terraform.tfvars           # Valores no sensibles
├── secrets.auto.tfvars        # ⚠️ Credenciales (NO COMMITEAR)
├── .gitignore                 # Protección de archivos sensibles
│
├── deploy.ps1                 # 🚀 Script de despliegue automatizado
├── destroy.ps1                # 🔥 Script de destrucción
│
└── modules/
    └── service-ec2/
        ├── main.tf            # Módulo EC2 reutilizable
        ├── variables.tf       # Variables del módulo
        └── user_data.tpl      # Bootstrap script
```

## 🔐 Configuración de Credenciales

### 1. Archivo `secrets.auto.tfvars`

Este archivo contiene las credenciales sensibles y **NUNCA** debe commitearse a Git:

```hcl
# OpenAI
openai_api_key = "sk-proj-..."

# MongoDB Atlas
mongodb_url      = "mongodb+srv://user:pass@cluster.mongodb.net/..."
mongodb_database = "MervalDB"

# Configuración del servidor
backend_url = "http://localhost:8080"
host        = "0.0.0.0"
port        = "8084"
```

### 2. Variables de Infraestructura (`terraform.tfvars`)

Configuración no sensible de la infraestructura:

```hcl
project       = "chat"
region        = "us-east-1"
instance_type = "t3.micro"
key_name      = "millaveuade"

vpc_id      = "vpc-0a9472df1004235bd"
subnet_id   = "subnet-0936477549098d860"
intra_sg_id = "sg-060fffa1e9ad51d8f"

enable_ssh = true
ssh_cidr   = "0.0.0.0/0"

container_port   = 8084
public_http_port = 80
```

## 🚀 Despliegue Automatizado

### Opción 1: Script PowerShell (Recomendado)

```powershell
# Despliegue completo en un solo comando
.\deploy.ps1

# Saltar la espera de bootstrap (si ya sabes que Docker está listo)
.\deploy.ps1 -SkipWait

# Personalizar tiempo de espera
.\deploy.ps1 -WaitSeconds 120
```

El script `deploy.ps1` realiza automáticamente:
1. ✅ Terraform apply (crea EC2 + Security Groups)
2. ✅ Espera a que el bootstrap complete (90 seg)
3. ✅ Crea directorios en la instancia
4. ✅ Copia código de la aplicación
5. ✅ Instala Docker Compose
6. ✅ Inicia los contenedores
7. ✅ Verifica el health endpoint

### Opción 2: Paso a Paso Manual

```powershell
# 1. Inicializar Terraform (solo la primera vez)
terraform init

# 2. Validar configuración
terraform validate

# 3. Ver plan de ejecución
terraform plan

# 4. Desplegar infraestructura
terraform apply -auto-approve

# 5. Ver outputs
terraform output
```

Luego, copiar archivos y arrancar servicio manualmente (ver sección de Comandos Útiles).

## 🔥 Destruir Infraestructura

```powershell
# Con confirmación interactiva
.\destroy.ps1

# Forzar destrucción sin confirmación
.\destroy.ps1 -Force

# O directamente con Terraform
terraform destroy -auto-approve
```

## 📊 Outputs

Después del despliegue, se obtienen:

```hcl
chat_public_dns = "ec2-52-90-36-99.compute-1.amazonaws.com"
chat_private_ip = "10.0.1.106"
url             = "http://ec2-52-90-36-99.compute-1.amazonaws.com/health"
```

## 🌐 Endpoints de la API

Una vez desplegado:

- **Health Check**: `http://<DNS>/health`
- **Documentación Interactiva**: `http://<DNS>/docs`
- **Chat**: `POST http://<DNS>/api/chat/message`
- **Test (Dev)**: `POST http://<DNS>/api/chat/test`

## 🛠️ Comandos Útiles

```powershell
# Conectarse por SSH
ssh -i ~/.ssh/millaveuade.pem ec2-user@<DNS>

# Ver logs en tiempo real
ssh -i ~/.ssh/millaveuade.pem ec2-user@<DNS> "cd /opt/app/src && docker-compose logs -f"

# Reiniciar servicio
ssh -i ~/.ssh/millaveuade.pem ec2-user@<DNS> "cd /opt/app/src && docker-compose restart"

# Ver estado de contenedores
ssh -i ~/.ssh/millaveuade.pem ec2-user@<DNS> "cd /opt/app/src && docker-compose ps"

# Parar servicio
ssh -i ~/.ssh/millaveuade.pem ec2-user@<DNS> "cd /opt/app/src && docker-compose down"

# Actualizar código (desde local)
scp -i ~/.ssh/millaveuade.pem -r ../chat-service/* ec2-user@<DNS>:/opt/app/src/
ssh -i ~/.ssh/millaveuade.pem ec2-user@<DNS> "cd /opt/app/src && docker-compose restart"
```

## 🔧 Modificar Configuración

### Cambiar credenciales

1. Editar `secrets.auto.tfvars`
2. Ejecutar: `terraform apply -auto-approve`
3. Reiniciar servicio en EC2

### Cambiar tipo de instancia

1. Editar `terraform.tfvars`: `instance_type = "t3.small"`
2. Ejecutar: `terraform apply -auto-approve`

### Cambiar región

1. Editar `terraform.tfvars`: `region = "us-west-2"`
2. Actualizar VPC/Subnet/SG IDs de esa región
3. Ejecutar: `terraform apply -auto-approve`

## 🐛 Troubleshooting

### Error: "The vpc ID does not exist"

Verifica que `vpc_id`, `subnet_id` y `intra_sg_id` en `terraform.tfvars` correspondan a recursos existentes en la región configurada.

```powershell
aws ec2 describe-vpcs --region us-east-1
```

### Error: SSH connection refused

El bootstrap puede tomar hasta 2 minutos. Espera y reintenta.

```powershell
ssh -i ~/.ssh/millaveuade.pem ec2-user@<DNS> "tail /var/log/cloud-init-output.log"
```

### Error: Health endpoint no responde

El servicio tarda ~30 segundos en instalar dependencias y arrancar:

```powershell
ssh -i ~/.ssh/millaveuade.pem ec2-user@<DNS> "cd /opt/app/src && docker-compose logs chat-api"
```

## 📦 Variables de Entorno en EC2

Las variables se inyectan automáticamente en el contenedor Docker desde Terraform:

- `OPENAI_API_KEY` - Clave de OpenAI
- `MONGODB_URL` - URL de conexión a MongoDB
- `MONGODB_DATABASE` - Nombre de la base de datos
- `BACKEND_URL` - URL del backend
- `HOST` - Host del servidor (0.0.0.0)
- `PORT` - Puerto del servidor (8084)

## 🔒 Seguridad

### Archivos protegidos por `.gitignore`

- ✅ `secrets.auto.tfvars` - Credenciales
- ✅ `.terraform/` - Providers descargados
- ✅ `*.tfstate*` - Estado de Terraform (puede contener secretos)
- ✅ `.terraform.lock.hcl` - Lock de versiones

### Security Groups

- **Ingress**:
  - HTTP (80) desde 0.0.0.0/0
  - SSH (22) desde 0.0.0.0/0 ⚠️ (cambiar `ssh_cidr` para restringir)
  - TCP (0-65535) desde 10.0.0.0/8 (intra-VPC)

- **Egress**:
  - Todo el tráfico permitido (0.0.0.0/0)

### Recomendaciones

1. Cambiar `ssh_cidr = "0.0.0.0/0"` a tu IP pública: `ssh_cidr = "X.X.X.X/32"`
2. Nunca commitear `secrets.auto.tfvars`
3. Rotar credenciales periódicamente
4. Usar AWS Secrets Manager en producción

## 📚 Recursos

- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Amazon Linux 2023 User Guide](https://docs.aws.amazon.com/linux/al2023/ug/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

## 📝 Notas

- La instancia usa **Amazon Linux 2023** (AMI más reciente)
- Docker y Docker Compose se instalan automáticamente via `user_data`
- El código de la aplicación se copia **manualmente** desde local (no hay repo Git configurado)
- La instancia se reinicia automáticamente con `restart: unless-stopped` en Docker Compose

## 🤝 Contribuir

Para agregar mejoras al módulo Terraform:

1. Modificar `modules/service-ec2/`
2. Probar con `terraform plan`
3. Validar con `terraform validate`
4. Documentar cambios en este README

---

**Autor**: Chat Service Team  
**Última actualización**: Octubre 2025
