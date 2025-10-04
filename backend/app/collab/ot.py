"""
Operational Transform (OT) Implementation for Collaborative Editing
"""
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import uuid

class OperationType(Enum):
    INSERT = "insert"
    DELETE = "delete"
    RETAIN = "retain"
    REPLACE = "replace"

@dataclass
class Operation:
    """Represents a single operation in the document"""
    id: str
    type: OperationType
    position: int
    content: str = ""
    length: int = 0
    user_id: str = ""
    username: str = ""
    timestamp: str = ""
    version: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert operation to dictionary"""
        return {
            "id": self.id,
            "type": self.type.value,
            "position": self.position,
            "content": self.content,
            "length": self.length,
            "user_id": self.user_id,
            "username": self.username,
            "timestamp": self.timestamp,
            "version": self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Operation':
        """Create operation from dictionary"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            type=OperationType(data["type"]),
            position=data["position"],
            content=data.get("content", ""),
            length=data.get("length", 0),
            user_id=data.get("user_id", ""),
            username=data.get("username", ""),
            timestamp=data.get("timestamp", ""),
            version=data.get("version", 0)
        )

class OperationalTransform:
    """Operational Transform implementation"""
    
    @staticmethod
    def transform(op1: Operation, op2: Operation) -> Tuple[Operation, Operation]:
        """
        Transform two operations against each other.
        Returns (transformed_op1, transformed_op2)
        """
        if op1.type == OperationType.RETAIN and op2.type == OperationType.RETAIN:
            return op1, op2
        
        elif op1.type == OperationType.INSERT and op2.type == OperationType.RETAIN:
            if op1.position <= op2.position:
                return op1, Operation(
                    id=op2.id,
                    type=op2.type,
                    position=op2.position + len(op1.content),
                    content=op2.content,
                    length=op2.length,
                    user_id=op2.user_id,
                    username=op2.username,
                    timestamp=op2.timestamp,
                    version=op2.version
                )
            else:
                return op1, op2
        
        elif op1.type == OperationType.RETAIN and op2.type == OperationType.INSERT:
            if op2.position <= op1.position:
                return Operation(
                    id=op1.id,
                    type=op1.type,
                    position=op1.position + len(op2.content),
                    content=op1.content,
                    length=op1.length,
                    user_id=op1.user_id,
                    username=op1.username,
                    timestamp=op1.timestamp,
                    version=op1.version
                ), op2
            else:
                return op1, op2
        
        elif op1.type == OperationType.DELETE and op2.type == OperationType.RETAIN:
            if op1.position < op2.position:
                new_position = max(op1.position, op2.position - op1.length)
                return op1, Operation(
                    id=op2.id,
                    type=op2.type,
                    position=new_position,
                    content=op2.content,
                    length=op2.length,
                    user_id=op2.user_id,
                    username=op2.username,
                    timestamp=op2.timestamp,
                    version=op2.version
                )
            else:
                return op1, op2
        
        elif op1.type == OperationType.RETAIN and op2.type == OperationType.DELETE:
            if op2.position < op1.position:
                new_position = max(op2.position, op1.position - op2.length)
                return Operation(
                    id=op1.id,
                    type=op1.type,
                    position=new_position,
                    content=op1.content,
                    length=op1.length,
                    user_id=op1.user_id,
                    username=op1.username,
                    timestamp=op1.timestamp,
                    version=op1.version
                ), op2
            else:
                return op1, op2
        
        elif op1.type == OperationType.INSERT and op2.type == OperationType.INSERT:
            # Two concurrent insertions
            if op1.position <= op2.position:
                # op1 comes before op2, adjust op2's position
                return op1, Operation(
                    id=op2.id,
                    type=op2.type,
                    position=op2.position + len(op1.content),
                    content=op2.content,
                    length=op2.length,
                    user_id=op2.user_id,
                    username=op2.username,
                    timestamp=op2.timestamp,
                    version=op2.version
                )
            else:
                # op2 comes before op1, adjust op1's position
                return Operation(
                    id=op1.id,
                    type=op1.type,
                    position=op1.position + len(op2.content),
                    content=op1.content,
                    length=op1.length,
                    user_id=op1.user_id,
                    username=op1.username,
                    timestamp=op1.timestamp,
                    version=op1.version
                ), op2
        
        elif op1.type == OperationType.DELETE and op2.type == OperationType.DELETE:
            # Two concurrent deletions
            if op1.position <= op2.position:
                if op1.position + op1.length <= op2.position:
                    # Non-overlapping deletions, adjust op2's position
                    return op1, Operation(
                        id=op2.id,
                        type=op2.type,
                        position=op2.position - op1.length,
                        content=op2.content,
                        length=op2.length,
                        user_id=op2.user_id,
                        username=op2.username,
                        timestamp=op2.timestamp,
                        version=op2.version
                    )
                else:
                    # Overlapping deletions, merge them
                    new_length = max(op1.position + op1.length, op2.position + op2.length) - op1.position
                    return Operation(
                        id=op1.id,
                        type=op1.type,
                        position=op1.position,
                        content="",
                        length=new_length,
                        user_id=op1.user_id,
                        username=op1.username,
                        timestamp=op1.timestamp,
                        version=op1.version
                    ), Operation(
                        id=op2.id,
                        type=OperationType.RETAIN,
                        position=0,
                        content="",
                        length=0,
                        user_id=op2.user_id,
                        username=op2.username,
                        timestamp=op2.timestamp,
                        version=op2.version
                    )
            else:
                # op2 comes before op1
                if op2.position + op2.length <= op1.position:
                    # Non-overlapping deletions, adjust op1's position
                    return Operation(
                        id=op1.id,
                        type=op1.type,
                        position=op1.position - op2.length,
                        content=op1.content,
                        length=op1.length,
                        user_id=op1.user_id,
                        username=op1.username,
                        timestamp=op1.timestamp,
                        version=op1.version
                    ), op2
                else:
                    # Overlapping deletions, merge them
                    new_length = max(op1.position + op1.length, op2.position + op2.length) - op2.position
                    return Operation(
                        id=op1.id,
                        type=OperationType.RETAIN,
                        position=0,
                        content="",
                        length=0,
                        user_id=op1.user_id,
                        username=op1.username,
                        timestamp=op1.timestamp,
                        version=op1.version
                    ), Operation(
                        id=op2.id,
                        type=op2.type,
                        position=op2.position,
                        content="",
                        length=new_length,
                        user_id=op2.user_id,
                        username=op2.username,
                        timestamp=op2.timestamp,
                        version=op2.version
                    )
        
        elif op1.type == OperationType.INSERT and op2.type == OperationType.DELETE:
            if op1.position <= op2.position:
                # Insert comes before delete, adjust delete position
                return op1, Operation(
                    id=op2.id,
                    type=op2.type,
                    position=op2.position + len(op1.content),
                    content=op2.content,
                    length=op2.length,
                    user_id=op2.user_id,
                    username=op2.username,
                    timestamp=op2.timestamp,
                    version=op2.version
                )
            elif op1.position >= op2.position + op2.length:
                # Insert comes after delete, adjust insert position
                return Operation(
                    id=op1.id,
                    type=op1.type,
                    position=op1.position - op2.length,
                    content=op1.content,
                    length=op1.length,
                    user_id=op1.user_id,
                    username=op1.username,
                    timestamp=op1.timestamp,
                    version=op1.version
                ), op2
            else:
                # Insert is within delete range, insert at delete position
                return Operation(
                    id=op1.id,
                    type=op1.type,
                    position=op2.position,
                    content=op1.content,
                    length=op1.length,
                    user_id=op1.user_id,
                    username=op1.username,
                    timestamp=op1.timestamp,
                    version=op1.version
                ), op2
        
        elif op1.type == OperationType.DELETE and op2.type == OperationType.INSERT:
            if op2.position <= op1.position:
                # Insert comes before delete, adjust delete position
                return Operation(
                    id=op1.id,
                    type=op1.type,
                    position=op1.position + len(op2.content),
                    content=op1.content,
                    length=op1.length,
                    user_id=op1.user_id,
                    username=op1.username,
                    timestamp=op1.timestamp,
                    version=op1.version
                ), op2
            elif op2.position >= op1.position + op1.length:
                # Insert comes after delete, adjust insert position
                return op1, Operation(
                    id=op2.id,
                    type=op2.type,
                    position=op2.position - op1.length,
                    content=op2.content,
                    length=op2.length,
                    user_id=op2.user_id,
                    username=op2.username,
                    timestamp=op2.timestamp,
                    version=op2.version
                )
            else:
                # Insert is within delete range, insert at delete position
                return op1, Operation(
                    id=op2.id,
                    type=op2.type,
                    position=op1.position,
                    content=op2.content,
                    length=op2.length,
                    user_id=op2.user_id,
                    username=op2.username,
                    timestamp=op2.timestamp,
                    version=op2.version
                )
        
        else:
            # Handle other combinations or fallback
            return op1, op2
    
    @staticmethod
    def apply_operation(text: str, operation: Operation) -> str:
        """Apply a single operation to text"""
        if operation.type == OperationType.INSERT:
            return text[:operation.position] + operation.content + text[operation.position:]
        
        elif operation.type == OperationType.DELETE:
            start = operation.position
            end = min(operation.position + operation.length, len(text))
            return text[:start] + text[end:]
        
        elif operation.type == OperationType.REPLACE:
            # Replace the entire content
            return operation.content
        
        elif operation.type == OperationType.RETAIN:
            return text
        
        return text
    
    @staticmethod
    def compose_operations(op1: Operation, op2: Operation) -> List[Operation]:
        """Compose two operations into a single operation"""
        if op1.type == OperationType.RETAIN and op2.type == OperationType.RETAIN:
            return [Operation(
                id=str(uuid.uuid4()),
                type=OperationType.RETAIN,
                position=op1.position,
                content="",
                length=op1.length + op2.length,
                user_id=op2.user_id,
                username=op2.username,
                timestamp=op2.timestamp,
                version=op2.version
            )]
        
        elif op1.type == OperationType.INSERT and op2.type == OperationType.DELETE:
            if op1.position == op2.position:
                return [op1]  # Insert wins over delete at same position
            else:
                return [op1, op2]
        
        else:
            return [op1, op2]
    
    @staticmethod
    def transform_against_history(operation: Operation, history: List[Operation]) -> Operation:
        """Transform an operation against a history of operations"""
        transformed_op = operation
        
        for hist_op in history:
            if hist_op.version >= operation.version:
                continue
            
            transformed_op, _ = OperationalTransform.transform(transformed_op, hist_op)
        
        return transformed_op

class DocumentState:
    """Represents the current state of a collaborative document"""
    
    def __init__(self, document_id: str, content: str = "", version: int = 0, title: str = "Untitled Document"):
        self.document_id = document_id
        self.content = content
        self.version = version
        self.title = title
        self.operations: List[Operation] = []
    
    def apply_operation(self, operation: Operation) -> bool:
        """Apply an operation to the document state"""
        try:
            # Transform operation against history
            transformed_op = OperationalTransform.transform_against_history(
                operation, self.operations
            )
            
            # Apply to content
            self.content = OperationalTransform.apply_operation(
                self.content, transformed_op
            )
            
            # Update version
            self.version += 1
            transformed_op.version = self.version
            
            # Add to operations history
            self.operations.append(transformed_op)
            
            return True
        except Exception as e:
            print(f"Error applying operation: {e}")
            return False
    
    def get_content(self) -> str:
        """Get current document content"""
        return self.content
    
    def get_version(self) -> int:
        """Get current document version"""
        return self.version
    
    def get_operations_since(self, version: int) -> List[Operation]:
        """Get operations since a specific version"""
        return [op for op in self.operations if op.version > version]
