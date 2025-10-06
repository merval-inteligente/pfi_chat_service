# Configuración del proyecto
project       = "chat"
region        = "us-east-1"
instance_type = "t3.micro"
key_name      = "millaveuade"

# Red (reutilizando infraestructura de alertas)
vpc_id        = "vpc-0a9472df1004235bd"
subnet_id     = "subnet-0936477549098d860"
intra_sg_id   = "sg-060fffa1e9ad51d8f"

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
