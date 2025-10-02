"""
Collaborative Editing Service
Main service for managing collaborative document editing
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from .operational_transform import operational_transform, Operation, DocumentState
from .websocket_manager import websocket_manager

logger = logging.getLogger(__name__)

class CollaborativeEditingService:
    """Service for managing collaborative document editing"""
    
    def __init__(self):
        self.document_states: Dict[str, DocumentState] = {}
        self.document_locks: Dict[str, bool] = {}
        self.user_sessions: Dict[str, Dict] = {}
        
    async def create_document(self, document_id: str, initial_content: str = "", title: str = "") -> Dict:
        """Create a new collaborative document"""
        try:
            if document_id in self.document_states:
                return {
                    "success": False,
                    "error": "Document already exists"
                }
            
            # Create new document state
            self.document_states[document_id] = DocumentState(document_id, initial_content)
            self.document_locks[document_id] = False
            
            logger.info(f"Created document: {document_id}")
            
            return {
                "success": True,
                "document_id": document_id,
                "version": 0,
                "content": initial_content,
                "title": title or f"Document {document_id}",
                "created_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating document: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to create document: {str(e)}"
            }
    
    async def get_document(self, document_id: str) -> Optional[Dict]:
        """Get document state"""
        try:
            if document_id not in self.document_states:
                return None
            
            state = self.document_states[document_id].get_state()
            return {
                "success": True,
                "document": state
            }
            
        except Exception as e:
            logger.error(f"Error getting document: {str(e)}")
            return None
    
    async def apply_operation(self, document_id: str, operation_data: Dict, user_id: str) -> Dict:
        """Apply operation to document"""
        try:
            if document_id not in self.document_states:
                return {
                    "success": False,
                    "error": "Document not found"
                }
            
            # Check if document is locked
            if self.document_locks.get(document_id, False):
                return {
                    "success": False,
                    "error": "Document is locked"
                }
            
            # Create operation from data
            operation = Operation.from_dict(operation_data)
            
            # Apply operation to document state
            success = self.document_states[document_id].apply_operation(operation)
            
            if success:
                # Broadcast operation to all connected users
                await self._broadcast_operation(document_id, operation, user_id)
                
                return {
                    "success": True,
                    "version": self.document_states[document_id].version,
                    "operation_id": operation.id
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to apply operation"
                }
                
        except Exception as e:
            logger.error(f"Error applying operation: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to apply operation: {str(e)}"
            }
    
    async def get_operation_history(self, document_id: str, from_version: int = 0) -> Dict:
        """Get operation history for document"""
        try:
            if document_id not in self.document_states:
                return {
                    "success": False,
                    "error": "Document not found"
                }
            
            operations = operational_transform.get_operations_since(document_id, from_version)
            operations_data = [op.to_dict() for op in operations]
            
            return {
                "success": True,
                "operations": operations_data,
                "current_version": self.document_states[document_id].version
            }
            
        except Exception as e:
            logger.error(f"Error getting operation history: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to get operation history: {str(e)}"
            }
    
    async def save_document(self, document_id: str, file_path: Optional[str] = None) -> Dict:
        """Save document to persistent storage"""
        try:
            if document_id not in self.document_states:
                return {
                    "success": False,
                    "error": "Document not found"
                }
            
            state = self.document_states[document_id].get_state()
            
            # Save to file if path provided
            if file_path:
                save_path = Path(file_path)
                save_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(save_path, 'w', encoding='utf-8') as f:
                    json.dump(state, f, indent=2, ensure_ascii=False)
            
            return {
                "success": True,
                "message": "Document saved successfully",
                "document_id": document_id,
                "version": state["version"],
                "last_modified": state["last_modified"],
                "file_path": file_path
            }
            
        except Exception as e:
            logger.error(f"Error saving document: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to save document: {str(e)}"
            }
    
    async def load_document(self, document_id: str, file_path: str) -> Dict:
        """Load document from persistent storage"""
        try:
            load_path = Path(file_path)
            if not load_path.exists():
                return {
                    "success": False,
                    "error": "File not found"
                }
            
            with open(load_path, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
            
            # Create document state
            self.document_states[document_id] = DocumentState(document_id, state_data.get("content", ""))
            self.document_states[document_id].version = state_data.get("version", 0)
            self.document_states[document_id].last_modified = state_data.get("last_modified", datetime.now().isoformat())
            
            return {
                "success": True,
                "message": "Document loaded successfully",
                "document_id": document_id,
                "version": self.document_states[document_id].version,
                "content": self.document_states[document_id].content
            }
            
        except Exception as e:
            logger.error(f"Error loading document: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to load document: {str(e)}"
            }
    
    async def lock_document(self, document_id: str, user_id: str) -> Dict:
        """Lock document for exclusive editing"""
        try:
            if document_id not in self.document_states:
                return {
                    "success": False,
                    "error": "Document not found"
                }
            
            if self.document_locks.get(document_id, False):
                return {
                    "success": False,
                    "error": "Document is already locked"
                }
            
            self.document_locks[document_id] = True
            
            # Notify all users about lock
            await self._broadcast_message(document_id, {
                "type": "document_locked",
                "locked_by": user_id,
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "success": True,
                "message": "Document locked successfully"
            }
            
        except Exception as e:
            logger.error(f"Error locking document: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to lock document: {str(e)}"
            }
    
    async def unlock_document(self, document_id: str, user_id: str) -> Dict:
        """Unlock document for collaborative editing"""
        try:
            if document_id not in self.document_states:
                return {
                    "success": False,
                    "error": "Document not found"
                }
            
            if not self.document_locks.get(document_id, False):
                return {
                    "success": False,
                    "error": "Document is not locked"
                }
            
            self.document_locks[document_id] = False
            
            # Notify all users about unlock
            await self._broadcast_message(document_id, {
                "type": "document_unlocked",
                "unlocked_by": user_id,
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "success": True,
                "message": "Document unlocked successfully"
            }
            
        except Exception as e:
            logger.error(f"Error unlocking document: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to unlock document: {str(e)}"
            }
    
    async def get_active_users(self, document_id: str) -> List[Dict]:
        """Get list of active users in document"""
        try:
            if document_id not in self.document_states:
                return []
            
            return self.document_states[document_id].active_users
            
        except Exception as e:
            logger.error(f"Error getting active users: {str(e)}")
            return []
    
    async def _broadcast_operation(self, document_id: str, operation: Operation, user_id: str):
        """Broadcast operation to all connected users"""
        try:
            message = {
                "type": "text_operation",
                "operation": operation.to_dict(),
                "version": self.document_states[document_id].version,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket_manager._broadcast_to_document(document_id, message)
            
        except Exception as e:
            logger.error(f"Error broadcasting operation: {str(e)}")
    
    async def _broadcast_message(self, document_id: str, message: Dict):
        """Broadcast message to all connected users"""
        try:
            await websocket_manager._broadcast_to_document(document_id, message)
        except Exception as e:
            logger.error(f"Error broadcasting message: {str(e)}")
    
    def list_documents(self) -> List[Dict]:
        """List all active documents"""
        try:
            documents = []
            for doc_id, state in self.document_states.items():
                documents.append({
                    "document_id": doc_id,
                    "version": state.version,
                    "last_modified": state.last_modified,
                    "active_users_count": len(state.active_users),
                    "content_length": len(state.content),
                    "is_locked": self.document_locks.get(doc_id, False)
                })
            
            return documents
            
        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            return []

# Global service instance
collaborative_service = CollaborativeEditingService()
