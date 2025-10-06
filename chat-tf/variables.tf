variable "project" {
  type    = string
  default = "chat"
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "instance_type" {
  type    = string
  default = "t3.micro"
}

variable "key_name" {
  type    = string
  default = "millaveuade"
}

variable "enable_ssh" {
  type    = bool
  default = true
}

variable "ssh_cidr" {
  type    = string
  default = "0.0.0.0/0"
}

variable "vpc_id" {
  type    = string
  default = "vpc-0a9472df1004235bd"
}

variable "subnet_id" {
  type    = string
  default = "subnet-0936477549098d860"
}

variable "intra_sg_id" {
  type    = string
  default = "sg-060fffa1e9ad51d8f"
}

variable "container_port" {
  type    = number
  default = 8084
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
  type    = string
  default = "pip install --no-cache-dir -r requirements.txt && uvicorn main:app --host 0.0.0.0 --port 8084"
}

variable "extra_env" {
  type = map(string)
  default = {}
}

# ============================================
# Variables sensibles (definidas en secrets.auto.tfvars)
# ============================================

variable "openai_api_key" {
  type        = string
  description = "OpenAI API Key"
  sensitive   = true
}

variable "mongodb_url" {
  type        = string
  description = "MongoDB connection URL"
  sensitive   = true
}

variable "mongodb_database" {
  type        = string
  description = "MongoDB database name"
  default     = "MervalDB"
}

variable "backend_url" {
  type        = string
  description = "Backend URL"
  default     = "http://localhost:8080"
}

variable "host" {
  type        = string
  description = "Server host"
  default     = "0.0.0.0"
}

variable "port" {
  type        = string
  description = "Server port"
  default     = "8084"
}
