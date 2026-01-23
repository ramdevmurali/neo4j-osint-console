import logging
from neo4j import GraphDatabase, Driver
from src.config import Config

logger = logging.getLogger(__name__)

class GraphManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GraphManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self, force: bool = False):
        if force and getattr(self, "driver", None):
            try:
                self.driver.close()
            except Exception:
                pass
        try:
            self.driver: Driver = GraphDatabase.driver(
                Config.NEO4J_URI, 
                auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD)
            )
            self.driver.verify_connectivity()
            self.setup_constraints()
        except Exception as e:
            logger.error(f"❌ DB Connection Failed: {e}")
            raise e

    def close(self):
        if self.driver:
            self.driver.close()

    def setup_constraints(self):
        queries = [
            "CREATE CONSTRAINT document_url_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.url IS UNIQUE",
            "CREATE CONSTRAINT person_name_unique IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS UNIQUE",
            "CREATE CONSTRAINT org_name_unique IF NOT EXISTS FOR (o:Organization) REQUIRE o.name IS UNIQUE",
            "CREATE CONSTRAINT location_name_unique IF NOT EXISTS FOR (l:Location) REQUIRE l.name IS UNIQUE",
            "CREATE CONSTRAINT topic_name_unique IF NOT EXISTS FOR (t:Topic) REQUIRE t.name IS UNIQUE",
            "CREATE FULLTEXT INDEX entity_name_index IF NOT EXISTS FOR (n:Person|Organization) ON EACH [n.name]",
            "CREATE FULLTEXT INDEX entity_name_index_loc_topic IF NOT EXISTS FOR (n:Location|Topic) ON EACH [n.name]",
        ]
        with self.driver.session() as session:
            for q in queries:
                try:
                    session.run(q)
                except Exception as e:
                    logger.error(f"Constraint Failed: {e}")

    def session(self):
        try:
            self.driver.verify_connectivity()
        except Exception as e:
            logger.warning(f"🔁 Reconnecting Neo4j driver due to: {e}")
            self._initialize(force=True)
        return self.driver.session()

if __name__ == "__main__":
    GraphManager().setup_constraints()
