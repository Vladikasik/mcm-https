#!/bin/bash

echo "🔍 Echo MCP Server Debug Script"
echo "==============================="

echo ""
echo "📊 Service Status:"
systemctl status echo-mcp-server --no-pager

echo ""
echo "📋 Recent Logs (last 20 lines):"
journalctl -u echo-mcp-server --lines=20 --no-pager

echo ""
echo "🔐 SSL Certificate Check:"
if [ -f "/home/aynshteyn.dev-ssl-bundle/domain.cert.pem" ]; then
    echo "✓ SSL cert file exists"
    ls -la /home/aynshteyn.dev-ssl-bundle/domain.cert.pem
else
    echo "❌ SSL cert file NOT found: /home/aynshteyn.dev-ssl-bundle/domain.cert.pem"
fi

if [ -f "/home/aynshteyn.dev-ssl-bundle/private.key.pem" ]; then
    echo "✓ SSL key file exists"
    ls -la /home/aynshteyn.dev-ssl-bundle/private.key.pem
else
    echo "❌ SSL key file NOT found: /home/aynshteyn.dev-ssl-bundle/private.key.pem"
fi

echo ""
echo "📁 Installation Directory:"
ls -la /opt/echo-mcp-server/

echo ""
echo "🐍 Python Environment:"
/opt/echo-mcp-server/env/bin/python --version
/opt/echo-mcp-server/env/bin/pip list | grep -E "mcp|fastapi|uvicorn"

echo ""
echo "⚙️ Environment Configuration:"
cat /opt/echo-mcp-server/.env

echo ""
echo "🧪 Manual Test (debug mode):"
echo "Running: /opt/echo-mcp-server/env/bin/python -m echo_mcp_server --production --log-level debug"
cd /opt/echo-mcp-server
sudo -u www-data /opt/echo-mcp-server/env/bin/python -m echo_mcp_server --production --log-level debug --no-ssl || echo "❌ Manual test failed" 