# Memory MCP Server

**Production-ready SSE MCP server specifically designed for Anthropic API compatibility.**

## ✅ Working with Anthropic API

This server uses **SSE (Server-Sent Events)** transport, which is **required** by Anthropic's MCP connector API.

## Features

- **🔄 SSE Transport**: Fully compatible with Anthropic's MCP API requirements
- **🔒 HTTPS/TLS**: Production-ready SSL/TLS support for domain deployment
- **🛠️ Multiple Tools**: Echo, memory storage, and memory retrieval tools
- **🌐 Domain Ready**: Configured for `memory.aynshteyn.dev`
- **⚡ Clean Implementation**: Minimal, focused codebase without unnecessary complexity

## Endpoints

- **SSE (Anthropic API)**: `https://memory.aynshteyn.dev/sse`
- **Health Check**: Available via root endpoint

## Tools Available

1. **echo**: Returns input text with "Echo: " prefix
2. **store_memory**: Store key-value pairs in memory
3. **get_memory**: Retrieve values from memory by key

## Quick Start

### Development Mode

```bash
# Clone and setup
git clone <repo>
cd memory-mcp-server
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
pip install -e .

# Run development server (generates self-signed certificates)
python main.py
```

### Production Mode

```bash
# Copy and edit configuration
cp config.env.example .env
# Edit .env with your SSL certificate paths

# Run production server
ENV=production python main.py
```

## Configuration

All configuration is done via environment variables (use `.env` file):

```bash
# Environment
ENV=production                           # or development

# Server
HOST=0.0.0.0                            # Bind to all interfaces
PORT=8443                               # HTTPS port (FastMCP uses defaults)
SERVER_NAME=MemoryMCP                   # Server name

# SSL Certificates (Production only)
SSL_CERTFILE=/path/to/domain.cert.pem   # SSL certificate
SSL_KEYFILE=/path/to/private.key.pem    # SSL private key

# Optional
LOG_LEVEL=info                          # Log level
DOMAIN=memory.aynshteyn.dev             # Domain name
```

## Testing with Anthropic API

```bash
curl https://api.anthropic.com/v1/messages \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: mcp-client-2025-04-04" \
  -d '{
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 1000,
    "messages": [{"role": "user", "content": "What tools do you have available?"}],
    "mcp_servers": [
        {
          "type": "url",
          "url": "https://memory.aynshteyn.dev/sse",
          "name": "memory"
        }
    ]
}'
```

## Testing Locally

### Development Testing

```bash
# Start the server
ENV=development python main.py

# Test SSE endpoint (should return event stream)
curl http://127.0.0.1:8000/sse
```

### MCP Inspector Testing

For testing with MCP Inspector, you'll need to use mcp-proxy or similar tools since the inspector typically expects Streamable HTTP, but our server is SSE-only for Anthropic compatibility.

## Production Deployment

### Manual Deployment

1. Copy files to server
2. Create `.env` with production settings
3. Install dependencies: `pip install -e .`
4. Run: `ENV=production python main.py`

### Systemd Service

```bash
# Copy service file
sudo cp deploy/systemd/echo-mcp-server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable echo-mcp-server
sudo systemctl start echo-mcp-server
```

### With Caddy Reverse Proxy

```bash
# Copy Caddyfile
sudo cp deploy/caddy/Caddyfile /etc/caddy/Caddyfile
sudo systemctl restart caddy
```

## Architecture

```
Anthropic API ──→ HTTPS ──→ memory.aynshteyn.dev/sse ──→ FastMCP (SSE)
```

## Why This Works with Anthropic

- **SSE Transport**: Anthropic requires Server-Sent Events transport (✅ Implemented)
- **Stateless**: Each request is independent, no persistent connections required
- **HTTPS**: Production-ready SSL/TLS with valid certificates
- **Proper Protocol**: Implements MCP specification correctly for SSE transport

## Key Differences from Previous Version

- **SSE-Only**: Simplified to focus only on Anthropic API compatibility
- **No Custom FastAPI**: Uses FastMCP's built-in SSE implementation
- **Default Ports**: FastMCP handles port configuration automatically
- **Cleaner Code**: Removed unnecessary complexity and mounting issues

## Troubleshooting

### Anthropic Connection Issues

1. **Check SSL certificates**: Ensure valid SSL certs for your domain
2. **Verify endpoint**: Use `/sse` endpoint specifically
3. **Check firewall**: Ensure port is accessible
4. **Test manually**: `curl https://memory.aynshteyn.dev/sse` should return SSE stream

### Common Issues

1. **FastMCP version**: Ensure you have the latest MCP SDK
2. **Environment variables**: Check your `.env` file configuration
3. **SSL setup**: Verify certificate paths and permissions

### Successful SSE Response

A working SSE endpoint should return:
```
HTTP/1.1 200 OK
content-type: text/event-stream; charset=utf-8

event: endpoint
data: /messages/?session_id=...

: ping - [timestamp]
```

## License

MIT 