"""
Judgment Metadata Storage Service
Manages persistent storage of judgment metadata using JSON files
"""

import json
import os
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class JudgmentMetadataStorage:
    """Service for managing judgment metadata storage"""
    
    def __init__(self, storage_dir: str = "judgment_metadata"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.metadata_file = self.storage_dir / "judgments.json"
        
        # Initialize storage if it doesn't exist
        if not self.metadata_file.exists():
            self._initialize_storage()

    def _initialize_storage(self):
        """Initialize the metadata storage file"""
        initial_data = {
            "judgments": [],
            "last_updated": datetime.now().isoformat(),
            "version": "1.0"
        }
        self._save_data(initial_data)

    def _load_data(self) -> Dict:
        """Load all metadata from storage"""
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading metadata: {str(e)}")
            return {"judgments": [], "last_updated": datetime.now().isoformat()}

    def _save_data(self, data: Dict):
        """Save all metadata to storage"""
        try:
            data["last_updated"] = datetime.now().isoformat()
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving metadata: {str(e)}")

    def save_judgment_metadata(self, judgment_id: int, metadata: Dict) -> bool:
        """Save metadata for a specific judgment"""
        try:
            data = self._load_data()
            
            # Add or update judgment metadata
            judgment_data = {
                "id": judgment_id,
                "filename": metadata.get("filename", ""),
                "petitioner": metadata.get("petitioner", "Unknown Petitioner"),
                "respondent": metadata.get("respondent", "Unknown Respondent"),
                "judgment_date": metadata.get("judgment_date"),
                "case_number": metadata.get("case_number", ""),
                "court": metadata.get("court", "Supreme Court"),
                "case_title": metadata.get("case_title", ""),
                "summary": metadata.get("summary", ""),
                "judges": metadata.get("judges", []),
                "extraction_date": metadata.get("extraction_date", datetime.now().isoformat()),
                "extraction_status": metadata.get("extraction_status", "success"),
                "file_path": metadata.get("file_path", ""),
                "file_size": metadata.get("file_size", 0),
                "upload_date": metadata.get("upload_date", datetime.now().isoformat())
            }
            
            # Check if judgment already exists
            existing_index = None
            for i, existing in enumerate(data["judgments"]):
                if existing["id"] == judgment_id:
                    existing_index = i
                    break
            
            if existing_index is not None:
                # Update existing judgment
                data["judgments"][existing_index] = judgment_data
            else:
                # Add new judgment
                data["judgments"].append(judgment_data)
            
            self._save_data(data)
            return True
            
        except Exception as e:
            logger.error(f"Error saving judgment metadata: {str(e)}")
            return False

    def get_judgment_metadata(self, judgment_id: int) -> Optional[Dict]:
        """Get metadata for a specific judgment"""
        try:
            data = self._load_data()
            for judgment in data["judgments"]:
                if judgment["id"] == judgment_id:
                    return judgment
        except Exception as e:
            logger.error(f"Error getting judgment metadata: {str(e)}")
        
        return None

    def get_all_judgments(self) -> List[Dict]:
        """Get metadata for all judgments"""
        try:
            data = self._load_data()
            return data.get("judgments", [])
        except Exception as e:
            logger.error(f"Error getting all judgments: {str(e)}")
            return []

    def delete_judgment_metadata(self, judgment_id: int) -> bool:
        """Delete metadata for a specific judgment"""
        try:
            data = self._load_data()
            data["judgments"] = [j for j in data["judgments"] if j["id"] != judgment_id]
            self._save_data(data)
            return True
        except Exception as e:
            logger.error(f"Error deleting judgment metadata: {str(e)}")
            return False

    def search_judgments(self, query: str) -> List[Dict]:
        """Search judgments by query"""
        try:
            judgments = self.get_all_judgments()
            query_lower = query.lower()
            
            results = []
            for judgment in judgments:
                # Search in various fields
                searchable_text = " ".join([
                    judgment.get("case_title", ""),
                    judgment.get("petitioner", ""),
                    judgment.get("respondent", ""),
                    judgment.get("case_number", ""),
                    judgment.get("summary", ""),
                    judgment.get("court", "")
                ]).lower()
                
                if query_lower in searchable_text:
                    results.append(judgment)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching judgments: {str(e)}")
            return []

    def get_storage_stats(self) -> Dict:
        """Get storage statistics"""
        try:
            data = self._load_data()
            judgments = data.get("judgments", [])
            
            return {
                "total_judgments": len(judgments),
                "last_updated": data.get("last_updated"),
                "storage_file_size": self.metadata_file.stat().st_size if self.metadata_file.exists() else 0,
                "successful_extractions": len([j for j in judgments if j.get("extraction_status") == "success"]),
                "failed_extractions": len([j for j in judgments if j.get("extraction_status") == "error"])
            }
        except Exception as e:
            logger.error(f"Error getting storage stats: {str(e)}")
            return {"total_judgments": 0, "error": str(e)}
