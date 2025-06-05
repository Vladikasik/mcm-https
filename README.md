# Echo MCP HTTPS Server

A production-ready HTTPS MCP (Model Context Protocol) server with an echo tool that supports both development and production environments.

## Features

- 🔧 **Simple Echo Tool**: Returns input text unchanged
- 🔒 **HTTPS Support**: Built-in SSL/TLS support with real certificates
- 🛠️ **Development Mode**: Auto-generates self-signed certificates for local development
- 🚀 **Production Ready**: Support for SSL certificates and public deployment
- 🔄 **Environment Detection**: Automatically detects development vs production mode
- ⚙️ **Configurable**: Command-line arguments and environment variables
- 📦 **Easy Deployment**: Automated deployment scripts and systemd integration
- 🔍 **MCP Inspector Ready**: Built-in solutions for HTTPS certificate issues
- 🔐 **Security Features**: Rate limiting, IP whitelisting, reverse proxy support

## Quick Start

### Production Deployment (Public Server)

**1. Automated Installation:**
```bash
# Copy project to server
scp -r echo-mcp-server/ user@your-server:/tmp/

# Run automated deployment
ssh user@your-server
sudo /tmp/echo-mcp-server/deploy/install.sh your-domain.com
```

**2. Configure SSL Certificates:**
```bash
# Edit environment file
sudo nano /opt/echo-mcp-server/.env

# Set your certificate paths:
SSL_CERTFILE=/home/aynshteyn.dev-ssl-bundle/domain.cert.pem
SSL_KEYFILE=/home/aynshteyn.dev-ssl-bundle/private.key.pem
ENV=production
HOST=0.0.0.0
PORT=8443
```

**3. Start the Service:**
```bash
sudo systemctl start echo-mcp-server
sudo systemctl status echo-mcp-server
```

**4. Test Deployment:**
```bash
curl -k https://your-domain.com:8443/mcp
```

### For MCP Inspector Testing (Development)

**Option 1: HTTP Mode (Easiest)**
```bash
# Install dependencies
pip install -e .

# Run in HTTP mode - works immediately with MCP Inspector
python main.py --no-ssl --port 8080
```
Connect MCP Inspector to: `http://127.0.0.1:8080/mcp`

**Option 2: HTTPS with Auto-Trust**
```bash
# Run with automatic certificate installation (requires sudo)
python main.py --trust-cert
```
Connect MCP Inspector to: `https://127.0.0.1:8443/mcp`

### Development Mode (Default)

```bash
# Install dependencies
pip install -e .

# Run in development mode (auto-generates self-signed certificate)
python main.py
```

The server will:
- Auto-generate a self-signed certificate for `127.0.0.1`
- Start on `https://127.0.0.1:8443/mcp`
- Show a security warning (normal for self-signed certificates)

## Production Deployment Guide

### Prerequisites

- Ubuntu/Debian server with root access
- Domain name pointing to your server
- SSL certificate files (Let's Encrypt recommended)
- Python 3.9+

### Manual Production Setup

**1. Install Dependencies:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx openssl
```

**2. Create Installation Directory:**
```bash
sudo mkdir -p /opt/echo-mcp-server
cd /opt/echo-mcp-server
```

**3. Copy Project Files:**
```bash
# Clone from git or copy files
git clone https://github.com/Vladikasik/mcm-https.git .
```

**4. Setup Python Environment:**
```bash
sudo python3 -m venv env
source env/bin/activate
sudo pip install -e .
```

**5. Configure Environment:**
```bash
# Copy and edit environment file
sudo cp config.env.example .env
sudo nano .env
```

Set your production configuration:
```env
ENV=production
HOST=0.0.0.0
PORT=8443
SSL_CERTFILE=/home/aynshteyn.dev-ssl-bundle/domain.cert.pem
SSL_KEYFILE=/home/aynshteyn.dev-ssl-bundle/private.key.pem
SERVER_NAME=EchoMCPServer
LOG_LEVEL=info
```

**6. Install Systemd Service:**
```bash
sudo cp deploy/systemd/echo-mcp-server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable echo-mcp-server
sudo systemctl start echo-mcp-server
```

**7. Configure Nginx (Optional but Recommended):**
```bash
sudo cp deploy/nginx/echo-mcp-server.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/echo-mcp-server.conf /etc/nginx/sites-enabled/

# Edit nginx config with your domain and SSL paths
sudo nano /etc/nginx/sites-available/echo-mcp-server.conf

# Test and restart nginx
sudo nginx -t
sudo systemctl restart nginx
```

### Security Configuration

**1. IP Whitelisting:**
Update nginx configuration with your allowed IPs:
```nginx
# In /etc/nginx/sites-available/echo-mcp-server.conf
location /mcp {
    allow YOUR_WHITELISTED_IP;
    allow 192.168.1.0/24;  # Your network
    deny all;
    # ... rest of config
}
```

**2. Firewall Setup:**
```bash
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8443/tcp  # Direct MCP access
sudo ufw enable
```

**3. SSL Certificate Setup (Let's Encrypt):**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### Monitoring and Maintenance

**Check Service Status:**
```bash
sudo systemctl status echo-mcp-server
sudo journalctl -u echo-mcp-server -f
```

**View Logs:**
```bash
# Service logs
sudo journalctl -u echo-mcp-server --since today

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

**Update Deployment:**
```bash
cd /opt/echo-mcp-server
sudo git pull
sudo systemctl restart echo-mcp-server
```

## MCP Inspector Connectivity

### The Problem
MCP Inspector may not connect to HTTPS servers with self-signed certificates due to certificate trust issues. **This is a Node.js-specific problem** - installing certificates to your system keychain doesn't make them available to Node.js applications.

### 🎯 **Best Solution: Node.js SSL Bypass**

**For HTTPS servers with self-signed certificates:**
```bash
NODE_TLS_REJECT_UNAUTHORIZED=0 npx @modelcontextprotocol/inspector
```

This is the **easiest and most effective solution** for MCP Inspector connectivity issues.

### Alternative Solutions

#### 1. HTTP Mode (Recommended for Testing)
```bash
python main.py --no-ssl --port 8080
# Connect to: http://127.0.0.1:8080/mcp
```
✅ **Pros**: Works immediately, no certificate issues  
❌ **Cons**: No encryption (fine for local testing)

#### 2. Node.js Certificate Path
```bash
NODE_EXTRA_CA_CERTS=/path/to/cert.pem npx @modelcontextprotocol/inspector
# Connect to: https://127.0.0.1:8443/mcp
```
✅ **Pros**: Proper certificate validation  
❌ **Cons**: Requires path to certificate file

#### 3. Auto-Trust Certificate
```bash
python main.py --trust-cert
# Connect to: https://127.0.0.1:8443/mcp
```
✅ **Pros**: HTTPS encryption, automatic setup  
❌ **Cons**: Requires sudo permissions, doesn't help Node.js apps

#### 4. Manual Certificate Trust

**macOS:**
```bash
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain .ssl/cert.pem
```

**Linux:**
```bash
sudo cp .ssl/cert.pem /usr/local/share/ca-certificates/mcp-dev.crt
sudo update-ca-certificates
```

**Windows:**
1. Open `certlm.msc`
2. Navigate to "Trusted Root Certification Authorities"
3. Import `.ssl/cert.pem`

**Note**: Manual trust installation affects browsers but **not Node.js applications**.

#### 5. Browser Bypass Method
1. Open `https://127.0.0.1:8443/mcp` in your browser
2. Click "Advanced" → "Proceed to 127.0.0.1"
3. Now try MCP Inspector (may inherit browser's certificate acceptance)

### Quick Test Script

Use the included test script for easy MCP Inspector connection:
```bash
./test_mcp_inspector.sh
```

This script automatically detects your server type and runs MCP Inspector with the correct settings.

## Installation

### Using pip

```bash
# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

### Using uv (Recommended)

```bash
# Install dependencies
uv sync

# Run the server
uv run python main.py
```

## Usage

### Command Line Interface

```bash
# Basic usage
python -m echo_mcp_server [OPTIONS]

# Get help
python -m echo_mcp_server --help
```

#### Options

**Server Configuration:**
- `--host HOST`: Host to bind to (default: 127.0.0.1, production: 0.0.0.0)
- `--port PORT`: Port to bind to (default: 8443 for HTTPS, 8080 for HTTP)
- `--name NAME`: Name for the MCP server (default: EchoHTTPS)

**SSL/TLS Configuration:**
- `--cert-file PATH`: Path to SSL certificate file (can be set via SSL_CERTFILE env var)
- `--key-file PATH`: Path to SSL private key file (can be set via SSL_KEYFILE env var)
- `--no-ssl`: Disable SSL and run in HTTP mode (recommended for MCP Inspector testing)
- `--trust-cert`: Automatically install self-signed certificate to system trust store (requires sudo)

**Environment Mode:**
- `--development`: Force development mode (auto-generates certificates)
- `--production`: Force production mode (requires provided certificates or env vars)

**Uvicorn Options:**
- `--workers N`: Number of worker processes (default: 1)
- `--reload`: Enable auto-reload for development
- `--log-level LEVEL`: Log level (critical, error, warning, info, debug, trace)

### Environment Variables

Create a `.env` file in the project root:

```env
# Environment mode
ENV=production

# Server configuration
HOST=0.0.0.0
PORT=8443

# SSL configuration (for production)
SSL_CERTFILE=/home/aynshteyn.dev-ssl-bundle/domain.cert.pem
SSL_KEYFILE=/home/aynshteyn.dev-ssl-bundle/private.key.pem

# Optional settings
SERVER_NAME=EchoMCPServer
LOG_LEVEL=info
WORKERS=1
```

### Examples

```bash
# Development with auto-generated certificates
python main.py

# MCP Inspector testing (HTTP - easiest)
python main.py --no-ssl

# MCP Inspector testing (HTTPS with Node.js bypass)
python main.py
NODE_TLS_REJECT_UNAUTHORIZED=0 npx @modelcontextprotocol/inspector

# MCP Inspector testing (HTTPS with auto-trust)
python main.py --trust-cert

# Production with environment variables
python -m echo_mcp_server --production

# Production with explicit certificates
python -m echo_mcp_server \
  --production \
  --cert-file /path/to/cert.pem \
  --key-file /path/to/key.pem \
  --host 0.0.0.0 \
  --port 8443

# Development with auto-reload
python main.py --reload --log-level debug
```

## MCP Tool

The server provides one simple tool:

### `echo`

**Description**: Echo tool - returns the input text unchanged

**Parameters**:
- `text` (string): The text to echo back

**Returns**: The same text that was provided as input

## SSL Certificates

### Development Mode

In development mode, the server automatically generates self-signed certificates for `127.0.0.1` and `localhost`. These certificates:

- Are stored in the `.ssl/` directory
- Are valid for 365 days
- Include Subject Alternative Names for localhost and 127.0.0.1
- Will cause browser security warnings (this is normal)

### Production Mode

For production, you should use certificates from a trusted Certificate Authority (CA):

#### Let's Encrypt (Recommended)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com

# Certificates will be at:
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem
```

#### Self-Signed for Production

```bash
# Generate production self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

## Testing the Server

### Using curl

```bash
# Test HTTPS endpoint (ignore self-signed certificate warning)
curl -k https://127.0.0.1:8443/mcp

# Test HTTP endpoint
curl http://127.0.0.1:8080/mcp

# Test production deployment
curl -k https://your-domain.com:8443/mcp
```

### Using MCP Inspector

The server is compatible with any MCP client. Connect to:
- **HTTP (Recommended for testing)**: `http://127.0.0.1:8080/mcp`
- **HTTPS**: `https://127.0.0.1:8443/mcp`
- **Production**: `https://your-domain.com:8443/mcp`

### Testing the Echo Tool

Use any MCP client to call the `echo` tool with a text parameter.

## Project Structure

```
echo-mcp-https-server/
├── echo_mcp_server/
│   ├── __init__.py          # Package initialization
│   ├── __main__.py          # Module entry point
│   ├── main.py              # CLI and main function
│   ├── server.py            # MCP server implementation
│   └── ssl_utils.py         # SSL certificate utilities
├── deploy/
│   ├── install.sh           # Automated deployment script
│   ├── systemd/
│   │   └── echo-mcp-server.service  # Systemd service file
│   └── nginx/
│       └── echo-mcp-server.conf     # Nginx configuration
├── main.py                  # Simple wrapper script
├── test_mcp_inspector.sh    # MCP Inspector test helper
├── config.env.example       # Example environment configuration
├── pyproject.toml           # Project configuration
├── README.md                # This file
└── .ssl/                    # Generated certificates (created automatically)
    ├── cert.pem
    └── key.pem
```

## Development

### Setting up for Development

```bash
# Clone the repository
git clone https://github.com/Vladikasik/mcm-https.git
cd mcm-https

# Install in development mode
pip install -e ".[dev]"

# Run tests (if available)
pytest

# Run with auto-reload
python main.py --reload --log-level debug
```

### Code Formatting

```bash
# Format code
black echo_mcp_server/

# Lint code
ruff check echo_mcp_server/
```

## Troubleshooting

### MCP Inspector Connection Issues

**Problem**: MCP Inspector won't connect to HTTPS server

**Solutions** (in order of effectiveness):
1. **Use Node.js SSL bypass**: `NODE_TLS_REJECT_UNAUTHORIZED=0 npx @modelcontextprotocol/inspector`
2. Use HTTP mode: `python main.py --no-ssl`
3. Use Node.js cert path: `NODE_EXTRA_CA_CERTS=/path/to/cert.pem npx @modelcontextprotocol/inspector`
4. Use auto-trust: `python main.py --trust-cert`
5. Manually trust the certificate (see instructions above)
6. Use browser bypass method

### Production Issues

1. **Service won't start**
   ```bash
   sudo journalctl -u echo-mcp-server -f
   # Check SSL certificate paths in .env file
   ```

2. **Permission denied on port 443**
   ```bash
   # Use CAP_NET_BIND_SERVICE capability (already in systemd service)
   # Or run on higher port (8443) with nginx proxy
   ```

3. **SSL certificate errors**
   ```bash
   # Verify certificate files exist and are readable
   sudo ls -la /path/to/certificates/
   # Check certificate validity
   openssl x509 -in /path/to/cert.pem -text -noout
   ```

4. **Nginx proxy errors**
   ```bash
   sudo nginx -t  # Test configuration
   sudo tail -f /var/log/nginx/error.log
   ```

### Common Issues

1. **Port already in use**
   ```bash
   # Use a different port
   python main.py --port 9443
   ```

2. **Certificate errors**
   ```bash
   # Delete and regenerate certificates
   rm -rf .ssl/
   python main.py
   ```

3. **Browser warnings for self-signed certificates**
   - This is normal for development
   - Click "Advanced" → "Proceed to 127.0.0.1" (or similar)
   - For production, use certificates from a trusted CA

4. **Node.js applications ignore system certificates**
   - This is expected behavior - Node.js has its own certificate validation
   - Use `NODE_TLS_REJECT_UNAUTHORIZED=0` for quick testing
   - Use `NODE_EXTRA_CA_CERTS` for proper certificate validation

### Logs

Enable debug logging to see detailed information:

```bash
# Development
python main.py --log-level debug

# Production
sudo systemctl status echo-mcp-server
sudo journalctl -u echo-mcp-server -f
```

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions:
- GitHub Issues: https://github.com/Vladikasik/mcm-https/issues
- Documentation: See README.md sections above 