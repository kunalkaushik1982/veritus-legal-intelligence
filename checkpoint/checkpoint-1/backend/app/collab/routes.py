"""
WebSocket endpoints for collaborative editing
Handles real-time communication between clients
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

from .websocket_manager import websocket_manager
from .operational_transform import operational_transform, DocumentState, Operation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/collab", tags=["collaborative-editing"])

# Store document states
document_states: Dict[str, DocumentState] = {}

# Store active WebSocket connections for broadcasting
active_connections: Dict[str, List[WebSocket]] = {}

async def broadcast_to_document(document_id: str, message: dict, exclude_connection_id: str = None):
    """Broadcast message to all users connected to a document"""
    if document_id not in active_connections:
        return
                           
    for websocket in active_connections[document_id]:
        try:
            # Get connection ID from websocket if possible (simplified approach)
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            print(f"Error broadcasting to WebSocket: {e}")

@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify collab router is working"""
    print("Test endpoint called - PRINT STATEMENT")
    logger.info("Test endpoint called - LOGGER")
    return {"message": "Collab router is working", "status": "success"}

@router.post("/clear-all")
async def clear_all_documents():
    """Clear all document states and files - for testing purposes"""
    global document_states
                           
    # Clear in-memory document states
    document_states.clear()
    print("All document states cleared from memory")
                           
    # Clear all document files
    import os
    import shutil
                           
    collab_dir = "/app/collab_documents"
    if os.path.exists(collab_dir):
        for filename in os.listdir(collab_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(collab_dir, filename)
                os.remove(file_path)
                print(f"Removed file: {filename}")
                           
    return {"message": "All documents and states cleared", "cleared_documents": len(document_states)}

@router.post("/cleanup-stale-users")
async def cleanup_stale_users():
    """Remove stale users who may not have disconnected properly"""
    global document_states
                           
    cleaned_count = 0
    for doc_id, doc_state in document_states.items():
        initial_count = len(doc_state.active_users)
        # Remove users who haven't been active for more than 5 minutes
        current_time = datetime.now()
        doc_state.active_users = [
            user for user in doc_state.active_users
            if (current_time - datetime.fromisoformat(user.get("connected_at", current_time.isoformat()))).total_seconds() < 300
        ]
        final_count = len(doc_state.active_users)
        if initial_count != final_count:
            cleaned_count += (initial_count - final_count)
            print(f"Cleaned {initial_count - final_count} stale users from document {doc_id}")
                           
    return {"message": f"Cleaned {cleaned_count} stale users", "cleaned_count": cleaned_count}

@router.websocket("/test")
async def test_websocket(websocket: WebSocket):
    """Simple test WebSocket endpoint"""
    logger.info("Test WebSocket connection attempt")
    await websocket.accept()
    logger.info("Test WebSocket accepted")
                           
    try:
        await websocket.send_text("Hello from test WebSocket!")
        logger.info("Test message sent")
                           
        while True:
            message = await websocket.receive_text()
            logger.info(f"Test WebSocket received: {message}")
            await websocket.send_text(f"Echo: {message}")
    except WebSocketDisconnect:
        logger.info("Test WebSocket disconnected")
    except Exception as e:
        logger.error(f"Test WebSocket error: {str(e)}")

@router.websocket("/simple")
async def simple_websocket(websocket: WebSocket):
    """Very simple WebSocket endpoint"""
    print("Simple WebSocket connection attempt")
    await websocket.accept()
    print("Simple WebSocket accepted")
                           
    try:
        await websocket.send_text("Hello from simple WebSocket!")
        print("Simple message sent")
                           
        while True:
            message = await websocket.receive_text()
            print(f"Simple WebSocket received: {message}")
            await websocket.send_text(f"Echo: {message}")
    except Exception as e:
        print(f"Simple WebSocket error: {str(e)}")

@router.websocket("/ws/{document_id}")
async def websocket_endpoint(websocket: WebSocket, document_id: str):
    """Simplified WebSocket endpoint for collaborative editing"""
    print(f"WebSocket connection attempt for document: {document_id}")
                           
    # Initialize document state if it doesn't exist
    if document_id not in document_states:
        document_states[document_id] = DocumentState(document_id)
                           
    connected_user = None
    user_id = None
    username = None
                           
    try:
        await websocket.accept()
        print(f"WebSocket accepted for document: {document_id}")
                           
        # Register this WebSocket connection for broadcasting
        if document_id not in active_connections:
            active_connections[document_id] = []
        active_connections[document_id].append(websocket)
                           
        # Wait for user identification message first
        try:
            auth_message = await websocket.receive_text()
            print(f"Auth message received: {auth_message}")
                           
            auth_data = json.loads(auth_message)
            user_id = auth_data.get("user_id", f"user-{datetime.now().timestamp()}")
            username = auth_data.get("username", "Anonymous User")
            frontend_connection_id = auth_data.get("connection_id", f"{user_id}-{datetime.now().timestamp()}-{id(websocket)}")
                           
            # Use frontend connection ID or generate one
            connection_id = frontend_connection_id
                           
            # Check if this user already has an active connection by username
            existing_user_index = None
            for i, user in enumerate(document_states[document_id].active_users):
                if user["username"] == username:
                    existing_user_index = i
                    break
                           
            if existing_user_index is not None:
                # Update existing user's connection
                connected_user = document_states[document_id].active_users[existing_user_index]
                connected_user["user_id"] = user_id  # Update to new session ID
                connected_user["connection_id"] = connection_id
                connected_user["connected_at"] = datetime.now().isoformat()
                print(f"User {username} ({user_id}) connection updated in document {document_id}")
            else:
                # Add new user entry
                connected_user = {
                    "user_id": user_id,
                    "username": username,
                    "connection_id": connection_id,
                    "cursor_position": 0,
                    "color": f"hsl({hash(user_id) % 360}, 70%, 50%)",
                    "connected_at": datetime.now().isoformat()
                }
                document_states[document_id].active_users.append(connected_user)
                print(f"User {username} ({user_id}) added to document {document_id} with connection {connection_id}")
                           
        except Exception as e:
            print(f"Error processing auth message: {e}")
            # Create anonymous user
            user_id = f"anonymous-{datetime.now().timestamp()}"
            username = "Anonymous User"
            connection_id = f"{user_id}-{datetime.now().timestamp()}-{id(websocket)}"
            connected_user = {
                "user_id": user_id,
                "username": username,
                "connection_id": connection_id,
                "cursor_position": 0,
                "color": f"hsl({hash(user_id) % 360}, 70%, 50%)",
                "connected_at": datetime.now().isoformat()
            }
            document_states[document_id].active_users.append(connected_user)
                           
        # Send welcome message with current user list
        await websocket.send_text(json.dumps({
            "type": "welcome",
            "message": f"Connected to document {document_id}",
            "document_id": document_id,
            "user_id": user_id,
            "username": username,
            "active_users": document_states[document_id].active_users
        }))
        print(f"Welcome message sent for document: {document_id}")
        print(f"Current active users in document {document_id}: {len(document_states[document_id].active_users)}")
        for user in document_states[document_id].active_users:
            print(f"  - {user['username']} ({user['user_id']})")
                           
        # Message loop
        while True:
            try:
                message = await websocket.receive_text()
                print(f"Received: {message}")
                           
                try:
                    data = json.loads(message)
                           
                    # Handle different message types
                    if data.get("type") == "text_operation":
                        # Handle text operations with OT
                        operation_data = data.get("operation", {})
                        client_version = data.get("version", 0)
                           
                        # Ensure document state exists
                        if document_id not in document_states:
                            document_states[document_id] = DocumentState(document_id)
                            print(f"Created new document state for: {document_id}")
                           
                        if operation_data and document_id in document_states:
                            try:
                                # Create operation from received data
                                operation = Operation.from_dict(operation_data)
                           
                                # Add user attribution to operation
                                operation.user_id = connected_user.get("user_id")
                                operation.username = connected_user.get("username")
                                operation.user_color = connected_user.get("color", "#7c3aed")
                           
                                # Apply operation to document state
                                success = document_states[document_id].apply_operation(operation)
                           
                                if success:
                                    # Broadcast operation to all other users
                                    broadcast_message = {
                                        "type": "operation_applied",
                                        "operation": operation.to_dict(),
                                        "document_version": document_states[document_id].version,
                                        "document_content": document_states[document_id].content,
                                        "timestamp": datetime.now().isoformat()
                                    }
                           
                                    # Broadcast to all connected users except sender
                                    await broadcast_to_document(document_id, broadcast_message, connected_user.get("connection_id"))
                           
                                    print(f"Operation applied successfully: {operation.type} at position {operation.position}")
                                else:
                                    print(f"Failed to apply operation: {operation.type}")
                           
                            except Exception as e:
                                print(f"Error processing text operation: {e}")
                                # Send error message back to client
                                await websocket.send_text(json.dumps({
                                    "type": "error",
                                    "message": f"Error processing operation: {str(e)}",
                                    "timestamp": datetime.now().isoformat()
                                }))
                                       
                           elif data.get("type") == "cursor_update":
                               # Handle cursor updates
                               if connected_user:
                                   connected_user["cursor_position"] = data.get("cursor_position", 0)
                                       
                           # Echo back with timestamp
                    response = {
                        "type": "echo",
                        "original": data,
                        "timestamp": datetime.now().isoformat(),
                        "document_id": document_id,
                        "active_users": document_states[document_id].active_users
                    }
                    await websocket.send_text(json.dumps(response))
                           
                except json.JSONDecodeError:
                    # Echo non-JSON as text
                    await websocket.send_text(json.dumps({
                        "type": "echo_text",
                        "message": message,
                        "timestamp": datetime.now().isoformat(),
                        "document_id": document_id,
                        "active_users": document_states[document_id].active_users
                    }))
                           
            except WebSocketDisconnect:
                print(f"WebSocket disconnected for document: {document_id}")
                break
            except Exception as e:
                print(f"Error in message loop for document {document_id}: {str(e)}")
                break
                           
    except WebSocketDisconnect:
        print(f"WebSocket disconnected during setup for document: {document_id}")
    except Exception as e:
        print(f"WebSocket setup error for document {document_id}: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
    finally:
        # Remove WebSocket connection from active connections
        if document_id in active_connections:
            try:
                active_connections[document_id].remove(websocket)
                if not active_connections[document_id]:
                    del active_connections[document_id]
            except ValueError:
                pass  # WebSocket not in list
                           
        # Remove user from active users when they disconnect
        if connected_user and document_id in document_states:
            initial_count = len(document_states[document_id].active_users)
            document_states[document_id].active_users = [
                user for user in document_states[document_id].active_users 
                if user.get("connection_id") != connected_user.get("connection_id")
            ]
            final_count = len(document_states[document_id].active_users)
            print(f"User {connected_user['username']} ({connected_user['user_id']}) connection {connected_user.get('connection_id')} removed from document {document_id}")
            print(f"Remaining users in document {document_id}: {final_count}")
                           
            # Broadcast updated user list to remaining users
            if document_states[document_id].active_users:
                print(f"Broadcasting user list update to {len(document_states[document_id].active_users)} remaining users")

@router.get("/documents/{document_id}/state")
async def get_document_state(document_id: str):
    """Get current state of a document"""
    try:
        # Create document if it doesn't exist
        if document_id not in document_states:
            logger.info(f"Creating new document state for: {document_id}")
                           
            # Try to load from persistent storage first
            import os
            import json
                           
            doc_file_path = f"/app/collab_documents/{document_id}.json"
            if os.path.exists(doc_file_path):
                try:
                    with open(doc_file_path, 'r', encoding='utf-8') as f:
                        saved_data = json.load(f)
                           
                    # Create document state with saved content
                    document_states[document_id] = DocumentState(document_id, saved_data.get('content', ''))
                    document_states[document_id].last_modified = saved_data.get('last_modified', datetime.now().isoformat())
                    print(f"Loaded document {document_id} from persistent storage")
                except Exception as e:
                    print(f"Error loading saved document {document_id}: {e}")
                    document_states[document_id] = DocumentState(document_id)
            else:
                document_states[document_id] = DocumentState(document_id)
                           
        state = document_states[document_id].get_state()
        return {
            "success": True,
            "document": state
        }
    except Exception as e:
        logger.error(f"Error getting document state: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting document state: {str(e)}")

@router.post("/documents/{document_id}/operations")
async def apply_operation(document_id: str, operation_data: Dict):
    """Apply operation to document (for testing/debugging)"""
    try:
        if document_id not in document_states:
            raise HTTPException(status_code=404, detail="Document not found")
                           
        from .operational_transform import Operation
                           
        operation = Operation.from_dict(operation_data)
        success = document_states[document_id].apply_operation(operation)
                           
        if success:
            return {
                "success": True,
                "message": "Operation applied successfully",
                "version": document_states[document_id].version
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to apply operation")
                           
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying operation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error applying operation: {str(e)}")

@router.get("/documents/{document_id}/history")
async def get_operation_history(document_id: str, from_version: int = 0):
    """Get operation history for a document"""
    try:
        if document_id not in document_states:
            raise HTTPException(status_code=404, detail="Document not found")
                           
        operations = operational_transform.get_operations_since(document_id, from_version)
        operations_data = [op.to_dict() for op in operations]
                           
        return {
            "success": True,
            "operations": operations_data,
            "current_version": document_states[document_id].version
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting operation history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting operation history: {str(e)}")

@router.get("/documents/{document_id}/users")
async def get_active_users(document_id: str):
    """Get list of active users in a document"""
    try:
        if document_id not in document_states:
            raise HTTPException(status_code=404, detail="Document not found")
                           
        return {
            "success": True,
            "active_users": document_states[document_id].active_users
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting active users: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting active users: {str(e)}")

@router.post("/documents/{document_id}/save")
async def save_document(document_id: str, request: Request):
    """Save document state to persistent storage"""
    try:
        if document_id not in document_states:
            raise HTTPException(status_code=404, detail="Document not found")
                           
        # Get the content from the request body
        body = await request.json()
        content = body.get("content", "")
                           
        # Update the document state with the new content
        document_states[document_id].content = content
        document_states[document_id].last_modified = datetime.now().isoformat()
                           
        # Save to persistent storage (JSON file)
        import os
        import json
                           
        # Create collab_documents directory if it doesn't exist
        os.makedirs("/app/collab_documents", exist_ok=True)
                           
        # Save document to file
        doc_file_path = f"/app/collab_documents/{document_id}.json"
        doc_data = {
            "document_id": document_id,
            "content": content,
            "version": document_states[document_id].version,
            "last_modified": document_states[document_id].last_modified,
            "created_at": getattr(document_states[document_id], 'created_at', datetime.now().isoformat())
        }
                           
        with open(doc_file_path, 'w', encoding='utf-8') as f:
            json.dump(doc_data, f, indent=2, ensure_ascii=False)
                           
        print(f"Document {document_id} saved to {doc_file_path}")
                           
        return {
            "success": True,
            "message": "Document saved successfully",
            "document_id": document_id,
            "version": document_states[document_id].version,
            "last_modified": document_states[document_id].last_modified
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving document: {str(e)}")

@router.get("/documents")
async def list_documents():
    """List all active documents"""
    try:
        documents = []
        for doc_id, state in document_states.items():
            documents.append({
                "document_id": doc_id,
                "version": state.version,
                "last_modified": state.last_modified,
                "active_users_count": len(state.active_users),
                "content_length": len(state.content)
            })
                           
        return {
            "success": True,
            "documents": documents
        }
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@router.post("/documents")
async def create_document(request: Request):
    """Create a new collaborative document"""
    try:
        body = await request.json()
        document_id = body.get("document_id")
        title = body.get("title", "")
        initial_content = body.get("initial_content", "")
                           
        if not document_id:
            raise HTTPException(status_code=400, detail="Document ID is required")
                           
        # Allow overwriting existing documents
        if document_id in document_states:
            print(f"Overwriting existing document: {document_id}")
            # Clear existing document state
            del document_states[document_id]
                           
        # Create new document state
        document_states[document_id] = DocumentState(document_id, initial_content)
                           
        logger.info(f"Created document: {document_id}")
                           
        return {
            "success": True,
            "document_id": document_id,
            "title": title,
            "version": 0,
            "content": initial_content,
            "message": "Document created successfully"
        }
                           
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating document: {str(e)}")

@router.get("/test")
async def test_collaborative_editing():
    """Test page for collaborative editing"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Collaborative Editing Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 800px; margin: 0 auto; }
            .editor { border: 1px solid #ccc; padding: 10px; min-height: 300px; }
            .users { margin-top: 20px; }
            .user { display: inline-block; margin: 5px; padding: 5px 10px; border-radius: 3px; color: white; }
            .status { margin-top: 10px; padding: 10px; background: #f0f0f0; border-radius: 3px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Collaborative Editing Test</h1>
            <div class="status" id="status">Connecting...</div>
            <div class="editor" id="editor" contenteditable="true"></div>
            <div class="users" id="users"></div>
        </div>
                           
        <script>
            const documentId = 'test-document';
            const userId = 'user-' + Math.random().toString(36).substr(2, 9);
            const username = 'User ' + userId.substr(-3);
                           
            let ws = null;
            let documentVersion = 0;
            let isApplyingRemoteOperation = false;
                           
            function connect() {
                ws = new WebSocket(`ws://localhost:8000/collab/ws/${documentId}`);
                           
                ws.onopen = function() {
                    // Send authentication
                    ws.send(JSON.stringify({
                        user_id: userId,
                        username: username
                    }));
                    updateStatus('Connected');
                };
                           
                ws.onmessage = function(event) {
                    const message = JSON.parse(event.data);
                    handleMessage(message);
                };
                           
                ws.onclose = function() {
                    updateStatus('Disconnected');
                    setTimeout(connect, 3000);
                };
                           
                ws.onerror = function(error) {
                    updateStatus('Error: ' + error);
                };
            }
                           
            function handleMessage(message) {
                switch(message.type) {
                    case 'document_state':
                        documentVersion = message.version;
                        document.getElementById('editor').innerHTML = message.content;
                        updateUsers(message.active_users);
                        break;
                           
                    case 'text_operation':
                        applyRemoteOperation(message.operation);
                        documentVersion = message.version;
                        break;
                           
                    case 'user_joined':
                        addUser(message.user);
                        break;
                           
                    case 'user_left':
                        removeUser(message.user_id);
                        break;
                           
                    case 'cursor_update':
                        updateUserCursor(message.user_id, message.cursor_position);
                        break;
                           
                    case 'error':
                        updateStatus('Error: ' + message.message);
                        break;
                }
            }
                           
            function applyRemoteOperation(operation) {
                isApplyingRemoteOperation = true;
                const editor = document.getElementById('editor');
                           
                if (operation.type === 'insert') {
                    const textNode = document.createTextNode(operation.text);
                    const range = document.createRange();
                    range.setStart(editor.firstChild || editor, operation.position);
                    range.insertNode(textNode);
                } else if (operation.type === 'delete') {
                    const range = document.createRange();
                    range.setStart(editor.firstChild || editor, operation.position);
                    range.setEnd(editor.firstChild || editor, operation.position + operation.length);
                    range.deleteContents();
                }
                           
                isApplyingRemoteOperation = false;
            }
                           
            function sendOperation(operation) {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({
                        type: 'text_operation',
                        operation: operation,
                        version: documentVersion
                    }));
                }
            }
                           
            function updateUsers(users) {
                const usersDiv = document.getElementById('users');
                usersDiv.innerHTML = '';
                users.forEach(user => {
                    const userDiv = document.createElement('div');
                    userDiv.className = 'user';
                    userDiv.style.backgroundColor = user.color;
                    userDiv.textContent = user.username;
                    usersDiv.appendChild(userDiv);
                });
            }
                           
            function addUser(user) {
                const usersDiv = document.getElementById('users');
                const userDiv = document.createElement('div');
                userDiv.className = 'user';
                userDiv.style.backgroundColor = user.color;
                userDiv.textContent = user.username;
                userDiv.id = 'user-' + user.user_id;
                usersDiv.appendChild(userDiv);
            }
                           
            function removeUser(userId) {
                const userDiv = document.getElementById('user-' + userId);
                if (userDiv) {
                    userDiv.remove();
                }
            }
                           
            function updateUserCursor(userId, position) {
                // Implement cursor visualization
            }
                           
            function updateStatus(message) {
                document.getElementById('status').textContent = message;
            }
                           
            // Handle text input
            document.getElementById('editor').addEventListener('input', function(e) {
                if (isApplyingRemoteOperation) return;
                           
                // Simple operation detection (in production, use proper diff algorithm)
                const operation = {
                    type: 'insert',
                    position: 0,
                    text: e.target.textContent
                };
                           
                sendOperation(operation);
            });
                           
            // Connect when page loads
            connect();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
