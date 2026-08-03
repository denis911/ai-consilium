"""
Pydantic v2 Data Contract Schemas for AI Consilium
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field, field_validator


class ConsiliumQueryInput(BaseModel):
    """User query input and context payload for consensus research."""
    query: str = Field(..., min_length=1, description="Target query prompt")
    context_chunks: List[str] = Field(default_factory=list, description="Retrieved RAG context snippets")
    selected_models: List[str] = Field(default_factory=list, description="List of LLM providers to query")

    @field_validator("query")
    @classmethod
    def validate_query_not_whitespace(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("Query must be a string")
        if not v.strip():
            raise ValueError("Query string cannot be empty or whitespace only")
        return v.strip()


class ModelResponsePayload(BaseModel):
    """Raw response payload and performance metrics from an individual LLM provider."""
    model_name: str = Field(..., min_length=1, description="Model provider identifier (e.g. gpt-4o)")
    response_text: str = Field(..., description="Generated answer text")
    latency_ms: float = Field(default=0.0, ge=0.0, description="Provider response latency in milliseconds")
    prompt_tokens: int = Field(default=0, ge=0, description="Prompt token count")
    completion_tokens: int = Field(default=0, ge=0, description="Completion token count")
    cost_usd: float = Field(default=0.0, ge=0.0, description="Estimated query cost in USD")
    status: str = Field(default="success", description="Status of the provider request (success/error/timeout)")


class ContradictionItem(BaseModel):
    """Detailed log item representing a point of disagreement among model responses."""
    topic: str = Field(..., min_length=1, description="Topic or point of contention")
    description: str = Field(..., description="Explanation of the contradiction")
    conflicting_models: List[str] = Field(default_factory=list, description="Models holding opposing views")


class ConsensusMetrics(BaseModel):
    """Quantitative evaluation metrics computed across model responses."""
    consensus_score: float = Field(..., ge=0.0, le=100.0, description="Overall numerical consensus percentage (0-100%)")
    outlier_models: List[str] = Field(default_factory=list, description="Models identified as statistical outliers")
    pairwise_similarity: Dict[str, Dict[str, float]] = Field(
        default_factory=dict, description="Pairwise similarity matrix between models"
    )
    insufficient_responses: bool = Field(default=False, description="Flag indicating if fewer than 2 valid model responses were available")


class ConsiliumFinalArtifact(BaseModel):
    """Final validated consensus artifact ready for UI rendering and Obsidian export."""
    query: str = Field(..., min_length=1, description="Original query text")
    consensus_score: float = Field(..., ge=0.0, le=100.0, description="Numerical consensus score (0-100%)")
    agreement_points: List[str] = Field(default_factory=list, description="Points of unanimous consensus")
    contradictions: List[ContradictionItem] = Field(default_factory=list, description="Logged contradictions")
    mermaid_code: str = Field(default="", description="Generated Mermaid.js visualization syntax")
    obsidian_title: str = Field(default="", description="Recommended human-readable note title")
    tags: List[str] = Field(default_factory=list, description="Categorization tags for Obsidian metadata")
    responses: List[ModelResponsePayload] = Field(default_factory=list, description="Individual model responses")
    context_chunks: List[str] = Field(default_factory=list, description="RAG reference context snippets used to ground query")
