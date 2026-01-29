"""
Refiner Agent
Responsibility: Improve content using reviewer feedback.
"""

from .base import BaseAgent
from models import (
    GeneratorOutput,
    RefinerInput,
    ReviewFeedback,
)
from config import MAX_REFINEMENT_ATTEMPTS
import json


class RefinerAgent(BaseAgent[RefinerInput, GeneratorOutput]):
    """
    Agent that refines content based on reviewer feedback.
    
    Rules:
    - Maximum 2 refinement attempts
    - Each attempt must be logged (handled by orchestrator)
    - If still failing → final status is rejected
    """
    
    name = "RefinerAgent"
    output_schema = GeneratorOutput
    
    def _build_system_prompt(self) -> str:
        return """You are an expert educational content refiner. Your job is to improve 
content based on specific feedback while maintaining the overall structure.

You MUST:
1. Address ALL feedback items
2. Maintain the exact same JSON structure
3. Keep improvements minimal and targeted
4. Preserve what was already good

OUTPUT FORMAT (same as original content):
{
    "explanation": {
        "text": "Improved explanation...",
        "grade": <grade_number>
    },
    "mcqs": [
        {
            "question": "Question text...",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_index": <0-3>
        }
    ],
    "teacher_notes": {
        "learning_objective": "...",
        "common_misconceptions": ["..."]
    }
}

CRITICAL: Output valid JSON only. Do not include any other text."""

    def _build_user_prompt(self, input_data: RefinerInput) -> str:
        feedback_text = self._format_feedback(input_data.feedback)
        content_json = json.dumps(input_data.current_content.model_dump(), indent=2)
        
        return f"""REFINEMENT TASK (Attempt {input_data.attempt_number}/{MAX_REFINEMENT_ATTEMPTS})

ORIGINAL REQUEST:
- Grade: {input_data.original_input.grade}
- Topic: {input_data.original_input.topic}

CURRENT CONTENT:
{content_json}

FEEDBACK TO ADDRESS:
{feedback_text}

Please refine the content to address ALL feedback items.
Output the complete improved content in the same JSON format."""

    def _format_feedback(self, feedback: list[ReviewFeedback]) -> str:
        """Format feedback items for the prompt."""
        lines = []
        for i, fb in enumerate(feedback, 1):
            severity_emoji = {"critical": "🔴", "major": "🟠", "minor": "🟡"}.get(fb.severity, "⚪")
            lines.append(f"{i}. {severity_emoji} [{fb.field}] {fb.issue}")
            if fb.suggestion:
                lines.append(f"   Suggestion: {fb.suggestion}")
        return "\n".join(lines) if lines else "No specific feedback provided."

    def refine(self, refiner_input: RefinerInput) -> GeneratorOutput:
        """
        Refine content based on feedback.
        
        Args:
            refiner_input: Contains original input, current content, and feedback
            
        Returns:
            Refined GeneratorOutput
        """
        return super().run(refiner_input, max_retries=1)