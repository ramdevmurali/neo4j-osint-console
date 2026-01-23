import logging
import re
from difflib import SequenceMatcher
from src.graph_db import GraphManager
from src.schema import KnowledgeGraphUpdate

logger = logging.getLogger("graph_ops")

_INDEX_BY_LABEL = {
    "Person": "entity_name_index",
    "Organization": "entity_name_index",
    "Location": "entity_name_index_loc_topic",
    "Topic": "entity_name_index_loc_topic",
}

def _find_fuzzy_match(session, name, label, threshold=0.6):
    """Internal helper to find matches."""
    index = _INDEX_BY_LABEL.get(label, "entity_name_index")
    query = f"""
    CALL db.index.fulltext.queryNodes("{index}", $name + "~") YIELD node, score
    WHERE $label IN labels(node) AND score > $threshold
    RETURN node.name as name, score ORDER BY score DESC LIMIT 1
    """
    return session.run(query, name=name, label=label, threshold=threshold).single()

def _normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())

def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, _normalize_name(a), _normalize_name(b)).ratio()

def resolve_entity(session, name, label):
    """Auto-resolves name conflicts for writing."""
    exact = session.run(f"MATCH (n:{label}) WHERE n.name = $name RETURN n.name", name=name).single()
    if exact: return exact[0]

    fuzzy = _find_fuzzy_match(session, name, label)
    if fuzzy:
        candidate = fuzzy["name"]
        score = fuzzy["score"]
        similarity = _similarity(name, candidate)
        if similarity >= 0.85:
            logger.info(f"🔄 Merging '{name}' -> Existing '{candidate}' ({score:.2f}, sim {similarity:.2f})")
            return candidate
        logger.info(f"⚠️ Skipping fuzzy match '{name}' -> '{candidate}' ({score:.2f}, sim {similarity:.2f})")
    
    return name

def insert_knowledge(data: KnowledgeGraphUpdate) -> str:
    db = GraphManager()
    logger.info(f"Ingesting: {data.source_url}")

    with db.session() as session:
        session.run("MERGE (d:Document {url: $url}) ON CREATE SET d.created_at = timestamp()", url=data.source_url)

        name_map = {}
        for entity in data.entities:
            final_name = resolve_entity(session, entity.name, entity.label)
            name_map[entity.name] = final_name
            session.run(
                f"MERGE (e:{entity.label} {{name: $name}}) ON CREATE SET e += $props ON MATCH SET e += $props",
                name=final_name, props=entity.properties
            )

        count = 0
        for rel in data.relationships:
            s_name = name_map.get(rel.source, rel.source)
            t_name = name_map.get(rel.target, rel.target)
            
            session.run(
                """
                MATCH (d:Document {url: $url})
                WITH d
                MATCH (s {name: $s})
                WITH d, s
                MATCH (t {name: $t})
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
    with db.session() as session:
        for label in ["Person", "Organization", "Location", "Topic"]:
            match = _find_fuzzy_match(session, name, label, threshold=0.7)
            if match:
                candidate = match["name"]
                similarity = _similarity(name, candidate)
                if similarity >= 0.85:
                    return f"Found similar entity: '{candidate}' ({label})"
    return "No matching entity found."
