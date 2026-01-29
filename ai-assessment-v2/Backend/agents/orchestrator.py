"""
Orchestrator
Responsibility: Coordinate the full pipeline and produce RunArtifact.
"""

from datetime import datetime
from typing import Optional
import logging

from .generator import GeneratorAgent
from .reviewer import ReviewerAgent
from .refiner import RefinerAgent
from .tagger import TaggerAgent
from .base import AgentError

from models import (
    GeneratorInput,
    GeneratorOutput,
    ReviewerOutput,
    RefinerInput,
    TaggerOutput,
    AttemptRecord,
    FinalResult,
    Timestamps,
    RunArtifact,
)
from config import MAX_REFINEMENT_ATTEMPTS

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Orchestrates the full pipeline:
    1. Generate content
    2. Review content
    3. If review fails, refine (max attempts)
    4. If approved, tag content
    5. Produce complete RunArtifact
    """

    def __init__(self):
        self.generator = GeneratorAgent()
        self.reviewer = ReviewerAgent()
        self.refiner = RefinerAgent()
        self.tagger = TaggerAgent()
        self.max_refinements = MAX_REFINEMENT_ATTEMPTS

    def run(
        self,
        input_data: GeneratorInput,
        user_id: Optional[str] = None
    ) -> RunArtifact:

        artifact = RunArtifact(
            user_id=user_id,
            input=input_data,
            timestamps=Timestamps(started_at=datetime.utcnow())
        )

        try:
            logger.info(f"[Orchestrator] Starting pipeline for Grade {input_data.grade}: {input_data.topic}")

            # Step 1: Generate
            current_content = self._generate(input_data)

            attempt_number = 1
            final_content = None
            final_review = None

            # Step 2: Review loop
            while attempt_number <= self.max_refinements + 1:
                review = self._review(input_data, current_content)

                attempt = AttemptRecord(
                    attempt=attempt_number,
                    draft=current_content,
                    review=review,
                    refined=None
                )

                # Approved
                if review.pass_decision:
                    artifact.attempts.append(attempt)
                    final_content = current_content
                    final_review = review
                    break

                # No more refinements allowed
                if attempt_number > self.max_refinements:
                    artifact.attempts.append(attempt)
                    final_review = review
                    break

                # Refine
                refined_content = self._refine(input_data, current_content, review, attempt_number)
                attempt.refined = refined_content
                artifact.attempts.append(attempt)

                current_content = refined_content
                attempt_number += 1

            # Step 3: Final result
            if final_content is not None:
                tags = self._tag(input_data, final_content)

                artifact.final = FinalResult(
                    status="approved",
                    content=final_content,
                    tags=tags
                )
            else:
                artifact.final = FinalResult(
                    status="rejected",
                    content=None,
                    tags=None,
                    rejection_reason=f"Failed review after {len(artifact.attempts)} attempts. "
                                    f"Final issues: {self._summarize_feedback(final_review)}"
                )

        except AgentError as e:
            logger.error(f"[Orchestrator] Pipeline failed: {e}")
            artifact.final = FinalResult(
                status="rejected",
                content=None,
                tags=None,
                rejection_reason=f"Pipeline error: {str(e)}"
            )

        except Exception as e:
            logger.error(f"[Orchestrator] Unexpected error: {e}")
            artifact.final = FinalResult(
                status="rejected",
                content=None,
                tags=None,
                rejection_reason=f"Unexpected error: {str(e)}"
            )

        finally:
            artifact.timestamps.finished_at = datetime.utcnow()
            artifact.timestamps.duration_seconds = (
                artifact.timestamps.finished_at - artifact.timestamps.started_at
            ).total_seconds()

        return artifact

    def _generate(self, input_data: GeneratorInput) -> GeneratorOutput:
        return self.generator.run(input_data)

    def _review(self, input_data: GeneratorInput, content: GeneratorOutput) -> ReviewerOutput:
        return self.reviewer.review(input_data, content)

    def _refine(
        self,
        input_data: GeneratorInput,
        content: GeneratorOutput,
        review: ReviewerOutput,
        attempt: int
    ) -> GeneratorOutput:
        refiner_input = RefinerInput(
            original_input=input_data,
            current_content=content,
            feedback=review.feedback,
            attempt_number=attempt
        )
        # IMPORTANT: must use run(), not refine()
        return self.refiner.run(refiner_input)

    def _tag(self, input_data: GeneratorInput, content: GeneratorOutput) -> TaggerOutput:
        # IMPORTANT: must use run(), not tag()
        return self.tagger.run(input_data, content)

    def _summarize_feedback(self, review: Optional[ReviewerOutput]) -> str:
        if not review or not review.feedback:
            return "No specific feedback available"

        critical = [f for f in review.feedback if f.severity == "critical"]
        if critical:
            return "; ".join(f"{f.field}: {f.issue}" for f in critical[:3])

        return "; ".join(f"{f.field}: {f.issue}" for f in review.feedback[:3])
