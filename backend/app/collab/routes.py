"""
Collaborative Editing API Routes
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Dict, List, Any
import json
import uuid
from datetime import datetime
import logging

from .models import Document, Operation, Snapshot, Comment, Presence
from .ot import Operation as OTOperation, OperationalTransform, DocumentState
from .redis_manager import redis_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/collab", tags=["collaborative-editing"])

# In-memory document states (in production, use Redis or database)
document_states: Dict[str, DocumentState] = {}
active_connections: Dict[str, List[WebSocket]] = {}

@router.websocket("/ws/docs/{document_id}")
async def websocket_endpoint(websocket: WebSocket, document_id: str):
    """WebSocket endpoint for real-time collaborative editing"""
    logger.info(f"WebSocket connection attempt for document: {document_id}")
    
    # Track the user for this connection
    connected_user = None
    
    try:
        await websocket.accept()
        logger.info(f"WebSocket accepted for document: {document_id}")
        
        # Initialize document state if it doesn't exist
        if document_id not in document_states:
            document_states[document_id] = DocumentState(document_id, title="Untitled Document")
            logger.info(f"Created new document state for: {document_id}")
        
        # Add connection to active connections
        if document_id not in active_connections:
            active_connections[document_id] = []
        active_connections[document_id].append(websocket)
        
        logger.info(f"WebSocket connected for document: {document_id}")
        
        try:
            while True:
                # Receive message
                data = await websocket.receive_text()
                logger.info(f"Received message from {document_id}: {data[:100]}...")
                
                try:
                    message = json.loads(data)
                    # Track the connected user from auth message
                    if message.get("type") == "auth":
                        connected_user = {
                            "user_id": message.get("user_id"),
                            "username": message.get("username")
                        }
                    await handle_websocket_message(websocket, document_id, message)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error for {document_id}: {e}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }))
                except Exception as e:
                    logger.error(f"Error handling message for {document_id}: {e}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"Error processing message: {str(e)}"
                    }))
                    
        except WebSocketDisconnect as e:
            logger.info(f"WebSocket disconnected for document: {document_id}, code: {e.code}")
        except Exception as e:
            logger.error(f"Error in WebSocket loop for document {document_id}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
    except Exception as e:
        logger.error(f"Error accepting WebSocket for document {document_id}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        # Remove connection and broadcast updated user list
        if document_id in active_connections:
            try:
                active_connections[document_id].remove(websocket)
                if not active_connections[document_id]:
                    del active_connections[document_id]
                logger.info(f"Removed connection for document: {document_id}")
                
                # Remove user from Redis and broadcast updated user list
                if connected_user:
                    try:
                        await redis_manager.remove_user_presence(document_id, connected_user["user_id"])
                        logger.info(f"Removed user presence for: {connected_user['username']}")
                        
                        # Broadcast updated active users list to remaining users
                        if document_id in active_connections and active_connections[document_id]:
                            active_users = await redis_manager.get_active_users(document_id)
                            await broadcast_to_document(document_id, {
                                "type": "active_users",
                                "users": active_users
                            }, None)
                            logger.info(f"Broadcasted updated user list after disconnect: {len(active_users)} users")
                    except Exception as e:
                        logger.error(f"Error removing user presence: {e}")
                        
            except ValueError:
                pass

async def handle_websocket_message(websocket: WebSocket, document_id: str, message: Dict[str, Any]):
    """Handle incoming WebSocket messages"""
    message_type = message.get("type")
    logger.info(f"Handling message type: {message_type} for document: {document_id}")
    
    try:
        if message_type == "auth":
            # Handle authentication
            user_id = message.get("user_id", "anonymous")
            username = message.get("username", "Anonymous User")
            
            logger.info(f"Authenticating user: {username} ({user_id}) for document: {document_id}")
            
            # Send welcome message
            auth_response = {
                "type": "auth_success",
                "user_id": user_id,
                "username": username,
                "document_id": document_id,
                "content": document_states[document_id].get_content(),
                "version": document_states[document_id].get_version()
            }
            await websocket.send_text(json.dumps(auth_response))
            logger.info(f"Sent auth_success for user: {username}")
            
            # Set user presence (with error handling)
            try:
                await redis_manager.set_user_presence(document_id, user_id, username)
                logger.info(f"Set user presence for: {username}")
            except Exception as e:
                logger.error(f"Error setting user presence for {username}: {e}")
            
            # Send active users to all connected users (including the new user)
            try:
                active_users = await redis_manager.get_active_users(document_id)
                users_response = {
                    "type": "active_users",
                    "users": active_users
                }
                
                # Send to all connected users in this document
                await broadcast_to_document(document_id, users_response, None)
                logger.info(f"Broadcasted active users list: {len(active_users)} users to all connected clients")
            except Exception as e:
                logger.error(f"Error getting active users: {e}")
                # Send empty users list as fallback to all users
                await broadcast_to_document(document_id, {
                    "type": "active_users",
                    "users": []
                }, None)
    
        elif message_type == "operation":
            # Handle operation
            await handle_operation(websocket, document_id, message)
        
        elif message_type == "cursor_update":
            # Handle cursor update
            await handle_cursor_update(document_id, message)
        
        elif message_type == "typing_start":
            # Handle typing start
            await handle_typing_start(document_id, message)
        
        elif message_type == "typing_stop":
            # Handle typing stop
            await handle_typing_stop(document_id, message)
        
        elif message_type == "comment_add":
            # Handle comment addition
            await handle_comment_add(document_id, message)
        
        elif message_type == "comment_update":
            # Handle comment update
            await handle_comment_update(document_id, message)
        
        elif message_type == "comment_delete":
            # Handle comment deletion
            await handle_comment_delete(document_id, message)
        
        elif message_type == "cursor_update":
            # Handle cursor position update
            await handle_cursor_update(document_id, message)
        
        else:
            logger.warning(f"Unknown message type: {message_type}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Unknown message type: {message_type}"
            }))
            
    except Exception as e:
        logger.error(f"Error in handle_websocket_message for {document_id}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Internal server error: {str(e)}"
            }))
        except:
            pass  # WebSocket might be closed

async def handle_operation(websocket: WebSocket, document_id: str, message: Dict[str, Any]):
    """Handle document operation"""
    try:
        operation_data = message.get("operation", {})
        operation = OTOperation.from_dict(operation_data)
        
        # Apply operation to document state
        success = document_states[document_id].apply_operation(operation)
        
        if success:
            # Broadcast to other clients
            await broadcast_to_document(document_id, {
                "type": "operation_applied",
                "operation": operation.to_dict(),
                "document_version": document_states[document_id].get_version(),
                "document_content": document_states[document_id].get_content()
            }, websocket)
            
            logger.info(f"Operation applied successfully: {operation.type} at position {operation.position}")
        else:
            # Send error back to client
            await websocket.send_text(json.dumps({
                "type": "operation_error",
                "message": "Failed to apply operation"
            }))
            
    except Exception as e:
        logger.error(f"Error handling operation: {e}")
        await websocket.send_text(json.dumps({
            "type": "operation_error",
            "message": str(e)
        }))

async def handle_cursor_update(document_id: str, message: Dict[str, Any]):
    """Handle cursor position update"""
    try:
        user_id = message.get("user_id")
        username = message.get("username")
        cursor_position = message.get("cursor_position", 0)
        selection_start = message.get("selection_start", cursor_position)
        selection_end = message.get("selection_end", cursor_position)
        
        if user_id:
            # Update user presence with cursor and selection data
            await redis_manager.set_user_presence(
                document_id, user_id, username, cursor_position, selection_start, selection_end
            )
            
            # Prepare cursor data for broadcasting
            cursor_data = {
                "type": "cursor_update",
                "user_id": user_id,
                "username": username,
                "cursor_position": cursor_position,
                "selection_start": selection_start,
                "selection_end": selection_end,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Broadcast cursor update to all connected users
            await broadcast_to_document(document_id, cursor_data, None)
            
            # Also publish to dedicated cursor channel for Redis subscribers
            await redis_manager.publish_cursor_update(document_id, cursor_data)
            
        logger.info(f"Cursor updated for user {username} at position {cursor_position} in document {document_id}")
        
    except Exception as e:
        logger.error(f"Error handling cursor update for document {document_id}: {e}")

async def handle_typing_start(document_id: str, message: Dict[str, Any]):
    """Handle typing start"""
    try:
        await broadcast_to_document(document_id, {
            "type": "typing_start",
            "user_id": message.get("user_id"),
            "username": message.get("username")
        }, None)
    except Exception as e:
        logger.error(f"Error handling typing start: {e}")

async def handle_typing_stop(document_id: str, message: Dict[str, Any]):
    """Handle typing stop"""
    try:
        await broadcast_to_document(document_id, {
            "type": "typing_stop",
            "user_id": message.get("user_id"),
            "username": message.get("username")
        }, None)
    except Exception as e:
        logger.error(f"Error handling typing stop: {e}")

async def broadcast_to_document(document_id: str, message: Dict[str, Any], exclude_websocket: WebSocket = None):
    """Broadcast message to all connected clients for a document"""
    if document_id in active_connections:
        disconnected = []
        for websocket in active_connections[document_id]:
            if websocket != exclude_websocket:
                try:
                    await websocket.send_text(json.dumps(message))
                except:
                    disconnected.append(websocket)
        
        # Remove disconnected websockets
        for ws in disconnected:
            try:
                active_connections[document_id].remove(ws)
            except ValueError:
                pass

# REST API Endpoints

@router.post("/documents")
async def create_document(request: Request):
    """Create a new collaborative document"""
    try:
        data = await request.json()
        document_id = data.get("id", str(uuid.uuid4()))
        title = data.get("title", "Untitled Document")
        user_id = data.get("user_id", "anonymous")
        
        # Initialize document state with title
        document_states[document_id] = DocumentState(document_id, title=title)
        
        return JSONResponse({
            "success": True,
            "document_id": document_id,
            "title": title,
            "message": "Document created successfully"
        })
        
    except Exception as e:
        logger.error(f"Error creating document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents")
async def list_documents():
    """List all collaborative documents"""
    try:
        documents = []
        for doc_id, state in document_states.items():
            # Get the actual title from the document state
            title = state.title
            documents.append({
                "id": doc_id,
                "title": title,
                "version": state.get_version(),
                "content_length": len(state.get_content()),
                "active_users": len(active_connections.get(doc_id, []))
            })
        
        return JSONResponse({
            "success": True,
            "documents": documents
        })
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a collaborative document"""
    try:
        if document_id not in document_states:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Remove from document states
        del document_states[document_id]
        
        # Remove from active connections
        if document_id in active_connections:
            del active_connections[document_id]
        
        # Remove from Redis presence
        try:
            redis_manager = RedisManager()
            await redis_manager.remove_document_presence(document_id)
        except Exception as e:
            logger.warning(f"Error removing Redis presence for document {document_id}: {e}")
        
        # Remove document file if it exists
        import os
        doc_file = f"/app/collab_documents/{document_id}.json"
        if os.path.exists(doc_file):
            try:
                os.remove(doc_file)
            except Exception as e:
                logger.warning(f"Error removing document file {doc_file}: {e}")
        
        return JSONResponse({
            "success": True,
            "message": "Document deleted successfully"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/{document_id}/state")
async def get_document_state(document_id: str):
    """Get document state"""
    try:
        if document_id not in document_states:
            # Create new document if it doesn't exist
            document_states[document_id] = DocumentState(document_id, title="Untitled Document")
        
        state = document_states[document_id]
        return JSONResponse({
            "success": True,
            "document": {
                "id": document_id,
                "content": state.get_content(),
                "version": state.get_version()
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting document state: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/documents/{document_id}/save")
async def save_document(document_id: str, request: Request):
    """Save document content"""
    try:
        data = await request.json()
        content = data.get("content", "")
        
        if document_id not in document_states:
            document_states[document_id] = DocumentState(document_id, title="Untitled Document")
        
        # Update document state
        document_states[document_id].content = content
        
        return JSONResponse({
            "success": True,
            "message": "Document saved successfully"
        })
        
    except Exception as e:
        logger.error(f"Error saving document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/{document_id}/users")
async def get_active_users(document_id: str):
    """Get active users for a document"""
    try:
        active_users = await redis_manager.get_active_users(document_id)
        return JSONResponse({
            "success": True,
            "users": active_users
        })
        
    except Exception as e:
        logger.error(f"Error getting active users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clear-all")
async def clear_all_documents():
    """Clear all documents and states (for testing)"""
    try:
        document_states.clear()
        active_connections.clear()
        
        # Also clear Redis presence data
        try:
            await redis_manager.remove_user_presence("all", "all")
        except:
            pass
        
        return JSONResponse({
            "success": True,
            "message": "All documents and states cleared"
        })
        
    except Exception as e:
        logger.error(f"Error clearing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Comment WebSocket Handlers

async def handle_comment_add(document_id: str, message: Dict[str, Any]):
    """Handle comment addition via WebSocket"""
    try:
        comment_data = message.get("comment", {})
        
        # Store comment in document state
        if document_id not in document_states:
            document_states[document_id] = DocumentState(document_id, title="Untitled Document")
        
        if not hasattr(document_states[document_id], 'comments'):
            document_states[document_id].comments = []
        
        comment_data["id"] = str(uuid.uuid4())
        comment_data["created_at"] = datetime.utcnow().isoformat()
        comment_data["is_resolved"] = False
        
        document_states[document_id].comments.append(comment_data)
        
        # Broadcast to all connected users
        await broadcast_to_document(document_id, {
            "type": "comment_added",
            "comment": comment_data
        }, None)
        
        logger.info(f"Comment added to document {document_id} by {comment_data.get('username', 'unknown')}")
        
    except Exception as e:
        logger.error(f"Error handling comment add for document {document_id}: {e}")

async def handle_comment_update(document_id: str, message: Dict[str, Any]):
    """Handle comment update via WebSocket"""
    try:
        comment_id = message.get("comment_id")
        comment_data = message.get("comment", {})
        
        if document_id not in document_states or not hasattr(document_states[document_id], 'comments'):
            return
        
        # Find and update comment
        for comment in document_states[document_id].comments:
            if comment["id"] == comment_id:
                comment.update(comment_data)
                comment["updated_at"] = datetime.utcnow().isoformat()
                break
        
        # Broadcast update
        await broadcast_to_document(document_id, {
            "type": "comment_updated",
            "comment_id": comment_id,
            "comment": comment_data
        }, None)
        
        logger.info(f"Comment {comment_id} updated in document {document_id}")
        
    except Exception as e:
        logger.error(f"Error handling comment update for document {document_id}: {e}")

async def handle_comment_delete(document_id: str, message: Dict[str, Any]):
    """Handle comment deletion via WebSocket"""
    try:
        comment_id = message.get("comment_id")
        
        if document_id not in document_states or not hasattr(document_states[document_id], 'comments'):
            return
        
        # Find and remove comment
        for i, comment in enumerate(document_states[document_id].comments):
            if comment["id"] == comment_id:
                del document_states[document_id].comments[i]
                break
        
        # Broadcast deletion
        await broadcast_to_document(document_id, {
            "type": "comment_deleted",
            "comment_id": comment_id
        }, None)
        
        logger.info(f"Comment {comment_id} deleted from document {document_id}")
        
    except Exception as e:
        logger.error(f"Error handling comment delete for document {document_id}: {e}")

# Comments API Endpoints

@router.get("/documents/{document_id}/comments")
async def get_document_comments(document_id: str):
    """Get all comments for a document"""
    try:
        if document_id not in document_states:
            return JSONResponse({
                "success": True,
                "comments": []
            })
        
        comments = getattr(document_states[document_id], 'comments', [])
        
        return JSONResponse({
            "success": True,
            "comments": comments
        })
        
    except Exception as e:
        logger.error(f"Error getting comments for document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/documents/{document_id}/comments")
async def create_comment(document_id: str, request: Request):
    """Create a new comment for a document"""
    try:
        data = await request.json()
        
        comment_data = {
            "id": str(uuid.uuid4()),
            "document_id": document_id,
            "user_id": data.get("user_id"),
            "username": data.get("username"),
            "content": data.get("content"),
            "anchor_node_id": data.get("anchor_node_id"),
            "anchor_offset": data.get("anchor_offset"),
            "position": data.get("position", 0),
            "created_at": datetime.utcnow().isoformat(),
            "is_resolved": False
        }
        
        # Store comment in document state (in-memory for now)
        if document_id not in document_states:
            document_states[document_id] = DocumentState(document_id, title="Untitled Document")
        
        if not hasattr(document_states[document_id], 'comments'):
            document_states[document_id].comments = []
        
        document_states[document_id].comments.append(comment_data)
        
        # Broadcast comment to all connected users
        await redis_manager.publish_comment(document_id, {
            "type": "comment_added",
            "comment": comment_data
        })
        
        return JSONResponse({
            "success": True,
            "comment": comment_data,
            "message": "Comment created successfully"
        })
        
    except Exception as e:
        logger.error(f"Error creating comment for document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/documents/{document_id}/comments/{comment_id}")
async def update_comment(document_id: str, comment_id: str, request: Request):
    """Update an existing comment"""
    try:
        data = await request.json()
        
        if document_id not in document_states or not hasattr(document_states[document_id], 'comments'):
            raise HTTPException(status_code=404, detail="Document or comments not found")
        
        # Find and update comment
        comment_found = False
        for comment in document_states[document_id].comments:
            if comment["id"] == comment_id:
                comment["content"] = data.get("content", comment["content"])
                comment["is_resolved"] = data.get("is_resolved", comment["is_resolved"])
                comment["updated_at"] = datetime.utcnow().isoformat()
                comment_found = True
                break
        
        if not comment_found:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        # Broadcast update
        await redis_manager.publish_comment(document_id, {
            "type": "comment_updated",
            "comment_id": comment_id,
            "comment": comment
        })
        
        return JSONResponse({
            "success": True,
            "message": "Comment updated successfully"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating comment {comment_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/documents/{document_id}/comments/{comment_id}")
async def delete_comment(document_id: str, comment_id: str):
    """Delete a comment"""
    try:
        if document_id not in document_states or not hasattr(document_states[document_id], 'comments'):
            raise HTTPException(status_code=404, detail="Document or comments not found")
        
        # Find and remove comment
        comment_found = False
        for i, comment in enumerate(document_states[document_id].comments):
            if comment["id"] == comment_id:
                del document_states[document_id].comments[i]
                comment_found = True
                break
        
        if not comment_found:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        # Broadcast deletion
        await redis_manager.publish_comment(document_id, {
            "type": "comment_deleted",
            "comment_id": comment_id
        })
        
        return JSONResponse({
            "success": True,
            "message": "Comment deleted successfully"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting comment {comment_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))