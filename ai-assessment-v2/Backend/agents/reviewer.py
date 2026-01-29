"""
Reviewer Agent
Responsibility: Quantitatively evaluate quality and decide pass/fail.
"""

from .base import BaseAgent
from models import (
    GeneratorInput,
    GeneratorOutput, 
    ReviewerOutput,
    ReviewScore,
    ReviewFeedback,
)
from config import PASS_THRESHOLDS, MIN_AVERAGE_SCORE


class ReviewerAgent(BaseAgent[dict, ReviewerOutput]):
    """
    Agent that reviews educational content for quality and appropriateness.
    
    Rules:
    - Define and document pass thresholds
    - Feedback must reference specific fields (explainable review)
    - Quantitative scores on 1-5 scale
    """
    
    name = "ReviewerAgent"
    output_schema = ReviewerOutput
    
    def __init__(self):
        super().__init__()
        self.thresholds = PASS_THRESHOLDS
        self.min_average = MIN_AVERAGE_SCORE
    
    def _build_system_prompt(self) -> str:
        threshold_text = "\n".join(
            f"- {k}: minimum {v}/5" for k, v in self.thresholds.items()
        )
        
        return f"""You are an expert educational content reviewer and quality gatekeeper.
Your job is to evaluate content rigorously and provide actionable feedback.

EVALUATION CRITERIA (1-5 scale):
1. age_appropriateness: Is vocabulary/complexity suitable for the grade?
2. correctness: Are all facts and MCQ answers accurate?
3. clarity: Is the content easy to understand?
4. coverage: Does it adequately cover the topic?

PASS THRESHOLDS:
{threshold_text}
- Minimum average score: {self.min_average}

OUTPUT FORMAT (strict JSON):
{{
    "scores": {{
        "age_appropriateness": <1-5>,
        "correctness": <1-5>,
        "clarity": <1-5>,
        "coverage": <1-5>
    }},
    "pass": <true/false>,
    "feedback": [
        {{
            "field": "path.to.field",
            "issue": "Description of problem",
            "severity": "critical|major|minor",
            "suggestion": "How to fix it"
        }}
    ],
    "summary": "Brief overall assessment"
}}

RULES:
1. Be strict but fair
2. Feedback MUST reference specific fields using dot notation
3. Mark "pass": false if ANY threshold is not met
4. Provide at least one feedback item even if passing"""

    def _build_user_prompt(self, input_data: dict) -> str:
        import json
        
        grade = input_data["grade"]
        topic = input_data["topic"]
        content = input_data["content"]
        
        content_json = json.dumps(content.model_dump(), indent=2)
        
        return f"""Review the following educational content:

TARGET GRADE: {grade}
TOPIC: {topic}

CONTENT TO REVIEW:
{content_json}

Evaluate against all criteria and determine if it passes quality thresholds.
Provide specific, actionable feedback referencing exact fields."""

    def review(
        self, 
        original_input: GeneratorInput, 
        content: GeneratorOutput
    ) -> ReviewerOutput:
        """
        Review generated content.
        
        Args:
            original_input: The original generation request
            content: The generated content to review
            
        Returns:
            ReviewerOutput with scores, pass decision, and feedback
        """
        input_data = {
            "grade": original_input.grade,
            "topic": original_input.topic,
            "content": content
        }
        
        result = super().run(input_data, max_retries=1)
        
        # Validate pass decision against thresholds
        result = self._validate_pass_decision(result)
        
        return result
    
    def _validate_pass_decision(self, result: ReviewerOutput) -> ReviewerOutput:
        """
        Ensure pass decision is consistent with thresholds.
        LLM might not correctly apply thresholds, so we enforce them.
        """
        scores = result.scores
        
        # Check each threshold
        should_pass = True
        reasons = []
        
        for criterion, threshold in self.thresholds.items():
            score = getattr(scores, criterion)
            if score < threshold:
                should_pass = False
                reasons.append(f"{criterion} ({score}) below threshold ({threshold})")
        
        # Check average
        avg_score = (
            scores.age_appropriateness + 
            scores.correctness + 
            scores.clarity + 
            scores.coverage
        ) / 4
        
        if avg_score < self.min_average:
            should_pass = False
            reasons.append(f"Average score ({avg_score:.1f}) below minimum ({self.min_average})")
        
        # Update pass decision if needed
        if result.pass_decision != should_pass:
            result = ReviewerOutput(
                scores=result.scores,
                pass_decision=should_pass,
                feedback=result.feedback,
                summary=result.summary + f" [Auto-corrected: {'; '.join(reasons)}]"
            )
        
        return result