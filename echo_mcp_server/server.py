"""
HTTPS MCP Server with Echo Tool

This module implements a simple MCP server with an echo tool that can run over HTTPS.
Supports both development (with auto-generated self-signed certificates) and production modes.
"""

import asyncio
import os
import ssl
from pathlib import Path
from typing import Optional

import uvicorn
from mcp.server.fastmcp import FastMCP

from .ssl_utils import generate_self_signed_cert, install_certificate_to_system


class EchoMCPServer:
    """
    HTTPS MCP Server with Echo Tool
    
    Features:
    - Single echo tool that returns input text
    - HTTPS support with SSL/TLS
    - Development mode with auto-generated self-signed certificates
    - Production mode with provided certificates
    - Environment detection
    - MCP Inspector compatibility
    """
    
    def __init__(self, name: str = "EchoHTTPS"):
        """Initialize the MCP server."""
        self.mcp = FastMCP(
            name=name,
            stateless_http=True,  # Required for HTTP transport
        )
        
        # Register the echo tool
        self._register_tools()
    
    def _register_tools(self):
        """Register all MCP tools."""
        
        @self.mcp.tool(description="Echo tool - returns the input text unchanged")
        def echo(text: str) -> str:
            """
            Echo the input text back to the user.
            
            Args:
                text: The text to echo back
                
            Returns:
                The same text that was provided as input
            """
            return text
    
    def get_ssl_context(
        self, 
        cert_file: Optional[str] = None, 
        key_file: Optional[str] = None,
        development_mode: bool = True,
        no_ssl: bool = False,
        trust_cert: bool = False
    ) -> Optional[ssl.SSLContext]:
        """
        Get SSL context for HTTPS server.
        
        Args:
            cert_file: Path to SSL certificate file
            key_file: Path to SSL private key file
            development_mode: Whether to generate self-signed certs for development
            no_ssl: Whether to disable SSL entirely
            trust_cert: Whether to install certificate to system trust store
            
        Returns:
            SSL context or None if SSL should be disabled
        """
        if no_ssl:
            print("SSL disabled by user request. Running in HTTP mode.")
            return None
            
        if development_mode and not cert_file and not key_file:
            # Generate self-signed certificate for development
            cert_dir = Path(".ssl")
            cert_path, key_path = generate_self_signed_cert(cert_dir)
            cert_file = str(cert_path)
            key_file = str(key_path)
            
            # Install certificate to system trust store if requested
            if trust_cert:
                print("\n🔒 Installing certificate to system trust store for MCP Inspector...")
                success = install_certificate_to_system(cert_path)
                if success:
                    print("✓ Certificate installed! MCP Inspector should now work with HTTPS.")
                    print("  You may need to restart your browser/MCP Inspector.")
                else:
                    print("✗ Certificate installation failed.")
                    print("  Try manual installation or use --no-ssl for MCP Inspector testing.")
                print()
        
        if not cert_file or not key_file:
            print("Warning: No SSL certificates provided. Running in HTTP mode.")
            return None
        
        if not Path(cert_file).exists():
            raise FileNotFoundError(f"Certificate file not found: {cert_file}")
        
        if not Path(key_file).exists():
            raise FileNotFoundError(f"Key file not found: {key_file}")
        
        # Create SSL context
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert_file, key_file)
        
        print(f"SSL enabled with certificate: {cert_file}")
        return context
    
    def run(
        self,
        host: str = "127.0.0.1",
        port: int = 8443,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        development_mode: Optional[bool] = None,
        no_ssl: bool = False,
        trust_cert: bool = False,
        **uvicorn_kwargs
    ):
        """
        Run the HTTPS MCP server.
        
        Args:
            host: Host to bind to (default: 127.0.0.1)
            port: Port to bind to (default: 8443 for HTTPS)
            cert_file: Path to SSL certificate file
            key_file: Path to SSL private key file
            development_mode: Force development mode (auto-detects if None)
            no_ssl: Disable SSL and run in HTTP mode
            trust_cert: Install self-signed certificate to system trust store
            **uvicorn_kwargs: Additional arguments to pass to uvicorn
        """
        # Auto-detect development mode if not specified
        if development_mode is None:
            development_mode = (
                os.getenv("ENV", "development").lower() == "development" or
                os.getenv("ENVIRONMENT", "development").lower() == "development" or
                (cert_file is None and key_file is None and not no_ssl)
            )
        
        print(f"Starting Echo MCP Server in {'development' if development_mode else 'production'} mode")
        print(f"Server: {host}:{port}")
        
        # Get SSL context
        ssl_context = self.get_ssl_context(cert_file, key_file, development_mode, no_ssl, trust_cert)
        
        # Get the ASGI app from FastMCP
        app = self.mcp.streamable_http_app() if hasattr(self.mcp, 'streamable_http_app') else self.mcp.create_asgi_app()
        
        # Update uvicorn config
        config = {
            "host": host,
            "port": port,
            "app": app,
            **uvicorn_kwargs
        }
        
        if ssl_context:
            config.update({
                "ssl_certfile": cert_file if cert_file else str(Path(".ssl") / "cert.pem"),
                "ssl_keyfile": key_file if key_file else str(Path(".ssl") / "key.pem"),
            })
            protocol = "https"
        else:
            protocol = "http"
            if port == 8443:  # Default HTTPS port, switch to HTTP default
                config["port"] = 8080
                port = 8080
        
        print(f"MCP Server URL: {protocol}://{host}:{port}/mcp")
        print(f"Available tools: echo")
        
        if development_mode and ssl_context:
            print("\n" + "="*50)
            print("DEVELOPMENT MODE - SELF-SIGNED CERTIFICATE")
            print("="*50)
            if trust_cert:
                print("✓ Certificate has been installed to system trust store.")
                print("  MCP Inspector should work without certificate warnings.")
            else:
                print("The server is using a self-signed certificate.")
                print("Your browser/MCP Inspector will show security warnings.")
                print("")
                print("For MCP Inspector compatibility:")
                print("  🎯 BEST SOLUTION (Node.js apps):")
                print("    NODE_TLS_REJECT_UNAUTHORIZED=0 npx @modelcontextprotocol/inspector")
                print("")
                print("  Alternative solutions:")
                print("    --trust-cert    (installs certificate to system)")
                print("    --no-ssl        (uses HTTP instead of HTTPS)")
            print("="*50 + "\n")
        elif not ssl_context:
            print("\n" + "="*50)
            print("HTTP MODE - NO SSL")
            print("="*50)
            print("✓ Running in HTTP mode - fully compatible with MCP Inspector.")
            print("  No certificate warnings or SSL issues.")
            print("="*50 + "\n")
        
        # Run the server
        uvicorn.run(**config)
    
    async def run_async(
        self,
        host: str = "127.0.0.1",
        port: int = 8443,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        development_mode: Optional[bool] = None,
        no_ssl: bool = False,
        trust_cert: bool = False,
        **uvicorn_kwargs
    ):
        """
        Run the HTTPS MCP server asynchronously.
        
        This is useful when you want to run the server as part of a larger async application.
        """
        # Auto-detect development mode if not specified
        if development_mode is None:
            development_mode = (
                os.getenv("ENV", "development").lower() == "development" or
                os.getenv("ENVIRONMENT", "development").lower() == "development" or
                (cert_file is None and key_file is None and not no_ssl)
            )
        
        # Get SSL context
        ssl_context = self.get_ssl_context(cert_file, key_file, development_mode, no_ssl, trust_cert)
        
        # Get the ASGI app from FastMCP
        app = self.mcp.streamable_http_app() if hasattr(self.mcp, 'streamable_http_app') else self.mcp.create_asgi_app()
        
        # Create uvicorn config
        config_dict = {
            "host": host,
            "port": port,
            "app": app,
            **uvicorn_kwargs
        }
        
        if ssl_context:
            config_dict.update({
                "ssl_certfile": cert_file if cert_file else str(Path(".ssl") / "cert.pem"),
                "ssl_keyfile": key_file if key_file else str(Path(".ssl") / "key.pem"),
            })
        
        config = uvicorn.Config(**config_dict)
        server = uvicorn.Server(config)
        
        await server.serve()


def create_server(name: str = "EchoHTTPS") -> EchoMCPServer:
    """
    Factory function to create an EchoMCPServer instance.
    
    Args:
        name: Name for the MCP server
        
    Returns:
        EchoMCPServer instance
    """
    return EchoMCPServer(name=name) 