"""
Operational Transform (OT) Implementation for Collaborative Editing
Handles document synchronization and conflict resolution
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class Operation:
    """Represents a single operation on a document"""
    
    def __init__(self, op_type: str, position: int, **kwargs):
        self.id = str(uuid.uuid4())
        self.type = op_type  # 'insert', 'delete', 'retain'
        self.position = position
        self.timestamp = datetime.now().isoformat()
        
        # User attribution
        self.user_id = kwargs.get("user_id", "")
        self.username = kwargs.get("username", "Anonymous")
        self.user_color = kwargs.get("user_color", "#7c3aed")
        
        # Operation-specific data
        if op_type == "insert":
            self.text = kwargs.get("text", "")
            self.length = len(self.text)
        elif op_type == "delete":
            self.length = kwargs.get("length", 0)
            self.text = ""
        elif op_type == "retain":
            self.length = kwargs.get("length", 0)
            self.text = ""
        else:
            raise ValueError(f"Unknown operation type: {op_type}")
    
    def to_dict(self) -> Dict:
        """Convert operation to dictionary"""
        return {
            "id": self.id,
            "type": self.type,
            "position": self.position,
            "text": self.text,
            "length": self.length,
            "timestamp": self.timestamp,
            "user_id": self.user_id,
            "username": self.username,
            "user_color": self.user_color
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Operation':
        """Create operation from dictionary"""
        op = cls(
            op_type=data["type"],
            position=data["position"],
            text=data.get("text", ""),
            length=data.get("length", 0),
            user_id=data.get("user_id", ""),
            username=data.get("username", "Anonymous"),
            user_color=data.get("user_color", "#7c3aed")
        )
        op.id = data.get("id", str(uuid.uuid4()))
        op.timestamp = data.get("timestamp", datetime.now().isoformat())
        return op

class OperationalTransform:
    """Operational Transform implementation for collaborative editing"""
    
    def __init__(self):
        self.operation_history: Dict[str, List[Operation]] = {}
        self.document_versions: Dict[str, int] = {}
    
    def add_operation(self, document_id: str, operation: Operation) -> int:
        """Add operation to document history and return new version"""
        if document_id not in self.operation_history:
            self.operation_history[document_id] = []
            self.document_versions[document_id] = 0
        
        self.operation_history[document_id].append(operation)
        self.document_versions[document_id] += 1
        
        return self.document_versions[document_id]
    
    def transform_operation(self, op1: Operation, op2: Operation) -> Tuple[Operation, Operation]:
        """Transform two operations against each other"""
        if op1.type == "insert" and op2.type == "insert":
            return self._transform_insert_insert(op1, op2)
        elif op1.type == "insert" and op2.type == "delete":
            return self._transform_insert_delete(op1, op2)
        elif op1.type == "delete" and op2.type == "insert":
            return self._transform_delete_insert(op1, op2)
        elif op1.type == "delete" and op2.type == "delete":
            return self._transform_delete_delete(op1, op2)
        else:
            # No transformation needed
            return op1, op2
    
    def _transform_insert_insert(self, op1: Operation, op2: Operation) -> Tuple[Operation, Operation]:
        """Transform two insert operations"""
        if op1.position <= op2.position:
            # op1 happens before op2
            return op1, Operation("insert", op2.position + op1.length, text=op2.text)
        else:
            # op2 happens before op1
            return Operation("insert", op1.position + op2.length, text=op1.text), op2
    
    def _transform_insert_delete(self, op1: Operation, op2: Operation) -> Tuple[Operation, Operation]:
        """Transform insert against delete"""
        if op1.position <= op2.position:
            # Insert happens before delete
            return op1, Operation("delete", op2.position + op1.length, length=op2.length)
        else:
            # Delete happens before insert
            return Operation("insert", op1.position - op2.length, text=op1.text), op2
    
    def _transform_delete_insert(self, op1: Operation, op2: Operation) -> Tuple[Operation, Operation]:
        """Transform delete against insert"""
        if op1.position < op2.position:
            # Delete happens before insert
            return op1, Operation("insert", op2.position - op1.length, text=op2.text)
        else:
            # Insert happens before delete
            return Operation("delete", op1.position + op2.length, length=op1.length), op2
    
    def _transform_delete_delete(self, op1: Operation, op2: Operation) -> Tuple[Operation, Operation]:
        """Transform two delete operations"""
        if op1.position < op2.position:
            # op1 happens before op2
            if op1.position + op1.length <= op2.position:
                # No overlap
                return op1, Operation("delete", op2.position - op1.length, length=op2.length)
            else:
                # Overlap - adjust op2
                overlap = op1.position + op1.length - op2.position
                new_length = max(0, op2.length - overlap)
                if new_length > 0:
                    return op1, Operation("delete", op2.position - op1.length, length=new_length)
                else:
                    return op1, Operation("retain", 0, length=0)
        
        elif op1.position > op2.position:
            # op2 happens before op1
            if op2.position + op2.length <= op1.position:
                # No overlap
                return Operation("delete", op1.position - op2.length, length=op1.length), op2
            else:
                # Overlap - adjust op1
                overlap = op2.position + op2.length - op1.position
                new_length = max(0, op1.length - overlap)
                if new_length > 0:
                    return Operation("delete", op1.position - op2.length, length=new_length), op2
                else:
                    return Operation("retain", 0, length=0), op2
        
        else:
            # Same position - both delete the same text
            if op1.length >= op2.length:
                return Operation("delete", op1.position, length=op1.length - op2.length), Operation("retain", 0, length=0)
            else:
                return Operation("retain", 0, length=0), Operation("delete", op2.position, length=op2.length - op1.length)
    
    def transform_operation_against_history(self, operation: Operation, document_id: str, from_version: int) -> Operation:
        """Transform operation against operation history"""
        if document_id not in self.operation_history:
            return operation
        
        # Get operations that happened after the client's version
        concurrent_operations = self.operation_history[document_id][from_version:]
        
        transformed_operation = operation
        
        for concurrent_op in concurrent_operations:
            transformed_operation, _ = self.transform_operation(transformed_operation, concurrent_op)
        
        return transformed_operation
    
    def apply_operation_to_text(self, text: str, operation: Operation) -> str:
        """Apply operation to text content"""
        if operation.type == "insert":
            position = min(operation.position, len(text))
            return text[:position] + operation.text + text[position:]
        
        elif operation.type == "delete":
            start = min(operation.position, len(text))
            end = min(operation.position + operation.length, len(text))
            return text[:start] + text[end:]
        
        elif operation.type == "retain":
            return text
        
        else:
            raise ValueError(f"Unknown operation type: {operation.type}")
    
    def get_document_version(self, document_id: str) -> int:
        """Get current version of document"""
        return self.document_versions.get(document_id, 0)
    
    def get_operations_since(self, document_id: str, version: int) -> List[Operation]:
        """Get operations that happened since given version"""
        if document_id not in self.operation_history:
            return []
        
        return self.operation_history[document_id][version:]
    
    def create_insert_operation(self, position: int, text: str) -> Operation:
        """Create an insert operation"""
        return Operation("insert", position, text=text)
    
    def create_delete_operation(self, position: int, length: int) -> Operation:
        """Create a delete operation"""
        return Operation("delete", position, length=length)
    
    def create_retain_operation(self, length: int) -> Operation:
        """Create a retain operation"""
        return Operation("retain", 0, length=length)

class DocumentState:
    """Represents the state of a collaborative document"""
    
    def __init__(self, document_id: str, initial_content: str = ""):
        self.document_id = document_id
        self.content = initial_content
        self.version = 0
        self.last_modified = datetime.now().isoformat()
        self.active_users: List[Dict] = []
        self.ot = OperationalTransform()
    
    def apply_operation(self, operation: Operation) -> bool:
        """Apply operation to document state"""
        try:
            # Transform operation against concurrent operations
            transformed_op = self.ot.transform_operation_against_history(
                operation, self.document_id, self.version
            )
            
            # Apply transformed operation to content
            self.content = self.ot.apply_operation_to_text(self.content, transformed_op)
            
            # Add to operation history
            self.version = self.ot.add_operation(self.document_id, transformed_op)
            self.last_modified = datetime.now().isoformat()
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying operation: {str(e)}")
            return False
    
    def get_state(self) -> Dict:
        """Get current document state"""
        return {
            "document_id": self.document_id,
            "content": self.content,
            "version": self.version,
            "last_modified": self.last_modified,
            "active_users": self.active_users
        }
    
    def add_user(self, user_info: Dict):
        """Add user to active users list"""
        if not any(user["user_id"] == user_info["user_id"] for user in self.active_users):
            self.active_users.append(user_info)
    
    def remove_user(self, user_id: str):
        """Remove user from active users list"""
        self.active_users = [user for user in self.active_users if user["user_id"] != user_id]
    
    def update_user_cursor(self, user_id: str, cursor_position: int):
        """Update user's cursor position"""
        for user in self.active_users:
            if user["user_id"] == user_id:
                user["cursor_position"] = cursor_position
                break

# Global OT instance
operational_transform = OperationalTransform()
