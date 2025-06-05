#!/bin/bash

# Echo MCP HTTPS Server - One-Click Production Deployment
# Usage: curl -sSL https://raw.githubusercontent.com/Vladikasik/mcm-https/main/deploy/one-click-deploy.sh | sudo bash

set -e

# Configuration for memory.aynshteyn.dev
DOMAIN="memory.aynshteyn.dev"
PROJECT_NAME="echo-mcp-server"
INSTALL_DIR="/opt/$PROJECT_NAME"
SERVICE_USER="www-data"
SSL_CERTFILE="/home/aynshteyn.dev-ssl-bundle/domain.cert.pem"
SSL_KEYFILE="/home/aynshteyn.dev-ssl-bundle/private.key.pem"
REPO_URL="https://github.com/Vladikasik/mcm-https.git"

echo "🚀 Echo MCP HTTPS Server - One-Click Deployment"
echo "================================================="
echo "🌐 Domain: $DOMAIN"
echo "📁 Install Dir: $INSTALL_DIR"  
echo "🔐 SSL Cert: $SSL_CERTFILE"
echo "🔑 SSL Key: $SSL_KEYFILE"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root" 
   echo "Run: curl -sSL https://raw.githubusercontent.com/Vladikasik/mcm-https/main/deploy/one-click-deploy.sh | sudo bash"
   exit 1
fi

# Install system dependencies
echo "📦 Installing system dependencies..."
apt-get update -qq
apt-get install -y python3 python3-pip python3-venv git curl

# Create installation directory and clone project
echo "📁 Setting up project..."
rm -rf $INSTALL_DIR
mkdir -p $INSTALL_DIR
cd $INSTALL_DIR
git clone $REPO_URL .

# Create Python virtual environment
echo "🐍 Setting up Python environment..."
python3 -m venv env
source env/bin/activate
pip install --upgrade pip -q
pip install -e . -q

# Create production environment file
echo "⚙️ Creating production configuration..."
cat > .env << EOF
ENV=production
HOST=0.0.0.0
PORT=8443
SSL_CERTFILE=$SSL_CERTFILE
SSL_KEYFILE=$SSL_KEYFILE
SERVER_NAME=EchoMCPServer
LOG_LEVEL=info
WORKERS=1
EOF

# Set proper ownership
echo "🔐 Setting permissions..."
chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR
chmod 755 $INSTALL_DIR
chmod 600 $INSTALL_DIR/.env

# Install and start systemd service
echo "🔧 Installing systemd service..."
cp deploy/systemd/echo-mcp-server.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable echo-mcp-server
systemctl start echo-mcp-server

# Configure Caddy
echo "🌐 Setting up Caddy reverse proxy..."
cat > /etc/caddy/Caddyfile << EOF
# Echo MCP Server - Caddy Configuration
$DOMAIN {
    reverse_proxy 127.0.0.1:8443 {
        transport http {
            tls_insecure_skip_verify
        }
    }
    
    # Security headers
    header {
        X-Frame-Options DENY
        X-Content-Type-Options nosniff
        X-XSS-Protection "1; mode=block"
        Referrer-Policy "strict-origin-when-cross-origin"
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
    }
    
    # Rate limiting
    rate_limit {
        zone static_ip {
            key {remote_host}
            window 1m
            events 60
        }
    }
}

# Direct access on port 8443
$DOMAIN:8443 {
    reverse_proxy 127.0.0.1:8443 {
        transport http {
            tls_insecure_skip_verify
        }
    }
}
EOF

# Restart Caddy
echo "🔄 Restarting Caddy..."
systemctl restart caddy

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 5

# Verify deployment
echo "✅ Verifying deployment..."
if systemctl is-active --quiet echo-mcp-server; then
    echo "✓ Echo MCP Server is running"
else
    echo "❌ Echo MCP Server failed to start"
    systemctl status echo-mcp-server
    exit 1
fi

if systemctl is-active --quiet caddy; then
    echo "✓ Caddy is running"
else
    echo "❌ Caddy failed to start"
    systemctl status caddy
    exit 1
fi

# Test endpoints
echo "🧪 Testing endpoints..."
if curl -k -s https://127.0.0.1:8443/mcp > /dev/null; then
    echo "✓ Direct HTTPS endpoint working"
else
    echo "⚠️  Direct HTTPS endpoint not responding"
fi

if curl -s https://$DOMAIN/mcp > /dev/null; then
    echo "✓ Caddy proxy endpoint working"
else
    echo "⚠️  Caddy proxy endpoint not responding"
fi

echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "======================================"
echo "🌐 MCP Server URL: https://$DOMAIN/mcp"
echo "🔗 Direct Access:  https://$DOMAIN:8443/mcp"
echo ""
echo "📊 Service Status:"
echo "sudo systemctl status echo-mcp-server"
echo "sudo journalctl -u echo-mcp-server -f"
echo ""
echo "🔧 Configuration:"
echo "Edit: $INSTALL_DIR/.env"
echo "Logs: sudo journalctl -u echo-mcp-server -f"
echo ""
echo "🧪 Test with MCP Inspector:"
echo "npx @modelcontextprotocol/inspector"
echo "Connect to: https://$DOMAIN/mcp"
echo ""
echo "✨ Your MCP server is now live!"
echo "======================================" 