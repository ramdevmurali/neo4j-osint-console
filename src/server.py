from mcp.server.fastmcp import FastMCP
from src.graph_db import GraphManager
from src.schema import KnowledgeGraphUpdate
from src.search import perform_search
import logging

# Initialize Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_server")

mcp = FastMCP("Gotham Knowledge Graph")

@mcp.tool()
def add_knowledge(data: KnowledgeGraphUpdate) -> str:
    """
    Ingests extracted knowledge into the Neo4j Graph.
    Idempotently merges Nodes and Relationships.
    """
    db = GraphManager()
    
    # 1. Create the Document Node
    query_doc = """
    MERGE (d:Document {url: $url})
    ON CREATE SET d.created_at = timestamp()
    """
    with db.driver.session() as session:
        session.run(query_doc, url=data.source_url)

    # 2. Process Entities
    count_entities = 0
    with db.driver.session() as session:
        for entity in data.entities:
            cypher = f"""
            MERGE (e:{entity.label} {{name: $name}})
            ON CREATE SET e += $props
            ON MATCH SET e += $props
            """
            session.run(cypher, name=entity.name, props=entity.properties)
            count_entities += 1

    # 3. Process Relationships
    count_rels = 0
    with db.driver.session() as session:
        for rel in data.relationships:
            cypher = f"""
            MATCH (source {{name: $source_name}})
            MATCH (target {{name: $target_name}})
            MATCH (doc:Document {{url: $doc_url}})
            
            // Create the semantic relationship
            MERGE (source)-[r:{rel.type}]->(target)
            ON CREATE SET r += $props
            
            // Create provenance edges (Source -> Doc)
            MERGE (doc)-[:MENTIONS]->(source)
            MERGE (doc)-[:MENTIONS]->(target)
            """
            try:
                session.run(cypher, 
                            source_name=rel.source, 
                            target_name=rel.target, 
                            doc_url=data.source_url,
                            props=rel.properties)
                count_rels += 1
            except Exception as e:
                logger.error(f"Failed to link {rel.source} -> {rel.target}: {e}")

    return f"Successfully ingested {count_entities} entities and {count_rels} relationships from {data.source_url}"

@mcp.tool()
def search_web(query: str) -> str:
    """
    Searches the web for information using Tavily.
    Returns the top 3 results formatted as a string.
    """
    results = perform_search(query)
    
    formatted_output = f"--- Search Results for '{query}' ---\n"
    for r in results:
        formatted_output += f"Source: {r['title']} ({r['url']})\n"
        formatted_output += f"Content: {r['content']}\n"
        formatted_output += "-" * 20 + "\n"
        
    return formatted_output

if __name__ == "__main__":
    mcp.run()