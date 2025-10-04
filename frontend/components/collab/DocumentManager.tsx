import React, { useState, useEffect, useCallback } from 'react';
import { 
  Plus, 
  FileText, 
  Users, 
  Clock, 
  Edit3, 
  Eye,
  Trash2,
  Search,
  Filter
} from 'lucide-react';
import toast from 'react-hot-toast';
import API_CONFIG from '../../utils/config';

interface Document {
  id: string;
  title: string;
  version: number;
  content_length: number;
  active_users: number;
}

interface DocumentManagerProps {
  onDocumentSelect: (documentId: string, documentTitle: string) => void;
  selectedDocumentId?: string;
}

const DocumentManager: React.FC<DocumentManagerProps> = ({
  onDocumentSelect,
  selectedDocumentId
}) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newDocumentTitle, setNewDocumentTitle] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  // Load documents
  const loadDocuments = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await fetch(API_CONFIG.getApiUrl('/collab/documents'));
      const result = await response.json();
      
      if (result.success) {
        setDocuments(result.documents || []);
      } else {
        toast.error('Failed to load documents');
      }
    } catch (error) {
      console.error('Error loading documents:', error);
      toast.error('Error loading documents');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Create new document
  const createDocument = useCallback(async () => {
    if (!newDocumentTitle.trim()) {
      toast.error('Please enter a document title');
      return;
    }

    setIsCreating(true);
    try {
      const response = await fetch(API_CONFIG.getApiUrl('/collab/documents'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: newDocumentTitle.trim(),
          user_id: 'current-user', // In a real app, get from auth context
        }),
      });

      const result = await response.json();
      
      if (result.success) {
        toast.success('Document created successfully');
        setNewDocumentTitle('');
        setShowCreateDialog(false);
        loadDocuments(); // Reload documents
        onDocumentSelect(result.document_id, result.title); // Auto-select new document
      } else {
        toast.error('Failed to create document');
      }
    } catch (error) {
      console.error('Error creating document:', error);
      toast.error('Error creating document');
    } finally {
      setIsCreating(false);
    }
  }, [newDocumentTitle, loadDocuments, onDocumentSelect]);

  // Delete document
  const deleteDocument = useCallback(async (documentId: string) => {
    if (!confirm('Are you sure you want to delete this document? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch(API_CONFIG.getApiUrl(`/collab/documents/${documentId}`), {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to delete document');
      }

      const result = await response.json();
      toast.success(result.message || 'Document deleted successfully');
      
      // Refresh the documents list
      await loadDocuments();
      
    } catch (error) {
      console.error('Error deleting document:', error);
      toast.error(error instanceof Error ? error.message : 'Error deleting document');
    }
  }, [loadDocuments]);

  // Filter documents based on search query
  const filteredDocuments = documents.filter(doc =>
    doc.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading documents...</div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Documents</h1>
        <button
          onClick={() => setShowCreateDialog(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          <span>New Document</span>
        </button>
      </div>

      {/* Search and Filter */}
      <div className="flex items-center space-x-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search documents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <button className="flex items-center space-x-2 px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
          <Filter className="w-4 h-4" />
          <span>Filter</span>
        </button>
      </div>

      {/* Documents List */}
      <div className="space-y-3">
        {filteredDocuments.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {searchQuery ? 'No documents found' : 'No documents yet'}
            </h3>
            <p className="text-gray-500 mb-4">
              {searchQuery 
                ? 'Try adjusting your search terms'
                : 'Create your first collaborative document to get started'
              }
            </p>
            {!searchQuery && (
              <button
                onClick={() => setShowCreateDialog(true)}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 mx-auto"
              >
                <Plus className="w-4 h-4" />
                <span>Create Document</span>
              </button>
            )}
          </div>
        ) : (
          filteredDocuments.map((document) => (
            <div
              key={document.id}
              className={`p-4 border rounded-lg hover:shadow-md transition-shadow cursor-pointer ${
                selectedDocumentId === document.id 
                  ? 'border-blue-500 bg-blue-50' 
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => onDocumentSelect(document.id, document.title)}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    {document.title}
                  </h3>
                  <div className="flex items-center space-x-4 text-sm text-gray-500">
                    <div className="flex items-center space-x-1">
                      <Users className="w-4 h-4" />
                      <span>{document.active_users} active</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Clock className="w-4 h-4" />
                      <span>v{document.version}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <FileText className="w-4 h-4" />
                      <span>{document.content_length} chars</span>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDocumentSelect(document.id, document.title);
                    }}
                    className="flex items-center space-x-1 px-3 py-1 text-blue-600 hover:bg-blue-100 rounded"
                    title="Open document"
                  >
                    <Edit3 className="w-4 h-4" />
                    <span>Open</span>
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteDocument(document.id);
                    }}
                    className="flex items-center space-x-1 px-3 py-1 text-red-600 hover:bg-red-100 rounded"
                    title="Delete document"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Create Document Dialog */}
      {showCreateDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Create New Document</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Document Title
                </label>
                <input
                  type="text"
                  value={newDocumentTitle}
                  onChange={(e) => setNewDocumentTitle(e.target.value)}
                  placeholder="Enter document title..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  autoFocus
                />
              </div>
            </div>

            <div className="flex items-center justify-end space-x-3 mt-6">
              <button
                onClick={() => {
                  setShowCreateDialog(false);
                  setNewDocumentTitle('');
                }}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={createDocument}
                disabled={isCreating || !newDocumentTitle.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isCreating ? 'Creating...' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentManager;