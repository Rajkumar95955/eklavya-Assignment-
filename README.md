Governed, Auditable AI Content Pipeline

A structured AI system that generates educational content through a governed, testable, and auditable pipeline.
The project emphasizes engineering discipline over model creativity by enforcing strict schemas, bounded refinement, and a complete audit trail for every run.

📌 Project Overview

AI-generated content systems often lack transparency, explainability, and control. This project addresses those gaps by building a governed AI pipeline where:

Outputs are strictly schema-validated

Quality is quantitatively reviewed

Refinement is bounded and explainable

Every execution produces a full audit record

The system is designed to be deterministic, testable, and production-oriented, making it suitable for regulated or educational use cases.

🎯 Objectives

Generate grade-appropriate educational content

Enforce strict output schemas using validation

Quantitatively evaluate content quality

Refine content with bounded retries

Produce a single RunArtifact capturing the full lifecycle

Ensure the system is fully testable and auditable

🧠 Key Features

Schema-validated content generation (Pydantic)

Quantitative review with pass/fail thresholds

Field-level, explainable feedback

Bounded refinement (maximum two attempts)

Deterministic orchestration logic

Complete audit trail for every run

Mock-friendly design for reliable testing

🧩 Agent Architecture
Generator Agent

Produces an initial draft based on grade and topic

Outputs explanation, MCQs, and teacher notes

Retries once on schema validation failure

Reviewer Agent

Scores content on:

Age appropriateness

Correctness

Clarity

Coverage

Makes a pass/fail decision

Provides field-level feedback

Refiner Agent

Improves content using reviewer feedback

Maximum of two refinement attempts

Each attempt is logged

Tagger Agent

Runs only on approved content

Assigns subject, topic, grade, difficulty, and Bloom’s level

⚙️ Orchestration Logic

The orchestrator coordinates the full pipeline:

Generate content

Review content

Refine and re-review (bounded retries)

Approve and tag, or reject

Produce a single RunArtifact

Key guarantees:

Deterministic flow

No infinite retries

Clear rejection reasons

Full auditability

📦 RunArtifact (Audit Trail)

Each run produces a RunArtifact containing:

Input parameters

All generation, review, and refinement attempts

Final decision (approved or rejected)

Tags (if approved)

Timestamps and execution duration

This artifact serves as the single source of truth for auditing and analysis.

🛠️ Tech Stack

Programming Language: Python

Core Libraries:

Pydantic (schema validation)

Pytest (testing)

FastAPI-ready architecture

Testing:

Mocked LLM calls

Deterministic orchestration tests

🧪 Testing

The project includes tests covering:

Schema validation failure handling

Fail → refine → pass orchestration

Fail → refine → fail → reject orchestration

Complete audit trail integrity

All tests run without real LLM calls to ensure reliability.

🔄 Trade-offs

Determinism over creativity: bounded refinement ensures predictability

Strict schemas over flexibility: improves reliability and validation

Auditability over minimal code: additional structure for traceability

Logic-first design: API and persistence layers are thin wrappers

🚀 Future Extensions

FastAPI endpoints for /generate and /history

Persistence using SQLite or PostgreSQL

Dashboard for viewing run artifacts

Advanced reviewer scoring strategies

Deployment-ready API layer
