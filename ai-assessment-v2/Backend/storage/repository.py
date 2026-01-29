"""
Artifact storage repository using TinyDB.
"""

from typing import List, Optional
from datetime import datetime
from tinydb import TinyDB, Query
from pathlib import Path
import json

from models import RunArtifact
from config import STORAGE_PATH


class ArtifactRepository:
    """
    Repository for storing and retrieving RunArtifacts.
    Uses TinyDB for simple file-based persistence.
    """
    
    def __init__(self, storage_path: str = STORAGE_PATH):
        # Ensure directory exists
        Path(storage_path).parent.mkdir(parents=True, exist_ok=True)
        self.db = TinyDB(storage_path)
        self.artifacts = self.db.table('artifacts')
    
    def save(self, artifact: RunArtifact) -> str:
        """
        Save a RunArtifact.
        
        Args:
            artifact: The artifact to save
            
        Returns:
            The run_id of the saved artifact
        """
        # Convert to dict with JSON-serializable datetimes
        data = json.loads(artifact.model_dump_json())
        
        # Check if exists (update) or new (insert)
        Artifact = Query()
        existing = self.artifacts.search(Artifact.run_id == artifact.run_id)
        
        if existing:
            self.artifacts.update(data, Artifact.run_id == artifact.run_id)
        else:
            self.artifacts.insert(data)
        
        return artifact.run_id
    
    def get(self, run_id: str) -> Optional[RunArtifact]:
        """
        Retrieve a RunArtifact by ID.
        
        Args:
            run_id: The unique run identifier
            
        Returns:
            RunArtifact if found, None otherwise
        """
        Artifact = Query()
        results = self.artifacts.search(Artifact.run_id == run_id)
        
        if not results:
            return None
        
        return RunArtifact(**results[0])
    
    def get_by_user(self, user_id: str, limit: int = 50) -> List[RunArtifact]:
        """
        Retrieve all artifacts for a user.
        
        Args:
            user_id: The user identifier
            limit: Maximum number of results
            
        Returns:
            List of RunArtifacts
        """
        Artifact = Query()
        results = self.artifacts.search(Artifact.user_id == user_id)
        
        # Sort by timestamp (newest first) and limit
        results.sort(key=lambda x: x.get('timestamps', {}).get('started_at', ''), reverse=True)
        results = results[:limit]
        
        return [RunArtifact(**r) for r in results]
    
    def get_all(self, limit: int = 100) -> List[RunArtifact]:
        """
        Retrieve all artifacts.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of RunArtifacts
        """
        results = self.artifacts.all()
        
        # Sort by timestamp (newest first) and limit
        results.sort(key=lambda x: x.get('timestamps', {}).get('started_at', ''), reverse=True)
        results = results[:limit]
        
        return [RunArtifact(**r) for r in results]
    
    def get_stats(self) -> dict:
        """Get aggregate statistics."""
        all_artifacts = self.artifacts.all()
        
        approved = sum(1 for a in all_artifacts if a.get('final', {}).get('status') == 'approved')
        rejected = sum(1 for a in all_artifacts if a.get('final', {}).get('status') == 'rejected')
        
        return {
            "total_runs": len(all_artifacts),
            "approved": approved,
            "rejected": rejected,
            "approval_rate": approved / len(all_artifacts) if all_artifacts else 0
        }
    
    def clear(self):
        """Clear all artifacts (for testing)."""
        self.artifacts.truncate()