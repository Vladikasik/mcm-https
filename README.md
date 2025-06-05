# Echo MCP HTTPS Server

A simple HTTPS MCP (Model Context Protocol) server with an echo tool that supports both development and production environments.

## Features

- 🔧 **Simple Echo Tool**: Returns input text unchanged
- 🔒 **HTTPS Support**: Built-in SSL/TLS support
- 🛠️ **Development Mode**: Auto-generates self-signed certificates for local development
- 🚀 **Production Ready**: Support for provided SSL certificates
- 🔄 **Environment Detection**: Automatically detects development vs production mode
- ⚙️ **Configurable**: Command-line arguments and environment variables
- 📦 **Easy Deployment**: Simple setup and deployment
- 🔍 **MCP Inspector Ready**: Built-in solutions for HTTPS certificate issues

## Quick Start

### For MCP Inspector Testing (Recommended)

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

### Production Mode

```bash
# With your own SSL certificates
python -m echo_mcp_server \
  --production \
  --cert-file /path/to/cert.pem \
  --key-file /path/to/key.pem \
  --host 0.0.0.0 \
  --port 443
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
- `--host HOST`: Host to bind to (default: 127.0.0.1)
- `--port PORT`: Port to bind to (default: 8443 for HTTPS, 8080 for HTTP)
- `--name NAME`: Name for the MCP server (default: EchoHTTPS)

**SSL/TLS Configuration:**
- `--cert-file PATH`: Path to SSL certificate file
- `--key-file PATH`: Path to SSL private key file
- `--no-ssl`: Disable SSL and run in HTTP mode (recommended for MCP Inspector testing)
- `--trust-cert`: Automatically install self-signed certificate to system trust store (requires sudo)

**Environment Mode:**
- `--development`: Force development mode (auto-generates certificates)
- `--production`: Force production mode (requires provided certificates)

**Uvicorn Options:**
- `--workers N`: Number of worker processes (default: 1)
- `--reload`: Enable auto-reload for development
- `--log-level LEVEL`: Log level (critical, error, warning, info, debug, trace)

### Environment Variables

Create a `.env` file in the project root:

```env
# Environment mode
ENV=development

# Server configuration
HOST=127.0.0.1
PORT=8443

# SSL configuration (for production)
SSL_CERT_FILE=/path/to/cert.pem
SSL_KEY_FILE=/path/to/key.pem
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

# Development on all interfaces
python main.py --host 0.0.0.0

# Production with Let's Encrypt certificates
python -m echo_mcp_server \
  --production \
  --cert-file /etc/letsencrypt/live/yourdomain.com/fullchain.pem \
  --key-file /etc/letsencrypt/live/yourdomain.com/privkey.pem \
  --host 0.0.0.0 \
  --port 443

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
sudo apt install certbot

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Use the certificates
python -m echo_mcp_server \
  --production \
  --cert-file /etc/letsencrypt/live/yourdomain.com/fullchain.pem \
  --key-file /etc/letsencrypt/live/yourdomain.com/privkey.pem
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
```

### Using MCP Inspector

The server is compatible with any MCP client. Connect to:
- **HTTP (Recommended for testing)**: `http://127.0.0.1:8080/mcp`
- **HTTPS**: `https://127.0.0.1:8443/mcp`

### Testing the Echo Tool

Use any MCP client to call the `echo` tool with a text parameter.

## Deployment

### Docker (Optional)

Create a `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .

RUN pip install -e .

EXPOSE 8443

CMD ["python", "-m", "echo_mcp_server", "--host", "0.0.0.0"]
```

### Systemd Service (Linux)

Create `/etc/systemd/system/echo-mcp.service`:

```ini
[Unit]
Description=Echo MCP HTTPS Server
After=network.target

[Service]
Type=exec
User=your-user
WorkingDirectory=/path/to/echo-mcp-server
Environment=ENV=production
ExecStart=/usr/bin/python -m echo_mcp_server --production --host 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

## Project Structure

```
echo-mcp-https-server/
├── echo_mcp_server/
│   ├── __init__.py          # Package initialization
│   ├── __main__.py          # Module entry point
│   ├── main.py              # CLI and main function
│   ├── server.py            # MCP server implementation
│   └── ssl_utils.py         # SSL certificate utilities
├── main.py                  # Simple wrapper script
├── test_mcp_inspector.sh    # MCP Inspector test helper
├── pyproject.toml           # Project configuration
├── README.md                # This file
└── .ssl/                    # Generated certificates (created automatically)
    ├── cert.pem
    └── key.pem
```

## Development

### Setting up for Development

```bash
# Clone/download the project
git clone <repository>
cd echo-mcp-https-server

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

### Common Issues

1. **Port already in use**
   ```bash
   # Use a different port
   python main.py --port 9443
   ```

2. **Permission denied on port 443**
   ```bash
   # Run with sudo or use a higher port
   sudo python -m echo_mcp_server --port 443
   # Or use port 8443
   python main.py --port 8443
   ```

3. **Certificate errors**
   ```bash
   # Delete and regenerate certificates
   rm -rf .ssl/
   python main.py
   ```

4. **Browser warnings for self-signed certificates**
   - This is normal for development
   - Click "Advanced" → "Proceed to 127.0.0.1" (or similar)
   - For production, use certificates from a trusted CA

5. **`sudo` required for `--trust-cert`**
   - This is normal - installing certificates requires admin privileges
   - Alternative: use `--no-ssl` for testing

6. **Node.js applications ignore system certificates**
   - This is expected behavior - Node.js has its own certificate validation
   - Use `NODE_TLS_REJECT_UNAUTHORIZED=0` for quick testing
   - Use `NODE_EXTRA_CA_CERTS` for proper certificate validation

### Logs

Enable debug logging to see detailed information:

```bash
python main.py --log-level debug
```

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request 