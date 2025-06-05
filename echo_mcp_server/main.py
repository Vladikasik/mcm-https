"""
Main entry point for the Echo MCP HTTPS Server.

This module provides the command-line interface and main function
for running the HTTPS MCP server with environment configuration.
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from .server import EchoMCPServer
from .ssl_utils import install_certificate_to_system


def load_environment():
    """Load environment variables from .env file if it exists."""
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv(env_file)
        print(f"Loaded environment from {env_file}")


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Echo MCP HTTPS Server - A simple MCP server with echo tool over HTTPS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Development mode (auto-generates self-signed certificate)
  python -m echo_mcp_server
  
  # Development mode with auto-trust for MCP Inspector
  python -m echo_mcp_server --trust-cert
  
  # Development mode with custom host/port
  python -m echo_mcp_server --host 0.0.0.0 --port 8443
  
  # Production mode with your own certificates
  python -m echo_mcp_server --cert-file /path/to/cert.pem --key-file /path/to/key.pem --production
  
  # HTTP mode (no SSL) - works perfectly with MCP Inspector
  python -m echo_mcp_server --no-ssl --port 8080

Environment Variables:
  ENV                 - Set to 'production' for production mode
  ENVIRONMENT         - Alternative to ENV
  SSL_CERT_FILE       - Path to SSL certificate file
  SSL_KEY_FILE        - Path to SSL private key file
  HOST                - Host to bind to (default: 127.0.0.1)
  PORT                - Port to bind to (default: 8443 for HTTPS, 8080 for HTTP)

MCP Inspector Usage:
  For HTTPS: Use --trust-cert to automatically trust the self-signed certificate
  For HTTP:  Use --no-ssl for immediate compatibility without certificate issues
  
  Node.js SSL Issues: If MCP Inspector still fails with HTTPS, use:
    NODE_TLS_REJECT_UNAUTHORIZED=0 npx @modelcontextprotocol/inspector
        """
    )
    
    # Server configuration
    parser.add_argument(
        "--host",
        default=os.getenv("HOST", "127.0.0.1"),
        help="Host to bind to (default: 127.0.0.1)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", "8443")),
        help="Port to bind to (default: 8443 for HTTPS, 8080 for HTTP)"
    )
    
    parser.add_argument(
        "--name",
        default="EchoHTTPS",
        help="Name for the MCP server (default: EchoHTTPS)"
    )
    
    # SSL/TLS configuration
    ssl_group = parser.add_argument_group("SSL/TLS Configuration")
    
    ssl_group.add_argument(
        "--cert-file",
        default=os.getenv("SSL_CERT_FILE"),
        help="Path to SSL certificate file"
    )
    
    ssl_group.add_argument(
        "--key-file", 
        default=os.getenv("SSL_KEY_FILE"),
        help="Path to SSL private key file"
    )
    
    ssl_group.add_argument(
        "--no-ssl",
        action="store_true",
        help="Disable SSL and run in HTTP mode (recommended for MCP Inspector testing)"
    )
    
    ssl_group.add_argument(
        "--trust-cert",
        action="store_true",
        help="Automatically install self-signed certificate to system trust store (requires sudo)"
    )
    
    # Environment mode
    mode_group = parser.add_mutually_exclusive_group()
    
    mode_group.add_argument(
        "--development",
        action="store_true",
        help="Force development mode (auto-generates self-signed certificates)"
    )
    
    mode_group.add_argument(
        "--production",
        action="store_true", 
        help="Force production mode (requires provided certificates)"
    )
    
    # Uvicorn options
    uvicorn_group = parser.add_argument_group("Uvicorn Options")
    
    uvicorn_group.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (default: 1)"
    )
    
    uvicorn_group.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    
    uvicorn_group.add_argument(
        "--log-level",
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        default="info",
        help="Log level (default: info)"
    )
    
    return parser


def validate_arguments(args: argparse.Namespace) -> None:
    """Validate command-line arguments."""
    # Check SSL certificate files in production mode
    if args.production and not args.no_ssl:
        if not args.cert_file or not args.key_file:
            print("Error: Production mode requires --cert-file and --key-file", file=sys.stderr)
            sys.exit(1)
        
        if not Path(args.cert_file).exists():
            print(f"Error: Certificate file not found: {args.cert_file}", file=sys.stderr)
            sys.exit(1)
        
        if not Path(args.key_file).exists():
            print(f"Error: Key file not found: {args.key_file}", file=sys.stderr)
            sys.exit(1)
    
    # Adjust port for HTTP mode
    if args.no_ssl and args.port == 8443:
        args.port = 8080
        print("Info: Switched to port 8080 for HTTP mode")
    
    # Trust cert only works with development mode
    if args.trust_cert and args.production:
        print("Warning: --trust-cert only works with development mode certificates", file=sys.stderr)
    
    if args.trust_cert and args.no_ssl:
        print("Warning: --trust-cert has no effect when SSL is disabled", file=sys.stderr)


def handle_certificate_trust(cert_file: Path, trust_cert: bool) -> None:
    """Handle certificate trust installation if requested."""
    if trust_cert and cert_file and cert_file.exists():
        print("\n🔒 Installing certificate to system trust store...")
        success = install_certificate_to_system(cert_file)
        if success:
            print("✓ Certificate installed! MCP Inspector should now work with HTTPS.")
            print("  You may need to restart your browser/MCP Inspector.")
        else:
            print("✗ Certificate installation failed. Try manual installation or use --no-ssl")
        print()


def print_mcp_inspector_instructions(no_ssl: bool, host: str, port: int, development_mode: bool) -> None:
    """Print detailed MCP Inspector usage instructions."""
    print("\n" + "🔍" + " MCP INSPECTOR CONNECTION INSTRUCTIONS")
    print("=" * 60)
    
    if no_ssl:
        print("✅ HTTP MODE (Recommended for Testing)")
        print(f"   URL: http://{host}:{port}/mcp")
        print("   Command: npx @modelcontextprotocol/inspector")
        print("   Status: Ready - no certificate issues")
    else:
        print("🔒 HTTPS MODE (Certificate Required)")
        print(f"   URL: https://{host}:{port}/mcp")
        print()
        print("   If MCP Inspector fails to connect, try these solutions:")
        print()
        print("   Solution 1 (Easiest): Disable Node.js SSL verification")
        print("     NODE_TLS_REJECT_UNAUTHORIZED=0 npx @modelcontextprotocol/inspector")
        print()
        print("   Solution 2: Add certificate to Node.js")
        cert_path = Path(".ssl/cert.pem").absolute()
        print(f"     NODE_EXTRA_CA_CERTS={cert_path} npx @modelcontextprotocol/inspector")
        print()
        print("   Solution 3: Use HTTP mode instead")
        print(f"     python main.py --no-ssl")
        print(f"     Then connect to: http://{host}:8080/mcp")
        
        if development_mode or development_mode is None:
            print()
            print("   Note: System certificate installation doesn't affect Node.js applications")
    
    print("=" * 60)


def main():
    """Main entry point for the application."""
    # Load environment variables
    load_environment()
    
    # Parse command-line arguments
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Validate arguments
    validate_arguments(args)
    
    # Determine development mode
    development_mode = None
    if args.development:
        development_mode = True
    elif args.production:
        development_mode = False
    
    # Handle no-ssl mode
    cert_file = args.cert_file if not args.no_ssl else None
    key_file = args.key_file if not args.no_ssl else None
    
    # Create and configure the server
    server = EchoMCPServer(name=args.name)
    
    # Print startup information
    print("="*60)
    print("Echo MCP HTTPS Server")
    print("="*60)
    print(f"Mode: {'Development' if development_mode else 'Production' if development_mode is False else 'Auto-detect'}")
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"SSL: {'Disabled' if args.no_ssl else 'Enabled'}")
    
    if not args.no_ssl:
        if cert_file and key_file:
            print(f"Certificate: {cert_file}")
            print(f"Private Key: {key_file}")
        else:
            print("Certificate: Auto-generated (development)")
    
    # Print MCP Inspector instructions
    print_mcp_inspector_instructions(args.no_ssl, args.host, args.port, development_mode)
    
    # Prepare uvicorn kwargs
    uvicorn_kwargs = {
        "log_level": args.log_level,
    }
    
    if args.workers > 1:
        uvicorn_kwargs["workers"] = args.workers
    
    if args.reload:
        uvicorn_kwargs["reload"] = True
    
    try:
        # Run the server
        server.run(
            host=args.host,
            port=args.port,
            cert_file=cert_file,
            key_file=key_file,
            development_mode=development_mode,
            no_ssl=args.no_ssl,
            trust_cert=args.trust_cert,  # Pass trust_cert flag
            **uvicorn_kwargs
        )
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Error starting server: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main() 