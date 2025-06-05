#!/bin/bash

# Echo MCP HTTPS Server - Production Deployment Script
# Usage: sudo ./deploy/install.sh [domain.com]

set -e

# Configuration
PROJECT_NAME="echo-mcp-server"
INSTALL_DIR="/opt/$PROJECT_NAME"
SERVICE_USER="www-data"
DOMAIN="${1:-your-domain.com}"

echo "🚀 Echo MCP HTTPS Server - Production Deployment"
echo "================================================="
echo "Domain: $DOMAIN"
echo "Install Directory: $INSTALL_DIR"
echo "Service User: $SERVICE_USER"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root (use sudo)" 
   exit 1
fi

# Create installation directory
echo "📁 Creating installation directory..."
mkdir -p $INSTALL_DIR
cd $INSTALL_DIR

# Install system dependencies
echo "📦 Installing system dependencies..."
apt-get update
apt-get install -y python3 python3-pip python3-venv nginx openssl curl

# Create Python virtual environment
echo "🐍 Setting up Python virtual environment..."
python3 -m venv env
source env/bin/activate

# Clone or copy project files
if [ -d "/tmp/echo-mcp-server" ]; then
    echo "📋 Copying project files..."
    cp -r /tmp/echo-mcp-server/* .
elif [ ! -f "pyproject.toml" ]; then
    echo "❌ Project files not found. Please copy the project to $INSTALL_DIR first."
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -e .

# Set up environment file
echo "⚙️ Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp config.env.example .env
    echo "📝 Created .env file. Please edit it with your SSL certificate paths:"
    echo "   SSL_CERTFILE=/path/to/your/domain.cert.pem"
    echo "   SSL_KEYFILE=/path/to/your/private.key.pem"
fi

# Set proper ownership
echo "🔐 Setting file permissions..."
chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR
chmod 755 $INSTALL_DIR
chmod 600 $INSTALL_DIR/.env

# Install systemd service
echo "🔧 Installing systemd service..."
cp deploy/systemd/echo-mcp-server.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable echo-mcp-server

# Configure nginx (optional)
if command -v nginx &> /dev/null; then
    echo "🌐 Setting up nginx configuration..."
    cp deploy/nginx/echo-mcp-server.conf /etc/nginx/sites-available/
    
    # Update domain in nginx config
    sed -i "s/your-domain.com/$DOMAIN/g" /etc/nginx/sites-available/echo-mcp-server.conf
    
    # Create symlink if it doesn't exist
    if [ ! -L "/etc/nginx/sites-enabled/echo-mcp-server.conf" ]; then
        ln -s /etc/nginx/sites-available/echo-mcp-server.conf /etc/nginx/sites-enabled/
    fi
    
    # Test nginx configuration
    nginx -t && echo "✅ Nginx configuration is valid"
    
    echo "⚠️  Remember to:"
    echo "   1. Update SSL certificate paths in nginx config"
    echo "   2. Update IP whitelist in nginx config"
    echo "   3. Restart nginx: systemctl restart nginx"
fi

# Create SSL certificate directory (if needed)
SSL_DIR="/etc/ssl/private/$PROJECT_NAME"
mkdir -p $SSL_DIR
chown root:ssl-cert $SSL_DIR
chmod 750 $SSL_DIR

echo ""
echo "✅ Installation completed!"
echo ""
echo "Next steps:"
echo "1. Edit $INSTALL_DIR/.env with your SSL certificate paths"
echo "2. Start the service: systemctl start echo-mcp-server"
echo "3. Check status: systemctl status echo-mcp-server"
echo "4. View logs: journalctl -u echo-mcp-server -f"
echo ""
echo "For nginx setup:"
echo "1. Update /etc/nginx/sites-available/echo-mcp-server.conf"
echo "2. Set correct SSL certificate paths"
echo "3. Update IP whitelist"
echo "4. Restart nginx: systemctl restart nginx"
echo ""
echo "Test your deployment:"
echo "curl -k https://$DOMAIN:8443/mcp"
echo "" 