import asyncio
import logging
from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from src.graph_db import GraphManager

logger = logging.getLogger("graph")
router = APIRouter()


@router.get("/graph/sample")
async def graph_sample(doc_limit: int = 5):
    db = GraphManager()

    def query():
        cypher = """
        MATCH (d:Document)
        WITH d ORDER BY coalesce(d.created_at, 0) DESC LIMIT $doc_limit
        OPTIONAL MATCH (d)-[:MENTIONS]->(e)
        OPTIONAL MATCH (e)-[r:RELATED]->(t)
        WITH collect(distinct d) AS docs, collect(distinct e) AS ent_nodes, collect(distinct t) AS target_nodes, collect(distinct r) AS rels
        WITH docs, ent_nodes, target_nodes, rels
        UNWIND ent_nodes + target_nodes AS n
        WITH docs, rels, collect(distinct n) AS uniq_nodes
        WITH docs,
             [n IN uniq_nodes | {id: elementId(n), labels: labels(n), name: coalesce(n.name, n.url), props: properties(n)}] AS nodes,
             [r IN rels WHERE r IS NOT NULL | {id: elementId(r), type: type(r), source: elementId(startNode(r)), target: elementId(endNode(r)), props: properties(r)}] AS edges
        RETURN nodes,
               edges,
               size(nodes) AS node_count,
               size(edges) AS edge_count,
               [d IN docs | {id: elementId(d), url: d.url, created_at: d.created_at}] AS documents
        """
        with db.session() as session:
            record = session.run(cypher, {"doc_limit": doc_limit}).single()
            if not record:
                return {"nodes": [], "edges": [], "node_count": 0, "edge_count": 0, "documents": []}
            return {
                "nodes": record["nodes"],
                "edges": record["edges"],
                "node_count": record["node_count"],
                "edge_count": record["edge_count"],
                "documents": record["documents"],
            }

    try:
        return await asyncio.wait_for(run_in_threadpool(query), timeout=10)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Graph sample timed out")
    except Exception as e:
        logger.error(f"Graph sample error: {e}")
        raise HTTPException(status_code=500, detail="Graph sample failed")


@router.get("/graph/competitors")
async def get_competitors(company: str):
    if not company:
        raise HTTPException(status_code=400, detail="company is required")
    db = GraphManager()

    def query():
        cypher = """
        MATCH (c:Organization)
        WHERE toLower(c.name) = toLower($company)
        MATCH (c)-[r:RELATED {type:'COMPETES_WITH'}]->(o:Organization)
        RETURN o.name AS competitor, r.reason AS reason, r.source_url AS source
        ORDER BY o.name
        """
        with db.session() as session:
            return [
                {"competitor": rec["competitor"], "reason": rec["reason"], "source": rec["source"]}
                for rec in session.run(cypher, {"company": company})
            ]

    try:
        data = await asyncio.wait_for(run_in_threadpool(query), timeout=8)
        return {"company": company, "competitors": data}
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Competitors query timed out")
    except Exception as e:
        logger.error(f"Competitors query error: {e}")
        raise HTTPException(status_code=500, detail="Competitors query failed")


@router.get("/graph/stats")
async def graph_stats():
    db = GraphManager()

    def query():
        cypher = """
        MATCH (n)
        WHERE any(l IN labels(n) WHERE l IN ["Person","Organization","Location","Topic"])
        WITH count(n) AS entity_count, count(distinct toLower(trim(n.name))) AS distinct_names
        MATCH (d:Document)
        RETURN entity_count AS entities,
               count(d)    AS sources,
               (CASE
                    WHEN entity_count = 0 THEN 100
                    ELSE round(100.0 * distinct_names / entity_count)
               END) AS dedupe_confidence
        """
        with db.session() as session:
            record = session.run(cypher).single()
            if not record:
                return {"entities": 0, "sources": 0, "dedupe_confidence": 100}
            return {
                "entities": record["entities"],
                "sources": record["sources"],
                "dedupe_confidence": record["dedupe_confidence"],
            }

    try:
        return await asyncio.wait_for(run_in_threadpool(query), timeout=8)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Graph stats timed out")
    except Exception as e:
        logger.error(f"Graph stats error: {e}")
        raise HTTPException(status_code=500, detail="Graph stats failed")


@router.get("/graph/recent-docs")
async def recent_docs(limit: int = 15):
    db = GraphManager()

    def query():
        cypher = """
        MATCH (d:Document)
        RETURN d.url AS url, d.created_at AS created_at
        ORDER BY coalesce(d.created_at,0) DESC
        LIMIT $limit
        """
        with db.session() as session:
            return [{"url": rec["url"], "created_at": rec["created_at"]} for rec in session.run(cypher, {"limit": limit})]

    try:
        docs = await asyncio.wait_for(run_in_threadpool(query), timeout=8)
        return {"documents": docs}
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Recent docs timed out")
    except Exception as e:
        logger.error(f"Recent docs error: {e}")
        raise HTTPException(status_code=500, detail="Recent docs failed")


@router.get("/graph/profile")
async def entity_profile(name: str):
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    db = GraphManager()

    def query():
        cypher = """
        MATCH (e)
        WHERE toLower(e.name) = toLower($name)
        OPTIONAL MATCH (e)<-[m:MENTIONS]-(d:Document)
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

    try:
        data = await asyncio.wait_for(run_in_threadpool(query), timeout=8)
        if data is None:
            raise HTTPException(status_code=404, detail="Entity not found")
        return data
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Entity profile timed out")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Entity profile error: {e}")
        raise HTTPException(status_code=500, detail="Entity profile failed")
