"""
Main entry point for the Memory MCP Server.

This server runs on memory.aynshteyn.dev with both SSE and Streamable HTTP endpoints.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from .server import MCPServer


def load_environment():
    """Load environment variables from .env file."""
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Loaded configuration from {env_file}")
    else:
        print("⚠️  No .env file found, using environment variables")


def main():
    """Main entry point."""
    print("🚀 Memory MCP Server")
    print("="*50)
    
    # Load environment
    load_environment()
    
    # Configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8443"))
    cert_file = os.getenv("SSL_CERTFILE")
    key_file = os.getenv("SSL_KEYFILE")
    server_name = os.getenv("SERVER_NAME", "MemoryMCP")
    env_mode = os.getenv("ENV", "development").lower()
    log_level = os.getenv("LOG_LEVEL", "info")
    
    # Determine if this is production mode
    is_production = env_mode == "production"
    development_mode = not is_production
    
    print(f"🔧 Configuration:")
    print(f"   • Environment: {env_mode}")
    print(f"   • Host: {host}")
    print(f"   • Port: {port}")
    print(f"   • Server Name: {server_name}")
    
    if is_production:
        if not cert_file or not key_file:
            print("❌ ERROR: Production mode requires SSL certificates!")
            print("   Set SSL_CERTFILE and SSL_KEYFILE environment variables")
            print("   Example in .env file:")
            print("   SSL_CERTFILE=/path/to/domain.cert.pem")
            print("   SSL_KEYFILE=/path/to/private.key.pem")
            sys.exit(1)
        
        if not Path(cert_file).exists() or not Path(key_file).exists():
            print(f"❌ ERROR: Certificate files not found!")
            print(f"   Certificate: {cert_file}")
            print(f"   Key: {key_file}")
            sys.exit(1)
        
        print(f"   • SSL Certificate: {cert_file}")
        print(f"   • SSL Key: {key_file}")
    else:
        print(f"   • SSL: Development mode (self-signed)")
    
    print("="*50)
    
    try:
        # Create and run the server
        server = MCPServer(name=server_name)
        server.run(
            host=host,
            port=port,
            cert_file=cert_file,
            key_file=key_file,
            development_mode=development_mode,
            log_level=log_level
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down server...")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 