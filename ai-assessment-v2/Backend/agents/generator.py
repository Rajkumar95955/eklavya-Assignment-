"""
Generator Agent
Responsibility: Produce a draft educational artifact with strict schema validation.
"""

from .base import BaseAgent
from models import GeneratorInput, GeneratorOutput
from config import MAX_GENERATION_RETRIES


class GeneratorAgent(BaseAgent[GeneratorInput, GeneratorOutput]):
    """
    Agent that generates educational content for a given grade and topic.
    
    Rules:
    - Output must validate against GeneratorOutput schema
    - If validation fails → retry once, then fail gracefully
    - Language must be grade-appropriate
    """
    
    name = "GeneratorAgent"
    output_schema = GeneratorOutput
    
    def _build_system_prompt(self) -> str:
        return """You are an expert educational content creator. You create structured, 
age-appropriate educational content that strictly follows the required schema.

You MUST output valid JSON matching this exact structure:
{
    "explanation": {
        "text": "Detailed explanation (minimum 50 characters)...",
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
        "learning_objective": "Students will be able to...",
        "common_misconceptions": ["Misconception 1", "Misconception 2"]
    }
}

CRITICAL RULES:
1. ALWAYS include exactly 4 options per MCQ
2. correct_index must be 0, 1, 2, or 3
3. Include exactly 3-5 MCQs
4. explanation.text must be at least 50 characters
5. Include at least 1 common misconception
6. Match language complexity to the grade level"""

    def _build_user_prompt(self, input_data: GeneratorInput) -> str:
        grade_guidance = self._get_grade_guidance(input_data.grade)
        
        return f"""Create educational content for:

GRADE: {input_data.grade}
TOPIC: {input_data.topic}

GRADE-SPECIFIC GUIDANCE:
{grade_guidance}

Generate:
1. A comprehensive explanation (3-4 paragraphs, age-appropriate vocabulary)
2. 3-5 multiple choice questions testing understanding
3. Teacher notes with learning objectives and common misconceptions

Remember: Output must be valid JSON matching the required schema exactly."""

    def _get_grade_guidance(self, grade: int) -> str:
        """Return age-appropriate language guidance."""
        if grade <= 2:
            return """- Use very simple words (1-2 syllables preferred)
- Short sentences (5-8 words)
- Concrete examples only
- No abstract concepts"""
        elif grade <= 4:
            return """- Simple vocabulary with some new terms (defined)
- Sentences of 8-12 words
- Real-world examples
- Basic cause-and-effect"""
        elif grade <= 6:
            return """- Moderate vocabulary with subject-specific terms
- Varied sentence structure
- Examples and analogies
- Introduction to abstract concepts"""
        elif grade <= 8:
            return """- Academic vocabulary appropriate for middle school
- Complex sentences allowed
- Abstract reasoning
- Multiple perspectives"""
        else:
            return """- Advanced academic vocabulary
- Complex sentence structures
- Abstract and theoretical concepts
- Critical analysis expected"""

    def run(self, input_data: GeneratorInput) -> GeneratorOutput:
        """Run generator with configured retry limit."""
        return super().run(input_data, max_retries=MAX_GENERATION_RETRIES)