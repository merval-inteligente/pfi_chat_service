terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.60"
    }
  }
}

provider "aws" { region = var.region }

data "aws_ami" "al2023" {
  owners      = ["137112412989"]
  most_recent = true
  
  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
  
  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
  
  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }
}

module "svc_chat" {
  source            = "./modules/service-ec2"
  name              = "chat"
  project           = var.project
  vpc_id            = var.vpc_id
  subnet_id         = var.subnet_id
  intra_sg_id       = var.intra_sg_id
  ami_id            = data.aws_ami.al2023.id
  instance_type     = var.instance_type
  key_name          = var.key_name
  enable_ssh        = var.enable_ssh
  ssh_cidr          = var.ssh_cidr

  container_port    = var.container_port   # 8084
  public_http_port  = var.public_http_port # 80
  repo_url          = var.repo_url
  start_command     = var.start_command    # uvicorn --port 8084
  runtime_image     = "python:3.11-slim"
  source_code_path  = "${path.module}/.."
  extra_env         = merge(var.extra_env, {
    OPENAI_API_KEY    = var.openai_api_key
    MONGODB_URL       = var.mongodb_url
    MONGODB_DATABASE  = var.mongodb_database
    BACKEND_URL       = var.backend_url
    HOST              = var.host
    PORT              = var.port
  })
}
