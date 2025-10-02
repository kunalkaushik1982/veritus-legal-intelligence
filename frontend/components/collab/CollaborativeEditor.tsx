"use client";

import React, { useCallback, useEffect, useState, useRef } from 'react';
import { 
  Bold, 
  Italic, 
  Underline, 
  List, 
  ListOrdered, 
  AlignLeft, 
  AlignCenter, 
  AlignRight,
  Save,
  Users,
  Wifi,
  WifiOff,
  MessageSquare
} from 'lucide-react';
import toast from 'react-hot-toast';
import CommentsSidebar from './CommentsSidebar';
import CursorOverlay from './CursorOverlay';
import SimpleCursorOverlay from './SimpleCursorOverlay';
import DebugCursorOverlay from './DebugCursorOverlay';
import API_CONFIG from '../../utils/config';

interface CollaborativeEditorProps {
  documentId: string;
  documentTitle: string;
  userId: string;
  username: string;
  onConnectionChange?: (connected: boolean) => void;
}

interface ActiveUser {
  user_id: string;
  username: string;
  cursor_position: number;
  last_seen: string;
  is_active: boolean;
}

interface Operation {
  id: string;
  type: 'insert' | 'delete' | 'retain';
  position: number;
  content: string;
  length: number;
  user_id: string;
  username: string;
  timestamp: string;
  version: number;
}

const CollaborativeEditor: React.FC<CollaborativeEditorProps> = ({
  documentId,
  documentTitle,
  userId,
  username,
  onConnectionChange
}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [activeUsers, setActiveUsers] = useState<ActiveUser[]>([]);
  const [documentVersion, setDocumentVersion] = useState(0);
  const [isSaving, setIsSaving] = useState(false);
  const [content, setContent] = useState('');
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const editorRef = useRef<HTMLDivElement>(null);
  const editorContainerRef = useRef<HTMLDivElement>(null);
  const connectionAttemptRef = useRef<number>(0);

  // Comments state
  const [isCommentsSidebarOpen, setIsCommentsSidebarOpen] = useState(false);
  const [selectedText, setSelectedText] = useState<string>('');
  const [selectedPosition, setSelectedPosition] = useState<number>(0);

  // Cursor tracking state
  const [remoteCursors, setRemoteCursors] = useState<Array<{
    user_id: string;
    username: string;
    cursor_position: number;
    selection_start: number;
    selection_end: number;
    timestamp: string;
  }>>([]);
  const [lastCursorUpdate, setLastCursorUpdate] = useState<number>(0);

  // WebSocket connection management
  const connect = useCallback(() => {
    if (isConnecting || (wsRef.current && wsRef.current.readyState === WebSocket.OPEN)) {
      console.log('Connection already in progress or connected, skipping');
      return;
    }

    // Close existing connection if any
    if (wsRef.current) {
      console.log('Closing existing WebSocket connection');
      wsRef.current.close(1000, 'Reconnecting');
      wsRef.current = null;
    }

    connectionAttemptRef.current += 1;
    const currentAttempt = connectionAttemptRef.current;
    
    setIsConnecting(true);
    const wsUrl = API_CONFIG.getWsUrl(`/collab/ws/docs/${documentId}`);
    
    console.log(`🔌 Connection attempt ${currentAttempt} for document ${documentId}`);
    console.log(`🌐 WebSocket URL: ${wsUrl}`);
    
    try {
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        console.log(`WebSocket connected successfully (attempt ${currentAttempt})`);
        setIsConnected(true);
        setIsConnecting(false);
        onConnectionChange?.(true);
        
        // Send authentication
        const authMessage = {
          type: 'auth',
          user_id: userId,
          username: username
        };
        console.log('🔐 Sending authentication:', authMessage);
        wsRef.current?.send(JSON.stringify(authMessage));
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleWebSocketMessage(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      wsRef.current.onclose = (event) => {
        console.log(`WebSocket disconnected (attempt ${currentAttempt}):`, event.code, event.reason);
        setIsConnected(false);
        setIsConnecting(false);
        onConnectionChange?.(false);
        
        // Only attempt reconnection if not a normal closure, not already reconnecting, and not too many attempts
        if (event.code !== 1000 && event.code !== 1001 && !reconnectTimeoutRef.current && currentAttempt < 5) {
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectTimeoutRef.current = null;
            if (!isConnected && !isConnecting) {
              console.log('Attempting to reconnect...');
              connect();
            }
          }, 3000);
        } else if (currentAttempt >= 5) {
          console.log('Max reconnection attempts reached. Please refresh the page.');
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        console.error('WebSocket readyState:', wsRef.current?.readyState);
        console.error('WebSocket URL:', wsRef.current?.url);
        setIsConnecting(false);
        // Don't trigger reconnection on error - let onclose handle it
      };
    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
      setIsConnecting(false);
    }
  }, [documentId, userId, username, onConnectionChange]);

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((message: any) => {
    switch (message.type) {
      case 'auth_success':
        console.log('Authentication successful');
        if (message.content) {
          setContent(message.content);
          if (editorRef.current) {
            editorRef.current.innerHTML = message.content;
          }
          setDocumentVersion(message.version || 0);
        }
        break;

      case 'operation_applied':
        console.log('Operation applied:', message.operation);
        if (message.document_content) {
          setContent(message.document_content);
          if (editorRef.current) {
            editorRef.current.innerHTML = message.document_content;
          }
          setDocumentVersion(message.document_version || 0);
        }
        break;

      case 'active_users':
        console.log('👥 Received active users:', message.users);
        setActiveUsers(message.users || []);
        
        // Clean up cursors for users who are no longer active
        if (message.users) {
          const activeUserIds = message.users.map((user: any) => user.user_id);
          console.log('👥 Active user IDs:', activeUserIds);
          setRemoteCursors(prev => {
            const filtered = prev.filter(cursor => {
              const isActive = activeUserIds.includes(cursor.user_id);
              console.log(`👥 Cursor ${cursor.username} (${cursor.user_id}) active: ${isActive}`);
              return isActive;
            });
            console.log(`👥 Cursor cleanup from active users: ${prev.length} -> ${filtered.length}`);
            return filtered;
          });
        }
        break;

      case 'cursor_update':
        if (message.user_id !== userId) {
          setRemoteCursors(prev => {
            const newCursor = {
              user_id: message.user_id,
              username: message.username,
              cursor_position: message.cursor_position || 0,
              selection_start: message.selection_start || message.cursor_position || 0,
              selection_end: message.selection_end || message.cursor_position || 0,
              timestamp: message.timestamp || new Date().toISOString()
            };
            const existing = prev.filter(cursor => cursor.user_id !== message.user_id);
            return [...existing, newCursor];
          });
        }
        break;

      case 'typing_start':
        console.log('User started typing:', message.username);
        break;

      case 'typing_stop':
        console.log('User stopped typing:', message.username);
        break;

      default:
        console.log('Unknown message type:', message.type);
    }
  }, []);

  // Handle text changes
  const handleTextChange = useCallback(() => {
    if (!editorRef.current || !isConnected || !wsRef.current) return;

    const newContent = editorRef.current.innerHTML;
    if (newContent !== content) {
      console.log('📝 Content changed, sending update to server');
      
      // For now, send the complete content as a replacement operation
      // This prevents duplication by replacing rather than inserting
      const operation: Operation = {
        id: `op-${Date.now()}`,
        type: 'replace', // Use replace instead of insert
        position: 0,
        content: newContent,
        length: newContent.length,
        user_id: userId,
        username: username,
        timestamp: new Date().toISOString(),
        version: documentVersion
      };

      wsRef.current.send(JSON.stringify({
        type: 'operation',
        operation: operation
      }));
      
      // Update local content after sending
      setContent(newContent);
    }
  }, [content, isConnected, userId, username, documentVersion]);

  // Load document content
  const loadDocumentContent = useCallback(async () => {
    try {
      const response = await fetch(API_CONFIG.getApiUrl(`/collab/documents/${documentId}/state`));
      const result = await response.json();
      
      if (result.success && result.document) {
        const docContent = result.document.content || '';
        setContent(docContent);
        if (editorRef.current) {
          editorRef.current.innerHTML = docContent;
        }
        setDocumentVersion(result.document.version || 0);
        console.log('Document content loaded:', docContent);
      }
    } catch (error) {
      console.error('Error loading document content:', error);
    }
  }, [documentId]);

  // Save document
  const handleSave = useCallback(async () => {
    if (isSaving) return;

    setIsSaving(true);
    try {
      const response = await fetch(API_CONFIG.getApiUrl(`/collab/documents/${documentId}/save`), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content }),
      });

      if (response.ok) {
        toast.success('Document saved successfully');
      } else {
        toast.error('Failed to save document');
      }
    } catch (error) {
      console.error('Error saving document:', error);
      toast.error('Error saving document');
    } finally {
      setIsSaving(false);
    }
  }, [documentId, content, isSaving]);

  // Apply formatting
  const applyFormatting = useCallback((command: string, value?: string) => {
    if (!editorRef.current) return;
    
    document.execCommand(command, false, value);
    editorRef.current.focus();
    handleTextChange();
  }, [handleTextChange]);

  // Initialize connection and load content
  useEffect(() => {
    console.log('🚀 CollaborativeEditor useEffect triggered for document:', documentId);
    
    loadDocumentContent();
    
    // Add a small delay before connecting to ensure backend is ready
    const connectTimeout = setTimeout(() => {
      console.log('⏰ Timeout reached, attempting connection');
      connect();
    }, 1000);

    return () => {
      console.log('🧹 CollaborativeEditor cleanup for document:', documentId);
      clearTimeout(connectTimeout);
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      if (wsRef.current) {
        console.log('🔌 Closing WebSocket during cleanup');
        wsRef.current.close(1000, 'Component unmounting');
        wsRef.current = null;
      }
    };
  }, [documentId]); // Only depend on documentId to prevent infinite re-renders

  // Clean up old cursor data periodically
  useEffect(() => {
    const cleanupInterval = setInterval(() => {
      const now = Date.now();
      setRemoteCursors(prev => {
        const filtered = prev.filter(cursor => {
          const cursorTime = new Date(cursor.timestamp).getTime();
          const isRecent = now - cursorTime < 15000; // Remove cursors older than 15 seconds
          console.log(`🧹 Cursor cleanup: ${cursor.username} age=${now - cursorTime}ms, keeping=${isRecent}`);
          return isRecent;
        });
        console.log(`🧹 Cursor cleanup: ${prev.length} -> ${filtered.length} cursors`);
        return filtered;
      });
    }, 10000); // Run every 10 seconds instead of 5

    return () => clearInterval(cleanupInterval);
  }, []);

  // Handle text selection for comments
  const handleTextSelection = useCallback(() => {
    const selection = window.getSelection();
    if (selection && selection.toString().trim()) {
      setSelectedText(selection.toString().trim());
      // Get the position of the selection in the editor
      if (editorRef.current) {
        const range = selection.getRangeAt(0);
        const preCaretRange = range.cloneRange();
        preCaretRange.selectNodeContents(editorRef.current);
        preCaretRange.setEnd(range.startContainer, range.startOffset);
        setSelectedPosition(preCaretRange.toString().length);
      }
    } else {
      setSelectedText('');
      setSelectedPosition(0);
    }
  }, []);

  // Handle adding a comment
  const handleAddComment = useCallback((position: number) => {
    setSelectedPosition(position);
    setIsCommentsSidebarOpen(true);
  }, []);

  // Get current cursor position and selection
  const getCurrentCursorPosition = useCallback(() => {
    if (!editorRef.current) return { position: 0, selectionStart: 0, selectionEnd: 0 };

    try {
      const selection = window.getSelection();
      if (selection && selection.rangeCount > 0) {
        const range = selection.getRangeAt(0);
        const preCaretRange = range.cloneRange();
        preCaretRange.selectNodeContents(editorRef.current);
        preCaretRange.setEnd(range.startContainer, range.startOffset);
        
        const startPosition = preCaretRange.toString().length;
        const endPosition = startPosition + range.toString().length;
        
        
        return {
          position: startPosition,
          selectionStart: startPosition,
          selectionEnd: endPosition
        };
      }
    } catch (error) {
      console.error('Error getting cursor position:', error);
    }
    
    return { position: 0, selectionStart: 0, selectionEnd: 0 };
  }, []);

  // Send cursor position update
  const sendCursorUpdate = useCallback(() => {
    const now = Date.now();
    // Throttle cursor updates to avoid spam
    if (now - lastCursorUpdate < 100) return;
    
    const { position, selectionStart, selectionEnd } = getCurrentCursorPosition();
    
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'cursor_update',
        user_id: userId,
        username: username,
        cursor_position: position,
        selection_start: selectionStart,
        selection_end: selectionEnd
      }));
      
      setLastCursorUpdate(now);
    }
  }, [userId, username, getCurrentCursorPosition, lastCursorUpdate]);

  return (
    <div className="w-full max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h1 className="text-2xl font-bold text-gray-900">{documentTitle || 'Collaborative Editor'}</h1>
          <div className="flex items-center space-x-2">
            {isConnecting ? (
              <div className="flex items-center space-x-1 text-yellow-600">
                <div className="w-4 h-4 border-2 border-yellow-600 border-t-transparent rounded-full animate-spin"></div>
                <span className="text-sm">Connecting...</span>
              </div>
            ) : isConnected ? (
              <div className="flex items-center space-x-1 text-green-600">
                <Wifi className="w-4 h-4" />
                <span className="text-sm">Connected</span>
              </div>
            ) : (
              <div className="flex items-center space-x-1 text-red-600">
                <WifiOff className="w-4 h-4" />
                <span className="text-sm">Disconnected</span>
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-4">
          {/* Active Users */}
          <div className="flex items-center space-x-2">
            <Users className="w-4 h-4 text-gray-500" />
            <span className="text-sm text-gray-600">
              {activeUsers.length} user{activeUsers.length !== 1 ? 's' : ''}
            </span>
          </div>

          {/* Save Button */}
          <button
            onClick={handleSave}
            disabled={isSaving || !isConnected}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Save className="w-4 h-4" />
            <span>{isSaving ? 'Saving...' : 'Save'}</span>
          </button>
        </div>
      </div>

      {/* Toolbar */}
      <div className="flex items-center space-x-2 p-3 bg-gray-50 rounded-lg border">
        <button
          onClick={() => applyFormatting('bold')}
          className="p-2 rounded hover:bg-gray-200"
          title="Bold"
        >
          <Bold className="w-4 h-4" />
        </button>
        <button
          onClick={() => applyFormatting('italic')}
          className="p-2 rounded hover:bg-gray-200"
          title="Italic"
        >
          <Italic className="w-4 h-4" />
        </button>
        <button
          onClick={() => applyFormatting('underline')}
          className="p-2 rounded hover:bg-gray-200"
          title="Underline"
        >
          <Underline className="w-4 h-4" />
        </button>
        
        <div className="w-px h-6 bg-gray-300" />
        
        <button
          onClick={() => applyFormatting('insertUnorderedList')}
          className="p-2 rounded hover:bg-gray-200"
          title="Bullet List"
        >
          <List className="w-4 h-4" />
        </button>
        <button
          onClick={() => applyFormatting('insertOrderedList')}
          className="p-2 rounded hover:bg-gray-200"
          title="Numbered List"
        >
          <ListOrdered className="w-4 h-4" />
        </button>
        
        <div className="w-px h-6 bg-gray-300" />
        
        <button
          onClick={() => applyFormatting('justifyLeft')}
          className="p-2 rounded hover:bg-gray-200"
          title="Align Left"
        >
          <AlignLeft className="w-4 h-4" />
        </button>
        <button
          onClick={() => applyFormatting('justifyCenter')}
          className="p-2 rounded hover:bg-gray-200"
          title="Align Center"
        >
          <AlignCenter className="w-4 h-4" />
        </button>
        <button
          onClick={() => applyFormatting('justifyRight')}
          className="p-2 rounded hover:bg-gray-200"
          title="Align Right"
        >
          <AlignRight className="w-4 h-4" />
        </button>
        
        {/* Comments Button */}
        <div className="w-px h-6 bg-gray-300 mx-2" />
        <button
          onClick={() => setIsCommentsSidebarOpen(!isCommentsSidebarOpen)}
          className={`p-2 rounded hover:bg-gray-200 ${
            isCommentsSidebarOpen ? 'bg-blue-100 text-blue-600' : ''
          }`}
          title="Comments"
        >
          <MessageSquare className="w-4 h-4" />
        </button>
      </div>

      {/* Editor */}
      <div 
        ref={editorContainerRef}
        className="border border-gray-300 rounded-lg focus-within:ring-2 focus-within:ring-blue-500 focus-within:ring-opacity-50 relative"
      >
        <div
          ref={editorRef}
          contentEditable
          onInput={handleTextChange}
          onMouseUp={(e) => {
            handleTextSelection();
            sendCursorUpdate();
          }}
          onKeyUp={(e) => {
            handleTextSelection();
            sendCursorUpdate();
          }}
          onMouseMove={sendCursorUpdate}
          onKeyDown={sendCursorUpdate}
          className="prose prose-sm sm:prose lg:prose-lg xl:prose-2xl mx-auto focus:outline-none p-6 min-h-[400px]"
          style={{
            minHeight: '400px',
            fontSize: '16px',
            lineHeight: '1.6',
            fontFamily: 'system-ui, -apple-system, sans-serif'
          }}
          placeholder="Start typing your collaborative document..."
        />
        
        {/* Cursor Overlay */}
        <DebugCursorOverlay
          editorRef={editorRef}
          containerRef={editorContainerRef}
          cursors={remoteCursors}
          currentUserId={userId}
        />
      </div>

      {/* Active Users Display */}
      {activeUsers.length > 0 && (
        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-gray-700 mb-2">Active Users</h3>
          <div className="flex flex-wrap gap-2">
            {activeUsers.map((user, index) => (
              <div
                key={user.user_id || index}
                className="flex items-center space-x-2 px-3 py-1 bg-white rounded-full border"
              >
                <div
                  className="w-2 h-2 rounded-full"
                  style={{
                    backgroundColor: user.user_id === userId ? '#10b981' : '#7c3aed'
                  }}
                />
                <span className="text-sm">
                  {user.user_id === userId ? 'You' : user.username}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Comments Sidebar */}
      <CommentsSidebar
        documentId={documentId}
        userId={userId}
        username={username}
        isOpen={isCommentsSidebarOpen}
        onClose={() => setIsCommentsSidebarOpen(false)}
        onAddComment={handleAddComment}
        selectedPosition={selectedPosition}
      />
    </div>
  );
};

export default CollaborativeEditor;