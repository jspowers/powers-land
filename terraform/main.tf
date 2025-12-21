terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Get latest Ubuntu 24.04 LTS AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# IAM Role for EC2 with SSM permissions
resource "aws_iam_role" "ec2_ssm_role" {
  name = "powers-land-ec2-ssm-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name    = "powers-land-ec2-ssm-role"
    Project = "powers-land"
  }
}

# Attach AWS managed SSM policy
resource "aws_iam_role_policy_attachment" "ssm_policy" {
  role       = aws_iam_role.ec2_ssm_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# IAM Instance Profile
resource "aws_iam_instance_profile" "ec2_profile" {
  name = "powers-land-ec2-profile"
  role = aws_iam_role.ec2_ssm_role.name

  tags = {
    Name    = "powers-land-ec2-profile"
    Project = "powers-land"
  }
}

# Security Group
resource "aws_security_group" "web" {
  name        = "powers-land-web-sg"
  description = "Security group for powers.land web server"

  ingress {
    description = "SSH from allowed IP"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
  }

  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS from anywhere"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "powers-land-web-sg"
    Project = "powers-land"
  }
}

# EC2 Instance
resource "aws_instance" "web" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  key_name      = var.key_name

  vpc_security_group_ids = [aws_security_group.web.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  user_data = templatefile("${path.module}/user-data.sh", {
    domain_name           = var.domain_name
    app_secret_key        = var.app_secret_key
    spotify_client_id     = var.spotify_client_id
    spotify_client_secret = var.spotify_client_secret
  })

  tags = {
    Name    = "powers-land-web"
    Project = "powers-land"
  }
}

# Elastic IP
resource "aws_eip" "web" {
  instance = aws_instance.web.id
  domain   = "vpc"

  tags = {
    Name    = "powers-land-eip"
    Project = "powers-land"
  }
}

# Get existing Route 53 Hosted Zone
data "aws_route53_zone" "main" {
  name         = "${var.domain_name}."
  private_zone = false
}

# DNS A Record for root domain
resource "aws_route53_record" "root" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = var.domain_name
  type    = "A"
  ttl     = 300
  records = [aws_eip.web.public_ip]
}

# DNS A Record for www subdomain
resource "aws_route53_record" "www" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "www.${var.domain_name}"
  type    = "A"
  ttl     = 300
  records = [aws_eip.web.public_ip]
}

# Wait for instance to be ready and SSL to be configured
resource "null_resource" "configure_ssl" {
  depends_on = [
    aws_instance.web,
    aws_eip.web,
    aws_route53_record.root,
    aws_route53_record.www
  ]

  # Only run if SSL email is provided
  count = var.ssl_email != "" ? 1 : 0

  # Wait for DNS propagation and configure SSL
  provisioner "local-exec" {
    command = <<-EOT
      echo "Waiting 60 seconds for DNS propagation..."
      sleep 60
      echo "Configuring SSL certificate..."
      ssh -o StrictHostKeyChecking=no -i ~/.ssh/${var.key_name}.pem ubuntu@${aws_eip.web.public_ip} \
        "sudo certbot --nginx -d ${var.domain_name} -d www.${var.domain_name} \
         --non-interactive --agree-tos --email ${var.ssl_email} --redirect"
    EOT
  }

  triggers = {
    instance_id = aws_instance.web.id
    eip         = aws_eip.web.public_ip
  }
}
