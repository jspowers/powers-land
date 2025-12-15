#!/bin/bash
set -e

# Update system
apt-get update
apt-get upgrade -y

# Install dependencies
apt-get install -y python3.11 python3.11-venv python3-pip nginx git certbot python3-certbot-nginx

# Enable automatic security updates
apt-get install -y unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades

# Create application user
useradd -m -s /bin/bash powers-land
usermod -aG www-data powers-land

# Create application directory
mkdir -p /var/www/powers-land
chown powers-land:www-data /var/www/powers-land

# Create .env file
cat > /var/www/powers-land/.env << EOF
SECRET_KEY=${app_secret_key}
FLASK_ENV=production
DATABASE_URL=sqlite:////var/www/powers-land/instance/powers-land.db
DOMAIN_NAME=${domain_name}
EOF

chown powers-land:www-data /var/www/powers-land/.env
chmod 640 /var/www/powers-land/.env

# Create instance directory for database
mkdir -p /var/www/powers-land/instance
chown powers-land:www-data /var/www/powers-land/instance

# Create Gunicorn systemd service
cat > /etc/systemd/system/powers-land.service << 'EOF'
[Unit]
Description=Gunicorn instance for powers.land
After=network.target

[Service]
User=powers-land
Group=www-data
WorkingDirectory=/var/www/powers-land
Environment="PATH=/var/www/powers-land/venv/bin"
EnvironmentFile=/var/www/powers-land/.env
ExecStart=/var/www/powers-land/venv/bin/gunicorn --workers 3 --bind unix:/run/powers-land.sock wsgi:application

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
cat > /etc/nginx/sites-available/powers-land << 'NGINXEOF'
server {
    listen 80;
    server_name ${domain_name} www.${domain_name};

    location / {
        proxy_pass http://unix:/run/powers-land.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /var/www/powers-land/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    client_max_body_size 10M;
}
NGINXEOF

# Enable Nginx site
ln -sf /etc/nginx/sites-available/powers-land /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t

# Reload systemd
systemctl daemon-reload

# Start and enable Nginx
systemctl restart nginx
systemctl enable nginx

echo "User data script completed. Application setup ready for code deployment."
echo "Next steps:"
echo "1. SSH into instance and clone your repository to /var/www/powers-land"
echo "2. Create virtual environment and install dependencies"
echo "3. Run database migrations"
echo "4. Enable and start the powers-land service"
echo "5. Configure SSL with: certbot --nginx -d ${domain_name} -d www.${domain_name}"
