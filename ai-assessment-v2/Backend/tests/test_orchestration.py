"""
Test 2 & 3: Orchestration tests
- Fail → refine → pass orchestration
- Fail → refine → fail → reject orchestration
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from agents import Orchestrator, GeneratorAgent, ReviewerAgent, RefinerAgent, TaggerAgent
from models import (
    GeneratorInput,
    GeneratorOutput,
    ReviewerOutput,
    TaggerOutput,
    RunArtifact,
)


class TestOrchestrationSuccess:
    """Test 2: Fail → refine → pass orchestration."""
    
    @patch.object(TaggerAgent, 'run')
    @patch.object(RefinerAgent, 'run')
    @patch.object(ReviewerAgent, 'review')
    @patch.object(GeneratorAgent, 'run')
    def test_fail_refine_pass(
        self,
        mock_generator_run,
        mock_reviewer_review,
        mock_refiner_run,
        mock_tagger_run,
        sample_generator_input,
        sample_valid_generator_output,
        sample_failing_review,
        sample_passing_review,
        sample_tags
    ):
        """
        Scenario:
        1. Generator creates content
        2. Reviewer fails the content
        3. Refiner improves content
        4. Reviewer passes the refined content
        5. Tagger tags the approved content
        6. Final status: approved
        """
        # Setup mocks
        mock_generator_run.return_value = sample_valid_generator_output
        
        # First review fails, second review passes
        mock_reviewer_review.side_effect = [
            sample_failing_review,
            sample_passing_review
        ]
        
        # Refiner returns improved content
        mock_refiner_run.return_value = sample_valid_generator_output
        
        # Tagger returns tags
        mock_tagger_run.return_value = sample_tags
        
        # Run orchestrator
        orchestrator = Orchestrator()
        result = orchestrator.run(sample_generator_input, user_id="test-user")
        
        # Assertions
        assert isinstance(result, RunArtifact)
        assert result.final.status == "approved"
        assert result.final.content is not None
        assert result.final.tags is not None
        assert len(result.attempts) == 2  # Initial + 1 refinement
        
        # Verify first attempt failed
        assert result.attempts[0].review.pass_decision == False
        assert result.attempts[0].refined is not None
        
        # Verify second attempt passed
        assert result.attempts[1].review.pass_decision == True
        
        # Verify tagger was called
        mock_tagger_run.assert_called_once()
    
    @patch.object(ReviewerAgent, 'review')
    @patch.object(GeneratorAgent, 'run')
    def test_pass_on_first_attempt(
        self,
        mock_generator_run,
        mock_reviewer_review,
        sample_generator_input,
        sample_valid_generator_output,
        sample_passing_review
    ):
        """Content passes on first attempt - no refinement needed."""
        mock_generator_run.return_value = sample_valid_generator_output
        mock_reviewer_review.return_value = sample_passing_review
        
        with patch.object(TaggerAgent, 'run') as mock_tagger:
            mock_tagger.return_value = TaggerOutput(
                subject="Mathematics",
                topic="Fractions",
                grade=5,
                difficulty="Medium",
                content_type=["Explanation", "Quiz"],
                blooms_level="Understanding",
                keywords=["fractions"]
            )
            
            orchestrator = Orchestrator()
            result = orchestrator.run(sample_generator_input)
        
        assert result.final.status == "approved"
        assert len(result.attempts) == 1  # Only initial attempt
        assert result.attempts[0].refined is None  # No refinement


class TestOrchestrationRejection:
    """Test 3: Fail → refine → fail → reject orchestration."""
    
    @patch.object(RefinerAgent, 'run')
    @patch.object(ReviewerAgent, 'review')
    @patch.object(GeneratorAgent, 'run')
    def test_fail_refine_fail_reject(
        self,
        mock_generator_run,
        mock_reviewer_review,
        mock_refiner_run,
        sample_generator_input,
        sample_valid_generator_output,
        sample_failing_review
    ):
        """
        Scenario:
        1. Generator creates content
        2. Reviewer fails the content
        3. Refiner attempts to improve (attempt 1)
        4. Reviewer fails again
        5. Refiner attempts to improve (attempt 2)
        6. Reviewer fails again
        7. Max refinements reached → rejected
        8. Tagger is NOT called
        """
        # Setup mocks
        mock_generator_run.return_value = sample_valid_generator_output
        
        # All reviews fail
        mock_reviewer_review.return_value = sample_failing_review
        
        # Refiner returns content (but it still fails review)
        mock_refiner_run.return_value = sample_valid_generator_output
        
        # Run orchestrator
        orchestrator = Orchestrator()
        result = orchestrator.run(sample_generator_input, user_id="test-user")
        
        # Assertions
        assert isinstance(result, RunArtifact)
        assert result.final.status == "rejected"
        assert result.final.content is None
        assert result.final.tags is None
        assert result.final.rejection_reason is not None
        
        # Should have 3 attempts: initial + 2 refinements
        assert len(result.attempts) == 3
        
        # All reviews should have failed
        for attempt in result.attempts:
            assert attempt.review.pass_decision == False
    
    @patch.object(RefinerAgent, 'run')
    @patch.object(ReviewerAgent, 'review')
    @patch.object(GeneratorAgent, 'run')
    def test_fail_refine_once_then_pass(
        self,
        mock_generator_run,
        mock_reviewer_review,
        mock_refiner_run,
        sample_generator_input,
        sample_valid_generator_output,
        sample_failing_review,
        sample_passing_review
    ):
        """Content fails twice then passes on third attempt."""
        mock_generator_run.return_value = sample_valid_generator_output
        mock_refiner_run.return_value = sample_valid_generator_output
        
        # Fail, fail, pass
        mock_reviewer_review.side_effect = [
            sample_failing_review,
            sample_failing_review,
            sample_passing_review
        ]
        
        with patch.object(TaggerAgent, 'run') as mock_tagger:
            mock_tagger.return_value = TaggerOutput(
                subject="Mathematics",
                topic="Fractions",
                grade=5,
                difficulty="Medium",
                content_type=["Explanation"],
                blooms_level="Understanding",
                keywords=["fractions"]
            )
            
            orchestrator = Orchestrator()
            result = orchestrator.run(sample_generator_input)
        
        assert result.final.status == "approved"
        assert len(result.attempts) == 3


class TestOrchestrationAuditTrail:
    """Test audit trail completeness."""
    
    @patch.object(ReviewerAgent, 'review')
    @patch.object(GeneratorAgent, 'run')
    def test_artifact_has_complete_audit_trail(
        self,
        mock_generator_run,
        mock_reviewer_review,
        sample_generator_input,
        sample_valid_generator_output,
        sample_passing_review
    ):
        """RunArtifact should contain complete audit information."""
        mock_generator_run.return_value = sample_valid_generator_output
        mock_reviewer_review.return_value = sample_passing_review
        
        with patch.object(TaggerAgent, 'run') as mock_tagger:
            mock_tagger.return_value = TaggerOutput(
                subject="Mathematics",
                topic="Fractions",
                grade=5,
                difficulty="Medium",
                content_type=["Explanation"],
                blooms_level="Understanding",
                keywords=["fractions"]
            )
            
            orchestrator = Orchestrator()
            result = orchestrator.run(sample_generator_input, user_id="audit-test")
        
        # Check all required fields
        assert result.run_id is not None
        assert result.user_id == "audit-test"
        assert result.input == sample_generator_input
        assert len(result.attempts) >= 1
        assert result.final is not None
        assert result.timestamps.started_at is not None
        assert result.timestamps.finished_at is not None
        assert result.timestamps.duration_seconds >= 0
        
        # Check attempt structure
        attempt = result.attempts[0]
        assert attempt.attempt == 1
        assert attempt.draft is not None
        assert attempt.review is not None
        assert attempt.timestamp is not None
    
    def test_artifact_serialization(self, sample_generator_input, sample_valid_generator_output, sample_passing_review):
        """RunArtifact should serialize to JSON correctly."""
        with patch.object(GeneratorAgent, 'run') as mock_gen:
            with patch.object(ReviewerAgent, 'review') as mock_rev:
                with patch.object(TaggerAgent, 'run') as mock_tag:
                    mock_gen.return_value = sample_valid_generator_output
                    mock_rev.return_value = sample_passing_review
                    mock_tag.return_value = TaggerOutput(
                        subject="Mathematics",
                        topic="Fractions",
                        grade=5,
                        difficulty="Medium",
                        content_type=["Explanation"],
                        blooms_level="Understanding",
                        keywords=["fractions"]
                    )
                    
                    orchestrator = Orchestrator()
                    result = orchestrator.run(sample_generator_input)
        
        # Should serialize without error
        json_str = result.model_dump_json()
        assert isinstance(json_str, str)
        
        # Should deserialize back
        parsed = json.loads(json_str)
        assert parsed['run_id'] == result.run_id
        assert parsed['final']['status'] == 'approved'