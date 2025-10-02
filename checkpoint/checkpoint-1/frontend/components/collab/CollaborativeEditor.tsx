/**
 * Collaborative Editor Component
 * Real-time collaborative text editing with WebSocket support
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Users, Lock, Unlock, Save, Download, Upload, Bold, Italic, Underline, AlignLeft, AlignCenter, AlignRight, List, ListOrdered } from 'lucide-react';
import toast from 'react-hot-toast';

interface User {
  user_id: string;
  username: string;
  cursor_position: number;
  color: string;
  selection_range?: { start: number; end: number };
}

interface Operation {
  id: string;
  type: 'insert' | 'delete' | 'retain';
  position: number;
  text?: string;
  length?: number;
  timestamp: string;
}

interface DocumentState {
  document_id: string;
  content: string;
  version: number;
  last_modified: string;
  active_users: User[];
}

interface CollaborativeEditorProps {
  documentId: string;
  userId: string;
  username: string;
  onSave?: (content: string) => void;
  onLoad?: (documentId: string) => void;
  onConnectionChange?: (connected: boolean) => void;
}

export const CollaborativeEditor: React.FC<CollaborativeEditorProps> = ({
  documentId,
  userId,
  username,
  onSave,
  onLoad,
  onConnectionChange
}) => {
  const [documentState, setDocumentState] = useState<DocumentState | null>(null);
  const [content, setContent] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isLocked, setIsLocked] = useState(false);
  const [activeUsers, setActiveUsers] = useState<User[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string>('');
  const [lastContent, setLastContent] = useState('');
  const [documentVersion, setDocumentVersion] = useState(0);
  const [isApplyingRemoteOperation, setIsApplyingRemoteOperation] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [typingUsers, setTypingUsers] = useState<{[key: string]: number}>({});
  
  const wsRef = useRef<WebSocket | null>(null);
  const editorRef = useRef<HTMLTextAreaElement>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Handle incoming WebSocket messages
  const handleMessage = useCallback((message: any) => {
    console.log('Received message:', message);
    
    switch (message.type) {
      case 'welcome':
        console.log('Welcome message:', message.message);
        console.log('Active users:', message.active_users);
        setIsConnected(true);
        onConnectionChange?.(true);
        setActiveUsers(message.active_users || []);
        toast.success(`Connected to ${message.document_id} as ${message.username}`);
        break;
        
      case 'operation_applied':
        console.log('Operation applied:', message.operation);
        if (message.document_content !== undefined) {
          // Update content with the latest document state
          setContent(message.document_content);
          setLastContent(message.document_content); // Update lastContent
          if (editorRef.current) {
            editorRef.current.value = message.document_content;
          }
        }
        break;
        
      case 'echo':
        console.log('Echo received:', message.original);
        if (message.active_users) {
          setActiveUsers(message.active_users);
        }
        break;
        
      case 'typing_start':
        console.log('User started typing:', message.username);
        if (message.user_id !== userId) {
          setTypingUsers(prev => ({
            ...prev,
            [message.user_id]: Date.now()
          }));
        }
        break;
        
      case 'typing_stop':
        console.log('User stopped typing:', message.username);
        if (message.user_id !== userId) {
          setTypingUsers(prev => {
            const newTyping = { ...prev };
            delete newTyping[message.user_id];
            return newTyping;
          });
        }
        break;
        
      case 'echo_text':
        console.log('Text echo received:', message.message);
        if (message.active_users) {
          setActiveUsers(message.active_users);
        }
        break;
        
      case 'user_list_update':
        console.log('User list updated:', message.active_users);
        setActiveUsers(message.active_users || []);
        break;
        
      case 'error':
        console.error('WebSocket error:', message.message);
        toast.error(message.message);
        break;
        
      default:
        console.log('Unknown message type:', message.type, message);
    }
  }, [onConnectionChange]);

  // Simplified WebSocket connection
  const connect = useCallback(async () => {
    if (!documentId) {
      console.log('Missing documentId for WebSocket connection');
      return;
    }

    // Prevent multiple simultaneous connections
    if (isConnecting || (wsRef.current && (wsRef.current.readyState === WebSocket.CONNECTING || wsRef.current.readyState === WebSocket.OPEN))) {
      console.log('Connection already active, skipping...');
      return;
    }

    try {
      setIsConnecting(true);
      
      // Close existing connection if any
      if (wsRef.current) {
        console.log('Closing existing WebSocket connection');
        wsRef.current.close(1000, 'Starting new connection');
        wsRef.current = null;
      }
      
      // Small delay to ensure previous connection is fully closed
      await new Promise(resolve => setTimeout(resolve, 100));
      
      console.log(`Connecting to WebSocket for document: ${documentId}`);
      const ws = new WebSocket(`ws://localhost:8000/collab/ws/${documentId}`);
      
      // Set a connection timeout
      const connectionTimeout = setTimeout(() => {
        if (ws.readyState === WebSocket.CONNECTING) {
          console.log('WebSocket connection timeout, closing...');
          ws.close();
          setIsConnecting(false);
          setIsConnected(false);
          onConnectionChange?.(false);
          toast.error('Connection timeout - please try again');
        }
      }, 10000); // 10 second timeout
      
      ws.onopen = () => {
        console.log('WebSocket connected successfully');
        clearTimeout(connectionTimeout);
        setIsConnecting(false);
        
        // Generate unique session ID for this connection
        const collabUser = localStorage.getItem('collab_user');
        let baseUserId = '';
        
        if (collabUser) {
          try {
            const userData = JSON.parse(collabUser);
            baseUserId = userData.base_user_id || `user-${Date.now()}`;
          } catch (error) {
            console.error('Error parsing collab user:', error);
            baseUserId = `user-${Date.now()}`;
          }
        } else {
          baseUserId = `user-${Date.now()}`;
        }
        
        const sessionId = `${baseUserId}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const connectionId = `${sessionId}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        
        // Store current session ID for "You" comparison
        setCurrentSessionId(sessionId);
        
        // Send authentication message immediately
        ws.send(JSON.stringify({
          user_id: sessionId,
          username: username,
          connection_id: connectionId
        }));
      };
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleMessage(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      
      ws.onclose = (event) => {
        clearTimeout(connectionTimeout);
        console.log('WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        setIsConnecting(false);
        onConnectionChange?.(false);
        
        // Simple reconnection logic - only for unexpected disconnects
        if (event.code !== 1000 && event.code !== 1001 && !reconnectTimeoutRef.current) {
          console.log('Scheduling reconnection in 5 seconds...');
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Attempting to reconnect...');
            reconnectTimeoutRef.current = null;
            connect();
          }, 5000);
        }
      };
      
      ws.onerror = (error) => {
        clearTimeout(connectionTimeout);
        console.error('WebSocket error:', error);
        console.error('WebSocket readyState:', ws.readyState);
        console.error('WebSocket URL:', ws.url);
        setIsConnected(false);
        setIsConnecting(false);
        onConnectionChange?.(false);
        
        // Don't show error toast for connection errors during setup
        if (ws.readyState === WebSocket.CLOSED || ws.readyState === WebSocket.CLOSING) {
          console.log('WebSocket closed/closing, this is expected during connection setup');
          return;
        }
        
        toast.error('WebSocket connection error occurred');
      };
      
      wsRef.current = ws;
    } catch (error) {
      console.error('Error connecting to WebSocket:', error);
      setIsConnecting(false);
      toast.error('Failed to connect to collaborative editing');
    }
  }, [documentId, handleMessage, onConnectionChange]);

  // Apply remote operation with user attribution
  const applyRemoteOperationWithAttribution = useCallback((operation: any) => {
    if (!editorRef.current || isApplyingRemoteOperation) return;
    
    setIsApplyingRemoteOperation(true);
    
    try {
      if (operation.type === 'insert' && operation.text) {
        const editor = editorRef.current;
        
        // Get current cursor position
        const selection = window.getSelection();
        if (selection && selection.rangeCount > 0) {
          const range = selection.getRangeAt(0);
          const cursorPosition = range.startOffset;
          
          // Create a span with user attribution
          const span = document.createElement('span');
          span.textContent = operation.text;
          span.style.backgroundColor = operation.user_color + '20'; // 20% opacity
          span.style.borderBottom = `2px solid ${operation.user_color}`;
          span.style.padding = '1px 2px';
          span.style.borderRadius = '2px';
          span.title = `${operation.username} • ${new Date(operation.timestamp).toLocaleTimeString()}`;
          span.className = 'user-attribution';
          
          // Find the correct position to insert
          const textNode = editor.firstChild;
          if (textNode && textNode.nodeType === Node.TEXT_NODE) {
            const insertPosition = Math.min(operation.position, textNode.textContent.length);
            
            // Split the text node at the insert position
            const range = document.createRange();
            range.setStart(textNode, insertPosition);
            range.setEnd(textNode, insertPosition);
            
            // Insert the span
            range.insertNode(span);
          } else {
            // If no text node, just append
            editor.appendChild(span);
          }
        }
      }
    } catch (error) {
      console.error('Error applying remote operation with attribution:', error);
    } finally {
      setIsApplyingRemoteOperation(false);
    }
  }, [isApplyingRemoteOperation]);

  // Add user attribution to content
  const addUserAttributionToContent = useCallback((content: string, operation: any) => {
    if (!operation || operation.type !== 'insert' || !operation.text) {
      return content;
    }
    
    try {
      // Find the position where the text was inserted
      const insertPosition = operation.position;
      const insertText = operation.text;
      
      // Create attributed text with user styling
      const attributedText = `<span class="user-attribution" style="background-color: ${operation.user_color}20; border-bottom: 2px solid ${operation.user_color}; padding: 1px 2px; border-radius: 2px;" title="${operation.username} • ${new Date(operation.timestamp).toLocaleTimeString()}">${insertText}</span>`;
      
      // Insert the attributed text at the correct position
      const beforeText = content.substring(0, insertPosition);
      const afterText = content.substring(insertPosition);
      
      return beforeText + attributedText + afterText;
    } catch (error) {
      console.error('Error adding user attribution:', error);
      return content;
    }
  }, []);

  // Apply remote operation to editor (for contentEditable)
  const applyRemoteOperation = useCallback((operation: Operation) => {
    if (!editorRef.current || isApplyingRemoteOperation) return;
    
    setIsApplyingRemoteOperation(true);
    
    try {
      // For contentEditable, we update the HTML content
      if (operation.type === 'insert' && operation.text) {
        editorRef.current.innerHTML = operation.text;
      }
    } catch (error) {
      console.error('Error applying remote operation:', error);
    } finally {
      setIsApplyingRemoteOperation(false);
    }
  }, [isApplyingRemoteOperation]);

  // Handle missing operations (client needs to catch up)
  const handleMissingOperations = useCallback((operations: Operation[]) => {
    console.log('Applying missing operations:', operations);
    
    operations.forEach(operation => {
      applyRemoteOperation(operation);
    });
  }, [applyRemoteOperation]);

  // Send operation to server
  const sendOperation = useCallback((operation: Operation) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'text_operation',
        operation: operation,
        version: documentVersion
      }));
    }
  }, [documentVersion]);

  // Rich text formatting functions
  const formatText = useCallback((command: string, value?: string) => {
    if (command === 'insertUnorderedList') {
      // Custom bullet list implementation
      const selection = window.getSelection();
      if (selection && selection.rangeCount > 0) {
        const range = selection.getRangeAt(0);
        const listItem = document.createElement('li');
        
        if (range.collapsed) {
          // If no text is selected, insert a bullet point
          listItem.innerHTML = '&nbsp;';
        } else {
          // If text is selected, wrap it in a list item
          listItem.innerHTML = range.toString();
          range.deleteContents();
        }
        
        const ul = document.createElement('ul');
        ul.style.marginLeft = '20px';
        ul.style.paddingLeft = '20px';
        ul.appendChild(listItem);
        range.insertNode(ul);
        
        // Place cursor after the list item
        const newRange = document.createRange();
        newRange.setStartAfter(listItem);
        newRange.collapse(true);
        selection.removeAllRanges();
        selection.addRange(newRange);
      }
    } else if (command === 'insertOrderedList') {
      // Custom numbered list implementation
      const selection = window.getSelection();
      if (selection && selection.rangeCount > 0) {
        const range = selection.getRangeAt(0);
        const listItem = document.createElement('li');
        
        if (range.collapsed) {
          // If no text is selected, insert a numbered point
          listItem.innerHTML = '&nbsp;';
        } else {
          // If text is selected, wrap it in a list item
          listItem.innerHTML = range.toString();
          range.deleteContents();
        }
        
        const ol = document.createElement('ol');
        ol.style.marginLeft = '20px';
        ol.style.paddingLeft = '20px';
        ol.appendChild(listItem);
        range.insertNode(ol);
        
        // Place cursor after the list item
        const newRange = document.createRange();
        newRange.setStartAfter(listItem);
        newRange.collapse(true);
        selection.removeAllRanges();
        selection.addRange(newRange);
      }
    } else {
      // Use standard execCommand for other formatting
      document.execCommand(command, false, value);
    }
    editorRef.current?.focus();
  }, []);

  // Handle text input changes (reliable textarea approach)
  const handleTextChange = useCallback((event: React.ChangeEvent<HTMLTextAreaElement>) => {
    try {
      if (isApplyingRemoteOperation || isLocked) return;
      
      const newContent = event.target.value;
      const oldContent = lastContent;
      
      // Handle text changes (both insertion and deletion)
      if (newContent !== oldContent) {
        const cursorPosition = event.target.selectionStart || 0;
        
        if (newContent.length > oldContent.length) {
          // Handle insertion
          const addedLength = newContent.length - oldContent.length;
          const addedText = newContent.slice(-addedLength); // Get the last added characters
          
          // Send insert operation to server
          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
              type: 'text_operation',
              operation: {
                id: `op-${Date.now()}`,
                type: 'insert',
                position: cursorPosition - addedLength,
                text: addedText,
                timestamp: new Date().toISOString(),
                user_id: userId,
                username: username,
                user_color: `hsl(${username === 'kunal.kaushik1982' ? 150 : 270}, 70%, 50%)`
              },
              version: documentVersion
            }));
          }
        } else if (newContent.length < oldContent.length) {
          // Handle deletion
          const deletedLength = oldContent.length - newContent.length;
          
          // Send delete operation to server
          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
              type: 'text_operation',
              operation: {
                id: `op-${Date.now()}`,
                type: 'delete',
                position: cursorPosition,
                length: deletedLength,
                timestamp: new Date().toISOString(),
                user_id: userId,
                username: username,
                user_color: `hsl(${username === 'kunal.kaushik1982' ? 150 : 270}, 70%, 50%)`
              },
              version: documentVersion
            }));
          }
        }
        
        // Update content and last content
        setContent(newContent);
        setLastContent(newContent);
        
        // Send typing indicator
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({
            type: 'typing_start',
            user_id: userId,
            username: username
          }));
        }
      }
    } catch (error) {
      console.error('Error in handleTextChange:', error);
    }
  }, [isApplyingRemoteOperation, isLocked, documentVersion, lastContent, userId, username]);

  // Handle cursor position updates (for textarea)
  const handleCursorUpdate = useCallback(() => {
    try {
      if (!editorRef.current || isApplyingRemoteOperation) return;
      
      const cursorPosition = editorRef.current.selectionStart || 0;
      
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: 'cursor_update',
          cursor_position: cursorPosition
        }));
      }
      
      // Clear existing typing timeout and set a new one
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
      
      // Send typing stop after 2 seconds of inactivity
      typingTimeoutRef.current = setTimeout(() => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({
            type: 'typing_stop',
            user_id: userId,
            username: username
          }));
        }
      }, 2000);
      
    } catch (error) {
      console.error('Error in handleCursorUpdate:', error);
    }
  }, [isApplyingRemoteOperation, userId, username]);

  // Update user cursor visualization
  const updateUserCursor = useCallback((userId: string, position: number) => {
    // Implement cursor visualization for other users
    console.log(`User ${userId} cursor at position ${position}`);
  }, []);

  // Update user selection visualization
  const updateUserSelection = useCallback((userId: string, selectionRange: any) => {
    // Implement selection visualization for other users
    console.log(`User ${userId} selection:`, selectionRange);
  }, []);

  // Save document
  const handleSave = useCallback(async () => {
    try {
      const htmlContent = editorRef.current?.innerHTML || '';
      
      const response = await fetch(`http://localhost:8000/collab/documents/${documentId}/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: htmlContent,
          document_id: documentId
        })
      });
      
      const result = await response.json();
      
      if (result.success) {
        toast.success('Document saved successfully');
        onSave?.(htmlContent);
      } else {
        toast.error(result.error || 'Failed to save document');
      }
    } catch (error) {
      console.error('Error saving document:', error);
      toast.error('Failed to save document');
    }
  }, [documentId, onSave]);

  // Lock/unlock document
  const handleLockToggle = useCallback(async () => {
    try {
      const endpoint = isLocked ? 'unlock' : 'lock';
      const response = await fetch(`http://localhost:8000/collab/documents/${documentId}/${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_id: userId })
      });
      
      const result = await response.json();
      
      if (result.success) {
        toast.success(result.message);
      } else {
        toast.error(result.error || 'Failed to toggle lock');
      }
    } catch (error) {
      console.error('Error toggling lock:', error);
      toast.error('Failed to toggle lock');
    }
  }, [documentId, userId, isLocked]);

  // Load document content
  const loadDocumentContent = useCallback(async () => {
    try {
      const response = await fetch(`http://localhost:8000/collab/documents/${documentId}/state`);
      const result = await response.json();
      
      if (result.success && result.document) {
        const htmlContent = result.document.content || '';
        setContent(htmlContent);
        setLastContent(htmlContent); // Initialize lastContent
        setDocumentVersion(result.document.version || 0);
        setDocumentState(result.document);
        
        // Set the content in the editor
        if (editorRef.current) {
          editorRef.current.value = htmlContent;
        }
        
        console.log('Document content loaded:', htmlContent);
      }
    } catch (error) {
      console.error('Error loading document content:', error);
    }
  }, [documentId]);

  // Connect on mount and cleanup on unmount
  useEffect(() => {
    console.log('CollaborativeEditor mounting, connecting to:', documentId);
    loadDocumentContent();
    connect();
    
    return () => {
      console.log('CollaborativeEditor unmounting, cleaning up');
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
        typingTimeoutRef.current = null;
      }
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmounting');
      }
    };
  }, [documentId]); // Only depend on documentId to prevent infinite loop

  return (
    <div className="w-full max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <Users className="h-5 w-5" />
            Collaborative Editor - {documentId}
          </h2>
          <div className="flex items-center gap-2">
            <span className={`px-2 py-1 rounded text-xs font-medium ${
              isConnected ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
            }`}>
              {isConnected ? "Connected" : "Disconnected"}
            </span>
            <span className={`px-2 py-1 rounded text-xs font-medium ${
              isLocked ? "bg-red-100 text-red-800" : "bg-gray-100 text-gray-800"
            }`}>
              {isLocked ? "Locked" : "Unlocked"}
            </span>
          </div>
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">
              Version: {documentVersion}
            </span>
            <span className="text-sm text-gray-600">
              Users: {activeUsers.length}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50 disabled:opacity-50"
              onClick={handleLockToggle}
              disabled={!isConnected}
            >
              {isLocked ? <Unlock className="h-4 w-4 inline mr-1" /> : <Lock className="h-4 w-4 inline mr-1" />}
              {isLocked ? "Unlock" : "Lock"}
            </button>
            <button
              className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50 disabled:opacity-50"
              onClick={handleSave}
              disabled={!isConnected}
            >
              <Save className="h-4 w-4 inline mr-1" />
              Save
            </button>
          </div>
        </div>
      </div>

      {/* Active Users */}
      {activeUsers.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-sm font-semibold mb-4">Active Users ({activeUsers.length})</h3>
          <div className="flex flex-wrap gap-2">
            {activeUsers.map((user, index) => (
              <span
                key={user.connection_id || `${user.user_id}-${index}`}
                className="px-2 py-1 rounded text-xs font-medium text-white"
                style={{ 
                  backgroundColor: user.user_id === currentSessionId ? "#065f46" : "#7c3aed" 
                }}
              >
                {user.user_id === currentSessionId ? "You" : user.username}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Rich Text Editor */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        {/* Formatting Toolbar */}
        <div className="border-b border-gray-200 p-3 bg-gray-50 rounded-t-lg">
          <div className="flex items-center gap-2 flex-wrap">
            {/* Text Formatting */}
            <div className="flex items-center gap-1 border-r border-gray-300 pr-2 mr-2">
              <button
                type="button"
                onClick={() => formatText('bold')}
                className="p-2 hover:bg-gray-200 rounded transition-colors"
                title="Bold"
              >
                <Bold className="h-4 w-4" />
              </button>
              <button
                type="button"
                onClick={() => formatText('italic')}
                className="p-2 hover:bg-gray-200 rounded transition-colors"
                title="Italic"
              >
                <Italic className="h-4 w-4" />
              </button>
              <button
                type="button"
                onClick={() => formatText('underline')}
                className="p-2 hover:bg-gray-200 rounded transition-colors"
                title="Underline"
              >
                <Underline className="h-4 w-4" />
              </button>
            </div>

            {/* Alignment */}
            <div className="flex items-center gap-1 border-r border-gray-300 pr-2 mr-2">
              <button
                type="button"
                onClick={() => formatText('justifyLeft')}
                className="p-2 hover:bg-gray-200 rounded transition-colors"
                title="Align Left"
              >
                <AlignLeft className="h-4 w-4" />
              </button>
              <button
                type="button"
                onClick={() => formatText('justifyCenter')}
                className="p-2 hover:bg-gray-200 rounded transition-colors"
                title="Align Center"
              >
                <AlignCenter className="h-4 w-4" />
              </button>
              <button
                type="button"
                onClick={() => formatText('justifyRight')}
                className="p-2 hover:bg-gray-200 rounded transition-colors"
                title="Align Right"
              >
                <AlignRight className="h-4 w-4" />
              </button>
            </div>

            {/* Lists */}
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => formatText('insertUnorderedList')}
                className="p-2 hover:bg-gray-200 rounded transition-colors"
                title="Bullet List"
              >
                <List className="h-4 w-4" />
              </button>
              <button
                type="button"
                onClick={() => formatText('insertOrderedList')}
                className="p-2 hover:bg-gray-200 rounded transition-colors"
                title="Numbered List"
              >
                <ListOrdered className="h-4 w-4" />
              </button>
            </div>

            {/* Additional Formatting */}
            <div className="flex items-center gap-1 border-l border-gray-300 pl-2 ml-2">
              <button
                type="button"
                onClick={() => formatText('removeFormat')}
                className="px-3 py-1 text-sm bg-red-100 text-red-700 hover:bg-red-200 rounded transition-colors"
                title="Remove Formatting"
              >
                Clear
              </button>
            </div>
          </div>
        </div>

        {/* Collaborative Text Editor - Reliable Textarea Approach */}
        <div className="w-full min-h-[400px] border border-gray-300 rounded-lg focus-within:ring-2 focus-within:ring-blue-500 focus-within:ring-opacity-50 relative">
          <textarea
            ref={editorRef}
            disabled={isLocked}
            value={content}
            onChange={handleTextChange}
            onKeyUp={handleCursorUpdate}
            className="w-full min-h-[400px] p-4 focus:outline-none border-0 resize-none"
            style={{
              fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
              fontSize: '16px',
              lineHeight: '1.6',
              backgroundColor: 'transparent',
              direction: 'ltr',
              textAlign: 'left'
            }}
            placeholder="Start typing your document here..."
          />
          
          {/* User Attribution Display with Typing Indicators */}
          {activeUsers.length > 1 && (
            <div className="absolute top-2 right-2 bg-white bg-opacity-90 px-2 py-1 rounded text-xs shadow-sm">
              {activeUsers.map((user, index) => {
                const isTyping = typingUsers[user.user_id];
                const isCurrentUser = user.user_id === userId;
                
                return (
                  <span 
                    key={user.connection_id || index}
                    className="inline-block mr-2 flex items-center"
                    style={{ 
                      color: isCurrentUser ? '#065f46' : '#7c3aed',
                      fontWeight: isCurrentUser ? 'bold' : 'normal'
                    }}
                  >
                    {isCurrentUser ? 'You' : user.username}
                    {isTyping && (
                      <span className="ml-1 text-green-500 animate-pulse">
                        ✏️
                      </span>
                    )}
                  </span>
                );
              })}
            </div>
          )}
        </div>
        
        {/* Embedded CSS for user attribution and styling */}
        <style jsx>{`
          .user-attribution {
            transition: all 0.2s ease;
            cursor: help;
          }
          
          .user-attribution:hover {
            opacity: 0.8;
            transform: scale(1.02);
          }
          
          [contenteditable]:empty:before {
            content: attr(data-placeholder);
            color: #9ca3af;
            pointer-events: none;
          }
          
          .rich-text-editor ul {
            margin: 8px 0;
            padding-left: 24px;
          }
          .rich-text-editor ol {
            margin: 8px 0;
            padding-left: 24px;
          }
          .rich-text-editor li {
            margin: 4px 0;
            line-height: 1.6;
          }
          .rich-text-editor ul li {
            list-style-type: disc;
          }
          .rich-text-editor ol li {
            list-style-type: decimal;
          }
          .rich-text-editor p {
            margin: 8px 0;
          }
        `}</style>
        
        {/* Placeholder text */}
        {!content && (
          <div 
            className="absolute top-[120px] left-6 text-gray-400 pointer-events-none"
            style={{ fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', fontSize: '16px' }}
          >
            Start typing your document here...
          </div>
        )}
      </div>

      {/* Status */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="text-sm text-gray-600">
          <p>Document ID: {documentId}</p>
          <p>Your User ID: {userId}</p>
          <p>Last Modified: {documentState?.last_modified || 'Unknown'}</p>
          <p>Content Length: {content.length} characters</p>
        </div>
      </div>
    </div>
  );
};
