"""
Main entry point for the Memory MCP Server.

This server runs on memory.aynshteyn.dev with both SSE and Streamable HTTP endpoints.
Now includes Neo4j knowledge graph functionality alongside existing echo functionality.
"""

import os
import sys
import logging
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

from .server import MCPServer, Neo4jMemory

# Set up logging
logger = logging.getLogger('mcp_server_main')
logger.setLevel(logging.INFO)


def load_environment():
    """Load environment variables from .env file."""
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Loaded configuration from {env_file}")
    else:
        print("⚠️  No .env file found, using environment variables")


def setup_neo4j_connection():
    """Setup Neo4j connection if environment variables are available."""
    neo4j_url = os.getenv("NEO4J_URL")
    neo4j_username = os.getenv("NEO4J_USERNAME")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    if not all([neo4j_url, neo4j_username, neo4j_password]):
        print("⚠️  Neo4j environment variables not found. Running without Neo4j functionality.")
        print("   Required variables: NEO4J_URL, NEO4J_USERNAME, NEO4J_PASSWORD")
        return None
    
    try:
        print(f"🔗 Connecting to Neo4j at {neo4j_url}")
        
        # Connect to Neo4j
        neo4j_driver = GraphDatabase.driver(
            neo4j_url,
            auth=(neo4j_username, neo4j_password),
            database=neo4j_database
        )
        
        # Verify connection
        neo4j_driver.verify_connectivity()
        logger.info(f"✅ Connected to Neo4j at {neo4j_url}")
        
        # Initialize Neo4j memory
        neo4j_memory = Neo4jMemory(neo4j_driver)
        print("✅ Neo4j memory system initialized")
        
        return neo4j_memory
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to Neo4j: {e}")
        print(f"❌ Neo4j connection failed: {e}")
        print("   Server will run without Neo4j functionality")
        return None


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
    
    # Setup Neo4j connection
    neo4j_memory = setup_neo4j_connection()
    
    try:
        # Create and run the server
        server = MCPServer(name=server_name, neo4j_memory=neo4j_memory)
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