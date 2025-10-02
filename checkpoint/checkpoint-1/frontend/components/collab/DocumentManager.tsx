/**
 * Document Management Component
 * Manages collaborative documents and provides document operations
 */

import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Plus, 
  Users, 
  Clock, 
  Lock, 
  Unlock, 
  Download, 
  Upload,
  Eye,
  Edit
} from 'lucide-react';
import toast from 'react-hot-toast';

interface Document {
  document_id: string;
  version: number;
  last_modified: string;
  active_users_count: number;
  content_length: number;
  is_locked: boolean;
}

interface DocumentManagerProps {
  onDocumentSelect: (documentId: string) => void;
  onDocumentCreate: (documentId: string, title: string) => void;
}

export const DocumentManager: React.FC<DocumentManagerProps> = ({
  onDocumentSelect,
  onDocumentCreate
}) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [newDocumentId, setNewDocumentId] = useState('');
  const [newDocumentTitle, setNewDocumentTitle] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [conflictError, setConflictError] = useState<string | null>(null);
  const [suggestedId, setSuggestedId] = useState<string | null>(null);

  // Load documents
  const loadDocuments = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('http://localhost:8000/collab/documents');
      const result = await response.json();
      
      if (result.success) {
        setDocuments(result.documents);
      } else {
        toast.error('Failed to load documents');
      }
    } catch (error) {
      console.error('Error loading documents:', error);
      toast.error('Failed to load documents');
    } finally {
      setIsLoading(false);
    }
  };

  // Create new document
  const handleCreateDocument = async () => {
    if (!newDocumentId.trim()) {
      toast.error('Please enter a document ID');
      return;
    }

    try {
      setIsCreating(true);
      const response = await fetch('http://localhost:8000/collab/documents', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          document_id: newDocumentId.trim(),
          title: newDocumentTitle.trim() || newDocumentId.trim(),
          initial_content: ''
        }),
      });

      const result = await response.json();
      
      if (response.ok && result.success) {
        toast.success('Document created successfully');
        setIsCreateDialogOpen(false);
        setNewDocumentId('');
        setNewDocumentTitle('');
        loadDocuments();
        onDocumentCreate(result.document_id, result.title);
      } else {
        // Handle different error types
        if (response.status === 409) {
          // Suggest a unique ID
          const suggested = `${newDocumentId.trim()}-${Date.now().toString().slice(-4)}`;
          setConflictError(`A document with ID "${newDocumentId.trim()}" already exists.`);
          setSuggestedId(suggested);
          setNewDocumentId(suggested);
        } else if (response.status === 400) {
          setConflictError('Invalid document ID. Please enter a valid ID.');
          setSuggestedId(null);
        } else {
          setConflictError(result.detail || result.error || 'Failed to create document');
          setSuggestedId(null);
        }
      }
    } catch (error) {
      console.error('Error creating document:', error);
      toast.error('Failed to create document');
    } finally {
      setIsCreating(false);
    }
  };

  // Load document state
  const loadDocumentState = async (documentId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/collab/documents/${documentId}/state`);
      const result = await response.json();
      
      if (result.success) {
        return result.document;
      } else {
        toast.error('Failed to load document state');
        return null;
      }
    } catch (error) {
      console.error('Error loading document state:', error);
      toast.error('Failed to load document state');
      return null;
    }
  };

  // Handle document selection
  const handleDocumentSelect = async (documentId: string) => {
    const documentState = await loadDocumentState(documentId);
    if (documentState) {
      onDocumentSelect(documentId);
    }
  };

  // Format date
  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return 'Unknown';
    }
  };

  // Format file size
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Load documents on mount
  useEffect(() => {
    loadDocuments();
  }, []);

  return (
    <div className="w-full max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Collaborative Documents
          </h2>
          <button
            onClick={() => {
              setConflictError(null);
              setSuggestedId(null);
              setIsCreateDialogOpen(true);
            }}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            Create Document
          </button>
        </div>
      </div>

      {/* Create Document Modal */}
      {isCreateDialogOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Create New Document</h3>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium block mb-1">Document ID</label>
                <div className="relative">
                  <input
                    type="text"
                    placeholder="Enter document ID (e.g., legal-doc-001)"
                    value={newDocumentId}
                    onChange={(e) => {
                      setNewDocumentId(e.target.value);
                      setConflictError(null);
                      setSuggestedId(null);
                    }}
                    className={`w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 transition-all duration-200 ${
                      conflictError 
                        ? 'border-red-300 focus:ring-red-500 bg-red-50' 
                        : 'border-gray-300 focus:ring-blue-500'
                    }`}
                  />
                  {conflictError && (
                    <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                      <svg className="h-5 w-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                    </div>
                  )}
                </div>
                {conflictError && (
                  <div className="mt-2 flex items-center justify-between">
                    <p className="text-sm text-red-600 flex items-center">
                      <svg className="h-4 w-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                      {conflictError}
                    </p>
                    {suggestedId && (
                      <button
                        onClick={() => {
                          setNewDocumentId(suggestedId);
                          setConflictError(null);
                          setSuggestedId(null);
                        }}
                        className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded-full hover:bg-red-200 transition-colors duration-200"
                      >
                        Use: {suggestedId}
                      </button>
                    )}
                  </div>
                )}
              </div>
              <div>
                <label className="text-sm font-medium block mb-1">Document Title (Optional)</label>
                <input
                  type="text"
                  placeholder="Enter document title"
                  value={newDocumentTitle}
                  onChange={(e) => setNewDocumentTitle(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div className="flex justify-end gap-2">
                <button
                  onClick={() => {
                    setIsCreateDialogOpen(false);
                    setConflictError(null);
                    setSuggestedId(null);
                    setNewDocumentId('');
                    setNewDocumentTitle('');
                  }}
                  className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateDocument}
                  disabled={isCreating || !newDocumentId.trim()}
                  className={`px-4 py-2 rounded transition-all duration-200 flex items-center gap-2 ${
                    conflictError 
                      ? 'bg-red-600 hover:bg-red-700 text-white' 
                      : 'bg-blue-600 hover:bg-blue-700 text-white'
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                  {isCreating && (
                    <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  )}
                  {isCreating ? 'Creating...' : conflictError ? 'Try Again' : 'Create'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Documents List */}
      <div className="grid gap-4">
        {isLoading ? (
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="text-center text-gray-600">
              Loading documents...
            </div>
          </div>
        ) : documents.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="text-center text-gray-600">
              <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium mb-2">No documents found</p>
              <p className="text-sm">Create your first collaborative document to get started.</p>
            </div>
          </div>
        ) : (
          documents.map((doc) => (
            <div key={doc.document_id} className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="text-lg font-semibold">{doc.document_id}</h3>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      doc.is_locked ? "bg-red-100 text-red-800" : "bg-gray-100 text-gray-800"
                    }`}>
                      {doc.is_locked ? (
                        <>
                          <Lock className="h-3 w-3 inline mr-1" />
                          Locked
                        </>
                      ) : (
                        <>
                          <Unlock className="h-3 w-3 inline mr-1" />
                          Unlocked
                        </>
                      )}
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600">
                    <div className="flex items-center gap-1">
                      <Clock className="h-4 w-4" />
                      {formatDate(doc.last_modified)}
                    </div>
                    <div className="flex items-center gap-1">
                      <Users className="h-4 w-4" />
                      {doc.active_users_count} users
                    </div>
                    <div className="flex items-center gap-1">
                      <FileText className="h-4 w-4" />
                      v{doc.version}
                    </div>
                    <div className="flex items-center gap-1">
                      <span>{formatFileSize(doc.content_length)}</span>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleDocumentSelect(doc.document_id)}
                    className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50 flex items-center gap-1"
                  >
                    <Eye className="h-4 w-4" />
                    View
                  </button>
                  <button
                    onClick={() => handleDocumentSelect(doc.document_id)}
                    className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50 flex items-center gap-1"
                  >
                    <Edit className="h-4 w-4" />
                    Edit
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Refresh Button */}
      <div className="flex justify-center">
        <button 
          onClick={loadDocuments} 
          disabled={isLoading}
          className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
        >
          {isLoading ? 'Loading...' : 'Refresh Documents'}
        </button>
      </div>
    </div>
  );
};
