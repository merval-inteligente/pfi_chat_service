variable "name" {
  type = string
}

variable "project" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "subnet_id" {
  type = string
}

variable "intra_sg_id" {
  type = string
}

variable "ami_id" {
  type = string
}

variable "instance_type" {
  type = string
}

variable "key_name" {
  type    = string
  default = ""
}

variable "enable_ssh" {
  type    = bool
  default = false
}

variable "ssh_cidr" {
  type    = string
  default = "0.0.0.0/0"
}

variable "container_port" {
  type = number
}

variable "public_http_port" {
  type    = number
  default = 80
}

variable "repo_url" {
  type    = string
  default = ""
}

variable "start_command" {
  type = string
}

variable "runtime_image" {
  type    = string
  default = "python:3.11-slim"
}

variable "extra_env" {
  type    = map(string)
  default = {}
}

variable "source_code_path" {
  type        = string
  description = "Ruta local al código fuente de la aplicación"
  default     = ""
}

