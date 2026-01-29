"""
Test 1: Schema validation failure handling
"""

import pytest
from pydantic import ValidationError

from models import (
    GeneratorInput,
    GeneratorOutput,
    Explanation,
    MCQ,
    TeacherNotes,
)
from agents import GeneratorAgent, AgentError


class TestSchemaValidation:
    """Test schema validation and failure handling."""
    
    def test_valid_generator_input(self):
        """Valid input should pass validation."""
        input_data = GeneratorInput(grade=5, topic="Fractions")
        assert input_data.grade == 5
        assert input_data.topic == "Fractions"
    
    def test_invalid_grade_too_low(self):
        """Grade below 1 should fail."""
        with pytest.raises(ValidationError):
            GeneratorInput(grade=0, topic="Fractions")
    
    def test_invalid_grade_too_high(self):
        """Grade above 12 should fail."""
        with pytest.raises(ValidationError):
            GeneratorInput(grade=13, topic="Fractions")
    
    def test_invalid_topic_too_short(self):
        """Topic with fewer than 3 characters should fail."""
        with pytest.raises(ValidationError):
            GeneratorInput(grade=5, topic="Hi")
    
    def test_valid_mcq(self):
        """Valid MCQ should pass validation."""
        mcq = MCQ(
            question="What is 2 + 2?",
            options=["1", "2", "3", "4"],
            correct_index=3
        )
        assert mcq.correct_index == 3
        assert len(mcq.options) == 4
    
    def test_mcq_wrong_option_count(self):
        """MCQ with wrong number of options should fail."""
        with pytest.raises(ValidationError):
            MCQ(
                question="What is 2 + 2?",
                options=["1", "2", "3"],  # Only 3 options
                correct_index=2
            )
    
    def test_mcq_invalid_correct_index(self):
        """MCQ with invalid correct_index should fail."""
        with pytest.raises(ValidationError):
            MCQ(
                question="What is 2 + 2?",
                options=["1", "2", "3", "4"],
                correct_index=5  # Invalid: must be 0-3
            )
    
    def test_explanation_too_short(self):
        """Explanation with fewer than 50 characters should fail."""
        with pytest.raises(ValidationError):
            Explanation(text="Too short", grade=5)
    
    def test_teacher_notes_missing_misconceptions(self):
        """Teacher notes without misconceptions should fail."""
        with pytest.raises(ValidationError):
            TeacherNotes(
                learning_objective="Students will learn fractions.",
                common_misconceptions=[]  # Empty list
            )
    
    def test_full_generator_output_validation(self, sample_valid_generator_output):
        """Complete valid output should pass validation."""
        # Access the fixture to ensure it validates
        assert sample_valid_generator_output.explanation.grade == 5
        assert len(sample_valid_generator_output.mcqs) == 3
        assert len(sample_valid_generator_output.teacher_notes.common_misconceptions) >= 1
    
    def test_generator_output_mcq_count_validation(self):
        """Generator output with too few MCQs should fail."""
        with pytest.raises(ValidationError):
            GeneratorOutput(
                explanation=Explanation(
                    text="This is a valid explanation that is long enough to pass the minimum character requirement.",
                    grade=5
                ),
                mcqs=[
                    MCQ(
                        question="Only one question?",
                        options=["A", "B", "C", "D"],
                        correct_index=0
                    )
                ],  # Only 1 MCQ, minimum is 3
                teacher_notes=TeacherNotes(
                    learning_objective="Students will understand the topic.",
                    common_misconceptions=["Some misconception"]
                )
            )