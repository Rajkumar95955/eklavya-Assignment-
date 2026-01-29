"""
FastAPI Backend
Exposes the agent pipeline via REST API.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import logging

from agents import Orchestrator
from models import GeneratorInput, RunArtifact
from storage import ArtifactRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="AI Assessment API v2",
    description="Governed, Auditable AI Content Pipeline",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
orchestrator = Orchestrator()
repository = ArtifactRepository()


# ============== API Endpoints ==============

@app.get("/")
async def root():
    """API information."""
    return {
        "name": "AI Assessment API v2",
        "version": "2.0.0",
        "description": "Governed, Auditable AI Content Pipeline",
        "endpoints": {
            "POST /generate": "Run full pipeline, returns RunArtifact",
            "GET /history": "Get stored artifacts (optionally filtered by user_id)",
            "GET /artifact/{run_id}": "Get specific artifact by ID",
            "GET /stats": "Get aggregate statistics",
            "GET /health": "Health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.0.0"}


@app.post("/generate", response_model=RunArtifact)
async def generate_content(
    request: GeneratorInput,
    user_id: Optional[str] = Query(None, description="User identifier")
):
    """
    Run the full agent pipeline.
    
    Returns a complete RunArtifact with:
    - All generation attempts
    - Review scores and feedback
    - Refinement history
    - Final decision (approved/rejected)
    - Tags (if approved)
    - Full timestamps
    """
    try:
        logger.info(f"Starting pipeline: Grade {request.grade}, Topic: {request.topic}")
        
        # Run pipeline
        artifact = orchestrator.run(request, user_id=user_id)
        
        # Store artifact
        repository.save(artifact)
        
        logger.info(f"Pipeline complete: {artifact.run_id} - {artifact.final.status}")
        
        return artifact
    
    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history", response_model=List[RunArtifact])
async def get_history(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results")
):
    """
    Retrieve stored RunArtifacts.
    
    Optionally filter by user_id.
    """
    try:
        if user_id:
            artifacts = repository.get_by_user(user_id, limit=limit)
        else:
            artifacts = repository.get_all(limit=limit)
        
        return artifacts
    
    except Exception as e:
        logger.error(f"History retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/artifact/{run_id}", response_model=RunArtifact)
async def get_artifact(run_id: str):
    """
    Retrieve a specific RunArtifact by ID.
    """
    artifact = repository.get(run_id)
    
    if not artifact:
        raise HTTPException(status_code=404, detail=f"Artifact {run_id} not found")
    
    return artifact


@app.get("/stats")
async def get_stats():
    """
    Get aggregate statistics about pipeline runs.
    """
    return repository.get_stats()


# ============== Run Server ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)