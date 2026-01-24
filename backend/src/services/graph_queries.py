import re

from src.graph_db import GraphManager

_CORP_SUFFIXES = re.compile(
    r"\b(inc|inc\.|ltd|ltd\.|corp|corp\.|co|co\.|company|companies|group|ag|sa|plc|nv)\b",
    re.IGNORECASE,
)


def _canonical_company_name(name: str) -> str:
    """Lightweight canonicalizer to improve match hit-rate without renaming nodes."""
    cleaned = _CORP_SUFFIXES.sub("", name.strip())
    return re.sub(r"\s+", " ", cleaned).strip() or name.strip()


def _find_company_node(session, company: str):
    """Try exact, normalized, then full-text match; return the node or None."""
    candidates = [company]
    norm = _canonical_company_name(company)
    if norm.lower() != company.lower():
        candidates.append(norm)

    for cand in candidates:
        rec = session.run(
            "MATCH (c:Organization) WHERE toLower(c.name) = toLower($name) RETURN c LIMIT 1",
            name=cand,
        ).single()
        if rec:
            return rec["c"]

    for cand in candidates:
        rec = session.run(
            """
            CALL db.index.fulltext.queryNodes("entity_name_index", $q + "~")
            YIELD node, score
            WHERE 'Organization' IN labels(node)
            RETURN node, score
            ORDER BY score DESC LIMIT 1
            """,
            q=cand,
        ).single()
        if rec:
            return rec["node"]

    return None


def fetch_competitors(company: str) -> list[dict]:
    db = GraphManager()
    with db.session() as session:
        node = _find_company_node(session, company)
        if not node:
            return []

        cypher = """
        MATCH (c:Organization {name: $name})
        MATCH (c)-[r:RELATED {type:'COMPETES_WITH'}]->(o:Organization)
        RETURN o.name AS competitor, r.reason AS reason, r.source_url AS source
        ORDER BY o.name
        """
        return [
            {"competitor": rec["competitor"], "reason": rec["reason"], "source": rec["source"]}
            for rec in session.run(cypher, {"name": node["name"]})
        ]


def fetch_entity_profile(name: str) -> dict | None:
    db = GraphManager()
    cypher = """
    CALL () {
        WITH $name AS q
        MATCH (e) WHERE toLower(e.name) = toLower(q)
        RETURN e, 1.0 AS score
        UNION
        WITH $name AS q
        CALL db.index.fulltext.queryNodes("entity_name_index", q + "~") YIELD node, score
        RETURN node AS e, score
    } 
    WITH e, score ORDER BY score DESC LIMIT 1
    OPTIONAL MATCH (e)<-[:MENTIONS]-(d:Document)
    OPTIONAL MATCH (e)-[r:RELATED]-(n)
    RETURN e,
           collect(distinct {url: d.url, created_at: d.created_at}) AS sources,
           collect(distinct {id: elementId(n), name: n.name, labels: labels(n), type: type(r)}) AS related
    LIMIT 1
    """
    with db.session() as session:
        rec = session.run(cypher, {"name": name}).single()
        if not rec:
            return None
        node = rec["e"]
        return {
            "name": node.get("name"),
            "labels": list(node.labels),
            "properties": dict(node),
            "sources": rec["sources"],
            "related": rec["related"],
        }


__all__ = ["fetch_competitors", "fetch_entity_profile"]
