import logging
from src.graph_db import GraphManager
from src.schema import KnowledgeGraphUpdate

logger = logging.getLogger("graph_ops")

def _find_fuzzy_match(session, name, label, threshold=0.6):
    """Internal helper to find matches."""
    # Note: We compare labels(node)[0] against the passed label param
    query = f"""
    CALL db.index.fulltext.queryNodes("entity_name_index", $name + "~") YIELD node, score
    WHERE labels(node)[0] = $label AND score > $threshold
    RETURN node.name as name, score ORDER BY score DESC LIMIT 1
    """
    # FIX: Added 'label=label' here
    return session.run(query, name=name, label=label, threshold=threshold).single()

def resolve_entity(session, name, label):
    """Auto-resolves name conflicts for writing."""
    # 1. Exact Match (Fast) - Label injected safely via f-string (Pydantic validates this)
    exact = session.run(f"MATCH (n:{label}) WHERE n.name = $name RETURN n.name", name=name).single()
    if exact: return exact[0]

    # 2. Fuzzy Match (Smart)
    fuzzy = _find_fuzzy_match(session, name, label)
    if fuzzy:
        logger.info(f"🔄 Merging '{name}' -> Existing '{fuzzy['name']}' ({fuzzy['score']:.2f})")
        return fuzzy['name']
    
    return name

def insert_knowledge(data: KnowledgeGraphUpdate) -> str:
    db = GraphManager()
    logger.info(f"Ingesting: {data.source_url}")

    with db.driver.session() as session:
        # Document
        session.run("MERGE (d:Document {url: $url}) ON CREATE SET d.created_at = timestamp()", url=data.source_url)

        # Entities
        name_map = {}
        for entity in data.entities:
            final_name = resolve_entity(session, entity.name, entity.label)
            name_map[entity.name] = final_name
            session.run(
                f"MERGE (e:{entity.label} {{name: $name}}) ON CREATE SET e += $props ON MATCH SET e += $props",
                name=final_name, props=entity.properties
            )

        # Relationships
        count = 0
        for rel in data.relationships:
            s_name = name_map.get(rel.source, rel.source)
            t_name = name_map.get(rel.target, rel.target)
            
            session.run(
                """
                MATCH (s {name: $s}), (t {name: $t}), (d:Document {url: $url})
                MERGE (s)-[r:RELATED {type: $type}]->(t) SET r += $props
                MERGE (d)-[:MENTIONS]->(s)
                MERGE (d)-[:MENTIONS]->(t)
                """,
                s=s_name, t=t_name, url=data.source_url, type=rel.type, props=rel.properties
            )
            count += 1

    return f"Ingested {len(data.entities)} entities, {count} relationships."

def lookup_entity(name: str) -> str:
    """Read-only tool for Agent to check DB."""
    db = GraphManager()
    with db.driver.session() as session:
        # Check both Person and Organization
        for label in ["Person", "Organization"]:
            match = _find_fuzzy_match(session, name, label, threshold=0.7)
            if match:
                return f"Found similar entity: '{match['name']}' ({label})"
    return "No matching entity found."