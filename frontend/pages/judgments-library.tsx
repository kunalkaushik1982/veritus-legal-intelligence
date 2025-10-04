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
  Clock,
  Brain
} from 'lucide-react';
import toast from 'react-hot-toast';
import API_CONFIG from '../utils/config';

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
  extraction_status?: string;
  error?: string;
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
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'date' | 'title' | 'case_number'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [loading, setLoading] = useState(true);
  const [isGeneratingSummary, setIsGeneratingSummary] = useState<number | null>(null);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  // Extract metadata for display
  const extractMetadata = (judgment: Judgment): JudgmentMetadata => {
    // SIMPLE & ROBUST: Always use filename as the primary identifier
    // Filename is reliable, consistent, and always available
    const caseNumber = judgment.filename || `Case ${judgment.id}`;
    
    return {
      party1: judgment.petitioner || 'Unknown Petitioner',
      party2: judgment.respondent || 'Unknown Respondent',
      judgment_date: judgment.judgment_date || 'Date not available',
      case_number: caseNumber, // Always use filename - no complex logic needed
      court: 'Supreme Court of India'
    };
  };

  // Fetch judgments
  useEffect(() => {
    const fetchJudgments = async () => {
      try {
        const response = await fetch(API_CONFIG.getApiUrl('/api/judgments/'));
        if (response.ok) {
          const data = await response.json();
          setJudgments(data.judgments || []);
          setFilteredJudgments(data.judgments || []);
        } else {
          toast.error('Failed to load judgments');
        }
      } catch (error) {
        console.error('Error fetching judgments:', error);
        toast.error('Failed to load judgments');
      } finally {
        setLoading(false);
      }
    };

    fetchJudgments();
  }, []);

  // Filter and sort judgments
  useEffect(() => {
    // First filter based on search term
    let filtered = judgments;
    if (searchTerm) {
      filtered = judgments.filter(judgment => {
        const metadata = extractMetadata(judgment);
        const searchLower = searchTerm.toLowerCase();
        return (
          metadata.party1.toLowerCase().includes(searchLower) ||
          metadata.party2.toLowerCase().includes(searchLower) ||
          metadata.case_number.toLowerCase().includes(searchLower) ||
          (judgment.case_title && judgment.case_title.toLowerCase().includes(searchLower)) ||
          (judgment.filename && judgment.filename.toLowerCase().includes(searchLower))
        );
      });
    }

    // Then sort the filtered results
    const sorted = filtered.sort((a, b) => {
      let comparison = 0;
      
      switch (sortBy) {
        case 'date':
          const dateA = new Date(a.judgment_date || '').getTime();
          const dateB = new Date(b.judgment_date || '').getTime();
          comparison = dateA - dateB;
          break;
        case 'title':
          const titleA = a.case_title || '';
          const titleB = b.case_title || '';
          comparison = titleA.localeCompare(titleB);
          break;
        case 'case_number':
          const caseA = a.case_number || a.filename || '';
          const caseB = b.case_number || b.filename || '';
          comparison = caseA.localeCompare(caseB);
          break;
      }
      
      return sortOrder === 'asc' ? comparison : -comparison;
    });

    setFilteredJudgments(sorted);
    
    // Reset to first page when search term or sort changes
    setCurrentPage(1);
  }, [searchTerm, sortBy, sortOrder, judgments]);

  // Pagination logic
  const totalPages = Math.ceil(filteredJudgments.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentJudgments = filteredJudgments.slice(startIndex, endIndex);

  // Pagination handlers
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleItemsPerPageChange = (newItemsPerPage: number) => {
    setItemsPerPage(newItemsPerPage);
    setCurrentPage(1);
    // Save preference to localStorage
    localStorage.setItem('judgmentsItemsPerPage', newItemsPerPage.toString());
  };

  // Load items per page preference from localStorage
  useEffect(() => {
    const savedItemsPerPage = localStorage.getItem('judgmentsItemsPerPage');
    if (savedItemsPerPage) {
      setItemsPerPage(parseInt(savedItemsPerPage));
    }
  }, []);

  const formatDate = (dateString: string) => {
    if (!dateString) return 'Date not available';
    try {
      return new Date(dateString).toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    } catch {
      return dateString;
    }
  };

  const handleSummarizeCase = useCallback(async (judgment: Judgment) => {
    if (isGeneratingSummary === judgment.id) {
      toast('AI Summary is already generating for this judgment', {
        icon: 'ℹ️',
        duration: 2000,
      });
      return;
    }

    setIsGeneratingSummary(judgment.id);

    try {
      const response = await fetch(API_CONFIG.getApiUrl(`/api/summary/${judgment.id}`), {
        headers: {
          'Accept': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        const cacheStatus = data.from_cache ? 'cached' : 'AI generated';
        toast.success(`Summary loaded (${cacheStatus})`, { duration: 2000 });

        // Open summary in new window
        const summaryWindow = window.open('', '_blank', 'width=900,height=700,scrollbars=yes');
        if (summaryWindow) {
          const metadata = extractMetadata(judgment);
          summaryWindow.document.write(`
            <html>
              <head>
                <title>${judgment.case_title || 'Untitled Case'} - AI Summary</title>
                <style>
                  body { 
                    font-family: Arial, sans-serif; 
                    line-height: 1.6; 
                    margin: 20px; 
                    background: #f8fafc;
                  }
                  .header { 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px; 
                    border-radius: 12px; 
                    margin-bottom: 30px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                  }
                  .content { 
                    background: white;
                    padding: 30px;
                    border-radius: 12px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                  }
                  .section {
                    margin-bottom: 25px;
                    padding: 20px;
                    background: #f8fafc;
                    border-radius: 8px;
                    border-left: 4px solid #667eea;
                  }
                  .section h3 {
                    color: #2d3748;
                    margin-bottom: 15px;
                    font-size: 18px;
                  }
                  .section p, .section ul {
                    color: #4a5568;
                    margin: 0;
                  }
                  .cache-info {
                    background: #e6fffa;
                    border: 1px solid #81e6d9;
                    border-radius: 6px;
                    padding: 10px;
                    margin-bottom: 20px;
                    font-size: 14px;
                    color: #234e52;
                  }
                </style>
              </head>
              <body>
                <div class="header">
                  <h1>${judgment.case_title || 'Untitled Case'}</h1>
                  <p><strong>Case Number:</strong> ${metadata.case_number}</p>
                  <p><strong>Parties:</strong> ${metadata.party1} vs ${metadata.party2}</p>
                  <p><strong>Date:</strong> ${formatDate(judgment.judgment_date || '')}</p>
                </div>
                
                <div class="cache-info">
                  <strong>Summary Status:</strong> ${cacheStatus} | 
                  <strong>Model:</strong> ${data.model_used || 'N/A'} | 
                  <strong>Generated:</strong> ${new Date(data.generated_at).toLocaleString()}
                </div>
                
                <div class="content">
                  ${data.summary ? `
                    ${data.summary.facts ? `
                      <div class="section">
                        <h3>📋 Facts</h3>
                        <p>${data.summary.facts}</p>
                      </div>
                    ` : ''}
                    
                    ${data.summary.issues ? `
                      <div class="section">
                        <h3>⚖️ Legal Issues</h3>
                        <p>${data.summary.issues}</p>
                      </div>
                    ` : ''}
                    
                    ${data.summary.petitioner_arguments ? `
                      <div class="section">
                        <h3>👤 Petitioner's Arguments</h3>
                        <p>${data.summary.petitioner_arguments}</p>
                      </div>
                    ` : ''}
                    
                    ${data.summary.respondent_arguments ? `
                      <div class="section">
                        <h3>👥 Respondent's Arguments</h3>
                        <p>${data.summary.respondent_arguments}</p>
                      </div>
                    ` : ''}
                    
                    ${data.summary.court_reasoning ? `
                      <div class="section">
                        <h3>🏛️ Court's Reasoning</h3>
                        <p>${data.summary.court_reasoning}</p>
                      </div>
                    ` : ''}
                    
                    ${data.summary.decision ? `
                      <div class="section">
                        <h3>⚖️ Decision</h3>
                        <p>${data.summary.decision}</p>
                      </div>
                    ` : ''}
                    
                    ${data.summary.citations ? `
                      <div class="section">
                        <h3>📚 Citations</h3>
                        <ul>
                          ${data.summary.citations.map((citation: string) => `<li>${citation}</li>`).join('')}
                        </ul>
                      </div>
                    ` : ''}
                  ` : `
                    <div class="section">
                      <h3>⚠️ No Summary Available</h3>
                      <p>Summary data is not available for this judgment.</p>
                    </div>
                  `}
                  
                  ${data.raw_response ? `
                    <div class="section">
                      <h3>📄 Raw AI Response</h3>
                      <pre style="white-space: pre-wrap; background: #f7fafc; padding: 15px; border-radius: 6px; border: 1px solid #e2e8f0;">${data.raw_response}</pre>
                    </div>
                  ` : ''}
                </div>
              </body>
            </html>
          `);
          summaryWindow.document.close();
        }
      } else {
        const errorData = await response.json();
        const errorMessage = errorData.detail || 'Failed to load summary';
        
        // Handle specific quota error
        if (response.status === 503 || errorMessage.includes('quota') || errorMessage.includes('insufficient_quota')) {
          toast.error('🤖 AI service quota exceeded. Please try again later or contact support.', { duration: 6000 });
        } else {
          toast.error(`Failed to load summary: ${errorMessage}`);
        }
      }
    } catch (error) {
      console.error('Error loading summary:', error);
      toast.error('Failed to load case summary');
    } finally {
      setIsGeneratingSummary(null);
    }
  }, [isGeneratingSummary]);

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
          window.open(url, '_blank');
          toast.success(`Opened judgment ${judgment.id}`);
        } else {
          const errorData = await response.json().catch(() => ({}));
          toast.error(`Failed to view judgment: ${errorData.detail || 'Unknown error'}`);
        }
      } catch (error) {
        console.error('View judgment error:', error);
        toast.error('Failed to view judgment');
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
          a.download = judgment.filename || `judgment-${judgment.id}.pdf`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          window.URL.revokeObjectURL(url);
          toast.success(`Downloaded ${judgment.filename || 'judgment'}`);
        } else {
          const errorData = await response.json().catch(() => ({}));
          toast.error(`Failed to download judgment: ${errorData.detail || 'Unknown error'}`);
        }
      } catch (error) {
        console.error('Download judgment error:', error);
        toast.error('Failed to download judgment');
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
            const metadata = extractMetadata(judgment);
            textWindow.document.write(`
              <html>
                <head>
                  <title>${judgment.case_title || 'Untitled Case'} - Text</title>
                  <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }
                    .header { background: #f5f5f5; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
                    .content { white-space: pre-wrap; }
                  </style>
                </head>
                <body>
                  <div class="header">
                    <h1>${judgment.case_title || 'Untitled Case'}</h1>
                    <p><strong>Case Number:</strong> ${metadata.case_number}</p>
                    <p><strong>Date:</strong> ${formatDate(judgment.judgment_date || '')}</p>
                  </div>
                  <div class="content">${data.full_text || data.text || 'Text content not available'}</div>
                </body>
              </html>
            `);
            textWindow.document.close();
            toast.success(`Opened text for ${judgment.case_title || 'this case'}`);
          }
        } else {
          const errorData = await response.json().catch(() => ({}));
          toast.error(`Failed to load judgment text: ${errorData.detail || 'Unknown error'}`);
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
            const metadata = extractMetadata(judgment);
            timelineWindow.document.write(`
              <html>
                <head>
                  <title>${judgment.case_title || 'Untitled Case'} - Timeline</title>
                  <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }
                    .header { background: #f5f5f5; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
                    .timeline-event { border-left: 3px solid #3b82f6; padding-left: 20px; margin-bottom: 20px; }
                  </style>
                </head>
                <body>
                  <div class="header">
                    <h1>${judgment.case_title || 'Untitled Case'} - Timeline</h1>
                    <p><strong>Case Number:</strong> ${metadata.case_number}</p>
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
            toast.success(`Opened timeline for ${judgment.case_title || 'this case'}`);
          }
        } else {
          const errorData = await response.json().catch(() => ({}));
          toast.error(`Failed to load judgment timeline: ${errorData.detail || 'Unknown error'}`);
        }
      } catch (error) {
        console.error('View timeline error:', error);
        toast.error('Failed to load judgment timeline');
      }
    };
    
    setTimeout(() => viewTimelineAsync(), 0);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading judgments...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <Head>
        <title>Judgments Library - Veritus</title>
        <meta name="description" content="Browse and search Supreme Court judgments" />
      </Head>

      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-6">
              <div className="flex items-center">
                <button
                  onClick={() => router.back()}
                  className="mr-4 p-2 text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <ArrowLeft className="h-6 w-6" />
                </button>
                <div>
                  <h1 className="text-3xl font-bold text-gray-900">Judgments Library</h1>
                  <p className="text-gray-600 mt-1">
                    Browse and analyze Supreme Court judgments
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                  <BookOpen className="h-4 w-4" />
                  <span>{filteredJudgments.length} judgments</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Sticky Search and Filters */}
          <div className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm mb-6 -mx-4 sm:-mx-6 lg:-mx-8 px-4 sm:px-6 lg:px-8 py-4" style={{ position: 'sticky', top: '0px' }}>
            <div className="flex flex-col lg:flex-row gap-4">
              {/* Search */}
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
                  <input
                    type="text"
                    placeholder="Search judgments, parties, or case numbers..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              {/* Sort */}
              <div className="flex gap-2">
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="date">Date</option>
                  <option value="title">Title</option>
                  <option value="case_number">Case Number</option>
                </select>
                <button
                  onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                  className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  {sortOrder === 'asc' ? <SortAsc className="h-4 w-4" /> : <SortDesc className="h-4 w-4" />}
                </button>
              </div>
            </div>
            
            {/* Results Summary */}
            <div className="mt-3 text-sm text-gray-600">
              Showing {startIndex + 1}-{Math.min(endIndex, filteredJudgments.length)} of {filteredJudgments.length} judgments
              {searchTerm && ` matching "${searchTerm}"`}
            </div>
          </div>


          {/* Judgments List */}
          <div className="space-y-4">
            {filteredJudgments.length === 0 ? (
              <div className="text-center py-12">
                <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No judgments found</h3>
                <p className="text-gray-500">
                  {searchTerm ? 'Try adjusting your search terms' : 'No judgments available'}
                </p>
              </div>
            ) : (
              currentJudgments.map((judgment) => {
                const metadata = extractMetadata(judgment);
                return (
                  <div key={judgment.id} className="bg-white rounded-lg shadow-sm border p-6 hover:shadow-md transition-shadow">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <h3 className="text-lg font-semibold text-gray-900">
                            {judgment.case_title || 'Untitled Case'}
                          </h3>
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            {metadata.case_number || 'No Case Number'}
                          </span>
                        </div>
                        
                        <div className="flex items-center space-x-6 text-sm text-gray-600 mb-4">
                          <div className="flex items-center space-x-1">
                            <Users className="h-4 w-4" />
                            <span>{metadata.party1} vs {metadata.party2}</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <Calendar className="h-4 w-4" />
                            <span>{formatDate(judgment.judgment_date || '')}</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <Clock className="h-4 w-4" />
                            <span>{metadata.court}</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <FileText className="h-4 w-4" />
                            <span>{judgment.file_size ? `${(judgment.file_size / 1024).toFixed(1)} KB` : 'Unknown size'}</span>
                          </div>
                        </div>

                        {/* Processing Status Indicator */}
                        <div className="mb-4">
                          {judgment.is_processed ? (
                            <div className="flex items-center space-x-2">
                              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                              <span className="text-green-700 text-sm font-medium">
                                ✅ Successfully Processed ({judgment.extraction_status || 'completed'})
                              </span>
                            </div>
                          ) : (
                            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                              <div className="flex items-center">
                                <div className="w-2 h-2 bg-red-500 rounded-full mr-2"></div>
                                <span className="text-red-700 text-sm font-medium">
                                  ❌ Processing Failed: {judgment.extraction_status === 'failed' ? judgment.error || 'Could not process file' : 'File not processed'}
                                </span>
                              </div>
                            </div>
                          )}
                        </div>


                        <div className="flex flex-wrap gap-2">
                          <button
                            onClick={() => handleViewText(judgment)}
                            disabled={!judgment.is_processed}
                            className={`inline-flex items-center px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                              !judgment.is_processed
                                ? 'text-gray-400 bg-gray-100 cursor-not-allowed opacity-50'
                                : 'text-blue-700 bg-blue-100 hover:bg-blue-200'
                            }`}
                          >
                            <FileText className="h-4 w-4 mr-1" />
                            Text
                          </button>
                          
                          <button
                            onClick={() => handleViewTimeline(judgment)}
                            disabled={!judgment.is_processed}
                            className={`inline-flex items-center px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                              !judgment.is_processed
                                ? 'text-gray-400 bg-gray-100 cursor-not-allowed opacity-50'
                                : 'text-green-700 bg-green-100 hover:bg-green-200'
                            }`}
                          >
                            <Clock className="h-4 w-4 mr-1" />
                            Timeline
                          </button>
                          
                          <button
                            onClick={() => handleViewJudgment(judgment)}
                            disabled={!judgment.is_processed}
                            className={`inline-flex items-center px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                              !judgment.is_processed
                                ? 'text-gray-400 bg-gray-100 cursor-not-allowed opacity-50'
                                : 'text-purple-700 bg-purple-100 hover:bg-purple-200'
                            }`}
                          >
                            <Eye className="h-4 w-4 mr-1" />
                            View
                          </button>
                          
                          <button
                            onClick={() => handleDownloadJudgment(judgment)}
                            disabled={!judgment.is_processed}
                            className={`inline-flex items-center px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                              !judgment.is_processed
                                ? 'text-gray-400 bg-gray-100 cursor-not-allowed opacity-50'
                                : 'text-gray-700 bg-gray-100 hover:bg-gray-200'
                            }`}
                          >
                            <Download className="h-4 w-4 mr-1" />
                            Download
                          </button>
                          
                          <button
                            onClick={() => handleSummarizeCase(judgment)}
                            disabled={isGeneratingSummary === judgment.id || !judgment.is_processed}
                            className={`inline-flex items-center px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                              isGeneratingSummary === judgment.id
                                ? 'text-white bg-blue-500 opacity-75 cursor-not-allowed'
                                : !judgment.is_processed
                                ? 'text-gray-400 bg-gray-100 cursor-not-allowed opacity-50'
                                : 'text-orange-700 bg-orange-100 hover:bg-orange-200'
                            }`}
                          >
                            {isGeneratingSummary === judgment.id ? (
                              <>
                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-1"></div>
                                Generating...
                              </>
                            ) : (
                              <>
                                <Brain className="h-4 w-4 mr-1" />
                                AI Summary
                              </>
                            )}
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Pagination Controls */}
          {filteredJudgments.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm border p-6 mt-6">
              <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
                {/* Items per page selector */}
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <span>Show:</span>
                  <select
                    value={itemsPerPage}
                    onChange={(e) => handleItemsPerPageChange(parseInt(e.target.value))}
                    className="px-2 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value={10}>10</option>
                    <option value={50}>50</option>
                    <option value={100}>100</option>
                  </select>
                  <span>items per page</span>
                </div>

                {/* Page navigation */}
                {totalPages > 1 && (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handlePageChange(currentPage - 1)}
                      disabled={currentPage === 1}
                      className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Previous
                    </button>
                    
                    <div className="flex gap-1">
                      {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                        let pageNum;
                        if (totalPages <= 5) {
                          pageNum = i + 1;
                        } else if (currentPage <= 3) {
                          pageNum = i + 1;
                        } else if (currentPage >= totalPages - 2) {
                          pageNum = totalPages - 4 + i;
                        } else {
                          pageNum = currentPage - 2 + i;
                        }
                        
                        return (
                          <button
                            key={pageNum}
                            onClick={() => handlePageChange(pageNum)}
                            className={`px-3 py-2 border rounded-lg transition-colors ${
                              pageNum === currentPage
                                ? 'bg-blue-500 text-white border-blue-500'
                                : 'border-gray-300 hover:bg-gray-50'
                            }`}
                          >
                            {pageNum}
                          </button>
                        );
                      })}
                    </div>
                    
                    <button
                      onClick={() => handlePageChange(currentPage + 1)}
                      disabled={currentPage === totalPages}
                      className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Next
                    </button>
                  </div>
                )}

                {/* Page info */}
                <div className="text-sm text-gray-600">
                  Page {currentPage} of {totalPages}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}