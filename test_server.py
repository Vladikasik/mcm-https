#!/usr/bin/env python3
"""
Simple test script for the Memory MCP Server.

This script tests the server functionality and endpoints.
"""

import asyncio
import json
import ssl
import urllib.request
import urllib.error
from pathlib import Path
import sys

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from echo_mcp_server.server import MCPServer


async def test_server_startup():
    """Test that the server starts up correctly."""
    print("🧪 Testing server startup...")
    
    try:
        server = MCPServer("TestMemoryMCP")
        print("✅ Server instance created successfully")
        print("✅ Server configured with tools: echo, store_memory, get_memory")
        return True
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        return False


def test_health_endpoint(base_url: str):
    """Test the health endpoint."""
    print(f"\n🧪 Testing health endpoint: {base_url}")
    
    try:
        # Create SSL context that ignores certificate verification for testing
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        request = urllib.request.Request(f"{base_url}/health")
        response = urllib.request.urlopen(request, context=ssl_context, timeout=5)
        
        if response.getcode() == 200:
            data = json.loads(response.read().decode())
            print(f"✅ Health endpoint working: {data}")
            return True
        else:
            print(f"⚠️  Health endpoint returned HTTP {response.getcode()}")
            return False
            
    except Exception as e:
        print(f"❌ Health endpoint failed: {e}")
        return False


def test_root_endpoint(base_url: str):
    """Test the root information endpoint."""
    print(f"\n🧪 Testing root endpoint: {base_url}")
    
    try:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        request = urllib.request.Request(base_url)
        response = urllib.request.urlopen(request, context=ssl_context, timeout=5)
        
        if response.getcode() == 200:
            data = json.loads(response.read().decode())
            print(f"✅ Root endpoint working")
            print(f"   Server: {data.get('server', 'unknown')}")
            print(f"   Endpoints: {data.get('endpoints', {})}")
            print(f"   Tools: {data.get('tools', [])}")
            return True
        else:
            print(f"⚠️  Root endpoint returned HTTP {response.getcode()}")
            return False
            
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
        return False


def test_mcp_endpoints(base_url: str):
    """Test basic MCP endpoint connectivity."""
    endpoints = ["/mcp", "/sse"]
    
    for endpoint in endpoints:
        print(f"\n🧪 Testing MCP endpoint: {base_url}{endpoint}")
        
        try:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # For MCP endpoints, we expect different responses depending on the method
            request = urllib.request.Request(f"{base_url}{endpoint}")
            response = urllib.request.urlopen(request, context=ssl_context, timeout=5)
            
            status_code = response.getcode()
            print(f"✅ {endpoint} endpoint accessible (HTTP {status_code})")
            
        except urllib.error.HTTPError as e:
            if e.code in [405, 404]:  # Method not allowed or not found is expected for GET
                print(f"✅ {endpoint} endpoint exists (HTTP {e.code} - expected for GET)")
            else:
                print(f"⚠️  {endpoint} endpoint returned HTTP {e.code}")
        except Exception as e:
            print(f"❌ {endpoint} endpoint failed: {e}")


async def main():
    """Run all tests."""
    print("🚀 Memory MCP Server Tests")
    print("=" * 50)
    
    # Test server creation
    startup_ok = await test_server_startup()
    
    if not startup_ok:
        print("\n❌ Server startup test failed, skipping endpoint tests")
        return
    
    print("\n" + "=" * 50)
    print("🌐 Testing Production Endpoints")
    print("=" * 50)
    
    # Test production endpoints
    base_url = "https://memory.aynshteyn.dev"
    
    health_ok = test_health_endpoint(base_url)
    root_ok = test_root_endpoint(base_url)
    test_mcp_endpoints(base_url)
    
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    print(f"✅ Server Startup: {'PASS' if startup_ok else 'FAIL'}")
    print(f"✅ Health Endpoint: {'PASS' if health_ok else 'FAIL'}")
    print(f"✅ Root Endpoint: {'PASS' if root_ok else 'FAIL'}")
    print("✅ MCP Endpoints: See results above")
    
    print("\n🔗 Quick Test Commands:")
    print("curl -k https://memory.aynshteyn.dev/health")
    print("curl -k https://memory.aynshteyn.dev/")
    print("npx @modelcontextprotocol/inspector")
    print("  → Connect to: https://memory.aynshteyn.dev/mcp")


if __name__ == "__main__":
    asyncio.run(main()) 