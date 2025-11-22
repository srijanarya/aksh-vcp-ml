#!/bin/bash
# Configure Nginx to proxy dashboard on port 80

SERVER_IP="13.200.109.29"
USER="ubuntu"
KEY_PATH="~/.ssh/lightsail.pem"

echo "🌐 Configuring Nginx for Dashboard..."

ssh -i $KEY_PATH $USER@$SERVER_IP << 'EOF'
    # Install nginx if not present
    sudo apt-get install -y nginx -qq
    
    # Create nginx config for dashboard
    sudo tee /etc/nginx/sites-available/dashboard > /dev/null << 'NGINX_CONF'
server {
    listen 80;
    server_name _;
    
    # Dashboard on root path
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX_CONF

    # Enable the site
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo ln -sf /etc/nginx/sites-available/dashboard /etc/nginx/sites-enabled/
    
    # Test and reload nginx
    sudo nginx -t
    sudo systemctl reload nginx
    sudo systemctl status nginx --no-pager
    
    echo ""
    echo "✅ Nginx configured!"
    echo "📊 Dashboard now accessible at: http://13.200.109.29"
EOF

echo ""
echo "🎉 Configuration complete!"
echo "📊 Access Dashboard: http://$SERVER_IP"
