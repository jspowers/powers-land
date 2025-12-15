#!/bin/bash
set -e

# Log everything
exec > >(tee -a /var/log/user-data.log)
exec 2>&1

echo "Starting user-data script at $(date)"

# Update system
apt-get update
apt-get upgrade -y

# Install dependencies (Ubuntu 24.04 uses python3, not python3.11)
apt-get install -y python3 python3-venv python3-pip python3-dev build-essential \
    nginx git certbot python3-certbot-nginx unattended-upgrades

# Enable automatic security updates
dpkg-reconfigure -plow unattended-upgrades

# Create application user
if ! id -u powers-land > /dev/null 2>&1; then
    useradd -m -s /bin/bash powers-land
    usermod -aG www-data powers-land
fi

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

# Clone repository as powers-land user
sudo -u powers-land bash << 'USEREOF'
cd /var/www/powers-land
if [ ! -d ".git" ]; then
    git clone https://github.com/jspowers/powers-land.git /tmp/repo-temp
    rsync -av --exclude=.env /tmp/repo-temp/ /var/www/powers-land/
    rm -rf /tmp/repo-temp
fi

# Create virtual environment
python3 -m venv venv

# Install dependencies
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations
FLASK_APP=wsgi.py flask db upgrade
USEREOF

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
RuntimeDirectory=powers-land
ExecStart=/var/www/powers-land/venv/bin/gunicorn --workers 3 --bind unix:/run/powers-land/powers-land.sock --umask 007 wsgi:application

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
cat > /etc/nginx/sites-available/powers-land << 'NGINXEOF'
server {
    listen 80;
    server_name ${domain_name} www.${domain_name};

    location / {
        proxy_pass http://unix:/run/powers-land/powers-land.sock;
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

# Reload systemd and start services
systemctl daemon-reload
systemctl enable powers-land
systemctl start powers-land
systemctl restart nginx
systemctl enable nginx

echo "User data script completed successfully at $(date)"
echo "Application is running on HTTP. Configure SSL manually with:"
echo "sudo certbot --nginx -d ${domain_name} -d www.${domain_name} --non-interactive --agree-tos --email YOUR_EMAIL --redirect"
