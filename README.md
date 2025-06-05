# Memory MCP Server

**Production-ready SSE MCP server specifically designed for Anthropic API compatibility.**

## ✅ Working with Anthropic API

This server uses **SSE (Server-Sent Events)** transport, which is **required** by Anthropic's MCP connector API.

## Features

- **🔄 SSE Transport**: Fully compatible with Anthropic's MCP API requirements
- **🔒 HTTPS/TLS**: Production-ready SSL/TLS support for domain deployment
- **🛠️ Multiple Tools**: Echo, memory storage, and Neo4j knowledge graph tools
- **🧠 Neo4j Integration**: Full knowledge graph functionality with entities, relations, and observations
- **🌐 Domain Ready**: Configured for `memory.aynshteyn.dev`
- **⚡ Clean Implementation**: Minimal, focused codebase without unnecessary complexity
- **🔄 Graceful Fallback**: Runs with basic functionality if Neo4j is not available

## Endpoints

- **SSE (Anthropic API)**: `https://memory.aynshteyn.dev/sse`
- **Health Check**: Available via root endpoint

## Tools Available

### Basic Tools (Always Available)
1. **echo**: Returns input text with "Echo: " prefix
2. **store_memory**: Store key-value pairs in memory
3. **get_memory**: Retrieve values from memory by key

### Neo4j Knowledge Graph Tools (Available when Neo4j is configured)
4. **create_entities**: Create multiple new entities in the knowledge graph
5. **create_relations**: Create relationships between entities
6. **add_observations**: Add new observations to existing entities
7. **delete_entities**: Delete entities and their relations
8. **delete_observations**: Delete specific observations from entities
9. **delete_relations**: Delete relationships between entities
10. **read_graph**: Read the entire knowledge graph
11. **search_nodes**: Search for nodes using full-text search
12. **find_nodes**: Find specific nodes by their names
13. **open_nodes**: Open specific nodes by their names

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
# Edit .env with your SSL certificate paths and Neo4j credentials

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

# Neo4j Configuration (Optional)
NEO4J_URL=neo4j+s://your-database.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j                    # Optional, defaults to "neo4j"

# Optional
LOG_LEVEL=info                          # Log level
DOMAIN=memory.aynshteyn.dev             # Domain name
```

## Neo4j Setup

The server includes full Neo4j knowledge graph functionality. When Neo4j environment variables are provided, the server will:

1. **Connect to Neo4j**: Establish connection and verify connectivity
2. **Create Indexes**: Automatically create full-text search indexes
3. **Enable Tools**: Make all Neo4j tools available via MCP
4. **Graceful Fallback**: If Neo4j is unavailable, server runs with basic tools only

### Knowledge Graph Structure

- **Entities**: Nodes with name, type, and observations
- **Relations**: Directed relationships between entities
- **Observations**: List of text observations attached to entities
- **Full-text Search**: Search across entity names, types, and observations

### Example Usage

```python
# Creating entities
create_entities([
    {
        "name": "Project Alpha", 
        "type": "Project", 
        "observations": ["Started in Q1", "High priority"]
    }
])

# Creating relations
create_relations([
    {
        "source": "John Doe", 
        "target": "Project Alpha", 
        "relationType": "MANAGES"
    }
])
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