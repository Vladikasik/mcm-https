"""
Module entry point for running the Echo MCP HTTPS Server as a module.

This allows running the server with:
    python -m echo_mcp_server

"""

from .main import main

if __name__ == "__main__":
    main() 