import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { useQuery, useMutation } from 'react-query';
import { 
  MessageSquare, 
  Search, 
  BarChart3, 
  Clock, 
  BookOpen, 
  User, 
  LogOut,
  Send,
  Loader2,
  Star,
  ThumbsUp,
  ThumbsDown,
  FileText,
  Upload,
  Zap,
  Users
} from 'lucide-react';
import toast from 'react-hot-toast';
import API_CONFIG from '../utils/config';

interface ChatMessage {
  id: string;
  query: string;
  response: string;
  citations: any[];
  confidence_score: number;
  created_at: string;
  user_rating?: number;
}

interface QueryResponse {
  response: string;
  citations: any[];
  relevant_judgments: number[];
  confidence_score: number;
  response_time_ms: number;
  tokens_used: number;
  query_intent: string;
}

export default function Dashboard() {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [user, setUser] = useState<any>(null);
  const [isBatchProcessing, setIsBatchProcessing] = useState(false);
  const [batchStatus, setBatchStatus] = useState<string>('');

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem('access_token');
    const userData = localStorage.getItem('user');
    
    if (!token || !userData) {
      router.push('/login');
      return;
    }

    try {
      const parsedUser = JSON.parse(userData);
      setUser(parsedUser);
    } catch (error) {
      console.error('Error parsing user data:', error);
      // Clear invalid data
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      router.push('/login');
      return;
    }
  }, [router]);

  const chatMutation = useMutation(
    async (queryText: string) => {
      const token = localStorage.getItem('access_token');
      const response = await fetch(API_CONFIG.getApiUrl('/api/chatbot/query'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          query: queryText,
          context_limit: 5
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Query failed');
      }

      return response.json();
    },
    {
      onSuccess: (data: QueryResponse) => {
        const newMessage: ChatMessage = {
          id: Date.now().toString(),
          query: query,
          response: data.response,
          citations: data.citations,
          confidence_score: data.confidence_score,
          created_at: new Date().toISOString(),
        };
        
        setMessages(prev => [...prev, newMessage]);
        setQuery('');
        setIsLoading(false);
      },
      onError: (error: Error) => {
        toast.error(error.message);
        setIsLoading(false);
      },
    }
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;

    setIsLoading(true);
    chatMutation.mutate(query);
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    router.push('/');
  };

  const handleRating = (messageId: string, rating: number) => {
    setMessages(prev => 
      prev.map(msg => 
        msg.id === messageId ? { ...msg, user_rating: rating } : msg
      )
    );
    
    // Here you would typically send the rating to the backend
    toast.success('Thank you for your feedback!');
  };

  const processExistingPDFs = async () => {
    setIsBatchProcessing(true);
    setBatchStatus('Starting batch processing...');
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(API_CONFIG.getApiUrl('/api/batch/process-existing'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const result = await response.json();
        setBatchStatus(`Processed ${result.processed || 0} PDFs successfully`);
        toast.success(`Batch processing completed! Processed ${result.processed || 0} PDFs`);
      } else {
        const errorData = await response.json();
        setBatchStatus(`Error: ${errorData.detail || 'Failed to process PDFs'}`);
        toast.error('Batch processing failed');
      }
    } catch (error) {
      setBatchStatus(`Error: ${error}`);
      toast.error('Batch processing failed');
      console.error('Batch processing error:', error);
    } finally {
      setIsBatchProcessing(false);
    }
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <>
      <Head>
        <title>Dashboard - Veritus</title>
        <meta name="description" content="Veritus Legal Intelligence Dashboard" />
      </Head>

      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center">
                <h1 className="text-2xl font-bold text-gray-900">Veritus</h1>
                <span className="ml-4 text-sm text-gray-500">Legal Intelligence</span>
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-sm text-gray-700">
                  Welcome, {user.full_name}
                </div>
                <button
                  onClick={handleLogout}
                  className="flex items-center text-gray-700 hover:text-gray-900"
                >
                  <LogOut className="w-4 h-4 mr-1" />
                  Logout
                </button>
              </div>
            </div>
          </div>
        </header>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
            {/* Sidebar */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
                <div className="space-y-3">
                  <button className="w-full flex items-center p-3 text-left text-gray-700 hover:bg-gray-50 rounded-lg">
                    <Search className="w-5 h-5 mr-3" />
                    Search Judgments
                  </button>
                  <button 
                    onClick={() => router.push('/judgments-library')}
                    className="w-full flex items-center p-3 text-left text-gray-700 hover:bg-gray-50 rounded-lg"
                  >
                    <BookOpen className="w-5 h-5 mr-3" />
                    Judgments Library
                  </button>
                  <button 
                    onClick={() => router.push('/citation-analysis')}
                    className="w-full flex items-center p-3 text-left text-gray-700 hover:bg-gray-50 rounded-lg"
                  >
                    <BarChart3 className="w-5 h-5 mr-3" />
                    Citation Analysis
                  </button>
                  <button className="w-full flex items-center p-3 text-left text-gray-700 hover:bg-gray-50 rounded-lg">
                    <Clock className="w-5 h-5 mr-3" />
                    Timeline Extraction
                  </button>
                  <button 
                    onClick={() => router.push('/collaborative-editing')}
                    className="w-full flex items-center p-3 text-left text-gray-700 hover:bg-gray-50 rounded-lg"
                  >
                    <Users className="w-5 h-5 mr-3" />
                    Collaborative Editing
                  </button>
                  <button 
                    onClick={() => router.push('/batch-process')}
                    className="w-full flex items-center p-3 text-left text-gray-700 hover:bg-gray-50 rounded-lg"
                  >
                    <Zap className="w-5 h-5 mr-3" />
                    Process Existing PDFs
                  </button>
                </div>
                
                {batchStatus && (
                  <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                    <p className="text-sm text-blue-800">{batchStatus}</p>
                  </div>
                )}

                <div className="mt-8">
                  <h4 className="text-sm font-semibold text-gray-900 mb-3">Usage Stats</h4>
                  <div className="space-y-2 text-sm text-gray-600">
                    <div className="flex justify-between">
                      <span>Queries Today:</span>
                      <span className="font-medium">{user.queries_today || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Total Queries:</span>
                      <span className="font-medium">{user.total_queries || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Plan:</span>
                      <span className="font-medium capitalize">{user.subscription_tier}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Main Chat Area */}
            <div className="lg:col-span-3">
              <div className="bg-white rounded-lg shadow-sm h-[600px] flex flex-col">
                {/* Chat Header */}
                <div className="p-4 border-b border-gray-200">
                  <h2 className="text-lg font-semibold text-gray-900 flex items-center">
                    <MessageSquare className="w-5 h-5 mr-2" />
                    Legal Research Assistant
                  </h2>
                  <p className="text-sm text-gray-600 mt-1">
                    Ask questions about Supreme Court judgments and get AI-powered insights
                  </p>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {messages.length === 0 ? (
                    <div className="text-center text-gray-500 mt-20">
                      <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                      <p className="text-lg font-medium">Start a conversation</p>
                      <p className="text-sm">Ask me anything about Supreme Court judgments</p>
                    </div>
                  ) : (
                    messages.map((message) => (
                      <div key={message.id} className="space-y-3">
                        {/* User Query */}
                        <div className="flex justify-end">
                          <div className="bg-blue-600 text-white p-3 rounded-lg max-w-2xl">
                            {message.query}
                          </div>
                        </div>

                        {/* AI Response */}
                        <div className="flex justify-start">
                          <div className="bg-gray-100 p-3 rounded-lg max-w-2xl">
                            <div className="prose prose-sm max-w-none">
                              <p className="whitespace-pre-wrap">{message.response}</p>
                            </div>
                            
                            {/* Citations */}
                            {message.citations && message.citations.length > 0 && (
                              <div className="mt-3 pt-3 border-t border-gray-200">
                                <h4 className="text-sm font-medium text-gray-900 mb-2">Relevant Cases:</h4>
                                <div className="space-y-1">
                                  {message.citations.slice(0, 3).map((citation, index) => (
                                    <div key={index} className="text-xs text-gray-600">
                                      • {citation.case_title} ({citation.case_number})
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Confidence Score */}
                            <div className="mt-3 pt-3 border-t border-gray-200 flex items-center justify-between">
                              <div className="flex items-center text-xs text-gray-500">
                                <span>Confidence: {message.confidence_score}%</span>
                              </div>
                              
                              {/* Rating */}
                              <div className="flex items-center space-x-1">
                                <button
                                  onClick={() => handleRating(message.id, 1)}
                                  className={`p-1 rounded ${
                                    message.user_rating === 1 ? 'text-green-600' : 'text-gray-400 hover:text-green-600'
                                  }`}
                                >
                                  <ThumbsUp className="w-4 h-4" />
                                </button>
                                <button
                                  onClick={() => handleRating(message.id, 0)}
                                  className={`p-1 rounded ${
                                    message.user_rating === 0 ? 'text-red-600' : 'text-gray-400 hover:text-red-600'
                                  }`}
                                >
                                  <ThumbsDown className="w-4 h-4" />
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))
                  )}

                  {/* Loading indicator */}
                  {isLoading && (
                    <div className="flex justify-start">
                      <div className="bg-gray-100 p-3 rounded-lg">
                        <div className="flex items-center space-x-2">
                          <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                          <span className="text-sm text-gray-600">Analyzing your query...</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Input Form */}
                <div className="p-4 border-t border-gray-200">
                  <form onSubmit={handleSubmit} className="flex space-x-3">
                    <input
                      type="text"
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      placeholder="Ask about Supreme Court judgments..."
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      disabled={isLoading}
                    />
                    <button
                      type="submit"
                      disabled={!query.trim() || isLoading}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                    >
                      {isLoading ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Send className="w-4 h-4" />
                      )}
                    </button>
                  </form>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
