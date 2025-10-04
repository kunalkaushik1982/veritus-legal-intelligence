import React, { useState, useEffect, useCallback } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { 
  ArrowLeft,
  BookOpen,
  Calendar,
  Users,
  FileText,
  Search,
  Filter,
  Download,
  Eye,
  ChevronDown,
  ChevronUp,
  SortAsc,
  SortDesc,
  Clock
} from 'lucide-react';
import toast from 'react-hot-toast';
import API_CONFIG from '../utils/config';
import AISummaryCard from '../components/AISummaryCard';

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
  file_path?: string;
  file_size?: number;
}

interface JudgmentMetadata {
  party1: string;
  party2: string;
  judgment_date: string;
  case_number: string;
  court: string;
}

export default function JudgmentsLibrary() {
  const router = useRouter();
  const [judgments, setJudgments] = useState<Judgment[]>([]);
  const [filteredJudgments, setFilteredJudgments] = useState<Judgment[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'date' | 'title' | 'case_number'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [showFilters, setShowFilters] = useState(false);
  const [dateFilter, setDateFilter] = useState('');
  const [courtFilter, setCourtFilter] = useState('');
  
  // State for expandable AI Summary cards
  const [expandedCards, setExpandedCards] = useState<Set<number>>(new Set());

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
      return;
    }
    
    loadJudgments();
  }, []);

  useEffect(() => {
    filterAndSortJudgments();
  }, [judgments, searchQuery, sortBy, sortOrder, dateFilter, courtFilter]);

  const loadJudgments = async () => {
    setIsLoading(true);
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
    } finally {
      setIsLoading(false);
    }
  };

  const filterAndSortJudgments = () => {
    let filtered = [...judgments];

    // Apply search filter
    if (searchQuery) {
      filtered = filtered.filter(judgment =>
        judgment.case_title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        judgment.petitioner?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        judgment.respondent?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        judgment.case_number?.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Apply date filter
    if (dateFilter) {
      filtered = filtered.filter(judgment => {
        if (!judgment.judgment_date) return false;
        const judgmentYear = new Date(judgment.judgment_date).getFullYear().toString();
        return judgmentYear === dateFilter;
      });
    }

    // Apply court filter
    if (courtFilter) {
      filtered = filtered.filter(judgment => 
        judgment.case_number?.toLowerCase().includes(courtFilter.toLowerCase())
      );
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let comparison = 0;
      
      if (sortBy === 'date') {
        const dateA = new Date(a.judgment_date || '').getTime();
        const dateB = new Date(b.judgment_date || '').getTime();
        comparison = dateA - dateB;
      } else if (sortBy === 'title') {
        comparison = (a.case_title || '').localeCompare(b.case_title || '');
      } else if (sortBy === 'case_number') {
        comparison = (a.case_number || '').localeCompare(b.case_number || '');
      }
      
      return sortOrder === 'asc' ? comparison : -comparison;
    });

    setFilteredJudgments(filtered);
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    } catch {
      return dateString;
    }
  };

  const getAvailableYears = () => {
    const years = new Set<string>();
    judgments.forEach(judgment => {
      if (judgment.judgment_date) {
        years.add(new Date(judgment.judgment_date).getFullYear().toString());
      }
    });
    return Array.from(years).sort((a, b) => b.localeCompare(a));
  };

  const handleViewJudgment = useCallback((judgment: Judgment) => {
    const viewJudgmentAsync = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(API_CONFIG.getApiUrl(`/api/judgments/${judgment.id}/view`), {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          
          const newWindow = window.open(url, '_blank');
          if (!newWindow) {
            toast.error('Please allow popups to view PDFs');
          } else {
            toast.success(`Opening ${judgment.case_title}`);
          }
          
          setTimeout(() => {
            window.URL.revokeObjectURL(url);
          }, 1000);
        } else {
          toast.error('Failed to load PDF');
        }
      } catch (error) {
        console.error('Error viewing PDF:', error);
        toast.error('Failed to view PDF');
      }
    };
    
    setTimeout(() => viewJudgmentAsync(), 0);
  }, []);

  const handleDownloadJudgment = useCallback((judgment: Judgment) => {
    const downloadJudgmentAsync = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(API_CONFIG.getApiUrl(`/api/judgments/${judgment.id}/download`), {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = judgment.filename || `${judgment.case_title}.pdf`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          window.URL.revokeObjectURL(url);
          toast.success(`Downloaded ${judgment.case_title}`);
        } else {
          toast.error('Failed to download PDF');
        }
      } catch (error) {
        console.error('Error downloading PDF:', error);
        toast.error('Failed to download PDF');
      }
    };
    
    setTimeout(() => downloadJudgmentAsync(), 0);
  }, []);

  const handleViewText = useCallback((judgment: Judgment) => {
    const viewTextAsync = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(API_CONFIG.getApiUrl(`/api/judgments/${judgment.id}/text`), {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const data = await response.json();
          const textWindow = window.open('', '_blank', 'width=900,height=700,scrollbars=yes');
          if (textWindow) {
            textWindow.document.write(`
              <html>
                <head>
                  <title>${judgment.case_title} - Text</title>
                  <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }
                    .header { background: #f5f5f5; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
                    .content { white-space: pre-wrap; }
                  </style>
                </head>
                <body>
                  <div class="header">
                    <h1>${judgment.case_title}</h1>
                    <p><strong>Case Number:</strong> ${judgment.case_number}</p>
                    <p><strong>Date:</strong> ${formatDate(judgment.judgment_date || '')}</p>
                  </div>
                  <div class="content">${data.text}</div>
                </body>
              </html>
            `);
            textWindow.document.close();
            toast.success(`Opened text for ${judgment.case_title}`);
          }
        } else {
          toast.error('Failed to load judgment text');
        }
      } catch (error) {
        console.error('View text error:', error);
        toast.error('Failed to load judgment text');
      }
    };
    
    setTimeout(() => viewTextAsync(), 0);
  }, []);

  const handleViewTimeline = useCallback((judgment: Judgment) => {
    const viewTimelineAsync = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(API_CONFIG.getApiUrl(`/api/timeline/${judgment.id}`), {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const data = await response.json();
          const timelineWindow = window.open('', '_blank', 'width=900,height=700,scrollbars=yes');
          if (timelineWindow) {
            timelineWindow.document.write(`
              <html>
                <head>
                  <title>${judgment.case_title} - Timeline</title>
                  <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }
                    .header { background: #f5f5f5; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
                    .timeline-event { border-left: 3px solid #3b82f6; padding-left: 20px; margin-bottom: 20px; }
                  </style>
                </head>
                <body>
                  <div class="header">
                    <h1>${judgment.case_title} - Timeline</h1>
                    <p><strong>Case Number:</strong> ${judgment.case_number}</p>
                  </div>
                  <div class="timeline-events">
                    ${data.timeline_events?.map((event: any) => `
                      <div class="timeline-event">
                        <h3>${event.event_date || 'Date not specified'}</h3>
                        <p>${event.event_description}</p>
                        <small>Type: ${event.event_type} | Confidence: ${event.confidence_score}%</small>
                      </div>
                    `).join('') || '<p>No timeline events found.</p>'}
                  </div>
                </body>
              </html>
            `);
            timelineWindow.document.close();
            toast.success(`Opened timeline for ${judgment.case_title}`);
          }
        } else {
          toast.error('Failed to load judgment timeline');
        }
      } catch (error) {
        console.error('View timeline error:', error);
        toast.error('Failed to load judgment timeline');
      }
    };
    
    setTimeout(() => viewTimelineAsync(), 0);
  }, []);

  const toggleCardExpansion = (judgmentId: number) => {
    setExpandedCards(prev => {
      const newSet = new Set(prev);
      if (newSet.has(judgmentId)) {
        newSet.delete(judgmentId);
      } else {
        newSet.add(judgmentId);
      }
      return newSet;
    });
  };

  const extractMetadata = (judgment: Judgment): JudgmentMetadata => {
    return {
      party1: judgment.petitioner || 'Unknown Petitioner',
      party2: judgment.respondent || 'Unknown Respondent',
      judgment_date: judgment.judgment_date || 'Date not available',
      case_number: judgment.case_number || 'Case number not available',
      court: 'Supreme Court of India'
    };
  };

  return (
    <div>
      <Head>
        <title>Judgments Library - Veritus</title>
        <meta name="description" content="Browse and search Supreme Court judgments" />
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
                  <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-xl flex items-center justify-center shadow-lg">
                    <BookOpen className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                      Judgments Library
                    </h1>
                    <p className="text-sm text-gray-600 font-medium">Browse Supreme Court Judgments</p>
                  </div>
                </div>
              </div>
              
              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <div className="text-2xl font-bold text-gray-900">{judgments.length}</div>
                  <div className="text-sm text-gray-600">Total Judgments</div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-blue-600">{filteredJudgments.length}</div>
                  <div className="text-sm text-gray-600">Filtered Results</div>
                </div>
              </div>
            </div>
          </div>
        </header>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Search and Filters */}
          <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6 mb-8">
            <div className="flex flex-col lg:flex-row gap-4">
              {/* Search Bar */}
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                  <input
                    type="text"
                    placeholder="Search judgments, parties, or case numbers..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                  />
                </div>
              </div>

              {/* Filter Toggle */}
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="flex items-center px-4 py-3 bg-gray-100 hover:bg-gray-200 rounded-xl transition-colors"
              >
                <Filter className="w-5 h-5 mr-2" />
                <span className="font-medium">Filters</span>
                {showFilters ? <ChevronUp className="w-5 h-5 ml-2" /> : <ChevronDown className="w-5 h-5 ml-2" />}
              </button>
            </div>

            {/* Filters Panel */}
            {showFilters && (
              <div className="mt-6 pt-6 border-t border-gray-200">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Date Filter */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Year</label>
                    <select
                      value={dateFilter}
                      onChange={(e) => setDateFilter(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="">All Years</option>
                      {getAvailableYears().map(year => (
                        <option key={year} value={year}>{year}</option>
                      ))}
                    </select>
                  </div>

                  {/* Court Filter */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Court</label>
                    <select
                      value={courtFilter}
                      onChange={(e) => setCourtFilter(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="">All Courts</option>
                      <option value="supreme">Supreme Court</option>
                      <option value="high">High Court</option>
                      <option value="district">District Court</option>
                    </select>
                  </div>

                  {/* Sort Options */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Sort By</label>
                    <div className="flex gap-2">
                      <select
                        value={sortBy}
                        onChange={(e) => setSortBy(e.target.value as 'date' | 'title' | 'case_number')}
                        className="flex-1 px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      >
                        <option value="date">Date</option>
                        <option value="title">Title</option>
                        <option value="case_number">Case Number</option>
                      </select>
                      <button
                        onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                        className="px-3 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                      >
                        {sortOrder === 'asc' ? <SortAsc className="w-5 h-5" /> : <SortDesc className="w-5 h-5" />}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Judgments Grid */}
          <div className="space-y-6">
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
                  <span className="text-gray-600">Loading judgments...</span>
                </div>
              </div>
            ) : filteredJudgments.length > 0 ? (
              filteredJudgments.map((judgment) => {
                const metadata = extractMetadata(judgment);
                return (
                  <div key={judgment.id} className="bg-white rounded-2xl shadow-lg border border-gray-100 hover:shadow-xl hover:border-slate-300 transition-all duration-300 group overflow-hidden">
                    {/* Header Section */}
                    <div className="bg-gradient-to-r from-slate-800 to-slate-900 px-6 py-5 border-b border-slate-700">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                          <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg">
                            <BookOpen className="w-6 h-6 text-white" />
                          </div>
                          <div>
                            <h3 className="text-xl font-bold text-white group-hover:text-blue-200 transition-colors">
                              {judgment.case_title || 'Untitled Case'}
                            </h3>
                            <p className="text-slate-300 text-sm font-medium">
                              {metadata.party1} vs {metadata.party2}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-white font-semibold text-lg">{metadata.case_number}</div>
                          <div className="text-slate-300 text-sm">{formatDate(metadata.judgment_date)}</div>
                        </div>
                      </div>
                    </div>

                    {/* Content Section */}
                    <div className="p-6">
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Case Details */}
                        <div className="space-y-4">
                          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-4 border border-blue-200">
                            <div className="flex items-center space-x-2 mb-2">
                              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                              <span className="font-semibold text-gray-700 text-sm">Case Title</span>
                            </div>
                            <div className="text-gray-600 text-sm">{judgment.case_title || 'Not available'}</div>
                          </div>
                          
                          {judgment.summary && (
                            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-4 border border-blue-200">
                              <div className="flex items-center space-x-2 mb-2">
                                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                                <span className="font-semibold text-blue-700 text-sm">Summary</span>
                              </div>
                              <div className="text-blue-600 text-sm line-clamp-2">{judgment.summary}</div>
                            </div>
                          )}
                        </div>

                        {/* Action Buttons */}
                        <div className="border-t border-gray-100 pt-5">
                          <div className="flex items-center justify-between">
                            <div className="text-sm text-gray-500 font-medium">
                              Available Actions
                            </div>
                            <div className="flex items-center space-x-3">
                              <button
                                onClick={() => handleViewJudgment(judgment)}
                                className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm hover:shadow-md"
                              >
                                <Eye className="w-4 h-4 mr-2" />
                                <span className="text-sm font-medium">View PDF</span>
                              </button>
                              
                              <button
                                onClick={() => handleViewText(judgment)}
                                className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors shadow-sm hover:shadow-md"
                              >
                                <FileText className="w-4 h-4 mr-2" />
                                <span className="text-sm font-medium">Text</span>
                              </button>
                              
                              <button
                                onClick={() => handleViewTimeline(judgment)}
                                className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors shadow-sm hover:shadow-md"
                              >
                                <Clock className="w-4 h-4 mr-2" />
                                <span className="text-sm font-medium">Timeline</span>
                              </button>
                              
                              <AISummaryCard
                                judgment={judgment}
                                isExpanded={expandedCards.has(judgment.id)}
                                onToggle={() => toggleCardExpansion(judgment.id)}
                              />
                              
                              <button
                                onClick={() => handleDownloadJudgment(judgment)}
                                className="flex items-center px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors shadow-sm hover:shadow-md"
                              >
                                <Download className="w-4 h-4 mr-2" />
                                <span className="text-sm font-medium">Download</span>
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* AI Summary Section - Now handled by AISummaryCard component */}
                    {expandedCards.has(judgment.id) && (
                      <div className="border-t border-gray-200">
                        <AISummaryCard
                          judgment={judgment}
                          isExpanded={true}
                          onToggle={() => toggleCardExpansion(judgment.id)}
                        />
                      </div>
                    )}
                  </div>
                );
              })
            ) : (
              <div className="text-center py-12">
                <div className="w-24 h-24 bg-gradient-to-br from-gray-200 to-gray-300 rounded-full flex items-center justify-center mx-auto mb-4">
                  <BookOpen className="w-12 h-12 text-gray-400" />
                </div>
                <h3 className="text-lg font-semibold text-gray-600 mb-2">No judgments found</h3>
                <p className="text-gray-500">
                  {searchQuery || dateFilter || courtFilter 
                    ? 'Try adjusting your search criteria' 
                    : 'No judgments have been uploaded yet'
                  }
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
