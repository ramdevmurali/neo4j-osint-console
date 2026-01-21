from src.server import add_knowledge
from src.schema import KnowledgeGraphUpdate, Entity, Relationship

# 1. Create Mock Data
mock_data = KnowledgeGraphUpdate(
    source_url="https://project-gotham.test/briefing-001",
    entities=[
        Entity(name="Sarah Connor", label="Person", properties={"role": "Target", "status": "Active"}),
        Entity(name="Cyberdyne Systems", label="Organization", properties={"industry": "Defense"}),
        Entity(name="Los Angeles", label="Location", properties={})
    ],
    relationships=[
        Relationship(source="Sarah Connor", target="Cyberdyne Systems", type="INVESTIGATING", properties={"method": "physical_surveillance"}),
        Relationship(source="Cyberdyne Systems", target="Los Angeles", type="LOCATED_IN", properties={})
    ]
)

print("🚀 Attempting to ingest mock data...")

# 2. Run the tool function directly
try:
    result = add_knowledge(mock_data)
    print(f"✅ RESULT: {result}")
except Exception as e:
    print(f"❌ ERROR: {e}")
