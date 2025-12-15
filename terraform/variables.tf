variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "key_name" {
  description = "SSH key pair name"
  type        = string
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "powers.land"
}

variable "allowed_ssh_cidr" {
  description = "CIDR block allowed to SSH (your IP)"
  type        = string
}

variable "app_secret_key" {
  description = "Flask application secret key"
  type        = string
  sensitive   = true
}

variable "ssl_email" {
  description = "Email address for Let's Encrypt SSL certificate (leave empty to skip SSL configuration)"
  type        = string
  default     = ""
}
