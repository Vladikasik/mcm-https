"""
Production MCP Server with SSE Transport for Anthropic Compatibility

Clean, focused SSE implementation specifically designed for Anthropic's MCP API.
"""

import ssl
from pathlib import Path
from typing import Optional

import uvicorn
from mcp.server.fastmcp import FastMCP

from .ssl_utils import generate_self_signed_cert


class MCPServer:
    """Production MCP Server with SSE transport for Anthropic API."""
    
    def __init__(self, name: str = "MemoryMCP"):
        """Initialize the MCP server for SSE transport."""
        self.name = name
        
        # Initialize FastMCP for SSE transport (no stateless_http needed for SSE)
        self.mcp = FastMCP(name=name)
        
        # Register tools
        self._register_tools()
    
    def _register_tools(self):
        """Register MCP tools."""
        @self.mcp.tool(description="Echo tool - returns the input text unchanged")
        def echo(text: str) -> str:
            """Echo the input text back to the user."""
            return f"Echo: {text}"
        
        @self.mcp.tool(description="Memory storage tool")
        def store_memory(key: str, value: str) -> str:
            """Store a key-value pair in memory."""
            # Simple in-memory storage for demo
            if not hasattr(self, '_memory'):
                self._memory = {}
            self._memory[key] = value
            return f"Stored: {key} = {value}"
        
        @self.mcp.tool(description="Memory retrieval tool")
        def get_memory(key: str) -> str:
            """Retrieve a value from memory by key."""
            if not hasattr(self, '_memory'):
                self._memory = {}
            value = self._memory.get(key, "Not found")
            return f"Retrieved: {key} = {value}"
    
    def _get_ssl_context(self, cert_file: Optional[str], key_file: Optional[str], 
                        development_mode: bool) -> Optional[ssl.SSLContext]:
        """Get SSL context for HTTPS."""
        if development_mode and not cert_file and not key_file:
            # Generate self-signed certificate for development
            cert_dir = Path(".ssl")
            cert_path, key_path = generate_self_signed_cert(cert_dir)
            cert_file = str(cert_path)
            key_file = str(key_path)
        
        if not cert_file or not key_file:
            return None
        
        if not Path(cert_file).exists() or not Path(key_file).exists():
            raise FileNotFoundError(f"Certificate files not found: {cert_file}, {key_file}")
        
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert_file, key_file)
        return context
    
    def run(self, host: str = "0.0.0.0", port: int = 8443, 
           cert_file: Optional[str] = None, key_file: Optional[str] = None,
           development_mode: bool = False, **kwargs):
        """Run the MCP server with SSE transport."""
        
        print(f"🚀 Starting {self.name} Server (SSE)")
        print(f"📍 Host: {host}:{port}")
        print(f"🔐 Mode: {'Development' if development_mode else 'Production'}")
        
        # Configure FastMCP settings
        self.mcp.settings.host = host
        self.mcp.settings.port = port
        self.mcp.settings.debug = development_mode
        
        # Determine protocol and prepare SSL settings
        if cert_file and key_file:
            ssl_context = self._get_ssl_context(cert_file, key_file, development_mode)
            if ssl_context:
                protocol = "https"
                # For FastMCP with SSE and SSL, we need to use uvicorn directly
                # since FastMCP doesn't handle SSL configuration through settings
                print(f"🌐 Protocol: HTTPS")
                print(f"📋 SSE Endpoint: https://{host}:{port}/sse")
                print(f"🛠️  Tools: echo, store_memory, get_memory")
                print("="*60)
                
                # Run with uvicorn directly for SSL support
                import uvicorn
                app = self.mcp.sse_app()
                uvicorn.run(
                    app,
                    host=host,
                    port=port,
                    ssl_keyfile=key_file,
                    ssl_certfile=cert_file,
                    log_level="debug" if development_mode else "info"
                )
                return
            else:
                protocol = "http"
        else:
            protocol = "http"
        
        print(f"🌐 Protocol: {protocol.upper()}")
        print(f"📋 SSE Endpoint: {protocol}://{host}:{port}/sse")
        print(f"🛠️  Tools: echo, store_memory, get_memory")
        print("="*60)
        
        # Run FastMCP for HTTP
        try:
            self.mcp.run(transport="sse")
        except Exception as e:
            print(f"❌ Server error: {e}")
            raise


def create_server(name: str = "MemoryMCP") -> MCPServer:
    """Factory function to create an MCPServer instance."""
    return MCPServer(name=name) 