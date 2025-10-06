# Configuración del proyecto
project       = "chat"
region        = "us-east-1"
instance_type = "t3.micro"
key_name      = "millaveuade"

# Red (reutilizando infraestructura de alertas)
vpc_id        = "vpc-075ea12c12e95bae0"
subnet_id     = "subnet-0b69dcddae1c49d91"
intra_sg_id   = "sg-0efd45a3dff64e09f"

# SSH
enable_ssh = true
ssh_cidr   = "0.0.0.0/0"

# Puertos de la aplicación
container_port   = 8084
public_http_port = 80

# Repositorio (vacío para carga manual)
repo_url = ""

# Comando de inicio
start_command = "pip install --no-cache-dir -r requirements.txt && uvicorn main:app --host 0.0.0.0 --port 8084"

# Variables de entorno adicionales (vacío para este proyecto)
extra_env = {}
