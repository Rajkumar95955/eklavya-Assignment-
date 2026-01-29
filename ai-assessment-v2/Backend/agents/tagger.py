"""
Tagger Agent
Responsibility: Classify approved content only.
"""

from .base import BaseAgent
from models import (
    GeneratorInput,
    GeneratorOutput,
    TaggerOutput,
)
import json


class TaggerAgent(BaseAgent[dict, TaggerOutput]):
    """
    Agent that classifies approved educational content.
    
    Rules:
    - Only called for approved content
    - Must provide consistent, accurate tags
    """
    
    name = "TaggerAgent"
    output_schema = TaggerOutput
    
    def _build_system_prompt(self) -> str:
        return """You are an educational content classifier. Your job is to accurately 
tag and categorize educational content for easy discovery and organization.

OUTPUT FORMAT (strict JSON):
{
    "subject": "Mathematics|Science|English|History|...",
    "topic": "Specific topic name",
    "grade": <grade_number>,
    "difficulty": "Easy|Medium|Hard",
    "content_type": ["Explanation", "Quiz", "Exercise", "Example"],
    "blooms_level": "Remembering|Understanding|Applying|Analyzing|Evaluating|Creating",
    "keywords": ["keyword1", "keyword2", ...]
}

BLOOM'S TAXONOMY GUIDE:
- Remembering: Recall facts and basic concepts
- Understanding: Explain ideas or concepts
- Applying: Use information in new situations
- Analyzing: Draw connections among ideas
- Evaluating: Justify a decision or course of action
- Creating: Produce new or original work

Choose the PRIMARY Bloom's level based on what the content primarily teaches/tests."""

    def _build_user_prompt(self, input_data: dict) -> str:
        content_json = json.dumps(input_data["content"].model_dump(), indent=2)
        
        return f"""Classify the following educational content:

ORIGINAL REQUEST:
- Grade: {input_data["grade"]}
- Topic: {input_data["topic"]}

CONTENT:
{content_json}

Provide accurate classification tags."""

    def tag(
        self,
        original_input: GeneratorInput,
        content: GeneratorOutput
    ) -> TaggerOutput:
        """
        Tag approved content.
        
        Args:
            original_input: The original generation request
            content: The approved content to tag
            
        Returns:
            TaggerOutput with classification tags
        """
        input_data = {
            "grade": original_input.grade,
            "topic": original_input.topic,
            "content": content
        }
        
        return super().run(input_data, max_retries=1)