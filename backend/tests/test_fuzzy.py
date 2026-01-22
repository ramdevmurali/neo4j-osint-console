import logging

from src.graph_ops import insert_knowledge
from src.schema import KnowledgeGraphUpdate, Entity

logging.basicConfig(level=logging.INFO)

print("🧪 TESTING FUZZY MATCHING...")

mock_data = KnowledgeGraphUpdate(
    source_url="https://fuzzy-test.com",
    entities=[
        Entity(
            name="Space-X",
            label="Organization",
            properties={"note": "This should be merged into SpaceX automatically"}
        )
    ],
    relationships=[]
)

insert_knowledge(mock_data)

print("\n------------------------------------------------")
print("❓ DID IT WORK?")
print("Look for a log above saying: '🔄 RESOLUTION: Merging...'")
print("------------------------------------------------")
