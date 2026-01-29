Governed, Auditable AI Content Pipeline (AI Assessment – Part 2)
Overview

This project implements a deterministic, testable, and auditable AI content generation pipeline for educational material.
The system focuses on engineering discipline: strict schemas, bounded refinement, explainable decisions, and a complete audit trail for every run.

The core output of the system is a RunArtifact that captures the full lifecycle of a content generation attempt.

Agent Roles
1. Generator Agent

Purpose:
Generate a first draft of educational content for a given grade and topic.

Responsibilities:

Produce explanation text, MCQs, and teacher notes.

Enforce strict schema validation using Pydantic.

Retry once on schema validation failure.

Fail gracefully if validation fails again.

Guarantees:

Schema-valid output

Grade-appropriate language

Deterministic behavior per run

2. Reviewer Agent (Gatekeeper)

Purpose:
Quantitatively evaluate content quality and decide pass/fail.

Responsibilities:

Assign numeric scores (1–5) for:

Age appropriateness

Correctness

Clarity

Coverage

Produce an explicit pass/fail decision.

Provide field-level feedback for explainability.

Guarantees:

Transparent, explainable review decisions

Clear failure reasons tied to specific content fields

3. Refiner Agent

Purpose:
Improve content using structured reviewer feedback.

Responsibilities:

Apply reviewer feedback to refine content.

Maximum of two refinement attempts.

Each refinement attempt is logged.

Guarantees:

Bounded retries

No infinite refinement loops

Clear rejection when improvement fails

4. Tagger Agent

Purpose:
Classify approved content only.

Responsibilities:

Assign subject, topic, grade, difficulty, Bloom’s level, and content type.

Guarantees:

Never runs on rejected content

Produces lightweight, structured metadata

Pass / Fail Criteria
Pass Conditions

Content is approved when:

Schema validation succeeds

Reviewer pass decision is true

Quality scores meet defined thresholds

Tagger successfully classifies the content

Fail Conditions

Content is rejected when:

Schema validation fails twice

Reviewer fails content after maximum refinements

An agent error occurs during the pipeline

Each failure includes a clear rejection reason stored in the final artifact.

Orchestration Decisions

The orchestrator enforces a strict, deterministic pipeline:

Generate initial content

Review content

If review fails:

Refine → Review again

Maximum 2 refinements

If approved:

Tag content

Produce a single RunArtifact

Key Design Decisions

Bounded retries prevent runaway costs and non-determinism

Single source of truth (RunArtifact) for auditing

Early rejection on unrecoverable failure

Mock-friendly design for deterministic testing

RunArtifact (Audit Trail)

Each pipeline run produces a RunArtifact containing:

Input parameters

All attempts (draft → review → refinement)

Final decision (approved / rejected)

Tags (if approved)

Timestamps and execution duration

This ensures full traceability and explainability.

Trade-offs
Chosen Trade-offs

Determinism over creativity:
Limits refinement attempts to ensure predictability.

Explicit schemas over flexibility:
Strict validation reduces ambiguity but requires more structure.

Auditability over speed:
Full logging slightly increases overhead but enables governance.

Deferred Features

Full persistence layer (SQLite/Postgres) can be added easily.

API layer (FastAPI endpoints) is a thin wrapper over existing logic.

UI intentionally omitted (non-scoring).

Testing

The system includes comprehensive tests covering:

Schema validation failures

Fail → refine → pass orchestration

Fail → refine → fail → reject orchestration

Complete audit trail integrity

All LLM calls are mocked to ensure fast, deterministic tests.

Summary

This project demonstrates:

Strong separation of concerns

Governed AI execution

Explainable decision-making

Test-driven orchestration design

The focus is engineering rigor, not agent count.
