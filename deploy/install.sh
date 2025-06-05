#!/bin/bash

# Echo MCP HTTPS Server - Production Deployment Script
# Usage: sudo ./deploy/install.sh [domain.com]

set -e

# Configuration
PROJECT_NAME="echo-mcp-server"
INSTALL_DIR="/opt/$PROJECT_NAME"
SERVICE_USER="www-data"
DOMAIN="${1:-memory.aynshteyn.dev}"

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
apt-get install -y python3 python3-pip python3-venv git curl

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
    echo "   SSL_CERTFILE=/home/aynshteyn.dev-ssl-bundle/domain.cert.pem"
    echo "   SSL_KEYFILE=/home/aynshteyn.dev-ssl-bundle/private.key.pem"
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

# Configure Caddy (if available)
if command -v caddy &> /dev/null; then
    echo "🌐 Setting up Caddy configuration..."
    cp deploy/caddy/Caddyfile /etc/caddy/
    
    # Update domain in Caddy config
    sed -i "s/memory.aynshteyn.dev/$DOMAIN/g" /etc/caddy/Caddyfile
    
    # Test Caddy configuration
    caddy validate --config /etc/caddy/Caddyfile && echo "✅ Caddy configuration is valid"
    
    echo "⚠️  Remember to restart Caddy: systemctl restart caddy"
else
    echo "⚠️  Caddy not found. Install Caddy for reverse proxy support."
    echo "   Visit: https://caddyserver.com/docs/install"
fi

echo ""
echo "✅ Installation completed!"
echo ""
echo "Next steps:"
echo "1. Edit $INSTALL_DIR/.env with your SSL certificate paths"
echo "2. Start the service: systemctl start echo-mcp-server"
echo "3. Check status: systemctl status echo-mcp-server"
echo "4. View logs: journalctl -u echo-mcp-server -f"
echo ""
echo "For Caddy setup:"
echo "1. Restart Caddy: systemctl restart caddy"
echo "2. Check Caddy status: systemctl status caddy"
echo ""
echo "Test your deployment:"
echo "curl -k https://$DOMAIN:8443/mcp"
echo "curl -k https://$DOMAIN/mcp"
echo "" 