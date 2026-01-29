# 🧠 AI Assessment – Part 2

## Governed, Auditable AI Content Pipeline

This repository implements a **deterministic, auditable AI content generation pipeline** for educational material, extending **Part 1** with governance, validation, quality gates, bounded refinement, persistence, and testing.

The focus is **engineering discipline**, not agent count or UI polish.

---

## 📌 Core Objective

Build a pipeline where:

* All AI outputs are **schema-validated**
* Content quality is **quantitatively evaluated**
* Refinement is **bounded and explainable**
* Every run produces a **single, complete audit artifact**
* The system is **fully testable**
* All decisions are **deterministic and logged**

---

## 🏗️ Architecture Overview

```
POST /generate
  → Generator Agent
      → Schema Validation (retry once)
  → Reviewer Agent
      → Pass / Fail decision
  → Refiner Agent (max 2 attempts if failed)
      → Re-review after each refinement
  → Tagger Agent (only if approved)
  → Persist RunArtifact
  → Return RunArtifact
```

All steps contribute to **one immutable RunArtifact**.

---

## 🧩 Agent Roles

### 1️⃣ Generator Agent

**Purpose**
Generate an initial educational artifact for a given grade and topic.

**Input**

```json
{ "grade": 5, "topic": "Fractions as parts of a whole" }
```

**Output (Strictly Schema-Validated)**

* Explanation (grade-appropriate)
* MCQs
* Teacher notes

**Rules**

* Output must validate against Pydantic schema
* One automatic retry on schema failure
* Second failure → pipeline terminates gracefully
* No free-form output allowed

---

### 2️⃣ Reviewer Agent (Gatekeeper)

**Purpose**
Quantitatively evaluate content quality and decide pass/fail.

**Output**

```json
{
  "scores": {
    "age_appropriateness": 1-5,
    "correctness": 1-5,
    "clarity": 1-5,
    "coverage": 1-5
  },
  "pass": true,
  "feedback": [
    { "field": "explanation.text", "issue": "Sentence too complex" }
  ]
}
```

**Pass Criteria**

* Each score ≥ **3**
* Average score ≥ **3.5**
* No critical correctness issues

**Key Property**

* Feedback is **field-level and explainable**
* No subjective or vague feedback allowed

---

### 3️⃣ Refiner Agent

**Purpose**
Improve content using **only reviewer feedback**.

**Rules**

* Maximum **2 refinement attempts**
* Each attempt is logged
* Refinement is deterministic (same input → same output)
* If content still fails after 2 attempts → **rejected**

---

### 4️⃣ Tagger Agent

**Purpose**
Classify **approved content only**.

**Output**

```json
{
  "subject": "Mathematics",
  "topic": "Fractions",
  "grade": 5,
  "difficulty": "Medium",
  "content_type": ["Explanation", "Quiz"],
  "blooms_level": "Understanding"
}
```

**Rule**

* Never invoked if content is rejected

---

## 🔁 Orchestration Decisions

* **Deterministic flow** (no branching randomness)
* **Bounded retries**

  * Generator: 1 retry on schema failure
  * Refiner: max 2 attempts
* **Single RunArtifact per request**
* **Fail-fast** on unrecoverable errors
* **Explainability first**: every decision is logged

---

## 🧾 RunArtifact (Audit Trail)

Every `/generate` call returns and stores:

```json
{
  "run_id": "...",
  "input": { "grade": 5, "topic": "Fractions" },
  "attempts": [
    {
      "attempt": 1,
      "draft": { ... },
      "review": { ... },
      "refined": { ... }
    }
  ],
  "final": {
    "status": "approved | rejected",
    "content": { ... },
    "tags": { ... }
  },
  "timestamps": {
    "started_at": "...",
    "finished_at": "..."
  }
}
```

This artifact captures the **entire lifecycle** of the generation attempt.

---

## 💾 Persistence

* All RunArtifacts are stored
* Includes:

  * Inputs
  * Drafts
  * Reviews
  * Refinements
  * Final decision
  * Tags
  * Timestamps

**Database**

* SQLite (default)
* PostgreSQL compatible

---

## 🌐 API Endpoints

### `POST /generate`

Runs the full pipeline and returns the RunArtifact.

### `GET /history?user_id=...`

Returns stored RunArtifacts for a user.

---

## 🧪 Testing (Mandatory & Implemented)

LLM calls are **mocked**.

### Included Tests

1. **Schema validation failure handling**
2. **Fail → refine → pass orchestration**
3. **Fail → refine → fail → reject orchestration**

Tests ensure:

* Retry limits are enforced
* Final status is correct
* Audit trail is complete

---

## ⚖️ Trade-offs

* **Determinism over creativity**
  Ensures reproducibility and auditability.
* **Strict schemas over flexibility**
  Prevents silent failures.
* **Bounded refinement over infinite loops**
  Guarantees termination.
* **No agent autonomy**
  Orchestrator controls all flow.

---

## 🚫 Explicitly Excluded

* No background jobs
* No streaming
* No auto-scaling agents
* No UI dependency (frontend optional)
* No venv committed

---

## 🧪 Setup

```bash
pip install -r requirements.txt
```

Environment variables are documented in `.env.example`.

-
