#!/usr/bin/env python3
"""
Simple wrapper for the Memory MCP Server.

This provides a quick way to run the server for development and testing.
"""

import sys
from pathlib import Path

# Add the current directory to the Python path so we can import our package
sys.path.insert(0, str(Path(__file__).parent))

from echo_mcp_server.main import main

if __name__ == "__main__":
    main()
