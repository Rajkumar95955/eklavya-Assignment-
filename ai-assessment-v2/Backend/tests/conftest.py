"""
Pytest fixtures and configuration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from models import (
    GeneratorInput,
    GeneratorOutput,
    Explanation,
    MCQ,
    TeacherNotes,
    ReviewerOutput,
    ReviewScore,
    ReviewFeedback,
    TaggerOutput,
)


# ============== Sample Data Fixtures ==============

@pytest.fixture
def sample_generator_input():
    """Valid generator input."""
    return GeneratorInput(grade=5, topic="Fractions as parts of a whole")


@pytest.fixture
def sample_valid_generator_output():
    """Valid generator output that should pass schema validation."""
    return GeneratorOutput(
        explanation=Explanation(
            text="Fractions are a way to represent parts of a whole. When we divide something into equal parts, each part is a fraction. For example, if you cut a pizza into 4 equal slices, each slice is 1/4 (one-fourth) of the pizza. The top number (numerator) tells us how many parts we have, and the bottom number (denominator) tells us how many equal parts the whole is divided into.",
            grade=5
        ),
        mcqs=[
            MCQ(
                question="If a pizza is cut into 8 equal slices and you eat 3, what fraction of the pizza did you eat?",
                options=["1/8", "3/8", "5/8", "8/3"],
                correct_index=1
            ),
            MCQ(
                question="What does the denominator in a fraction tell us?",
                options=[
                    "How many parts we have",
                    "How many equal parts the whole is divided into",
                    "The size of each part",
                    "The total number"
                ],
                correct_index=1
            ),
            MCQ(
                question="Which fraction represents half of something?",
                options=["1/4", "1/3", "1/2", "2/1"],
                correct_index=2
            )
        ],
        teacher_notes=TeacherNotes(
            learning_objective="Students will be able to identify and represent fractions as parts of a whole using visual models and numerical notation.",
            common_misconceptions=[
                "Confusing numerator and denominator",
                "Thinking larger denominators mean larger fractions"
            ]
        )
    )


@pytest.fixture
def sample_passing_review():
    """Review output that passes."""
    return ReviewerOutput(
        scores=ReviewScore(
            age_appropriateness=5,
            correctness=5,
            clarity=5,
            coverage=4
        ),
        pass_decision=True,
        feedback=[
            ReviewFeedback(
                field="explanation.text",
                issue="Could include more visual examples",
                severity="minor",
                suggestion="Add diagram descriptions"
            )
        ],
        summary="Excellent content that meets all quality standards."
    )


@pytest.fixture
def sample_failing_review():
    """Review output that fails."""
    return ReviewerOutput(
        scores=ReviewScore(
            age_appropriateness=3,
            correctness=5,
            clarity=3,
            coverage=4
        ),
        pass_decision=False,
        feedback=[
            ReviewFeedback(
                field="explanation.text",
                issue="Vocabulary too complex for Grade 5",
                severity="critical",
                suggestion="Simplify language"
            ),
            ReviewFeedback(
                field="mcqs[0].question",
                issue="Question is confusing",
                severity="major",
                suggestion="Rephrase more clearly"
            )
        ],
        summary="Content needs significant improvement in age appropriateness and clarity."
    )


@pytest.fixture
def sample_tags():
    """Sample tagger output."""
    return TaggerOutput(
        subject="Mathematics",
        topic="Fractions",
        grade=5,
        difficulty="Medium",
        content_type=["Explanation", "Quiz"],
        blooms_level="Understanding",
        keywords=["fractions", "numerator", "denominator", "parts", "whole"]
    )


# ============== Mock Fixtures ==============

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    with patch('agents.base.OpenAI') as mock:
        yield mock


def create_mock_llm_response(content: dict) -> MagicMock:
    """Helper to create mock LLM response."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(content)
    return mock_response