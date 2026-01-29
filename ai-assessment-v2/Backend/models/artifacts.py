"""
Run Artifact schemas for complete audit trail.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
import uuid

from .schemas import (
    GeneratorInput,
    GeneratorOutput,
    ReviewerOutput,
    TaggerOutput,
)


class AttemptRecord(BaseModel):
    """Record of a single generation/refinement attempt."""
    attempt: int = Field(..., ge=1, description="Attempt number (1 = initial, 2+ = refinement)")
    draft: GeneratorOutput
    review: ReviewerOutput
    refined: Optional[GeneratorOutput] = Field(None, description="Refined content if review failed")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FinalResult(BaseModel):
    """Final pipeline decision."""
    status: Literal["approved", "rejected"]
    content: Optional[GeneratorOutput] = Field(None, description="Final approved content")
    tags: Optional[TaggerOutput] = Field(None, description="Tags (only if approved)")
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection (if rejected)")


class Timestamps(BaseModel):
    """Pipeline execution timestamps."""
    started_at: datetime
    finished_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None


class RunArtifact(BaseModel):
    """
    Complete audit trail for a single pipeline run.
    This is the core deliverable - captures entire lifecycle.
    """
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = Field(None, description="User who initiated the run")
    input: GeneratorInput
    attempts: List[AttemptRecord] = Field(default_factory=list)
    final: Optional[FinalResult] = None
    timestamps: Timestamps
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }