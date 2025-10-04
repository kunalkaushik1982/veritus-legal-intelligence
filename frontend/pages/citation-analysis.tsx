import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { 
  ArrowLeft,
  BarChart3,
  Network,
  TrendingUp,
  Loader2,
  Search,
  Eye,
  Target,
  Award,
  Activity,
  BookOpen,
  Upload,
  FileText,
  CheckCircle
} from 'lucide-react';
import toast from 'react-hot-toast';
import API_CONFIG from '../utils/config';

interface CitationAnalysis {
  citation_type: string;
  strength_score: number;
  confidence_score: number;
  legal_principle: string | null;
  statute_reference: string | null;
  issue_category: string | null;
  is_positive: boolean;
  context: string;
  analysis_timestamp: string;
  pdf_analysis?: any; // Optional PDF analysis data
}

interface NetworkNode {
  id: number;
  label: string;
  type: string;
  size: number;
}

interface NetworkEdge {
  source: number;
  target: number;
  weight: number;
  citation_type: string;
  color: string;
}

interface CitationNetwork {
  judgment_id: number;
  network: {
    nodes: NetworkNode[];
    edges: NetworkEdge[];
  };
  metrics: {
    in_degree: number;
    out_degree: number;
    pagerank: number;
    avg_citation_strength: number;
  };
  total_citations: number;
  is_sample_data?: boolean; // Optional sample data indicator
  target_file?: string; // Optional target file name
}

interface PrecedentRanking {
  judgment_id: number;
  case_title: string;
  case_number: string;
  average_strength: number;
  citation_count: number;
  max_strength: number;
  min_strength: number;
  consistency: number;
}

interface Judgment {
  id: number;
  case_title?: string;
  case_number?: string;
  petitioner?: string;
  respondent?: string;
  judgment_date?: string;
  summary?: string;
  is_processed: boolean;
  filename?: string;
}

export default function CitationAnalysis() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'browse' | 'analyze' | 'network' | 'ranking'>('browse');
  const [isLoading, setIsLoading] = useState(false);
  
  // Citation Analysis State
  const [analysisForm, setAnalysisForm] = useState({
    source_judgment_id: 1,
    target_judgment_id: 2,
    context_text: 'The court relied upon the landmark decision in State of Maharashtra v. Rajesh Kumar which established the principle that proper procedure must be followed in all criminal cases.'
  });
  const [analysisResult, setAnalysisResult] = useState<CitationAnalysis | null>(null);
  
  // Network Analysis State
  const [networkJudgmentId, setNetworkJudgmentId] = useState(1);
  const [networkResult, setNetworkResult] = useState<CitationNetwork | null>(null);
  
  // Precedent Ranking State
  const [rankingLimit, setRankingLimit] = useState(10);
  const [rankingResult, setRankingResult] = useState<PrecedentRanking[]>([]);

  // Browse Judgments State
  const [judgments, setJudgments] = useState<Judgment[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSource, setSelectedSource] = useState<Judgment | null>(null);
  const [selectedTarget, setSelectedTarget] = useState<Judgment | null>(null);
  const [uploadFile, setUploadFile] = useState<File | null>(null);

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
      return;
    }
    
    // Load judgments on component mount
    loadJudgments();
  }, []); // Remove router from dependencies

  const loadJudgments = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(API_CONFIG.getApiUrl('/api/judgments/'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setJudgments(data.judgments || []);
      } else {
        console.error('Failed to load judgments:', response.status);
        setJudgments([]);
      }
    } catch (error) {
      console.error('Error loading judgments:', error);
      setJudgments([]);
    }
  };

  const uploadPDF = async () => {
    if (!uploadFile) {
      toast.error('Please select a PDF file');
      return;
    }

    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', uploadFile);

      const token = localStorage.getItem('access_token');
      const response = await fetch(API_CONFIG.getApiUrl('/api/upload/pdf'), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          toast.success('PDF uploaded and processed successfully!');
          setUploadFile(null);
          // Add the new judgment to the list immediately
          if (data.judgment) {
            setJudgments(prev => [...prev, data.judgment]);
          }
          // Also reload the full list to be safe
          loadJudgments();
        } else {
          toast.error(data.error || 'Failed to process PDF');
        }
      } else {
        const errorData = await response.json();
        toast.error(errorData.detail || 'Failed to upload PDF');
      }
    } catch (error) {
      toast.error('Upload failed');
      console.error('Upload error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const analyzeCitation = async () => {
    setIsLoading(true);
    try {
      const sourceId = selectedSource?.id || analysisForm.source_judgment_id;
      const targetId = selectedTarget?.id || analysisForm.target_judgment_id;

      const response = await fetch(API_CONFIG.getApiUrl('/api/citations/analyze'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          source_judgment_id: sourceId,
          target_judgment_id: targetId,
          context_text: analysisForm.context_text
        }),
      });

      if (!response.ok) {
        throw new Error('Analysis failed');
      }

      const data = await response.json();
      setAnalysisResult(data.analysis);
      toast.success('Citation analysis completed!');
    } catch (error) {
      toast.error('Failed to analyze citation');
      console.error('Analysis error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getCitationNetwork = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(API_CONFIG.getApiUrl(`/api/citations/network/${networkJudgmentId}`));
      
      if (!response.ok) {
        throw new Error('Network analysis failed');
      }

      const data = await response.json();
      setNetworkResult(data.network);
      toast.success('Citation network loaded!');
    } catch (error) {
      toast.error('Failed to load citation network');
      console.error('Network error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getPrecedentRanking = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(API_CONFIG.getApiUrl(`/api/citations/strength-ranking?limit=${rankingLimit}`));
      
      if (!response.ok) {
        throw new Error('Ranking failed');
      }

      const data = await response.json();
      setRankingResult(data.ranking);
      toast.success('Precedent ranking loaded!');
    } catch (error) {
      toast.error('Failed to load precedent ranking');
      console.error('Ranking error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getStrengthColor = (strength: number) => {
    if (strength >= 80) return 'text-green-600 bg-green-100';
    if (strength >= 60) return 'text-blue-600 bg-blue-100';
    if (strength >= 40) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getCitationTypeColor = (type: string) => {
    const colors = {
      'relied_upon': 'bg-green-500',
      'followed': 'bg-blue-500',
      'referred': 'bg-purple-500',
      'distinguished': 'bg-orange-500',
      'overruled': 'bg-red-500',
      'cited': 'bg-gray-500'
    };
    return colors[type as keyof typeof colors] || 'bg-gray-500';
  };

  const filteredJudgments = judgments.filter(judgment =>
    (judgment.case_title && judgment.case_title.toLowerCase().includes(searchQuery.toLowerCase())) ||
    (judgment.case_number && judgment.case_number.toLowerCase().includes(searchQuery.toLowerCase())) ||
    (judgment.petitioner && judgment.petitioner.toLowerCase().includes(searchQuery.toLowerCase())) ||
    (judgment.respondent && judgment.respondent.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <>
      <Head>
        <title>Citation Analysis - Veritus</title>
        <meta name="description" content="Citation Analysis and Precedent Strength" />
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
        {/* Header */}
        <header className="bg-white/90 backdrop-blur-md shadow-xl border-b border-gray-200/50 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-20">
              <div className="flex items-center space-x-6">
                <button
                  onClick={() => router.push('/dashboard')}
                  className="flex items-center text-gray-600 hover:text-gray-900 transition-all duration-200 hover:bg-gray-100 px-4 py-2 rounded-xl group"
                >
                  <ArrowLeft className="w-5 h-5 mr-2 group-hover:-translate-x-1 transition-transform" />
                  <span className="font-medium">Back to Dashboard</span>
                </button>
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-xl flex items-center justify-center shadow-lg">
                    <BarChart3 className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                      Citation Analysis
                    </h1>
                    <p className="text-sm text-gray-600 font-medium">Advanced Legal Precedent Intelligence</p>
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2 bg-green-50 px-4 py-2 rounded-full border border-green-200">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-sm font-medium text-green-700">System Active</span>
                </div>
              </div>
            </div>
          </div>
        </header>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Tab Navigation */}
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-200/50 mb-8 overflow-hidden">
            <div className="bg-gradient-to-r from-gray-50 to-blue-50/50 px-6 py-2">
              <nav className="flex space-x-1">
                {[
                  { id: 'browse', label: 'Browse Judgments', icon: BookOpen },
                  { id: 'analyze', label: 'Citation Analysis', icon: Search },
                  { id: 'network', label: 'Citation Network', icon: Network },
                  { id: 'ranking', label: 'Precedent Ranking', icon: TrendingUp }
                ].map((tab) => {
                  const Icon = tab.icon;
                  const isActive = activeTab === tab.id;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id as any)}
                      className={`flex items-center py-4 px-6 rounded-xl font-semibold text-sm transition-all duration-300 ${
                        isActive
                          ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-lg transform scale-105'
                          : 'text-gray-600 hover:text-gray-900 hover:bg-white/60 hover:shadow-md'
                      }`}
                    >
                      <Icon className={`w-5 h-5 mr-3 ${isActive ? 'text-white' : 'text-gray-500'}`} />
                      {tab.label}
                    </button>
                  );
                })}
              </nav>
            </div>
          </div>

          {/* Tab Content */}
          <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-2xl border border-gray-200/50 p-8 min-h-[600px]">
            {/* Browse Judgments Tab */}
            {activeTab === 'browse' && (
              <div className="space-y-8">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-xl flex items-center justify-center shadow-lg">
                      <BookOpen className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <h2 className="text-2xl font-bold text-gray-900">Browse Judgments</h2>
                      <p className="text-gray-600">Upload and manage legal documents</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 bg-blue-50 px-4 py-2 rounded-full border border-blue-200">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span className="text-sm font-medium text-blue-700">
                      {judgments.length} judgment{judgments.length !== 1 ? 's' : ''} available
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                  {/* Upload and Search */}
                  <div className="space-y-6">
                    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-6 border border-blue-200/50">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                        <Upload className="w-5 h-5 mr-2 text-blue-600" />
                        Upload PDF
                      </h3>
                      
                      <div className="border-2 border-dashed border-blue-300 rounded-xl p-6 bg-white/50 hover:bg-white/80 transition-all duration-200">
                        <div className="text-center">
                          <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg">
                            <Upload className="w-8 h-8 text-white" />
                          </div>
                          <div className="text-sm font-medium text-gray-700 mb-2">
                            {uploadFile ? uploadFile.name : 'Select PDF file'}
                          </div>
                          <input
                            type="file"
                            accept=".pdf"
                            onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                            className="hidden"
                            id="pdf-upload"
                          />
                          <label
                            htmlFor="pdf-upload"
                            className="cursor-pointer inline-flex items-center px-4 py-2 bg-gradient-to-r from-blue-500 to-blue-600 text-white text-sm font-medium rounded-lg hover:from-blue-600 hover:to-blue-700 transition-all duration-200 shadow-md hover:shadow-lg"
                          >
                            Choose File
                          </label>
                        </div>
                        {uploadFile && (
                          <button
                            onClick={uploadPDF}
                            disabled={isLoading}
                            className="w-full mt-4 bg-gradient-to-r from-green-500 to-green-600 text-white py-3 px-4 rounded-lg hover:from-green-600 hover:to-green-700 disabled:opacity-50 flex items-center justify-center font-semibold shadow-md hover:shadow-lg transition-all duration-200"
                          >
                            {isLoading ? (
                              <Loader2 className="w-5 h-5 animate-spin mr-2" />
                            ) : (
                              <Upload className="w-5 h-5 mr-2" />
                            )}
                            Upload PDF
                          </button>
                        )}
                      </div>
                    </div>

                    <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl p-6 border border-purple-200/50">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                        <Search className="w-5 h-5 mr-2 text-purple-600" />
                        Search Judgments
                      </h3>
                      <div className="relative">
                        <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-purple-400 w-5 h-5" />
                        <input
                          type="text"
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          placeholder="Search by title, case number, or parties..."
                          className="w-full pl-12 pr-4 py-3 border border-purple-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white/80"
                        />
                      </div>
                    </div>

                    {/* Selection Summary */}
                    <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl p-6 border border-green-200/50">
                      <h4 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                        <Target className="w-5 h-5 mr-2 text-green-600" />
                        Selected for Analysis
                      </h4>
                      
                      <div className="space-y-3">
                        <div className="p-4 border border-green-200 rounded-xl bg-white/80">
                          <div className="text-xs font-medium text-green-700 uppercase tracking-wide">Source Judgment</div>
                          <div className="text-sm font-semibold text-gray-900 mt-1">
                            {selectedSource ? selectedSource.case_title : 'None selected'}
                          </div>
                        </div>
                        
                        <div className="p-4 border border-green-200 rounded-xl bg-white/80">
                          <div className="text-xs font-medium text-green-700 uppercase tracking-wide">Target Judgment</div>
                          <div className="text-sm font-semibold text-gray-900 mt-1">
                            {selectedTarget ? selectedTarget.case_title : 'None selected'}
                          </div>
                        </div>
                      </div>

                      {selectedSource && selectedTarget && (
                        <button
                          onClick={() => setActiveTab('analyze')}
                          className="w-full mt-4 bg-gradient-to-r from-green-500 to-emerald-600 text-white py-3 px-4 rounded-xl hover:from-green-600 hover:to-emerald-700 flex items-center justify-center font-semibold shadow-md hover:shadow-lg transition-all duration-200"
                        >
                          <Target className="w-5 h-5 mr-2" />
                          Analyze Citation
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Judgments List */}
                  <div className="lg:col-span-2 space-y-6">
                    <div className="flex items-center justify-between">
                      <h3 className="text-xl font-semibold text-gray-900 flex items-center">
                        <FileText className="w-6 h-6 mr-2 text-blue-600" />
                        Available Judgments
                      </h3>
                      <div className="text-sm text-gray-500">
                        {filteredJudgments.length} of {judgments.length} judgments
                      </div>
                    </div>
                    
                    <div className="space-y-4 max-h-96 overflow-y-auto pr-2">
                      {filteredJudgments.map((judgment) => (
                        <div key={judgment.id} className="bg-white/80 backdrop-blur-sm border border-gray-200/50 rounded-2xl p-6 hover:bg-white hover:shadow-lg transition-all duration-200 group">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center space-x-3 mb-3">
                                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-md">
                                  <FileText className="w-5 h-5 text-white" />
                                </div>
                                <div>
                                  <h4 className="font-bold text-gray-900 text-lg group-hover:text-blue-600 transition-colors">
                                    {judgment.case_title || judgment.filename || `Judgment ${judgment.id}`}
                                  </h4>
                                  <div className="flex items-center space-x-2">
                                    {judgment.is_processed && (
                                      <div className="flex items-center space-x-1 bg-green-100 px-2 py-1 rounded-full">
                                        <CheckCircle className="w-3 h-3 text-green-600" />
                                        <span className="text-xs font-medium text-green-700">Processed</span>
                                      </div>
                                    )}
                                    <span className="text-xs text-gray-500">ID: {judgment.id}</span>
                                  </div>
                                </div>
                              </div>
                              
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm text-gray-600">
                                <div className="bg-gray-50 rounded-lg p-3">
                                  <div className="font-semibold text-gray-700 mb-1">Case Number</div>
                                  <div>{judgment.case_number || 'Case number not available'}</div>
                                </div>
                                {judgment.petitioner && (
                                  <div className="bg-gray-50 rounded-lg p-3">
                                    <div className="font-semibold text-gray-700 mb-1">Petitioner</div>
                                    <div>{judgment.petitioner}</div>
                                  </div>
                                )}
                                {judgment.respondent && (
                                  <div className="bg-gray-50 rounded-lg p-3">
                                    <div className="font-semibold text-gray-700 mb-1">Respondent</div>
                                    <div>{judgment.respondent}</div>
                                  </div>
                                )}
                                {judgment.judgment_date && (
                                  <div className="bg-gray-50 rounded-lg p-3">
                                    <div className="font-semibold text-gray-700 mb-1">Date</div>
                                    <div>{new Date(judgment.judgment_date).toLocaleDateString()}</div>
                                  </div>
                                )}
                              </div>
                              
                              {judgment.summary && (
                                <div className="mt-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                                  <div className="text-xs font-medium text-blue-700 mb-1">Summary</div>
                                  <div className="text-sm text-blue-800">{judgment.summary}</div>
                                </div>
                              )}
                            </div>
                            
                            <div className="flex flex-col space-y-2 ml-6">
                              <button
                                onClick={() => setSelectedSource(judgment)}
                                className={`px-4 py-2 text-sm font-semibold rounded-xl transition-all duration-200 ${
                                  selectedSource?.id === judgment.id
                                    ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-lg'
                                    : 'bg-gray-100 text-gray-700 hover:bg-blue-100 hover:text-blue-700 hover:shadow-md'
                                }`}
                              >
                                Set as Source
                              </button>
                              <button
                                onClick={() => setSelectedTarget(judgment)}
                                className={`px-4 py-2 text-sm font-semibold rounded-xl transition-all duration-200 ${
                                  selectedTarget?.id === judgment.id
                                    ? 'bg-gradient-to-r from-green-500 to-green-600 text-white shadow-lg'
                                    : 'bg-gray-100 text-gray-700 hover:bg-green-100 hover:text-green-700 hover:shadow-md'
                                }`}
                              >
                                Set as Target
                              </button>
                            </div>
                          </div>
                        </div>
                      ))}
                      
                      {filteredJudgments.length === 0 && (
                        <div className="text-center py-12">
                          <div className="w-24 h-24 bg-gradient-to-br from-gray-200 to-gray-300 rounded-full flex items-center justify-center mx-auto mb-4">
                            <FileText className="w-12 h-12 text-gray-400" />
                          </div>
                          <h3 className="text-lg font-semibold text-gray-600 mb-2">No judgments found</h3>
                          <p className="text-gray-500">Try adjusting your search criteria or upload new PDFs</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Citation Analysis Tab */}
            {activeTab === 'analyze' && (
              <div className="space-y-6">
                <div className="flex items-center">
                  <Search className="w-6 h-6 mr-2 text-blue-600" />
                  <h2 className="text-xl font-semibold text-gray-900">Citation Analysis</h2>
                </div>
                
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Input Form */}
                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-gray-900">Analyze Citation Relationship</h3>
                    
                    {/* Selected Judgments Display */}
                    <div className="space-y-3">
                      <div className="p-3 border rounded-lg bg-blue-50">
                        <div className="text-sm font-medium text-blue-800">Source Judgment</div>
                        <div className="text-sm text-blue-700">
                          {selectedSource ? (
                            <>
                              <div className="font-semibold">{selectedSource.case_title}</div>
                              <div>{selectedSource.case_number}</div>
                            </>
                          ) : (
                            'No source judgment selected. Go to Browse Judgments tab to select.'
                          )}
                        </div>
                      </div>
                      
                      <div className="p-3 border rounded-lg bg-green-50">
                        <div className="text-sm font-medium text-green-800">Target Judgment</div>
                        <div className="text-sm text-green-700">
                          {selectedTarget ? (
                            <>
                              <div className="font-semibold">{selectedTarget.case_title}</div>
                              <div>{selectedTarget.case_number}</div>
                            </>
                          ) : (
                            'No target judgment selected. Go to Browse Judgments tab to select.'
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Fallback ID inputs for when no judgments are selected */}
                    {!selectedSource && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Source Judgment ID (Fallback)
                        </label>
                        <input
                          type="number"
                          value={analysisForm.source_judgment_id}
                          onChange={(e) => setAnalysisForm(prev => ({
                            ...prev,
                            source_judgment_id: parseInt(e.target.value)
                          }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                    )}
                    
                    {!selectedTarget && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Target Judgment ID (Fallback)
                        </label>
                        <input
                          type="number"
                          value={analysisForm.target_judgment_id}
                          onChange={(e) => setAnalysisForm(prev => ({
                            ...prev,
                            target_judgment_id: parseInt(e.target.value)
                          }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                    )}
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Citation Context
                      </label>
                      <textarea
                        value={analysisForm.context_text}
                        onChange={(e) => setAnalysisForm(prev => ({
                          ...prev,
                          context_text: e.target.value
                        }))}
                        rows={4}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Enter the text containing the citation..."
                      />
                    </div>
                    
                    <button
                      onClick={analyzeCitation}
                      disabled={isLoading}
                      className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                    >
                      {isLoading ? (
                        <Loader2 className="w-4 h-4 animate-spin mr-2" />
                      ) : (
                        <Search className="w-4 h-4 mr-2" />
                      )}
                      Analyze Citation
                    </button>
                  </div>
                  
                  {/* Analysis Results */}
                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-gray-900">Analysis Results</h3>
                    
                    {analysisResult ? (
                      <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div className="bg-gray-50 p-4 rounded-lg">
                            <div className="text-sm text-gray-600">Citation Type</div>
                            <div className="text-lg font-semibold capitalize">{analysisResult.citation_type.replace('_', ' ')}</div>
                          </div>
                          <div className="bg-gray-50 p-4 rounded-lg">
                            <div className="text-sm text-gray-600">Strength Score</div>
                            <div className={`text-lg font-semibold ${getStrengthColor(analysisResult.strength_score)} px-2 py-1 rounded`}>
                              {analysisResult.strength_score}/100
                            </div>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4">
                          <div className="bg-gray-50 p-4 rounded-lg">
                            <div className="text-sm text-gray-600">Confidence</div>
                            <div className="text-lg font-semibold">{analysisResult.confidence_score}%</div>
                          </div>
                          <div className="bg-gray-50 p-4 rounded-lg">
                            <div className="text-sm text-gray-600">Sentiment</div>
                            <div className={`text-lg font-semibold ${analysisResult.is_positive ? 'text-green-600' : 'text-red-600'}`}>
                              {analysisResult.is_positive ? 'Positive' : 'Negative'}
                            </div>
                          </div>
                        </div>
                        
                        {analysisResult.legal_principle && (
                          <div className="bg-blue-50 p-4 rounded-lg">
                            <div className="text-sm text-blue-600 font-medium">Legal Principle</div>
                            <div className="text-gray-900">{analysisResult.legal_principle}</div>
                          </div>
                        )}
                        
                        {analysisResult.issue_category && (
                          <div className="bg-purple-50 p-4 rounded-lg">
                            <div className="text-sm text-purple-600 font-medium">Issue Category</div>
                            <div className="text-gray-900 capitalize">{analysisResult.issue_category}</div>
                          </div>
                        )}
                        
                        {/* PDF Analysis Info */}
                        {analysisResult.pdf_analysis && (
                          <div className="bg-blue-50 p-4 rounded-lg">
                            <div className="text-sm text-blue-600 font-medium">Analysis Method</div>
                            <div className="text-gray-900">
                              {analysisResult.pdf_analysis.used_real_pdfs ? (
                                <div className="flex items-center">
                                  <CheckCircle className="w-4 h-4 text-green-600 mr-2" />
                                  <span>Analyzed actual PDF content</span>
                                  <span className="text-xs text-gray-500 ml-2">
                                    (Source: {analysisResult.pdf_analysis.source_content_length} chars, 
                                    Target: {analysisResult.pdf_analysis.target_content_length} chars)
                                  </span>
                                </div>
                              ) : (
                                <div className="flex items-center">
                                  <FileText className="w-4 h-4 text-yellow-600 mr-2" />
                                  <span>Analyzed context text only</span>
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="text-center text-gray-500 py-8">
                        <Search className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                        <p>Enter citation details and click &quot;Analyze Citation&quot; to see results</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Citation Network Tab */}
            {activeTab === 'network' && (
              <div className="space-y-6">
                <div className="flex items-center">
                  <Network className="w-6 h-6 mr-2 text-blue-600" />
                  <h2 className="text-xl font-semibold text-gray-900">Citation Network</h2>
                </div>
                
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Network Controls */}
                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-gray-900">Select Judgment for Network Analysis</h3>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Choose Judgment
                      </label>
                      <select
                        value={networkJudgmentId || ""}
                        onChange={(e) => setNetworkJudgmentId(parseInt(e.target.value))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="">Select a judgment...</option>
                        {judgments.map((judgment) => (
                          <option key={judgment.id} value={judgment.id}>
                            {judgment.case_title || judgment.filename || `Judgment ${judgment.id}`} (ID: {judgment.id})
                          </option>
                        ))}
                      </select>
                    </div>
                    
                    <button
                      onClick={getCitationNetwork}
                      disabled={isLoading || !networkJudgmentId}
                      className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                    >
                      {isLoading ? (
                        <Loader2 className="w-4 h-4 animate-spin mr-2" />
                      ) : (
                        <Network className="w-4 h-4 mr-2" />
                      )}
                      Load Network
                    </button>
                  </div>
                  
                  {/* Network Metrics */}
                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-gray-900">Network Metrics</h3>
                    
                    {networkResult ? (
                      <div className="space-y-3">
                        {/* Data Source Indicator */}
                        {networkResult.is_sample_data !== undefined && (
                          <div className={`p-3 rounded-lg ${networkResult.is_sample_data ? 'bg-yellow-50 border border-yellow-200' : 'bg-green-50 border border-green-200'}`}>
                            <div className={`text-sm font-medium ${networkResult.is_sample_data ? 'text-yellow-800' : 'text-green-800'}`}>
                              {networkResult.is_sample_data ? 'Sample Data' : 'Real Network Data'}
                            </div>
                            <div className={`text-xs ${networkResult.is_sample_data ? 'text-yellow-600' : 'text-green-600'}`}>
                              {networkResult.is_sample_data 
                                ? 'No PDFs uploaded - showing sample network' 
                                : `Analyzed ${networkResult.target_file || 'uploaded PDF'}`
                              }
                            </div>
                          </div>
                        )}
                        
                        <div className="bg-gray-50 p-3 rounded-lg">
                          <div className="text-sm text-gray-600">Total Citations</div>
                          <div className="text-xl font-semibold">{networkResult.total_citations}</div>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-3">
                          <div className="bg-blue-50 p-3 rounded-lg">
                            <div className="text-sm text-blue-600">In-degree</div>
                            <div className="text-lg font-semibold">{networkResult.metrics.in_degree}</div>
                          </div>
                          <div className="bg-green-50 p-3 rounded-lg">
                            <div className="text-sm text-green-600">Out-degree</div>
                            <div className="text-lg font-semibold">{networkResult.metrics.out_degree}</div>
                          </div>
                        </div>
                        
                        <div className="bg-purple-50 p-3 rounded-lg">
                          <div className="text-sm text-purple-600">PageRank</div>
                          <div className="text-lg font-semibold">{networkResult.metrics.pagerank.toFixed(4)}</div>
                        </div>
                        
                        <div className="bg-orange-50 p-3 rounded-lg">
                          <div className="text-sm text-orange-600">Avg. Citation Strength</div>
                          <div className="text-lg font-semibold">{networkResult.metrics.avg_citation_strength.toFixed(1)}</div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center text-gray-500 py-8">
                        <Network className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                        <p>Enter a judgment ID and click &quot;Load Network&quot; to see the citation network</p>
                      </div>
                    )}
                  </div>
                  
                  {/* Network Visualization */}
                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-gray-900">Network Visualization</h3>
                    
                    {networkResult ? (
                      <div className="space-y-3">
                        <div className="text-sm text-gray-600">Nodes: {networkResult.network.nodes.length}</div>
                        <div className="text-sm text-gray-600">Edges: {networkResult.network.edges.length}</div>
                        
                        <div className="space-y-2">
                          <div className="text-sm font-medium text-gray-900">Citation Types:</div>
                          {networkResult.network.edges.map((edge, index) => (
                            <div key={index} className="flex items-center space-x-2">
                              <div className={`w-3 h-3 rounded-full ${getCitationTypeColor(edge.citation_type)}`}></div>
                              <span className="text-sm capitalize">{edge.citation_type.replace('_', ' ')}</span>
                              <span className="text-sm text-gray-500">({edge.weight})</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <div className="text-center text-gray-500 py-8">
                        <Eye className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                        <p>Network visualization will appear here</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Precedent Ranking Tab */}
            {activeTab === 'ranking' && (
              <div className="space-y-6">
                <div className="flex items-center">
                  <TrendingUp className="w-6 h-6 mr-2 text-blue-600" />
                  <h2 className="text-xl font-semibold text-gray-900">Precedent Strength Ranking</h2>
                </div>
                
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                  {/* Ranking Controls */}
                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-gray-900">Ranking Settings</h3>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Number of Results
                      </label>
                      <input
                        type="number"
                        value={rankingLimit}
                        onChange={(e) => setRankingLimit(parseInt(e.target.value))}
                        min="1"
                        max="50"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    
                    <button
                      onClick={getPrecedentRanking}
                      disabled={isLoading}
                      className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                    >
                      {isLoading ? (
                        <Loader2 className="w-4 h-4 animate-spin mr-2" />
                      ) : (
                        <TrendingUp className="w-4 h-4 mr-2" />
                      )}
                      Load Ranking
                    </button>
                  </div>
                  
                  {/* Ranking Results */}
                  <div className="lg:col-span-3 space-y-4">
                    <h3 className="text-lg font-medium text-gray-900">Top Precedents by Influence</h3>
                    
                    {rankingResult.length > 0 ? (
                      <div className="space-y-3">
                        {rankingResult.map((precedent, index) => (
                          <div key={precedent.judgment_id} className="bg-gray-50 p-4 rounded-lg">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center space-x-3 mb-2">
                                  <div className="flex items-center justify-center w-8 h-8 bg-blue-600 text-white rounded-full text-sm font-semibold">
                                    {index + 1}
                                  </div>
                                  <div>
                                    <h4 className="font-semibold text-gray-900">{precedent.case_title}</h4>
                                    <p className="text-sm text-gray-600">{precedent.case_number}</p>
                                  </div>
                                </div>
                                
                                <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-3">
                                  <div className="text-center">
                                    <div className="text-sm text-gray-600">Strength</div>
                                    <div className={`text-lg font-semibold ${getStrengthColor(precedent.average_strength)} px-2 py-1 rounded`}>
                                      {precedent.average_strength}/100
                                    </div>
                                  </div>
                                  <div className="text-center">
                                    <div className="text-sm text-gray-600">Citations</div>
                                    <div className="text-lg font-semibold text-gray-900">{precedent.citation_count}</div>
                                  </div>
                                  <div className="text-center">
                                    <div className="text-sm text-gray-600">Consistency</div>
                                    <div className="text-lg font-semibold text-gray-900">{precedent.consistency}%</div>
                                  </div>
                                  <div className="text-center">
                                    <div className="text-sm text-gray-600">Range</div>
                                    <div className="text-lg font-semibold text-gray-900">
                                      {precedent.min_strength}-{precedent.max_strength}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center text-gray-500 py-8">
                        <Award className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                        <p>Click &quot;Load Ranking&quot; to see the most influential precedents</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
