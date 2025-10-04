
import React, { useState, useEffect, useRef } from 'react';
import { 
  MessageSquare, 
  Plus, 
  X, 
  Check, 
  Edit2, 
  Trash2,
  User,
  Clock
} from 'lucide-react';
import API_CONFIG from '../../utils/config';
import toast from 'react-hot-toast';

interface Comment {
  id: string;
  user_id: string;
  username: string;
  content: string;
  position: number;
  anchor_node_id?: string;
  anchor_offset?: number;
  created_at: string;
  updated_at?: string;
  is_resolved: boolean;
}

interface CommentsSidebarProps {
  documentId: string;
  userId: string;
  username: string;
  isOpen: boolean;
  onClose: () => void;
  onAddComment: (position: number) => void;
  selectedPosition?: number;
}

const CommentsSidebar: React.FC<CommentsSidebarProps> = ({
  documentId,
  userId,
  username,
  isOpen,
  onClose,
  onAddComment,
  selectedPosition
}) => {
  const [comments, setComments] = useState<Comment[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [newComment, setNewComment] = useState('');
  const [editingComment, setEditingComment] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');

  // Load comments when sidebar opens
  useEffect(() => {
    if (isOpen && documentId) {
      loadComments();
    }
  }, [isOpen, documentId]);

  const loadComments = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(API_CONFIG.getApiUrl(`/collab/documents/${documentId}/comments`));
      const result = await response.json();
      
      if (result.success) {
        setComments(result.comments || []);
      } else {
        toast.error('Failed to load comments');
      }
    } catch (error) {
      console.error('Error loading comments:', error);
      toast.error('Error loading comments');
    } finally {
      setIsLoading(false);
    }
  };

  const addComment = async () => {
    if (!newComment.trim() || selectedPosition === undefined) return;

    try {
      const response = await fetch(API_CONFIG.getApiUrl(`/collab/documents/${documentId}/comments`), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          username: username,
          content: newComment.trim(),
          position: selectedPosition,
          anchor_node_id: `node-${selectedPosition}`,
          anchor_offset: 0
        }),
      });

      const result = await response.json();
      
      if (result.success) {
        setComments(prev => [...prev, result.comment]);
        setNewComment('');
        toast.success('Comment added successfully');
      } else {
        toast.error('Failed to add comment');
      }
    } catch (error) {
      console.error('Error adding comment:', error);
      toast.error('Error adding comment');
    }
  };

  const updateComment = async (commentId: string) => {
    if (!editContent.trim()) return;

    try {
      const response = await fetch(`http://localhost:8000/collab/documents/${documentId}/comments/${commentId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: editContent.trim()
        }),
      });

      const result = await response.json();
      
      if (result.success) {
        setComments(prev => prev.map(comment => 
          comment.id === commentId 
            ? { ...comment, content: editContent.trim(), updated_at: new Date().toISOString() }
            : comment
        ));
        setEditingComment(null);
        setEditContent('');
        toast.success('Comment updated successfully');
      } else {
        toast.error('Failed to update comment');
      }
    } catch (error) {
      console.error('Error updating comment:', error);
      toast.error('Error updating comment');
    }
  };

  const deleteComment = async (commentId: string) => {
    if (!confirm('Are you sure you want to delete this comment?')) return;

    try {
      const response = await fetch(`http://localhost:8000/collab/documents/${documentId}/comments/${commentId}`, {
        method: 'DELETE',
      });

      const result = await response.json();
      
      if (result.success) {
        setComments(prev => prev.filter(comment => comment.id !== commentId));
        toast.success('Comment deleted successfully');
      } else {
        toast.error('Failed to delete comment');
      }
    } catch (error) {
      console.error('Error deleting comment:', error);
      toast.error('Error deleting comment');
    }
  };

  const resolveComment = async (commentId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/collab/documents/${documentId}/comments/${commentId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          is_resolved: true
        }),
      });

      const result = await response.json();
      
      if (result.success) {
        setComments(prev => prev.map(comment => 
          comment.id === commentId 
            ? { ...comment, is_resolved: true }
            : comment
        ));
        toast.success('Comment resolved');
      } else {
        toast.error('Failed to resolve comment');
      }
    } catch (error) {
      console.error('Error resolving comment:', error);
      toast.error('Error resolving comment');
    }
  };

  const startEdit = (comment: Comment) => {
    setEditingComment(comment.id);
    setEditContent(comment.content);
  };

  const cancelEdit = () => {
    setEditingComment(null);
    setEditContent('');
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed right-0 top-0 h-full w-80 bg-white border-l border-gray-200 shadow-lg z-50 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <MessageSquare className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">Comments</h3>
          <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
            {comments.length}
          </span>
        </div>
        <button
          onClick={onClose}
          className="p-1 text-gray-400 hover:text-gray-600 rounded"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Add Comment Section */}
      {selectedPosition !== undefined && (
        <div className="p-4 border-b border-gray-200 bg-gray-50">
          <div className="space-y-3">
            <div className="text-sm text-gray-600">
              Add comment at position {selectedPosition}
            </div>
            <div className="flex space-x-2">
              <input
                type="text"
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="Write a comment..."
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                onKeyPress={(e) => e.key === 'Enter' && addComment()}
              />
              <button
                onClick={addComment}
                disabled={!newComment.trim()}
                className="px-3 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-1"
              >
                <Plus className="w-4 h-4" />
                <span>Add</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Comments List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center p-8">
            <div className="text-gray-500">Loading comments...</div>
          </div>
        ) : comments.length === 0 ? (
          <div className="flex items-center justify-center p-8">
            <div className="text-center text-gray-500">
              <MessageSquare className="w-12 h-12 mx-auto mb-2 text-gray-300" />
              <p>No comments yet</p>
              <p className="text-sm">Select text and add a comment</p>
            </div>
          </div>
        ) : (
          <div className="p-4 space-y-4">
            {comments.map((comment) => (
              <div
                key={comment.id}
                className={`p-3 rounded-lg border ${
                  comment.is_resolved 
                    ? 'bg-gray-50 border-gray-200 opacity-75' 
                    : 'bg-white border-gray-200'
                }`}
              >
                {/* Comment Header */}
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <User className="w-4 h-4 text-gray-400" />
                    <span className="text-sm font-medium text-gray-900">
                      {comment.username}
                    </span>
                    <span className="text-xs text-gray-500">
                      at position {comment.position}
                    </span>
                  </div>
                  {comment.user_id === userId && (
                    <div className="flex items-center space-x-1">
                      {!comment.is_resolved && (
                        <>
                          <button
                            onClick={() => startEdit(comment)}
                            className="p-1 text-gray-400 hover:text-blue-600 rounded"
                            title="Edit comment"
                          >
                            <Edit2 className="w-3 h-3" />
                          </button>
                          <button
                            onClick={() => resolveComment(comment.id)}
                            className="p-1 text-gray-400 hover:text-green-600 rounded"
                            title="Resolve comment"
                          >
                            <Check className="w-3 h-3" />
                          </button>
                        </>
                      )}
                      <button
                        onClick={() => deleteComment(comment.id)}
                        className="p-1 text-gray-400 hover:text-red-600 rounded"
                        title="Delete comment"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  )}
                </div>

                {/* Comment Content */}
                {editingComment === comment.id ? (
                  <div className="space-y-2">
                    <textarea
                      value={editContent}
                      onChange={(e) => setEditContent(e.target.value)}
                      className="w-full px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      rows={3}
                    />
                    <div className="flex space-x-2">
                      <button
                        onClick={() => updateComment(comment.id)}
                        className="px-2 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700"
                      >
                        Save
                      </button>
                      <button
                        onClick={cancelEdit}
                        className="px-2 py-1 bg-gray-300 text-gray-700 rounded text-xs hover:bg-gray-400"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="text-sm text-gray-700 mb-2">
                    {comment.content}
                  </div>
                )}

                {/* Comment Footer */}
                <div className="flex items-center space-x-2 text-xs text-gray-500">
                  <Clock className="w-3 h-3" />
                  <span>{formatDate(comment.created_at)}</span>
                  {comment.updated_at && comment.updated_at !== comment.created_at && (
                    <>
                      <span>•</span>
                      <span>edited {formatDate(comment.updated_at)}</span>
                    </>
                  )}
                  {comment.is_resolved && (
                    <>
                      <span>•</span>
                      <span className="text-green-600 font-medium">Resolved</span>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default CommentsSidebar;
