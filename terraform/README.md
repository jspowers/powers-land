# Terraform Infrastructure for powers.land

This directory contains Terraform configuration to fully automate the deployment of powers.land to AWS.

## What Gets Automated

✅ **EC2 Instance** - Ubuntu 24.04 LTS
✅ **Elastic IP** - Static IP address
✅ **Security Groups** - Firewall rules
✅ **Route 53 DNS** - Automatic A records
✅ **Application Deployment** - Automatic git clone, dependencies, migrations
✅ **Gunicorn + Nginx** - Web server configuration
✅ **SSL Certificate** - Let's Encrypt with auto-renewal
✅ **Systemd Services** - Auto-start on boot

## Prerequisites

1. **AWS Account** with credentials configured (`aws configure`)
2. **SSH Key Pair** created in AWS EC2 console
3. **Route 53 Hosted Zone** for your domain
4. **Terraform** installed (`brew install terraform` on macOS)
5. **Local SSH key** saved at `~/.ssh/powers-land-keypair.pem`

## Quick Start

### 1. Configure Variables

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your values:

```hcl
aws_region        = "us-east-1"
instance_type     = "t3.micro"
key_name          = "powers-land-keypair"      # Your AWS key pair name
domain_name       = "powers.land"
allowed_ssh_cidr  = "YOUR_IP/32"               # Get with: curl ifconfig.me
app_secret_key    = "GENERATE_RANDOM_KEY"       # python3 -c "import secrets; print(secrets.token_urlsafe(32))"
ssl_email         = "your@email.com"            # For Let's Encrypt notifications
```

### 2. Deploy Everything

```bash
terraform init
terraform plan
terraform apply
```

**That's it!** Terraform will:
1. Create the EC2 instance
2. Assign the Elastic IP
3. Configure security groups
4. Set up DNS records
5. Clone your repository
6. Install dependencies
7. Run migrations
8. Start the application
9. Configure SSL/HTTPS

After ~5 minutes, your site will be live at `https://powers.land`!

## Verify Deployment

```bash
# Check outputs
terraform output

# Test the site
curl -I https://powers.land
```

## Updating the Application

### Method 1: GitHub Actions (Recommended)
Just push to `main` branch - GitHub Actions will auto-deploy.

### Method 2: Manual SSH
```bash
ssh -i ~/.ssh/powers-land-keypair.pem ubuntu@$(terraform output -raw elastic_ip)
sudo systemctl restart powers-land
```

### Method 3: Terraform Taint (Nuclear Option)
```bash
terraform taint null_resource.configure_ssl
terraform apply
```

## Destroying Infrastructure

**⚠️ WARNING: This will delete everything!**

```bash
terraform destroy
```

DNS records and the database will be deleted. Back up data first if needed.

## Recreating from Scratch

If you need to rebuild everything:

```bash
# Destroy old infrastructure
terraform destroy

# Generate new secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Update terraform.tfvars with new secret
# Update allowed_ssh_cidr if IP changed

# Deploy
terraform apply
```

The user-data script will:
- Clone the latest code from GitHub
- Install all dependencies
- Run migrations
- Start services
- Configure SSL

## Troubleshooting

### Check User-Data Script Logs
```bash
ssh -i ~/.ssh/powers-land-keypair.pem ubuntu@$(terraform output -raw elastic_ip)
sudo tail -f /var/log/user-data.log
```

### Check Application Logs
```bash
ssh -i ~/.ssh/powers-land-keypair.pem ubuntu@$(terraform output -raw elastic_ip)
sudo journalctl -u powers-land -f
```

### Check Nginx Logs
```bash
ssh -i ~/.ssh/powers-land-keypair.pem ubuntu@$(terraform output -raw elastic_ip)
sudo tail -f /var/log/nginx/error.log
```

### SSL Certificate Issues
If SSL fails to configure automatically:

```bash
ssh -i ~/.ssh/powers-land-keypair.pem ubuntu@$(terraform output -raw elastic_ip)
sudo certbot --nginx -d powers.land -d www.powers.land --non-interactive --agree-tos --email YOUR_EMAIL --redirect
```

### DNS Not Resolving
DNS propagation can take 5-15 minutes. Check with:

```bash
dig +short powers.land
nslookup powers.land
```

## File Descriptions

- **main.tf** - Main infrastructure (EC2, EIP, DNS, SSL)
- **variables.tf** - Input variables
- **outputs.tf** - Exported values
- **terraform.tfvars** - Your configuration (gitignored)
- **terraform.tfvars.example** - Template for terraform.tfvars
- **user-data.sh** - Bootstrap script that runs on instance creation

## Cost Estimate

- **EC2 t3.micro**: ~$7.50/month
- **Elastic IP**: Free (when attached to running instance)
- **Route 53 Hosted Zone**: $0.50/month
- **Data Transfer**: ~$1-2/month (low traffic)
- **SSL Certificate**: Free (Let's Encrypt)

**Total**: ~$9-10/month

## Security Notes

- SSH restricted to your IP only
- HTTPS enforced with redirects
- Automatic security updates enabled
- Secret key stored in Terraform state (encrypted at rest)
- `.env` file has 640 permissions

## Advanced: Migrating to Larger Instance

```bash
# Update terraform.tfvars
instance_type = "t3.small"

# Apply changes
terraform apply

# Terraform will create new instance and migrate Elastic IP
# SSL certificate will be reconfigured automatically
```

## Terraform State

Terraform state is stored locally in `terraform.tfstate`. This file contains:
- Resource IDs
- Sensitive values (secret keys)

**⚠️ Never commit terraform.tfstate to git!**

For team collaboration, consider using Terraform Cloud or S3 backend:

```hcl
terraform {
  backend "s3" {
    bucket = "powers-land-terraform-state"
    key    = "prod/terraform.tfstate"
    region = "us-east-1"
  }
}
```

## Adding More Automation

You can extend this further:

- **CloudWatch Alarms**: Monitor instance health
- **Auto Scaling**: Add load balancer for high traffic
- **RDS**: Migrate from SQLite to PostgreSQL
- **S3**: Store static files in S3
- **CloudFront**: CDN for faster global delivery

See the [AWS Terraform Provider docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs) for more resources.
