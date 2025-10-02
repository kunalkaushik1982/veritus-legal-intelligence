"""
WebSocket Manager for Real-time Collaborative Editing
Handles WebSocket connections, user sessions, and real-time communication
"""

import asyncio
import json
import logging
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections for collaborative editing"""
    
    def __init__(self):
        # Active WebSocket connections by document_id
        self.document_connections: Dict[str, Set[Any]] = {}
        # User sessions by connection
        self.user_sessions: Dict[Any, Dict] = {}
        # Document states
        self.document_states: Dict[str, Dict] = {}
        # Operation history for OT
        self.operation_history: Dict[str, List[Dict]] = {}
        
    async def connect(self, websocket: Any, document_id: str, user_id: str, username: str):
        """Handle new WebSocket connection"""
        try:
            # Add connection to document room
            if document_id not in self.document_connections:
                self.document_connections[document_id] = set()
                self.document_states[document_id] = {
                    "content": "",
                    "version": 0,
                    "last_modified": datetime.now().isoformat(),
                    "active_users": []
                }
                self.operation_history[document_id] = []
            
            self.document_connections[document_id].add(websocket)
            
            # Store user session
            session_id = str(uuid.uuid4())
            self.user_sessions[websocket] = {
                "session_id": session_id,
                "document_id": document_id,
                "user_id": user_id,
                "username": username,
                "connected_at": datetime.now().isoformat(),
                "cursor_position": 0,
                "selection_range": None
            }
            
            # Add user to document's active users
            user_info = {
                "user_id": user_id,
                "username": username,
                "session_id": session_id,
                "cursor_position": 0,
                "color": self._get_user_color(user_id)
            }
            
            if user_info not in self.document_states[document_id]["active_users"]:
                self.document_states[document_id]["active_users"].append(user_info)
            
            # Send current document state to new user
            await self._send_to_connection(websocket, {
                "type": "document_state",
                "document_id": document_id,
                "content": self.document_states[document_id]["content"],
                "version": self.document_states[document_id]["version"],
                "active_users": self.document_states[document_id]["active_users"]
            })
            
            # Notify other users about new connection
            await self._broadcast_to_document(document_id, {
                "type": "user_joined",
                "user": user_info
            }, exclude_websocket=websocket)
            
            logger.info(f"User {username} connected to document {document_id}")
            
        except Exception as e:
            logger.error(f"Error connecting user: {str(e)}")
            await self._send_error(websocket, f"Connection failed: {str(e)}")
    
    async def disconnect(self, websocket: Any):
        """Handle WebSocket disconnection"""
        try:
            if websocket not in self.user_sessions:
                return
            
            session = self.user_sessions[websocket]
            document_id = session["document_id"]
            user_id = session["user_id"]
            username = session["username"]
            
            # Remove from document connections
            if document_id in self.document_connections:
                self.document_connections[document_id].discard(websocket)
                
                # Remove user from active users
                self.document_states[document_id]["active_users"] = [
                    user for user in self.document_states[document_id]["active_users"]
                    if user["user_id"] != user_id
                ]
                
                # Notify other users about disconnection
                await self._broadcast_to_document(document_id, {
                    "type": "user_left",
                    "user_id": user_id,
                    "username": username
                })
                
                # Clean up empty document rooms
                if not self.document_connections[document_id]:
                    del self.document_connections[document_id]
                    del self.document_states[document_id]
                    del self.operation_history[document_id]
            
            # Remove user session
            del self.user_sessions[websocket]
            
            logger.info(f"User {username} disconnected from document {document_id}")
            
        except Exception as e:
            logger.error(f"Error disconnecting user: {str(e)}")
    
    async def handle_message(self, websocket: Any, message: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            logger.info(f"Handling message type: {message_type}")
            
            if websocket not in self.user_sessions:
                logger.warning("WebSocket not in user sessions, sending authentication error")
                await self._send_error(websocket, "Not authenticated")
                return
            
            session = self.user_sessions[websocket]
            document_id = session["document_id"]
            
            if message_type == "auth":
                # Handle authentication message (already processed in routes.py)
                logger.info(f"Authentication confirmed for user {session['username']}")
                await self._send_to_connection(websocket, {"type": "auth_success"})
            elif message_type == "text_operation":
                await self._handle_text_operation(websocket, data, document_id)
            elif message_type == "cursor_update":
                await self._handle_cursor_update(websocket, data, document_id)
            elif message_type == "selection_update":
                await self._handle_selection_update(websocket, data, document_id)
            elif message_type == "ping":
                await self._send_to_connection(websocket, {"type": "pong"})
            else:
                logger.warning(f"Unknown message type: {message_type}")
                await self._send_error(websocket, f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON message received")
            await self._send_error(websocket, "Invalid JSON message")
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            await self._send_error(websocket, f"Message handling failed: {str(e)}")
    
    async def _handle_text_operation(self, websocket: Any, data: Dict, document_id: str):
        """Handle text editing operations"""
        try:
            operation = data.get("operation", {})
            client_version = data.get("version", 0)
            
            # Get current document state
            current_state = self.document_states[document_id]
            server_version = current_state["version"]
            
            # Check if client is up to date
            if client_version < server_version:
                # Client needs to catch up with operations
                missing_operations = self.operation_history[document_id][client_version:]
                await self._send_to_connection(websocket, {
                    "type": "operations_missing",
                    "operations": missing_operations,
                    "current_version": server_version
                })
                return
            
            # Transform operation against concurrent operations
            transformed_operation = await self._transform_operation(
                operation, document_id, client_version
            )
            
            # Apply transformed operation
            await self._apply_operation(document_id, transformed_operation)
            
            # Store operation in history
            operation_record = {
                "operation": transformed_operation,
                "version": server_version + 1,
                "user_id": self.user_sessions[websocket]["user_id"],
                "timestamp": datetime.now().isoformat()
            }
            self.operation_history[document_id].append(operation_record)
            
            # Update document version
            self.document_states[document_id]["version"] += 1
            self.document_states[document_id]["last_modified"] = datetime.now().isoformat()
            
            # Broadcast operation to other users
            await self._broadcast_to_document(document_id, {
                "type": "text_operation",
                "operation": transformed_operation,
                "version": self.document_states[document_id]["version"],
                "user_id": self.user_sessions[websocket]["user_id"]
            }, exclude_websocket=websocket)
            
            # Send acknowledgment to sender
            await self._send_to_connection(websocket, {
                "type": "operation_applied",
                "version": self.document_states[document_id]["version"]
            })
            
        except Exception as e:
            logger.error(f"Error handling text operation: {str(e)}")
            await self._send_error(websocket, f"Operation failed: {str(e)}")
    
    async def _handle_cursor_update(self, websocket: Any, data: Dict, document_id: str):
        """Handle cursor position updates"""
        try:
            cursor_position = data.get("cursor_position", 0)
            session = self.user_sessions[websocket]
            user_id = session["user_id"]
            
            # Update user's cursor position
            session["cursor_position"] = cursor_position
            
            # Update in document state
            for user in self.document_states[document_id]["active_users"]:
                if user["user_id"] == user_id:
                    user["cursor_position"] = cursor_position
                    break
            
            # Broadcast cursor update to other users
            await self._broadcast_to_document(document_id, {
                "type": "cursor_update",
                "user_id": user_id,
                "cursor_position": cursor_position
            }, exclude_websocket=websocket)
            
        except Exception as e:
            logger.error(f"Error handling cursor update: {str(e)}")
    
    async def _handle_selection_update(self, websocket: Any, data: Dict, document_id: str):
        """Handle text selection updates"""
        try:
            selection_range = data.get("selection_range")
            session = self.user_sessions[websocket]
            user_id = session["user_id"]
            
            # Update user's selection
            session["selection_range"] = selection_range
            
            # Update in document state
            for user in self.document_states[document_id]["active_users"]:
                if user["user_id"] == user_id:
                    user["selection_range"] = selection_range
                    break
            
            # Broadcast selection update to other users
            await self._broadcast_to_document(document_id, {
                "type": "selection_update",
                "user_id": user_id,
                "selection_range": selection_range
            }, exclude_websocket=websocket)
            
        except Exception as e:
            logger.error(f"Error handling selection update: {str(e)}")
    
    async def _transform_operation(self, operation: Dict, document_id: str, client_version: int) -> Dict:
        """Transform operation using Operational Transform"""
        try:
            # Get concurrent operations
            concurrent_operations = self.operation_history[document_id][client_version:]
            
            transformed_operation = operation.copy()
            
            # Apply OT transformation for each concurrent operation
            for op_record in concurrent_operations:
                concurrent_op = op_record["operation"]
                transformed_operation = self._transform_against_operation(
                    transformed_operation, concurrent_op
                )
            
            return transformed_operation
            
        except Exception as e:
            logger.error(f"Error transforming operation: {str(e)}")
            return operation
    
    def _transform_against_operation(self, op1: Dict, op2: Dict) -> Dict:
        """Transform operation op1 against operation op2"""
        # Simple OT implementation for insert/delete operations
        # This is a basic implementation - production systems use more sophisticated OT
        
        if op1["type"] == "insert" and op2["type"] == "insert":
            # Both are inserts
            if op1["position"] <= op2["position"]:
                return op1  # op1 happens before op2
            else:
                return {
                    "type": "insert",
                    "position": op1["position"] + len(op2["text"]),
                    "text": op1["text"]
                }
        
        elif op1["type"] == "insert" and op2["type"] == "delete":
            # op1 is insert, op2 is delete
            if op1["position"] <= op2["position"]:
                return op1  # op1 happens before op2
            else:
                return {
                    "type": "insert",
                    "position": op1["position"] - op2["length"],
                    "text": op1["text"]
                }
        
        elif op1["type"] == "delete" and op2["type"] == "insert":
            # op1 is delete, op2 is insert
            if op1["position"] < op2["position"]:
                return op1  # op1 happens before op2
            else:
                return {
                    "type": "delete",
                    "position": op1["position"] + len(op2["text"]),
                    "length": op1["length"]
                }
        
        elif op1["type"] == "delete" and op2["type"] == "delete":
            # Both are deletes
            if op1["position"] < op2["position"]:
                return op1  # op1 happens before op2
            elif op1["position"] > op2["position"]:
                return {
                    "type": "delete",
                    "position": op1["position"] - op2["length"],
                    "length": op1["length"]
                }
            else:
                # Same position - return empty operation
                return {"type": "noop"}
        
        return op1
    
    async def _apply_operation(self, document_id: str, operation: Dict):
        """Apply operation to document content"""
        try:
            content = self.document_states[document_id]["content"]
            
            if operation["type"] == "insert":
                position = operation["position"]
                text = operation["text"]
                content = content[:position] + text + content[position:]
            
            elif operation["type"] == "delete":
                position = operation["position"]
                length = operation["length"]
                content = content[:position] + content[position + length:]
            
            self.document_states[document_id]["content"] = content
            
        except Exception as e:
            logger.error(f"Error applying operation: {str(e)}")
    
    async def _broadcast_to_document(self, document_id: str, message: Dict, exclude_websocket: Any = None):
        """Broadcast message to all users in a document"""
        try:
            if document_id not in self.document_connections:
                return
            
            connections = self.document_connections[document_id].copy()
            if exclude_websocket:
                connections.discard(exclude_websocket)
            
            if connections:
                message_str = json.dumps(message)
                await asyncio.gather(*[
                    self._send_to_connection(ws, message_str) for ws in connections
                ], return_exceptions=True)
                
        except Exception as e:
            logger.error(f"Error broadcasting to document: {str(e)}")
    
    async def _send_to_connection(self, websocket: Any, message: Any):
        """Send message to a specific WebSocket connection"""
        try:
            if isinstance(message, dict):
                message = json.dumps(message)
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
    
    async def _send_error(self, websocket: Any, error_message: str):
        """Send error message to WebSocket connection"""
        try:
            await self._send_to_connection(websocket, {
                "type": "error",
                "message": error_message
            })
        except Exception as e:
            logger.error(f"Error sending error message: {str(e)}")
    
    def _get_user_color(self, user_id: str) -> str:
        """Generate a consistent color for a user"""
        colors = [
            "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
            "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9"
        ]
        return colors[hash(user_id) % len(colors)]
    
    def get_document_state(self, document_id: str) -> Optional[Dict]:
        """Get current state of a document"""
        return self.document_states.get(document_id)
    
    def get_active_users(self, document_id: str) -> List[Dict]:
        """Get list of active users in a document"""
        if document_id in self.document_states:
            return self.document_states[document_id]["active_users"]
        return []

# Global WebSocket manager instance
websocket_manager = WebSocketManager()
