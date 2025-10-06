#!/bin/bash
set -euxo pipefail

# Actualizar sistema e instalar Docker
dnf -y update
dnf -y install docker git
systemctl enable --now docker
usermod -aG docker ec2-user

# Instalar docker-compose standalone
curl -sL "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-linux-x86_64" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Crear estructura de directorios
mkdir -p /opt/app/src
cd /opt/app/src

# Generar .env completo con todas las variables
cat > .env <<'ENVEOF'
# Chat Service Configuration
${EXTRA_ENVS}
ENVEOF

# Crear docker-compose.yml
cat > docker-compose.yml <<'EOF'
version: '3.8'

services:
  chat-api:
    image: ${RUNTIME_IMAGE}
    container_name: chat-service
    working_dir: /app
    volumes:
      - .:/app
    ports:
      - "${PUBLIC_HTTP}:${CONTAINER_PORT}"
    environment:
      - PYTHONUNBUFFERED=1
    env_file:
      - .env
    command: >
      bash -c "
        ${START_COMMAND}
      "
    restart: unless-stopped
    networks:
      - chat-network

networks:
  chat-network:
    driver: bridge
EOF

# Nota: El código debe copiarse manualmente después del despliegue
# O se puede clonar desde un repositorio Git si REPO_URL está configurado
if [ -n "${REPO_URL}" ]; then
  git clone ${REPO_URL} /tmp/repo
  cp -r /tmp/repo/* /opt/app/src/
  rm -rf /tmp/repo
fi

# Dar permisos a ec2-user
chown -R ec2-user:ec2-user /opt/app

# Crear systemd service para auto-start
cat > /etc/systemd/system/chat-service.service <<'SYSEOF'
[Unit]
Description=Chat Service Docker Compose
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
WorkingDirectory=/opt/app/src
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
RemainAfterExit=yes
User=ec2-user

[Install]
WantedBy=multi-user.target
SYSEOF

systemctl daemon-reload
systemctl enable chat-service.service

# Log de finalización
echo "Bootstrap completado: $(date)" >> /var/log/bootstrap-complete.log

