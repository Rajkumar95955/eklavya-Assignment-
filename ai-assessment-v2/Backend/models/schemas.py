"""
Strict schema definitions for all agent inputs and outputs.
All outputs must validate against these schemas.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Optional
from enum import Enum


# ============== Generator Schemas ==============

class GeneratorInput(BaseModel):
    """Input schema for Generator Agent."""
    grade: int = Field(..., ge=1, le=12, description="Grade level (1-12)")
    topic: str = Field(..., min_length=3, max_length=200, description="Educational topic")


class Explanation(BaseModel):
    """Structured explanation with grade metadata."""
    text: str = Field(..., min_length=50, description="Educational explanation text")
    grade: int = Field(..., ge=1, le=12, description="Target grade level")


class MCQ(BaseModel):
    """Multiple choice question with strict structure."""
    question: str = Field(..., min_length=10, description="Question text")
    options: List[str] = Field(..., min_length=4, max_length=4, description="Exactly 4 options")
    correct_index: int = Field(..., ge=0, le=3, description="Index of correct answer (0-3)")
    
    @field_validator('options')
    @classmethod
    def validate_options(cls, v):
        if len(v) != 4:
            raise ValueError("Must have exactly 4 options")
        if any(len(opt.strip()) == 0 for opt in v):
            raise ValueError("Options cannot be empty")
        return v


class TeacherNotes(BaseModel):
    """Supplementary notes for teachers."""
    learning_objective: str = Field(..., min_length=20, description="Clear learning objective")
    common_misconceptions: List[str] = Field(..., min_length=1, description="List of common misconceptions")


class GeneratorOutput(BaseModel):
    """Complete output schema for Generator Agent."""
    explanation: Explanation
    mcqs: List[MCQ] = Field(..., min_length=3, max_length=5, description="3-5 MCQs")
    teacher_notes: TeacherNotes


# ============== Reviewer Schemas ==============

class ReviewScore(BaseModel):
    """Quantitative evaluation scores (1-5 scale)."""
    age_appropriateness: int = Field(..., ge=1, le=5, description="Language/concept appropriateness for grade")
    correctness: int = Field(..., ge=1, le=5, description="Factual accuracy of content")
    clarity: int = Field(..., ge=1, le=5, description="How clear and understandable the content is")
    coverage: int = Field(..., ge=1, le=5, description="How well the topic is covered")


class ReviewFeedback(BaseModel):
    """Field-specific feedback for explainability."""
    field: str = Field(..., description="JSON path to the problematic field (e.g., 'explanation.text')")
    issue: str = Field(..., description="Description of the issue")
    severity: Literal["critical", "major", "minor"] = Field(default="major")
    suggestion: Optional[str] = Field(None, description="Suggested improvement")


class ReviewerOutput(BaseModel):
    """Complete output schema for Reviewer Agent."""
    scores: ReviewScore
    pass_decision: bool = Field(..., alias="pass", description="Whether content passes review")
    feedback: List[ReviewFeedback] = Field(default_factory=list)
    summary: str = Field(..., description="Brief summary of review")
    
    class Config:
        populate_by_name = True


# ============== Refiner Schemas ==============

class RefinerInput(BaseModel):
    """Input for Refiner Agent."""
    original_input: GeneratorInput
    current_content: GeneratorOutput
    feedback: List[ReviewFeedback]
    attempt_number: int = Field(..., ge=1, le=2)


# ============== Tagger Schemas ==============

class DifficultyLevel(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class BloomsLevel(str, Enum):
    REMEMBERING = "Remembering"
    UNDERSTANDING = "Understanding"
    APPLYING = "Applying"
    ANALYZING = "Analyzing"
    EVALUATING = "Evaluating"
    CREATING = "Creating"


class ContentType(str, Enum):
    EXPLANATION = "Explanation"
    QUIZ = "Quiz"
    EXERCISE = "Exercise"
    EXAMPLE = "Example"


class TaggerOutput(BaseModel):
    """Classification tags for approved content."""
    subject: str = Field(..., description="Subject area (e.g., Mathematics)")
    topic: str = Field(..., description="Specific topic")
    grade: int = Field(..., ge=1, le=12)
    difficulty: DifficultyLevel
    content_type: List[ContentType] = Field(..., min_length=1)
    blooms_level: BloomsLevel
    keywords: List[str] = Field(default_factory=list, description="Searchable keywords")