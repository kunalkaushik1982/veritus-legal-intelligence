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
  upload_date?: string;
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
      toast.error('Failed to load judgments');
    } finally {
      setIsLoading(false);
    }
  };

  const filterAndSortJudgments = () => {
    let filtered = [...judgments];

    // Apply search filter
    if (searchQuery) {
      filtered = filtered.filter(judgment =>
        (judgment.case_title && judgment.case_title.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (judgment.case_number && judgment.case_number.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (judgment.petitioner && judgment.petitioner.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (judgment.respondent && judgment.respondent.toLowerCase().includes(searchQuery.toLowerCase()))
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
        (judgment.case_title && judgment.case_title.toLowerCase().includes(courtFilter.toLowerCase()))
      );
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let comparison = 0;
      
      switch (sortBy) {
        case 'date':
          const dateA = a.judgment_date ? new Date(a.judgment_date).getTime() : 0;
          const dateB = b.judgment_date ? new Date(b.judgment_date).getTime() : 0;
          comparison = dateA - dateB;
          break;
        case 'title':
          comparison = (a.case_title || '').localeCompare(b.case_title || '');
          break;
        case 'case_number':
          comparison = (a.case_number || '').localeCompare(b.case_number || '');
          break;
      }
      
      return sortOrder === 'asc' ? comparison : -comparison;
    });

    setFilteredJudgments(filtered);
  };

  const extractMetadata = (judgment: Judgment): JudgmentMetadata => {
    return {
      party1: judgment.petitioner || 'Unknown Petitioner',
      party2: judgment.respondent || 'Unknown Respondent',
      judgment_date: judgment.judgment_date || 'Unknown Date',
      case_number: judgment.case_number || 'Unknown Case Number',
      court: 'Supreme Court' // Default for now
    };
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

  const handleSort = (field: 'date' | 'title' | 'case_number') => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
  };

  const handleViewJudgment = useCallback((judgment: Judgment) => {
    // Make this non-blocking by using async immediately
    const viewJudgmentAsync = async () => {
      try {
        // Get the PDF file from the backend
        const token = localStorage.getItem('access_token');
        const response = await fetch(API_CONFIG.getApiUrl(`/api/judgments/${judgment.id}/view`), {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (response.ok) {
          // Get the PDF blob
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          
          // Open in new tab
          const newWindow = window.open(url, '_blank');
          if (!newWindow) {
            toast.error('Please allow popups to view PDFs');
          } else {
            toast.success(`Opening ${judgment.case_title}`);
          }
          
          // Clean up the URL after a delay
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
    
    // Start async operation without blocking UI thread
    setTimeout(() => viewJudgmentAsync(), 0);
  }, []);

  const handleDownloadJudgment = useCallback((judgment: Judgment) => {
    // Make this non-blocking by using async immediately
    const downloadJudgmentAsync = async () => {
      try {
        // Get the PDF file from the backend
        const token = localStorage.getItem('access_token');
        const response = await fetch(API_CONFIG.getApiUrl(`/api/judgments/${judgment.id}/download`), {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (response.ok) {
          // Get the PDF blob
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          
          // Create download link
          const link = document.createElement('a');
          link.href = url;
          link.download = `${judgment.case_title || judgment.filename || 'judgment'}.pdf`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          
          // Clean up the URL
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
    
    // Start async operation without blocking UI thread
    setTimeout(() => downloadJudgmentAsync(), 0);
  }, []);

  const handleViewText = useCallback((judgment: Judgment) => {
    // Make this non-blocking by using async immediately
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
        
        // Create a new window/tab to display the text
        const textWindow = window.open('', '_blank', 'width=800,height=600,scrollbars=yes');
        if (textWindow) {
          textWindow.document.write(`
            <html>
              <head>
                <title>${judgment.case_title} - Full Text</title>
                <style>
                  body { 
                    font-family: Arial, sans-serif; 
                    line-height: 1.6; 
                    margin: 20px; 
                    background-color: #f9f9f9;
                  }
                  .header { 
                    background: white; 
                    padding: 20px; 
                    border-radius: 8px; 
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    margin-bottom: 20px;
                  }
                  .content { 
                    background: white; 
                    padding: 20px; 
                    border-radius: 8px; 
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    white-space: pre-wrap;
                    font-size: 14px;
                  }
                  .meta { 
                    color: #666; 
                    font-size: 12px; 
                    margin-bottom: 10px;
                  }
                </style>
              </head>
              <body>
                <div class="header">
                  <h1>${judgment.case_title}</h1>
                  <div class="meta">
                    <strong>File:</strong> ${data.filename} | 
                    <strong>Text Length:</strong> ${data.text_length.toLocaleString()} characters | 
                    <strong>Pages:</strong> ${data.page_count}
                  </div>
                </div>
                <div class="content">${data.full_text}</div>
              </body>
            </html>
          `);
          textWindow.document.close();
        }
        
        toast.success(`Opened full text for ${judgment.case_title}`);
      } else {
        toast.error('Failed to load judgment text');
      }
    } catch (error) {
      console.error('View text error:', error);
      toast.error('Failed to load judgment text');
    }
    };
    
    // Start async operation without blocking UI thread
    setTimeout(() => viewTextAsync(), 0);
  }, []);

  const handleViewTimeline = useCallback((judgment: Judgment) => {
    // Make this non-blocking by using async immediately
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
        
        // Create timeline HTML
        const timelineHtml = data.timeline_events.map((event: any) => `
          <div class="timeline-event">
            <div class="event-header">
              <span class="event-date">${event.event_date || 'Date not specified'}</span>
              <span class="event-type ${event.event_type}">${event.event_type.toUpperCase()}</span>
            </div>
            <div class="event-description">${event.event_description}</div>
            ${event.parties_involved ? `<div class="event-parties"><strong>Parties:</strong> ${event.parties_involved.join(', ')}</div>` : ''}
            ${event.court_involved ? `<div class="event-court"><strong>Court:</strong> ${event.court_involved}</div>` : ''}
            <div class="event-meta">
              <span class="confidence">Confidence: ${event.confidence_score}%</span>
              <span class="significance">Significance: ${event.legal_significance}</span>
            </div>
          </div>
        `).join('');
        
        // Create a new window/tab to display the timeline
        const timelineWindow = window.open('', '_blank', 'width=900,height=700,scrollbars=yes');
        if (timelineWindow) {
          timelineWindow.document.write(`
            <html>
              <head>
                <title>${judgment.case_title} - Timeline</title>
                <style>
                  body { 
                    font-family: Arial, sans-serif; 
                    line-height: 1.6; 
                    margin: 20px; 
                    background-color: #f9f9f9;
                  }
                  .header { 
                    background: white; 
                    padding: 20px; 
                    border-radius: 8px; 
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    margin-bottom: 20px;
                  }
                  .timeline-container { 
                    background: white; 
                    padding: 20px; 
                    border-radius: 8px; 
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                  }
                  .timeline-event {
                    border-left: 3px solid #3b82f6;
                    padding-left: 20px;
                    margin-bottom: 20px;
                    position: relative;
                  }
                  .timeline-event::before {
                    content: '';
                    position: absolute;
                    left: -6px;
                    top: 0;
                    width: 10px;
                    height: 10px;
                    background: #3b82f6;
                    border-radius: 50%;
                  }
                  .event-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 10px;
                  }
                  .event-date {
                    font-weight: bold;
                    color: #1f2937;
                  }
                  .event-type {
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: bold;
                    text-transform: uppercase;
                  }
                  .event-type.judgment { background: #dcfce7; color: #166534; }
                  .event-type.hearing { background: #dbeafe; color: #1e40af; }
                  .event-type.filing { background: #fef3c7; color: #92400e; }
                  .event-type.appeal { background: #fce7f3; color: #be185d; }
                  .event-type.order { background: #e0e7ff; color: #3730a3; }
                  .event-type.general { background: #f3f4f6; color: #374151; }
                  .event-description {
                    margin-bottom: 10px;
                    color: #374151;
                  }
                  .event-parties, .event-court {
                    font-size: 14px;
                    color: #6b7280;
                    margin-bottom: 5px;
                  }
                  .event-meta {
                    font-size: 12px;
                    color: #9ca3af;
                    display: flex;
                    gap: 15px;
                  }
                  .meta { 
                    color: #666; 
                    font-size: 12px; 
                    margin-bottom: 10px;
                  }
                </style>
              </head>
              <body>
                <div class="header">
                  <h1>${judgment.case_title} - Timeline</h1>
                  <div class="meta">
                    <strong>File:</strong> ${data.filename} | 
                    <strong>Total Events:</strong> ${data.total_events} | 
                    <strong>Extraction Status:</strong> ${data.extraction_status}
                  </div>
                </div>
                <div class="timeline-container">
                  ${timelineHtml}
                </div>
              </body>
            </html>
          `);
          timelineWindow.document.close();
        }
        
        toast.success(`Opened timeline for ${judgment.case_title}`);
      } else {
        toast.error('Failed to load judgment timeline');
      }
    } catch (error) {
      console.error('View timeline error:', error);
      toast.error('Failed to load judgment timeline');
    }
    };
    
    // Start async operation without blocking UI thread
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
                <div className="flex items-center space-x-2 bg-blue-50 px-4 py-2 rounded-full border border-blue-200">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <span className="text-sm font-medium text-blue-700">
                    {judgments.length} judgment{judgments.length !== 1 ? 's' : ''} available
                  </span>
                </div>
              </div>
            </div>
          </div>
        </header>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Search and Filter Bar */}
          <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-200/50 p-6 mb-8">
            <div className="flex flex-col lg:flex-row gap-4">
              {/* Search */}
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search judgments by title, case number, or parties..."
                    className="w-full pl-12 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white/80"
                  />
                </div>
              </div>

              {/* Sort and Filter Controls */}
              <div className="flex items-center space-x-3">
                {/* Sort Dropdown */}
                <div className="relative">
                  <select
                    value={`${sortBy}-${sortOrder}`}
                    onChange={(e) => {
                      const [field, order] = e.target.value.split('-');
                      setSortBy(field as 'date' | 'title' | 'case_number');
                      setSortOrder(order as 'asc' | 'desc');
                    }}
                    className="appearance-none bg-white border border-gray-200 rounded-xl px-4 py-3 pr-10 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="date-desc">Date (Newest First)</option>
                    <option value="date-asc">Date (Oldest First)</option>
                    <option value="title-asc">Title (A-Z)</option>
                    <option value="title-desc">Title (Z-A)</option>
                    <option value="case_number-asc">Case Number (A-Z)</option>
                    <option value="case_number-desc">Case Number (Z-A)</option>
                  </select>
                  <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                </div>

                {/* Filter Toggle */}
                <button
                  onClick={() => setShowFilters(!showFilters)}
                  className={`flex items-center px-4 py-3 rounded-xl border transition-all duration-200 ${
                    showFilters 
                      ? 'bg-blue-50 border-blue-200 text-blue-700' 
                      : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  <Filter className="w-4 h-4 mr-2" />
                  Filters
                  {showFilters ? (
                    <ChevronUp className="w-4 h-4 ml-2" />
                  ) : (
                    <ChevronDown className="w-4 h-4 ml-2" />
                  )}
                </button>
              </div>
            </div>

            {/* Advanced Filters */}
            {showFilters && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Year</label>
                    <select
                      value={dateFilter}
                      onChange={(e) => setDateFilter(e.target.value)}
                      className="w-full border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">All Years</option>
                      {getAvailableYears().map(year => (
                        <option key={year} value={year}>{year}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Court</label>
                    <select
                      value={courtFilter}
                      onChange={(e) => setCourtFilter(e.target.value)}
                      className="w-full border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">All Courts</option>
                      <option value="supreme">Supreme Court</option>
                      <option value="high">High Court</option>
                    </select>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Results Summary */}
          <div className="mb-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">
                {isLoading ? 'Loading judgments...' : `${filteredJudgments.length} judgment${filteredJudgments.length !== 1 ? 's' : ''} found`}
              </h2>
              {!isLoading && (
                <div className="text-sm text-gray-500">
                  Showing {filteredJudgments.length} of {judgments.length} judgments
                </div>
              )}
            </div>
          </div>

          {/* Judgments List */}
          <div className="space-y-4">
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-blue-600 mr-3" />
                <span className="text-gray-600">Loading judgments...</span>
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
                          <div className="w-14 h-14 bg-gradient-to-br from-amber-500 to-amber-600 rounded-2xl flex items-center justify-center shadow-lg">
                            <FileText className="w-7 h-7 text-white" />
                          </div>
                          <div>
                            <h3 className="text-white font-bold text-xl group-hover:text-amber-100 transition-colors">
                              {metadata.party1} vs {metadata.party2}
                            </h3>
                            <div className="flex items-center space-x-4 mt-2">
                              <div className="flex items-center text-slate-300 text-sm">
                                <Calendar className="w-4 h-4 mr-2" />
                                {formatDate(metadata.judgment_date)}
                              </div>
                              <div className="flex items-center text-slate-300 text-sm">
                                <FileText className="w-4 h-4 mr-2" />
                                {metadata.case_number}
                              </div>
                              <div className="flex items-center text-slate-300 text-sm">
                                <Users className="w-4 h-4 mr-2" />
                                {metadata.court}
                              </div>
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-slate-300 text-sm mb-1">Case ID: {judgment.id}</div>
                          {judgment.is_processed ? (
                            <div className="flex items-center space-x-1 bg-emerald-500/20 px-3 py-1 rounded-full border border-emerald-500/30">
                              <CheckCircle className="w-3 h-3 text-emerald-300" />
                              <span className="text-xs text-emerald-300 font-medium">Processed</span>
                            </div>
                          ) : (
                            <div className="flex items-center space-x-1 bg-amber-500/20 px-3 py-1 rounded-full border border-amber-500/30">
                              <Clock className="w-3 h-3 text-amber-300" />
                              <span className="text-xs text-amber-300 font-medium">Processing</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Content Section */}
                    <div className="p-6">
                      {/* Case Details Grid */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                        <div className="bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl p-4 border border-gray-200">
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

                      {/* Action Buttons - Professional Horizontal Layout */}
                      <div className="border-t border-gray-100 pt-5">
                        <div className="flex items-center justify-between">
                          <div className="text-sm text-gray-500 font-medium">
                            Available Actions
                          </div>
                          <div className="flex items-center space-x-3">
                            {/* Primary Actions */}
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

                    {/* Expandable AI Summary Section - Removed since AISummaryCard handles everything internally */}
                    {false && (
                      <div className="border-t border-gray-200 bg-gradient-to-r from-orange-50 to-amber-50">
                        <div className="p-6">
                          <div className="text-center text-gray-600">
                            <p>AI Summary content will be displayed here when expanded.</p>
                            <p className="text-sm mt-2">The AISummaryCard component handles both the button and the expanded content.</p>
                          </div>
                        </div>

                          {/* Loading State - Compact and Non-Blocking */}
                          {loadingSummariesRef.current.has(judgment.id) && (
                            <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                              <div className="flex items-center space-x-3">
                                <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />
                                <div className="flex-1">
                                  <p className="text-blue-800 font-medium text-sm">Generating AI Summary...</p>
                                  <div className="flex items-center space-x-2 mt-1">
                                    <div className="bg-blue-200 rounded-full h-1 flex-1 overflow-hidden">
                                      <div className="bg-blue-600 h-1 rounded-full animate-pulse" style={{ width: '65%' }}></div>
                                    </div>
                                    <span className="text-blue-600 text-xs">~12s</span>
                                  </div>
                                </div>
                              </div>
                              <p className="text-blue-600 text-xs mt-2">
                                💡 You can still use other features while this generates
                              </p>
                            </div>
                          )}

                          {/* Error State */}
                          {summaryErrorsRef.current[judgment.id] && (
                            <div className="p-4 bg-red-50 rounded-lg border border-red-200">
                              <div className="flex items-start space-x-3">
                                <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
                                <div className="flex-1">
                                  <h4 className="text-red-800 font-medium mb-1">Failed to Generate Summary</h4>
                                  <p className="text-red-600 text-sm mb-3">{summaryErrorsRef.current[judgment.id]}</p>
                                  <button
                                    onClick={() => retrySummary(judgment)}
                                    className="flex items-center space-x-2 px-3 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors text-sm"
                                  >
                                    <RefreshCw className="w-4 h-4" />
                                    <span>Retry</span>
                                  </button>
                                </div>
                              </div>
                            </div>
                          )}

                          {/* Summary Content */}
                          {summaryDataRef.current[judgment.id] && !loadingSummariesRef.current.has(judgment.id) && (
                            <div className="space-y-6">
                              {/* Summary Sections */}
                              {summaryDataRef.current[judgment.id].summary && (
                                <>
                                  {summaryDataRef.current[judgment.id].summary.facts && (
                                    <div className="bg-white rounded-lg p-4 border border-gray-200">
                                      <h4 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                                        <div className="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
                                        Facts
                                      </h4>
                                      <div className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                                        {summaryDataRef.current[judgment.id].summary.facts}
                                      </div>
                                    </div>
                                  )}

                                  {summaryDataRef.current[judgment.id].summary.issues && (
                                    <div className="bg-white rounded-lg p-4 border border-gray-200">
                                      <h4 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                                        <div className="w-2 h-2 bg-green-500 rounded-full mr-3"></div>
                                        Issues
                                      </h4>
                                      <div className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                                        {summaryDataRef.current[judgment.id].summary.issues}
                                      </div>
                                    </div>
                                  )}

                                  {summaryDataRef.current[judgment.id].summary.petitioner_arguments && (
                                    <div className="bg-white rounded-lg p-4 border border-gray-200">
                                      <h4 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                                        <div className="w-2 h-2 bg-purple-500 rounded-full mr-3"></div>
                                        Petitioner&apos;s Arguments
                                      </h4>
                                      <div className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                                        {summaryDataRef.current[judgment.id].summary.petitioner_arguments}
                                      </div>
                                    </div>
                                  )}

                                  {summaryDataRef.current[judgment.id].summary.respondent_arguments && (
                                    <div className="bg-white rounded-lg p-4 border border-gray-200">
                                      <h4 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                                        <div className="w-2 h-2 bg-indigo-500 rounded-full mr-3"></div>
                                        Respondent&apos;s Arguments
                                      </h4>
                                      <div className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                                        {summaryDataRef.current[judgment.id].summary.respondent_arguments}
                                      </div>
                                    </div>
                                  )}

                                  {summaryDataRef.current[judgment.id].summary.analysis_of_law && (
                                    <div className="bg-white rounded-lg p-4 border border-gray-200">
                                      <h4 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                                        <div className="w-2 h-2 bg-amber-500 rounded-full mr-3"></div>
                                        Analysis of the Law
                                      </h4>
                                      <div className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                                        {summaryDataRef.current[judgment.id].summary.analysis_of_law}
                                      </div>
                                    </div>
                                  )}

                                  {summaryDataRef.current[judgment.id].summary.precedent_analysis && (
                                    <div className="bg-white rounded-lg p-4 border border-gray-200">
                                      <h4 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                                        <div className="w-2 h-2 bg-teal-500 rounded-full mr-3"></div>
                                        Precedent Analysis
                                      </h4>
                                      <div className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                                        {summaryDataRef.current[judgment.id].summary.precedent_analysis}
                                      </div>
                                    </div>
                                  )}

                                  {summaryDataRef.current[judgment.id].summary.courts_reasoning && (
                                    <div className="bg-white rounded-lg p-4 border border-gray-200">
                                      <h4 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                                        <div className="w-2 h-2 bg-rose-500 rounded-full mr-3"></div>
                                        Court&apos;s Reasoning
                                      </h4>
                                      <div className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                                        {summaryDataRef.current[judgment.id].summary.courts_reasoning}
                                      </div>
                                    </div>
                                  )}

                                  {summaryDataRef.current[judgment.id].summary.conclusion && (
                                    <div className="bg-white rounded-lg p-4 border border-gray-200">
                                      <h4 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                                        <div className="w-2 h-2 bg-emerald-500 rounded-full mr-3"></div>
                                        Conclusion
                                      </h4>
                                      <div className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                                        {summaryDataRef.current[judgment.id].summary.conclusion}
                                      </div>
                                    </div>
                                  )}
                                </>
                              )}
                            </div>
                          )}
                        </div>
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
