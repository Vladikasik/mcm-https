# Echo MCP HTTPS Server

A production-ready HTTPS MCP (Model Context Protocol) server with an echo tool.

## ✨ One-Click Production Deployment

Deploy to `memory.aynshteyn.dev` with a single command:

```bash
curl -sSL https://raw.githubusercontent.com/Vladikasik/mcm-https/main/deploy/one-click-deploy.sh | sudo bash
```

**That's it!** Your MCP server will be live at:
- 🌐 **Main URL**: `https://memory.aynshteyn.dev/mcp`
- 🔗 **Direct URL**: `https://memory.aynshteyn.dev:8443/mcp`

## Features

- 🔧 **Echo Tool**: Returns input text unchanged
- 🔒 **HTTPS Support**: Real SSL certificates with Caddy reverse proxy
- 🚀 **Production Ready**: Systemd service, security headers
- ⚡ **One-Click Deploy**: Fully automated setup
- 🔍 **MCP Inspector Compatible**: Works out of the box
- 🌐 **Open Access**: No IP restrictions (as requested)

## Development Mode

```bash
# Install dependencies
pip install -e .

# Run locally (HTTP mode - easiest for testing)
python main.py --no-ssl --port 8080
```

Connect MCP Inspector to: `http://127.0.0.1:8080/mcp`

**For HTTPS development:**
```bash
# Auto-generates self-signed certificate
python main.py

# If MCP Inspector has SSL issues, use Node.js bypass:
NODE_TLS_REJECT_UNAUTHORIZED=0 npx @modelcontextprotocol/inspector
```

## MCP Inspector Usage

**Production (works immediately):**
```bash
npx @modelcontextprotocol/inspector
# Connect to: https://memory.aynshteyn.dev/mcp
```

**Development HTTPS (if certificate issues):**
```bash
NODE_TLS_REJECT_UNAUTHORIZED=0 npx @modelcontextprotocol/inspector
# Connect to: https://127.0.0.1:8443/mcp
```

## Configuration

The server uses environment variables from `.env`:

```env
ENV=production
HOST=0.0.0.0
PORT=8443
SSL_CERTFILE=/home/aynshteyn.dev-ssl-bundle/domain.cert.pem
SSL_KEYFILE=/home/aynshteyn.dev-ssl-bundle/private.key.pem
```

## Rate Limiting (Optional)

The basic deployment doesn't include rate limiting. To add it, you need a custom Caddy build:

```bash
# Build Caddy with rate limiting plugin
xcaddy build --with github.com/mholt/caddy-ratelimit

# Then add to your Caddyfile:
rate_limit {
    zone default {
        key {remote_host}
        events 60
        window 1m
    }
}
```

## Monitoring

```bash
# Check service status
sudo systemctl status echo-mcp-server

# View logs
sudo journalctl -u echo-mcp-server -f

# Test endpoints
curl -k https://memory.aynshteyn.dev/mcp
curl -k https://memory.aynshteyn.dev:8443/mcp
```

## Troubleshooting

**MCP Inspector SSL Issues:**
- Use HTTP mode: `python main.py --no-ssl`
- Use Node.js bypass: `NODE_TLS_REJECT_UNAUTHORIZED=0 npx @modelcontextprotocol/inspector`

**Service Issues:**
- Check logs: `sudo journalctl -u echo-mcp-server -f`
- Restart service: `sudo systemctl restart echo-mcp-server`
- Restart Caddy: `sudo systemctl restart caddy`

**Port Issues:**
- Use different port: `python main.py --port 9443`

## Project Structure

```
echo-mcp-server/
├── echo_mcp_server/          # Main server code
├── deploy/
│   ├── one-click-deploy.sh   # 🚀 One-click deployment script
│   ├── install.sh            # Manual deployment script
│   ├── systemd/              # Systemd service
│   └── caddy/                # Caddy configuration
├── main.py                   # Development entry point
├── config.env.example        # Environment configuration
└── README.md                 # This file
```

## Contributing

1. Fork the repository
2. Make your changes
3. Submit a pull request

## License

MIT License 