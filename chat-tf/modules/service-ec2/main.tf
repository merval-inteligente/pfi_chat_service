resource "aws_security_group" "svc_sg" {
  name        = "${var.project}-${var.name}-sg"
  description = "HTTP ${var.public_http_port} publico + intra-VPC"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTP publico"
    from_port   = var.public_http_port
    to_port     = var.public_http_port
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "intra VPC TCP"
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }

  dynamic "ingress" {
    for_each = var.enable_ssh ? [1] : []
    content {
      description = "SSH"
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = [var.ssh_cidr]
    }
  }

  egress {
    description = "Salida a Internet"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project}-${var.name}-sg" }
}

data "template_file" "user_data" {
  template = file("${path.module}/user_data.tpl")
  vars = {
    RUNTIME_IMAGE  = var.runtime_image
    CONTAINER_PORT = var.container_port
    PUBLIC_HTTP    = var.public_http_port
    REPO_URL       = var.repo_url
    START_COMMAND  = var.start_command
    EXTRA_ENVS     = join("\n", [for k, v in var.extra_env : "${k}=${v}"])
    APP_NAME       = var.name
  }
}

resource "aws_instance" "svc" {
  ami                         = var.ami_id
  instance_type               = var.instance_type
  subnet_id                   = var.subnet_id
  vpc_security_group_ids      = [aws_security_group.svc_sg.id, var.intra_sg_id]
  associate_public_ip_address = true
  key_name                    = var.key_name != "" ? var.key_name : null

  user_data = data.template_file.user_data.rendered

  tags = { Name = "${var.project}-${var.name}" }
}

output "public_dns" { value = aws_instance.svc.public_dns }
output "private_ip" { value = aws_instance.svc.private_ip }
