#!/bin/bash

echo "==========================================="
echo "MCP Inspector HTTPS Connection Test Script"
echo "==========================================="
echo ""

# Check if the server is running
echo "🔍 Checking if HTTPS MCP server is running..."
if curl -k -s https://127.0.0.1:8443/mcp >/dev/null 2>&1; then
    echo "✅ HTTPS server is running at https://127.0.0.1:8443/mcp"
    echo ""
    
    echo "🚀 Starting MCP Inspector with Node.js SSL bypass..."
    echo "   This resolves the DEPTH_ZERO_SELF_SIGNED_CERT error"
    echo ""
    echo "Command: NODE_TLS_REJECT_UNAUTHORIZED=0 npx @modelcontextprotocol/inspector"
    echo ""
    
    # Set the environment variable and run MCP Inspector
    NODE_TLS_REJECT_UNAUTHORIZED=0 npx @modelcontextprotocol/inspector
    
elif curl -s http://127.0.0.1:8080/mcp >/dev/null 2>&1; then
    echo "✅ HTTP server is running at http://127.0.0.1:8080/mcp"
    echo ""
    echo "🚀 Starting MCP Inspector (HTTP mode - no SSL issues)..."
    echo ""
    echo "Command: npx @modelcontextprotocol/inspector"
    echo ""
    
    # Run MCP Inspector normally for HTTP
    npx @modelcontextprotocol/inspector
    
else
    echo "❌ No MCP server found running on standard ports"
    echo ""
    echo "Please start your MCP server first:"
    echo "  For HTTPS: python main.py"
    echo "  For HTTP:  python main.py --no-ssl"
    echo ""
    echo "Then run this script again."
fi 