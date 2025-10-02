"use client";

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/router';
import { ArrowLeft, User, Settings, LogOut } from 'lucide-react';
import toast from 'react-hot-toast';

import DocumentManager from '../components/collab/DocumentManager';
import CollaborativeEditor from '../components/collab/CollaborativeEditor';

interface User {
  id: string;
  username: string;
  email?: string;
}

const CollaborativeEditingPage: React.FC = () => {
  const router = useRouter();
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);
  const [selectedDocumentTitle, setSelectedDocumentTitle] = useState<string>('');
  const [user, setUser] = useState<User | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const isMountedRef = useRef(true);

  // Initialize user from existing app authentication
  useEffect(() => {
    console.log('🔍 Initializing user for collaborative editing...');
    
    // Check if user is logged in (same as dashboard)
    const token = localStorage.getItem('access_token');
    const savedUser = localStorage.getItem('user');
    
    if (!token || !savedUser) {
      console.log('❌ No authentication found, redirecting to login');
      router.push('/login');
      return;
    }
    
    try {
      const userData = JSON.parse(savedUser);
      console.log('👤 Parsed user data from main app:', userData);
      
      const user = {
        id: userData.id?.toString() || `user-${Date.now()}`,
        username: userData.full_name || userData.username || 'User',
        email: userData.email
      };
      
      console.log('✅ Setting user for collaborative editing:', user);
      setUser(user);
      
      // Store in collab_user for the editor component
      localStorage.setItem('collab_user', JSON.stringify({
        username: user.username,
        user_id: user.id
      }));
      
    } catch (error) {
      console.error('❌ Error parsing user data:', error);
      // Clear invalid data and redirect to login
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      router.push('/login');
      return;
    }
  }, [router]);

  // Cleanup effect
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  const handleDocumentSelect = (documentId: string, documentTitle: string) => {
    setSelectedDocumentId(documentId);
    setSelectedDocumentTitle(documentTitle);
    toast.success(`Opened document "${documentTitle}"`);
  };

  const handleConnectionChange = (connected: boolean) => {
    setIsConnected(connected);
    if (connected) {
      toast.success('Connected to collaborative editing');
    } else {
      // Only show disconnect message if component is still mounted
      // This prevents showing the message when user navigates away
      if (isMountedRef.current) {
        toast.error('Disconnected from collaborative editing');
      }
    }
  };

  const handleLogout = () => {
    // Clear authentication data
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    localStorage.removeItem('collab_user');
    
    toast.success('Logged out successfully');
    router.push('/login');
  };

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-500">Loading user information...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push('/dashboard')}
                className="flex items-center space-x-2 text-gray-600 hover:text-gray-900"
              >
                <ArrowLeft className="w-5 h-5" />
                <span>Back to Dashboard</span>
              </button>
              <div className="w-px h-6 bg-gray-300" />
              <h1 className="text-xl font-semibold text-gray-900">
                Collaborative Editing
              </h1>
            </div>

            <div className="flex items-center space-x-4">
              {/* Connection Status */}
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-sm text-gray-600">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>

              {/* User Info */}
              <div className="flex items-center space-x-2">
                <User className="w-4 h-4 text-gray-500" />
                <span className="text-sm text-gray-700">{user.username}</span>
              </div>

              {/* Settings */}
              <button className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg">
                <Settings className="w-4 h-4" />
              </button>

              {/* Logout */}
              <button 
                onClick={handleLogout}
                className="flex items-center space-x-2 px-3 py-2 text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
                title="Logout"
              >
                <LogOut className="w-4 h-4" />
                <span className="text-sm">Logout</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {!selectedDocumentId ? (
          <DocumentManager onDocumentSelect={handleDocumentSelect} />
        ) : (
          <div className="space-y-6">
            {/* Document Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => setSelectedDocumentId(null)}
                  className="flex items-center space-x-2 text-gray-600 hover:text-gray-900"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>Back to Documents</span>
                </button>
                <div className="w-px h-6 bg-gray-300" />
                <h2 className="text-lg font-medium text-gray-900">
                  {selectedDocumentTitle || 'Collaborative Editor'}
                </h2>
              </div>
            </div>

            {/* Collaborative Editor */}
            <CollaborativeEditor
              documentId={selectedDocumentId}
              documentTitle={selectedDocumentTitle}
              userId={user.id}
              username={user.username}
              onConnectionChange={handleConnectionChange}
            />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500">
              Veritus Collaborative Editing Platform
            </div>
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <span>Real-time collaboration powered by Operational Transform</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default CollaborativeEditingPage;