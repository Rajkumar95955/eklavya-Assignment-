"""
Configuration and constants for the AI Assessment Pipeline.
"""

import os
from dotenv import load_dotenv
from typing import Dict

load_dotenv()

# ============== API Configuration ==============
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")

# ============== Pipeline Configuration ==============
MAX_GENERATION_RETRIES = 1  # Retry once on schema validation failure
MAX_REFINEMENT_ATTEMPTS = 2  # Maximum refinement passes

# ============== Pass/Fail Thresholds ==============
# Each score is 1-5. Content passes if ALL criteria meet thresholds.
PASS_THRESHOLDS: Dict[str, int] = {
    "age_appropriateness": 4,  # Must be >= 4
    "correctness": 5,          # Must be perfect (5)
    "clarity": 4,              # Must be >= 4
    "coverage": 3,             # Must be >= 3
}

# Minimum average score required
MIN_AVERAGE_SCORE = 4.0

# ============== Storage Configuration ==============
STORAGE_PATH = os.getenv("STORAGE_PATH", "./data/artifacts.json")