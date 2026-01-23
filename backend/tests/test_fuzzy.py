import logging

import pytest

from src.tools.graph import insert_knowledge
from src.schema import KnowledgeGraphUpdate, Entity

logging.basicConfig(level=logging.INFO)

@pytest.mark.integration
def test_fuzzy_ingest():
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

    result = insert_knowledge(mock_data)
    assert "Ingested" in result
