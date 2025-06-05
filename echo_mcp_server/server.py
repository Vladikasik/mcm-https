"""
Production MCP Server with SSE Transport for Anthropic Compatibility

Clean, focused SSE implementation specifically designed for Anthropic's MCP API.
Now includes Neo4j memory functionality alongside existing echo functionality.
"""

import os
import ssl
import logging
import json
from pathlib import Path
from typing import Optional, Any, Dict, List

import uvicorn
import neo4j
from neo4j import GraphDatabase
from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP

from .ssl_utils import generate_self_signed_cert

# Set up logging
logger = logging.getLogger('mcp_neo4j_memory')
logger.setLevel(logging.INFO)

# Models for our knowledge graph
class Entity(BaseModel):
    name: str
    type: str
    observations: List[str]

class Relation(BaseModel):
    source: str
    target: str
    relationType: str

class KnowledgeGraph(BaseModel):
    entities: List[Entity]
    relations: List[Relation]

class ObservationAddition(BaseModel):
    entityName: str
    contents: List[str]

class ObservationDeletion(BaseModel):
    entityName: str
    observations: List[str]

class Neo4jMemory:
    def __init__(self, neo4j_driver):
        self.neo4j_driver = neo4j_driver
        self.create_fulltext_index()

    def create_fulltext_index(self):
        try:
            query = """
            CREATE FULLTEXT INDEX search IF NOT EXISTS FOR (m:Memory) ON EACH [m.name, m.type, m.observations];
            """
            self.neo4j_driver.execute_query(query)
            logger.info("Created fulltext search index")
        except neo4j.exceptions.ClientError as e:
            if "An index with this name already exists" in str(e):
                logger.info("Fulltext search index already exists")
            else:
                raise e

    def load_graph(self, filter_query="*"):
        query = """
            CALL db.index.fulltext.queryNodes('search', $filter) yield node as entity, score
            OPTIONAL MATCH (entity)-[r]-(other)
            RETURN collect(distinct {
                name: entity.name, 
                type: entity.type, 
                observations: entity.observations
            }) as nodes,
            collect(distinct {
                source: startNode(r).name, 
                target: endNode(r).name, 
                relationType: type(r)
            }) as relations
        """
        
        result = self.neo4j_driver.execute_query(query, {"filter": filter_query})
        
        if not result.records:
            return KnowledgeGraph(entities=[], relations=[])
        
        record = result.records[0]
        nodes = record.get('nodes')
        rels = record.get('relations')
        
        entities = [
            Entity(
                name=node.get('name'),
                type=node.get('type'),
                observations=node.get('observations', [])
            )
            for node in nodes if node.get('name')
        ]
        
        relations = [
            Relation(
                source=rel.get('source'),
                target=rel.get('target'),
                relationType=rel.get('relationType')
            )
            for rel in rels if rel.get('source') and rel.get('target') and rel.get('relationType')
        ]
        
        logger.debug(f"Loaded entities: {entities}")
        logger.debug(f"Loaded relations: {relations}")
        
        return KnowledgeGraph(entities=entities, relations=relations)

    def create_entities(self, entities: List[Entity]) -> List[Entity]:
        query = """
        UNWIND $entities as entity
        MERGE (e:Memory { name: entity.name })
        SET e += entity {.type, .observations}
        SET e:$(entity.type)
        """
        
        entities_data = [entity.model_dump() for entity in entities]
        self.neo4j_driver.execute_query(query, {"entities": entities_data})
        return entities

    def create_relations(self, relations: List[Relation]) -> List[Relation]:
        for relation in relations:
            query = """
            UNWIND $relations as relation
            MATCH (from:Memory),(to:Memory)
            WHERE from.name = relation.source
            AND  to.name = relation.target
            MERGE (from)-[r:$(relation.relationType)]->(to)
            """
            
            self.neo4j_driver.execute_query(
                query, 
                {"relations": [relation.model_dump() for relation in relations]}
            )
        
        return relations

    def add_observations(self, observations: List[ObservationAddition]) -> List[Dict[str, Any]]:
        query = """
        UNWIND $observations as obs  
        MATCH (e:Memory { name: obs.entityName })
        WITH e, [o in obs.contents WHERE NOT o IN e.observations] as new
        SET e.observations = coalesce(e.observations,[]) + new
        RETURN e.name as name, new
        """
            
        result = self.neo4j_driver.execute_query(
            query, 
            {"observations": [obs.model_dump() for obs in observations]}
        )

        results = [{"entityName": record.get("name"), "addedObservations": record.get("new")} for record in result.records]
        return results

    def delete_entities(self, entity_names: List[str]) -> None:
        query = """
        UNWIND $entities as name
        MATCH (e:Memory { name: name })
        DETACH DELETE e
        """
        
        self.neo4j_driver.execute_query(query, {"entities": entity_names})

    def delete_observations(self, deletions: List[ObservationDeletion]) -> None:
        query = """
        UNWIND $deletions as d  
        MATCH (e:Memory { name: d.entityName })
        SET e.observations = [o in coalesce(e.observations,[]) WHERE NOT o IN d.observations]
        """
        self.neo4j_driver.execute_query(
            query, 
            {
                "deletions": [deletion.model_dump() for deletion in deletions]
            }
        )

    def delete_relations(self, relations: List[Relation]) -> None:
        query = """
        UNWIND $relations as relation
        MATCH (source:Memory)-[r:$(relation.relationType)]->(target:Memory)
        WHERE source.name = relation.source
        AND target.name = relation.target
        DELETE r
        """
        self.neo4j_driver.execute_query(
            query, 
            {"relations": [relation.model_dump() for relation in relations]}
        )

    def read_graph(self) -> KnowledgeGraph:
        return self.load_graph()

    def search_nodes(self, query: str) -> KnowledgeGraph:
        return self.load_graph(query)

    def find_nodes(self, names: List[str]) -> KnowledgeGraph:
        return self.load_graph("name: (" + " ".join(names) + ")")


class MCPServer:
    """Production MCP Server with SSE transport for Anthropic API."""
    
    def __init__(self, name: str = "MemoryMCP", neo4j_memory: Optional[Neo4jMemory] = None):
        """Initialize the MCP server for SSE transport."""
        self.name = name
        self.neo4j_memory = neo4j_memory
        
        # Initialize FastMCP for SSE transport
        self.mcp = FastMCP(name=name)
        
        # Register tools
        self._register_tools()
    
    def _register_tools(self):
        """Register MCP tools."""
        # Keep existing echo functionality
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
        
        # Add Neo4j tools if available
        if self.neo4j_memory:
            @self.mcp.tool(description="Create multiple new entities in the knowledge graph")
            def create_entities(entities: List[Dict[str, Any]]) -> str:
                """Create multiple new entities in the knowledge graph"""
                try:
                    entity_objects = [Entity(**entity) for entity in entities]
                    result = self.neo4j_memory.create_entities(entity_objects)
                    return json.dumps([e.model_dump() for e in result], indent=2)
                except Exception as e:
                    return f"Error: {str(e)}"
            
            @self.mcp.tool(description="Create multiple new relations between entities in the knowledge graph")
            def create_relations(relations: List[Dict[str, Any]]) -> str:
                """Create multiple new relations between entities in the knowledge graph"""
                try:
                    relation_objects = [Relation(**relation) for relation in relations]
                    result = self.neo4j_memory.create_relations(relation_objects)
                    return json.dumps([r.model_dump() for r in result], indent=2)
                except Exception as e:
                    return f"Error: {str(e)}"
            
            @self.mcp.tool(description="Add new observations to existing entities in the knowledge graph")
            def add_observations(observations: List[Dict[str, Any]]) -> str:
                """Add new observations to existing entities in the knowledge graph"""
                try:
                    observation_objects = [ObservationAddition(**obs) for obs in observations]
                    result = self.neo4j_memory.add_observations(observation_objects)
                    return json.dumps(result, indent=2)
                except Exception as e:
                    return f"Error: {str(e)}"
            
            @self.mcp.tool(description="Delete multiple entities and their associated relations from the knowledge graph")
            def delete_entities(entityNames: List[str]) -> str:
                """Delete multiple entities and their associated relations from the knowledge graph"""
                try:
                    self.neo4j_memory.delete_entities(entityNames)
                    return "Entities deleted successfully"
                except Exception as e:
                    return f"Error: {str(e)}"
            
            @self.mcp.tool(description="Delete specific observations from entities in the knowledge graph")
            def delete_observations(deletions: List[Dict[str, Any]]) -> str:
                """Delete specific observations from entities in the knowledge graph"""
                try:
                    deletion_objects = [ObservationDeletion(**deletion) for deletion in deletions]
                    self.neo4j_memory.delete_observations(deletion_objects)
                    return "Observations deleted successfully"
                except Exception as e:
                    return f"Error: {str(e)}"
            
            @self.mcp.tool(description="Delete multiple relations from the knowledge graph")
            def delete_relations(relations: List[Dict[str, Any]]) -> str:
                """Delete multiple relations from the knowledge graph"""
                try:
                    relation_objects = [Relation(**relation) for relation in relations]
                    self.neo4j_memory.delete_relations(relation_objects)
                    return "Relations deleted successfully"
                except Exception as e:
                    return f"Error: {str(e)}"
            
            @self.mcp.tool(description="Read the entire knowledge graph")
            def read_graph() -> str:
                """Read the entire knowledge graph"""
                try:
                    result = self.neo4j_memory.read_graph()
                    return json.dumps(result.model_dump(), indent=2)
                except Exception as e:
                    return f"Error: {str(e)}"
            
            @self.mcp.tool(description="Search for nodes in the knowledge graph based on a query")
            def search_nodes(query: str) -> str:
                """Search for nodes in the knowledge graph based on a query"""
                try:
                    result = self.neo4j_memory.search_nodes(query)
                    return json.dumps(result.model_dump(), indent=2)
                except Exception as e:
                    return f"Error: {str(e)}"
            
            @self.mcp.tool(description="Find specific nodes in the knowledge graph by their names")
            def find_nodes(names: List[str]) -> str:
                """Find specific nodes in the knowledge graph by their names"""
                try:
                    result = self.neo4j_memory.find_nodes(names)
                    return json.dumps(result.model_dump(), indent=2)
                except Exception as e:
                    return f"Error: {str(e)}"
            
            @self.mcp.tool(description="Open specific nodes in the knowledge graph by their names")
            def open_nodes(names: List[str]) -> str:
                """Open specific nodes in the knowledge graph by their names"""
                try:
                    result = self.neo4j_memory.find_nodes(names)
                    return json.dumps(result.model_dump(), indent=2)
                except Exception as e:
                    return f"Error: {str(e)}"
    
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
                
                # List available tools
                tools = ["echo", "store_memory", "get_memory"]
                if self.neo4j_memory:
                    tools.extend([
                        "create_entities", "create_relations", "add_observations",
                        "delete_entities", "delete_observations", "delete_relations",
                        "read_graph", "search_nodes", "find_nodes", "open_nodes"
                    ])
                print(f"🛠️  Tools: {', '.join(tools)}")
                print("="*60)
                
                # Run with uvicorn directly for SSL support
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
        
        # List available tools
        tools = ["echo", "store_memory", "get_memory"]
        if self.neo4j_memory:
            tools.extend([
                "create_entities", "create_relations", "add_observations",
                "delete_entities", "delete_observations", "delete_relations",
                "read_graph", "search_nodes", "find_nodes", "open_nodes"
            ])
        print(f"🛠️  Tools: {', '.join(tools)}")
        print("="*60)
        
        # Run FastMCP for HTTP
        try:
            self.mcp.run(transport="sse")
        except Exception as e:
            print(f"❌ Server error: {e}")
            raise


def create_server(name: str = "MemoryMCP", neo4j_memory: Optional[Neo4jMemory] = None) -> MCPServer:
    """Factory function to create an MCPServer instance."""
    return MCPServer(name=name, neo4j_memory=neo4j_memory) 