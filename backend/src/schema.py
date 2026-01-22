from typing import Literal, List

from pydantic import BaseModel, Field

class Entity(BaseModel):
    name: str = Field(..., description="The unique name of the entity.")
    label: Literal["Person", "Organization", "Location", "Topic"] = Field(..., description="The type of entity.")
    properties: dict = Field(default_factory=dict, description="Additional attributes like role, industry, etc.")

class Relationship(BaseModel):
    source: str = Field(..., description="Name of the source entity.")
    target: str = Field(..., description="Name of the target entity.")
    type: str = Field(..., description="The relationship type (e.g., WORKS_FOR, LOCATED_IN).")
    properties: dict = Field(default_factory=dict, description="Edge attributes.")

class KnowledgeGraphUpdate(BaseModel):
    """Atomic unit of knowledge to be added to the graph."""
    source_url: str = Field(..., description="The URL where this information was found.")
    entities: List[Entity] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
