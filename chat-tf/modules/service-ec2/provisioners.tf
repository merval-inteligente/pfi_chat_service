resource "null_resource" "deploy_code" {
  count = var.source_code_path != "" ? 1 : 0
  
  depends_on = [aws_instance.svc]

  # Este recurso se ejecuta cada vez que cambia la instancia
  triggers = {
    instance_id = aws_instance.svc.id
  }

  # Esperar a que la instancia esté lista y el bootstrap complete
  provisioner "local-exec" {
    command = "Start-Sleep -Seconds 90"
    interpreter = ["PowerShell", "-Command"]
  }

  # Crear directorio remoto
  provisioner "local-exec" {
    command = <<-EOT
      ssh -i $env:USERPROFILE\.ssh\millaveuade.pem -o StrictHostKeyChecking=no ec2-user@${aws_instance.svc.public_dns} "sudo mkdir -p /opt/app/src && sudo chown -R ec2-user:ec2-user /opt/app"
    EOT
    interpreter = ["PowerShell", "-Command"]
  }

  # Copiar archivos de la aplicación
  provisioner "local-exec" {
    command = <<-EOT
      scp -i $env:USERPROFILE\.ssh\millaveuade.pem -o StrictHostKeyChecking=no -r ${var.source_code_path}/app ${var.source_code_path}/main.py ${var.source_code_path}/requirements.txt ${var.source_code_path}/README.md ec2-user@${aws_instance.svc.public_dns}:/opt/app/src/
    EOT
    interpreter = ["PowerShell", "-Command"]
  }

  # Copiar docker-compose.yml
  provisioner "local-exec" {
    command = <<-EOT
      scp -i $env:USERPROFILE\.ssh\millaveuade.pem -o StrictHostKeyChecking=no ${var.source_code_path}/docker-compose.yml ec2-user@${aws_instance.svc.public_dns}:/opt/app/src/
    EOT
    interpreter = ["PowerShell", "-Command"]
  }

  # Instalar docker-compose e iniciar el servicio
  provisioner "local-exec" {
    command = <<-EOT
      ssh -i $env:USERPROFILE\.ssh\millaveuade.pem -o StrictHostKeyChecking=no ec2-user@${aws_instance.svc.public_dns} "sudo curl -sL 'https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-linux-x86_64' -o /usr/local/bin/docker-compose && sudo chmod +x /usr/local/bin/docker-compose && cd /opt/app/src && docker-compose up -d"
    EOT
    interpreter = ["PowerShell", "-Command"]
  }
}

