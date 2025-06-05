#!/usr/bin/env python3
"""
Simple wrapper for the Echo MCP HTTPS Server.

This provides a quick way to run the server for development and testing.
For full configuration options, use: python -m echo_mcp_server --help
"""

import os
import sys
from pathlib import Path

# Add the current directory to the Python path so we can import our package
sys.path.insert(0, str(Path(__file__).parent))

from echo_mcp_server.main import main

if __name__ == "__main__":
    # Quick development setup - you can modify these defaults
    default_args = []
    
    # Uncomment and modify these for quick testing:
    # default_args.extend(["--host", "0.0.0.0"])  # Bind to all interfaces
    # default_args.extend(["--port", "8443"])     # Custom port
    # default_args.extend(["--development"])      # Force development mode
    # default_args.extend(["--no-ssl"])           # Disable SSL for testing
    
    # Add default arguments to sys.argv if no arguments provided
    if len(sys.argv) == 1 and default_args:
        sys.argv.extend(default_args)
    
    main()
