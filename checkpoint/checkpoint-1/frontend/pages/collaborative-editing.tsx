/**
 * Collaborative Editing Page
 * Main page for collaborative document editing
 */

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { 
  Users, 
  FileText, 
  Settings, 
  ArrowLeft,
  RefreshCw,
  Info,
  Home
} from 'lucide-react';
import { CollaborativeEditor } from '@/components/collab/CollaborativeEditor';
import { DocumentManager } from '@/components/collab/DocumentManager';
import toast from 'react-hot-toast';

interface CollaborativeEditingPageProps {}

export const CollaborativeEditingPage: React.FC<CollaborativeEditingPageProps> = () => {
  const router = useRouter();
  const [currentDocumentId, setCurrentDocumentId] = useState<string | null>(null);
  const [currentDocumentTitle, setCurrentDocumentTitle] = useState<string>('');
  const [userId, setUserId] = useState<string>('');
  const [username, setUsername] = useState<string>('');
  const [isConnected, setIsConnected] = useState(false);
  const [activeTab, setActiveTab] = useState<'documents' | 'editor' | 'settings'>('documents');

  // Generate user ID and username on mount
  useEffect(() => {
    // Check if we have dashboard user data first
    const dashboardUser = localStorage.getItem('user');
    let displayName = '';
    let baseUserId = '';
    
    if (dashboardUser) {
      try {
        const userData = JSON.parse(dashboardUser);
        displayName = userData.full_name || userData.username || 'User';
        baseUserId = userData.id || userData.user_id || `user-${Date.now()}`;
      } catch (error) {
        console.error('Error parsing dashboard user:', error);
      }
    }
    
    // If no dashboard user, check collab user or generate new
    if (!displayName) {
      const collabUser = localStorage.getItem('collab_user');
      if (collabUser) {
        try {
          const userData = JSON.parse(collabUser);
          displayName = userData.username;
          baseUserId = userData.base_user_id || userData.user_id;
        } catch (error) {
          console.error('Error parsing collab user:', error);
        }
      }
    }
    
    // Generate new user if still no data
    if (!displayName) {
      const userNum = Math.floor(Math.random() * 1000) + 1;
      displayName = `User ${userNum}`;
      baseUserId = `user-${userNum}`;
    }
    
    // Store only the base user data, not the session ID
    localStorage.setItem('collab_user', JSON.stringify({
      username: displayName,
      base_user_id: baseUserId
    }));
    
    // Set username, but don't set userId here - it will be generated per connection
    setUsername(displayName);
  }, []);

  const generateNewUser = () => {
    const userNum = Math.floor(Math.random() * 1000) + 1;
    const newUserId = `user-${userNum}`;
    const newUsername = `User ${userNum}`;
    
    setUserId(newUserId);
    setUsername(newUsername);
    
    // Store in localStorage
    localStorage.setItem('collab_user', JSON.stringify({
      user_id: newUserId,
      username: newUsername
    }));
  };

  // Handle document selection
  const handleDocumentSelect = (documentId: string) => {
    setCurrentDocumentId(documentId);
    setCurrentDocumentTitle(documentId);
    setActiveTab('editor');
    toast.success(`Opened document: ${documentId}`);
  };

  // Handle document creation
  const handleDocumentCreate = (documentId: string, title: string) => {
    setCurrentDocumentId(documentId);
    setCurrentDocumentTitle(title);
    setActiveTab('editor');
    toast.success(`Created document: ${title}`);
  };

  // Handle document save
  const handleDocumentSave = (content: string) => {
    console.log('Document saved:', content);
    toast.success('Document saved successfully');
  };

  // Handle document load
  const handleDocumentLoad = (documentId: string) => {
    console.log('Document loaded:', documentId);
    toast.info(`Loading document: ${documentId}`);
  };

  // Handle connection status updates from CollaborativeEditor
  const handleConnectionStatusChange = (connected: boolean) => {
    setIsConnected(connected);
  };

  // Go back to documents list
  const handleBackToDocuments = () => {
    setCurrentDocumentId(null);
    setCurrentDocumentTitle('');
    setActiveTab('documents');
  };

  // Go back to dashboard
  const handleBackToDashboard = () => {
    router.push('/dashboard');
  };

  // Refresh connection status
  const refreshConnectionStatus = () => {
    // This would check WebSocket connection status
    setIsConnected(true); // Placeholder
    toast.success('Connection status refreshed');
  };


  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="border-b bg-white shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={handleBackToDashboard}
                className="flex items-center text-gray-700 hover:text-gray-900 px-3 py-2 rounded hover:bg-gray-100"
                title="Back to Dashboard"
              >
                <Home className="h-4 w-4 mr-2" />
                Dashboard
              </button>
              {currentDocumentId && (
                <button
                  onClick={handleBackToDocuments}
                  className="flex items-center text-gray-700 hover:text-gray-900 px-3 py-2 rounded hover:bg-gray-100"
                  title="Back to Documents"
                >
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Documents
                </button>
              )}
              <div>
                <h1 className="text-2xl font-bold">Collaborative Editing</h1>
                {currentDocumentId && (
                  <p className="text-sm text-gray-600">
                    Editing: {currentDocumentTitle}
                  </p>
                )}
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  isConnected ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                }`}>
                  {isConnected ? "Connected" : "Disconnected"}
                </span>
                <button
                  onClick={refreshConnectionStatus}
                  className="p-1 hover:bg-gray-100 rounded"
                  title="Refresh Connection"
                >
                  <RefreshCw className="h-4 w-4" />
                </button>
              </div>
              
              <div className="text-sm text-gray-600">
                <div>User: {username}</div>
                <div className="text-xs text-gray-500">ID: {userId}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-6">
        <div className="bg-white rounded-lg shadow-sm">
          {/* Tab Navigation */}
          <div className="border-b">
            <nav className="flex">
              <button
                onClick={() => setActiveTab('documents')}
                className={`px-6 py-3 text-sm font-medium border-b-2 ${
                  activeTab === 'documents'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <FileText className="h-4 w-4 inline mr-2" />
                Documents
              </button>
              <button
                onClick={() => setActiveTab('editor')}
                disabled={!currentDocumentId}
                className={`px-6 py-3 text-sm font-medium border-b-2 ${
                  activeTab === 'editor'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                } ${!currentDocumentId ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                <Users className="h-4 w-4 inline mr-2" />
                Editor
              </button>
              <button
                onClick={() => setActiveTab('settings')}
                className={`px-6 py-3 text-sm font-medium border-b-2 ${
                  activeTab === 'settings'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <Settings className="h-4 w-4 inline mr-2" />
                Settings
              </button>
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'documents' && (
              <DocumentManager
                onDocumentSelect={handleDocumentSelect}
                onDocumentCreate={handleDocumentCreate}
              />
            )}

            {activeTab === 'editor' && (
              currentDocumentId ? (
                <CollaborativeEditor
                  documentId={currentDocumentId}
                  userId={userId}
                  username={username}
                  onSave={handleDocumentSave}
                  onLoad={handleDocumentLoad}
                  onConnectionChange={handleConnectionStatusChange}
                />
              ) : (
                <div className="text-center text-gray-600">
                  <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p className="text-lg font-medium mb-2">No document selected</p>
                  <p className="text-sm">Please select a document from the Documents tab to start editing.</p>
                </div>
              )
            )}

            {activeTab === 'settings' && (
              <div className="space-y-6">
                {/* User Settings */}
                <div>
                  <h3 className="text-lg font-semibold mb-4">User Settings</h3>
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium block mb-1">Username</label>
                      <input
                        type="text"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        placeholder="Enter your username"
                        className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium block mb-1">User ID</label>
                      <input
                        type="text"
                        value={userId}
                        onChange={(e) => setUserId(e.target.value)}
                        placeholder="Enter your user ID"
                        className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                </div>

                {/* Connection Settings */}
                <div>
                  <h3 className="text-lg font-semibold mb-4">Connection Settings</h3>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">WebSocket Server</p>
                        <p className="text-sm text-gray-600">
                          ws://localhost:8000/collab/ws/
                        </p>
                      </div>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        isConnected ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                      }`}>
                        {isConnected ? "Connected" : "Disconnected"}
                      </span>
                    </div>
                    
                    <button
                      onClick={refreshConnectionStatus}
                      className="w-full px-4 py-2 border border-gray-300 rounded hover:bg-gray-50 flex items-center justify-center gap-2"
                    >
                      <RefreshCw className="h-4 w-4" />
                      Refresh Connection
                    </button>
                  </div>
                </div>

                {/* Information */}
                <div>
                  <h3 className="text-lg font-semibold mb-4">Information</h3>
                  <div className="space-y-2 text-sm text-gray-600">
                    <div className="flex items-center gap-2">
                      <Info className="h-4 w-4" />
                      <span>Real-time collaborative editing with Operational Transform (OT)</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Info className="h-4 w-4" />
                      <span>WebSocket-based communication for instant updates</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Info className="h-4 w-4" />
                      <span>Conflict resolution and document synchronization</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Info className="h-4 w-4" />
                      <span>User presence and cursor tracking</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CollaborativeEditingPage;
