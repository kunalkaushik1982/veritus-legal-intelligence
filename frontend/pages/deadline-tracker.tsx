import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { 
  Calendar,
  Clock,
  AlertTriangle,
  CheckCircle,
  Plus,
  Edit,
  Trash2,
  Filter,
  ChevronLeft,
  ChevronRight,
  MoreHorizontal,
  X,
  Save,
  User,
  Building,
  FileText
} from 'lucide-react';
import toast from 'react-hot-toast';
import API_CONFIG from '../utils/config';

interface Deadline {
  id: string;
  case_name: string;
  case_number: string;
  task_description: string;
  due_date: string;
  due_time: string;
  priority: 'urgent' | 'high' | 'medium' | 'low';
  status: 'pending' | 'in_progress' | 'completed' | 'overdue';
  assigned_to: string;
  court_name: string;
  case_type: 'civil' | 'criminal' | 'commercial' | 'family' | 'other';
  created_at: string;
  updated_at: string;
}

interface DeadlineStats {
  urgent: number;
  due_soon: number;
  upcoming: number;
  completed: number;
  overdue: number;
}

export default function DeadlineTracker() {
  const router = useRouter();
  const [deadlines, setDeadlines] = useState<Deadline[]>([]);
  const [stats, setStats] = useState<DeadlineStats>({
    urgent: 0,
    due_soon: 0,
    upcoming: 0,
    completed: 0,
    overdue: 0
  });
  const [isLoading, setIsLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(5);
  const [filter, setFilter] = useState<'all' | 'urgent' | 'due_soon' | 'upcoming' | 'completed' | 'overdue'>('all');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingDeadline, setEditingDeadline] = useState<Deadline | null>(null);
  const [user, setUser] = useState<any>(null);
  const [formData, setFormData] = useState({
    case_name: '',
    case_number: '',
    task_description: '',
    due_date: '',
    due_time: '',
    priority: 'medium' as 'urgent' | 'high' | 'medium' | 'low',
    assigned_to: '',
    court_name: '',
    case_type: 'civil' as 'civil' | 'criminal' | 'commercial' | 'family' | 'other'
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  // Sample data for demonstration
  const sampleDeadlines: Deadline[] = [
    {
      id: '1',
      case_name: 'State vs. Rajesh Kumar',
      case_number: 'Civil Appeal No. 1234/2024',
      task_description: 'File Written Statement',
      due_date: new Date().toISOString().split('T')[0],
      due_time: '14:00',
      priority: 'urgent',
      status: 'pending',
      assigned_to: 'John Doe',
      court_name: 'Supreme Court of India',
      case_type: 'civil',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    },
    {
      id: '2',
      case_name: 'Mohan Singh vs. Corporation',
      case_number: 'Writ Petition No. 5678/2024',
      task_description: 'Submit Documents',
      due_date: new Date().toISOString().split('T')[0],
      due_time: '17:00',
      priority: 'urgent',
      status: 'pending',
      assigned_to: 'Jane Smith',
      court_name: 'High Court of Delhi',
      case_type: 'commercial',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    },
    {
      id: '3',
      case_name: 'ABC Ltd vs. XYZ Corp',
      case_number: 'Commercial Suit No. 9012/2024',
      task_description: 'Appeal Filing',
      due_date: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      due_time: '10:00',
      priority: 'high',
      status: 'pending',
      assigned_to: 'Mike Johnson',
      court_name: 'District Court',
      case_type: 'commercial',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    },
    {
      id: '4',
      case_name: 'Family Dispute Case',
      case_number: 'Family Suit No. 3456/2024',
      task_description: 'Mediation Session',
      due_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      due_time: '15:00',
      priority: 'medium',
      status: 'pending',
      assigned_to: 'Sarah Wilson',
      court_name: 'Family Court',
      case_type: 'family',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    },
    {
      id: '5',
      case_name: 'Property Dispute Case',
      case_number: 'Property Suit No. 7890/2024',
      task_description: 'Submit Evidence',
      due_date: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      due_time: '11:00',
      priority: 'high',
      status: 'pending',
      assigned_to: 'David Brown',
      court_name: 'Civil Court',
      case_type: 'civil',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    },
    {
      id: '6',
      case_name: 'Criminal Appeal Case',
      case_number: 'Criminal Appeal No. 1111/2024',
      task_description: 'Submit Arguments',
      due_date: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      due_time: '09:00',
      priority: 'medium',
      status: 'pending',
      assigned_to: 'Lisa Davis',
      court_name: 'Sessions Court',
      case_type: 'criminal',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    },
    {
      id: '7',
      case_name: 'Tax Appeal Case',
      case_number: 'Tax Appeal No. 2222/2024',
      task_description: 'Filed Appeal',
      due_date: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      due_time: '14:00',
      priority: 'urgent',
      status: 'completed',
      assigned_to: 'Tom Wilson',
      court_name: 'Income Tax Appellate Tribunal',
      case_type: 'other',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    },
    {
      id: '8',
      case_name: 'Labour Dispute Case',
      case_number: 'Labour Case No. 3333/2024',
      task_description: 'Submitted Documents',
      due_date: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      due_time: '16:00',
      priority: 'high',
      status: 'completed',
      assigned_to: 'Emma Taylor',
      court_name: 'Labour Court',
      case_type: 'other',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }
  ];

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
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      router.push('/login');
      return;
    }

    // Load sample data
    setDeadlines(sampleDeadlines);
    calculateStats(sampleDeadlines);
    setIsLoading(false);
  }, [router]);

  const calculateStats = (deadlineList: Deadline[]) => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const tomorrow = new Date(today.getTime() + 24 * 60 * 60 * 1000);
    const weekFromNow = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000);

    const newStats = {
      urgent: 0,
      due_soon: 0,
      upcoming: 0,
      completed: 0,
      overdue: 0
    };

    deadlineList.forEach(deadline => {
      const deadlineDate = new Date(deadline.due_date);
      
      if (deadline.status === 'completed') {
        newStats.completed++;
      } else if (deadlineDate < today) {
        newStats.overdue++;
      } else if (deadline.priority === 'urgent' || deadlineDate <= today) {
        newStats.urgent++;
      } else if (deadlineDate <= tomorrow) {
        newStats.due_soon++;
      } else if (deadlineDate <= weekFromNow) {
        newStats.upcoming++;
      }
    });

    setStats(newStats);
  };

  const getFilteredDeadlines = () => {
    let filtered = deadlines;

    if (filter !== 'all') {
      const now = new Date();
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      const tomorrow = new Date(today.getTime() + 24 * 60 * 60 * 1000);
      const weekFromNow = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000);

      filtered = deadlines.filter(deadline => {
        const deadlineDate = new Date(deadline.due_date);
        
        switch (filter) {
          case 'urgent':
            return (deadline.priority === 'urgent' || deadlineDate <= today) && deadline.status !== 'completed';
          case 'due_soon':
            return deadlineDate <= tomorrow && deadlineDate > today && deadline.status !== 'completed';
          case 'upcoming':
            return deadlineDate <= weekFromNow && deadlineDate > tomorrow && deadline.status !== 'completed';
          case 'completed':
            return deadline.status === 'completed';
          case 'overdue':
            return deadlineDate < today && deadline.status !== 'completed';
          default:
            return true;
        }
      });
    }

    return filtered;
  };

  const getPaginatedDeadlines = () => {
    const filtered = getFilteredDeadlines();
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    return filtered.slice(startIndex, endIndex);
  };

  const getTotalPages = () => {
    const filtered = getFilteredDeadlines();
    return Math.ceil(filtered.length / itemsPerPage);
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleItemsPerPageChange = (newItemsPerPage: number) => {
    setItemsPerPage(newItemsPerPage);
    setCurrentPage(1);
    localStorage.setItem('deadlineItemsPerPage', newItemsPerPage.toString());
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return 'from-red-500 to-red-600';
      case 'high':
        return 'from-orange-500 to-orange-600';
      case 'medium':
        return 'from-yellow-500 to-yellow-600';
      case 'low':
        return 'from-green-500 to-green-600';
      default:
        return 'from-gray-500 to-gray-600';
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return '🚨';
      case 'high':
        return '⚠️';
      case 'medium':
        return '📅';
      case 'low':
        return '✅';
      default:
        return '📋';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'overdue':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const formatTimeRemaining = (deadline: Deadline) => {
    const now = new Date();
    const deadlineDateTime = new Date(`${deadline.due_date}T${deadline.due_time}`);
    const diffMs = deadlineDateTime.getTime() - now.getTime();
    
    if (diffMs < 0) {
      const hoursPast = Math.abs(Math.floor(diffMs / (1000 * 60 * 60)));
      return `${hoursPast}h overdue`;
    }
    
    const hours = Math.floor(diffMs / (1000 * 60 * 60));
    const days = Math.floor(hours / 24);
    
    if (days > 0) {
      return `${days}d remaining`;
    } else if (hours > 0) {
      return `${hours}h remaining`;
    } else {
      const minutes = Math.floor(diffMs / (1000 * 60));
      return `${minutes}m remaining`;
    }
  };

  const validateForm = () => {
    const errors: Record<string, string> = {};

    if (!formData.case_name.trim()) {
      errors.case_name = 'Case name is required';
    }
    if (!formData.case_number.trim()) {
      errors.case_number = 'Case number is required';
    }
    if (!formData.task_description.trim()) {
      errors.task_description = 'Task description is required';
    }
    if (!formData.due_date) {
      errors.due_date = 'Due date is required';
    }
    if (!formData.due_time) {
      errors.due_time = 'Due time is required';
    }
    if (!formData.assigned_to.trim()) {
      errors.assigned_to = 'Assigned to is required';
    }
    if (!formData.court_name.trim()) {
      errors.court_name = 'Court name is required';
    }

    // Check if due date is in the past
    if (formData.due_date) {
      const dueDate = new Date(formData.due_date);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      
      if (dueDate < today) {
        errors.due_date = 'Due date cannot be in the past';
      }
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const resetForm = () => {
    setFormData({
      case_name: '',
      case_number: '',
      task_description: '',
      due_date: '',
      due_time: '',
      priority: 'medium',
      assigned_to: '',
      court_name: '',
      case_type: 'civil'
    });
    setFormErrors({});
  };

  const handleAddDeadline = () => {
    if (!validateForm()) {
      toast.error('Please fix the form errors');
      return;
    }

    const newDeadline: Deadline = {
      id: Date.now().toString(),
      ...formData,
      status: 'pending',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    const updatedDeadlines = [...deadlines, newDeadline];
    setDeadlines(updatedDeadlines);
    calculateStats(updatedDeadlines);
    
    resetForm();
    setShowAddModal(false);
    toast.success('Deadline added successfully!');
  };

  const handleEditDeadline = () => {
    if (!editingDeadline || !validateForm()) {
      toast.error('Please fix the form errors');
      return;
    }

    const updatedDeadlines = deadlines.map(d => 
      d.id === editingDeadline.id 
        ? { ...d, ...formData, updated_at: new Date().toISOString() }
        : d
    );

    setDeadlines(updatedDeadlines);
    calculateStats(updatedDeadlines);
    
    resetForm();
    setShowEditModal(false);
    setEditingDeadline(null);
    toast.success('Deadline updated successfully!');
  };

  const openEditModal = (deadline: Deadline) => {
    setEditingDeadline(deadline);
    setFormData({
      case_name: deadline.case_name,
      case_number: deadline.case_number,
      task_description: deadline.task_description,
      due_date: deadline.due_date,
      due_time: deadline.due_time,
      priority: deadline.priority,
      assigned_to: deadline.assigned_to,
      court_name: deadline.court_name,
      case_type: deadline.case_type
    });
    setFormErrors({});
    setShowEditModal(true);
  };

  const closeModals = () => {
    setShowAddModal(false);
    setShowEditModal(false);
    setEditingDeadline(null);
    resetForm();
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const filteredDeadlines = getFilteredDeadlines();
  const paginatedDeadlines = getPaginatedDeadlines();
  const totalPages = getTotalPages();

  return (
    <>
      <Head>
        <title>Deadline Tracker - Veritus</title>
        <meta name="description" content="Legal deadline management system" />
      </Head>

      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center">
                <button
                  onClick={() => router.push('/dashboard')}
                  className="text-gray-600 hover:text-gray-900 mr-4"
                >
                  ← Back to Dashboard
                </button>
                <h1 className="text-2xl font-bold text-gray-900">Deadline Tracker</h1>
                <span className="ml-4 text-sm text-gray-500">Legal deadline management</span>
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-sm text-gray-700">
                  Welcome, {user.full_name}
                </div>
              </div>
            </div>
          </div>
        </header>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-gradient-to-r from-red-500 to-red-600 text-white rounded-xl p-6 shadow-lg">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-3xl font-bold">{stats.urgent}</div>
                  <div className="text-red-100">Urgent Today</div>
                  <div className="text-xs text-red-200 mt-1">Next: 2 hours</div>
                </div>
                <div className="text-4xl opacity-80">🚨</div>
              </div>
            </div>

            <div className="bg-gradient-to-r from-orange-500 to-orange-600 text-white rounded-xl p-6 shadow-lg">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-3xl font-bold">{stats.due_soon}</div>
                  <div className="text-orange-100">Due Soon</div>
                  <div className="text-xs text-orange-200 mt-1">Next: Tomorrow</div>
                </div>
                <div className="text-4xl opacity-80">⚠️</div>
              </div>
            </div>

            <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl p-6 shadow-lg">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-3xl font-bold">{stats.upcoming}</div>
                  <div className="text-blue-100">Upcoming</div>
                  <div className="text-xs text-blue-200 mt-1">Next: Oct 15</div>
                </div>
                <div className="text-4xl opacity-80">📅</div>
              </div>
            </div>

            <div className="bg-gradient-to-r from-green-500 to-green-600 text-white rounded-xl p-6 shadow-lg">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-3xl font-bold">{stats.completed}</div>
                  <div className="text-green-100">Completed</div>
                  <div className="text-xs text-green-200 mt-1">This month</div>
                </div>
                <div className="text-4xl opacity-80">✅</div>
              </div>
            </div>
          </div>

          {/* Filters and Controls */}
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
              <div className="flex flex-wrap gap-2">
                {[
                  { key: 'all', label: 'All Deadlines', count: deadlines.length },
                  { key: 'urgent', label: 'Urgent', count: stats.urgent },
                  { key: 'due_soon', label: 'Due Soon', count: stats.due_soon },
                  { key: 'upcoming', label: 'Upcoming', count: stats.upcoming },
                  { key: 'completed', label: 'Completed', count: stats.completed },
                  { key: 'overdue', label: 'Overdue', count: stats.overdue }
                ].map((filterOption) => (
                  <button
                    key={filterOption.key}
                    onClick={() => {
                      setFilter(filterOption.key as any);
                      setCurrentPage(1);
                    }}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      filter === filterOption.key
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {filterOption.label} ({filterOption.count})
                  </button>
                ))}
              </div>

              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">Show:</span>
                  <select
                    value={itemsPerPage}
                    onChange={(e) => handleItemsPerPageChange(Number(e.target.value))}
                    className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value={5}>5</option>
                    <option value={10}>10</option>
                    <option value={20}>20</option>
                  </select>
                </div>

                <button
                  onClick={() => setShowAddModal(true)}
                  className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Add Deadline
                </button>
              </div>
            </div>
          </div>

          {/* Deadlines List */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold text-gray-900">
                {filter === 'all' ? 'All Deadlines' : 
                 filter === 'urgent' ? 'Urgent Deadlines' :
                 filter === 'due_soon' ? 'Due Soon' :
                 filter === 'upcoming' ? 'Upcoming Deadlines' :
                 filter === 'completed' ? 'Completed Deadlines' :
                 'Overdue Deadlines'}
              </h2>
              <div className="text-sm text-gray-600">
                Showing {((currentPage - 1) * itemsPerPage) + 1}-{Math.min(currentPage * itemsPerPage, filteredDeadlines.length)} of {filteredDeadlines.length}
              </div>
            </div>

            {isLoading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p className="text-gray-500 mt-2">Loading deadlines...</p>
              </div>
            ) : paginatedDeadlines.length === 0 ? (
              <div className="text-center py-12">
                <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500 text-lg">No deadlines found</p>
                <p className="text-gray-400 text-sm">Try adjusting your filters or add a new deadline</p>
              </div>
            ) : (
              <div className="space-y-4">
                {paginatedDeadlines.map((deadline) => (
                  <div
                    key={deadline.id}
                    className={`border-l-4 rounded-lg p-6 transition-all hover:shadow-md ${
                      deadline.priority === 'urgent' ? 'border-red-500 bg-red-50' :
                      deadline.priority === 'high' ? 'border-orange-500 bg-orange-50' :
                      deadline.priority === 'medium' ? 'border-yellow-500 bg-yellow-50' :
                      'border-green-500 bg-green-50'
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="text-2xl">{getPriorityIcon(deadline.priority)}</span>
                          <h3 className="text-lg font-semibold text-gray-900">{deadline.case_name}</h3>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(deadline.status)}`}>
                            {deadline.status.replace('_', ' ')}
                          </span>
                        </div>
                        
                        <div className="text-sm text-gray-600 mb-2">
                          <div className="flex items-center gap-4">
                            <span>{deadline.case_number}</span>
                            <span>•</span>
                            <span>{deadline.task_description}</span>
                            <span>•</span>
                            <span>{deadline.court_name}</span>
                          </div>
                        </div>

                        <div className="flex items-center gap-6 text-sm">
                          <div className="flex items-center gap-1">
                            <Clock className="w-4 h-4 text-gray-400" />
                            <span className="text-gray-600">
                              {new Date(deadline.due_date).toLocaleDateString()} at {deadline.due_time}
                            </span>
                          </div>
                          <div className="flex items-center gap-1">
                            <span className="text-gray-600">Assigned to:</span>
                            <span className="font-medium">{deadline.assigned_to}</span>
                          </div>
                          <div className={`font-medium ${
                            deadline.priority === 'urgent' ? 'text-red-600' :
                            deadline.priority === 'high' ? 'text-orange-600' :
                            deadline.priority === 'medium' ? 'text-yellow-600' :
                            'text-green-600'
                          }`}>
                            {formatTimeRemaining(deadline)}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 ml-4">
                        <button
                          onClick={() => {
                            // Mark as completed
                            const updatedDeadlines = deadlines.map(d => 
                              d.id === deadline.id ? { ...d, status: 'completed' as any } : d
                            );
                            setDeadlines(updatedDeadlines);
                            calculateStats(updatedDeadlines);
                            toast.success('Deadline marked as completed!');
                          }}
                          className="p-2 text-green-600 hover:bg-green-100 rounded-lg transition-colors"
                          title="Mark as completed"
                        >
                          <CheckCircle className="w-5 h-5" />
                        </button>
                        <button
                          onClick={() => openEditModal(deadline)}
                          className="p-2 text-blue-600 hover:bg-blue-100 rounded-lg transition-colors"
                          title="Edit deadline"
                        >
                          <Edit className="w-5 h-5" />
                        </button>
                        <button
                          onClick={() => {
                            // Delete deadline
                            if (confirm('Are you sure you want to delete this deadline?')) {
                              const updatedDeadlines = deadlines.filter(d => d.id !== deadline.id);
                              setDeadlines(updatedDeadlines);
                              calculateStats(updatedDeadlines);
                              toast.success('Deadline deleted!');
                            }
                          }}
                          className="p-2 text-red-600 hover:bg-red-100 rounded-lg transition-colors"
                          title="Delete deadline"
                        >
                          <Trash2 className="w-5 h-5" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex justify-between items-center mt-8 pt-6 border-t border-gray-200">
                <div className="text-sm text-gray-600">
                  Page {currentPage} of {totalPages}
                </div>
                
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                    className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronLeft className="w-4 h-4 mr-1" />
                    Previous
                  </button>
                  
                  {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                    <button
                      key={page}
                      onClick={() => handlePageChange(page)}
                      className={`px-3 py-2 text-sm font-medium rounded-lg ${
                        page === currentPage
                          ? 'bg-blue-600 text-white'
                          : 'text-gray-700 bg-white border border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      {page}
                    </button>
                  ))}
                  
                  <button
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                    className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                    <ChevronRight className="w-4 h-4 ml-1" />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Add Deadline Modal */}
        {showAddModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between p-6 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900 flex items-center">
                  <Plus className="w-5 h-5 mr-2" />
                  Add New Deadline
                </h2>
                <button
                  onClick={closeModals}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Case Name */}
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <FileText className="w-4 h-4 inline mr-1" />
                      Case Name *
                    </label>
                    <input
                      type="text"
                      value={formData.case_name}
                      onChange={(e) => setFormData({ ...formData, case_name: e.target.value })}
                      className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                        formErrors.case_name ? 'border-red-500' : 'border-gray-300'
                      }`}
                      placeholder="e.g., State vs. John Doe"
                    />
                    {formErrors.case_name && (
                      <p className="text-red-500 text-sm mt-1">{formErrors.case_name}</p>
                    )}
                  </div>

                  {/* Case Number */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Case Number *
                    </label>
                    <input
                      type="text"
                      value={formData.case_number}
                      onChange={(e) => setFormData({ ...formData, case_number: e.target.value })}
                      className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                        formErrors.case_number ? 'border-red-500' : 'border-gray-300'
                      }`}
                      placeholder="e.g., Civil Appeal No. 1234/2024"
                    />
                    {formErrors.case_number && (
                      <p className="text-red-500 text-sm mt-1">{formErrors.case_number}</p>
                    )}
                  </div>

                  {/* Case Type */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Case Type
                    </label>
                    <select
                      value={formData.case_type}
                      onChange={(e) => setFormData({ ...formData, case_type: e.target.value as any })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="civil">Civil</option>
                      <option value="criminal">Criminal</option>
                      <option value="commercial">Commercial</option>
                      <option value="family">Family</option>
                      <option value="other">Other</option>
                    </select>
                  </div>

                  {/* Task Description */}
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Task Description *
                    </label>
                    <input
                      type="text"
                      value={formData.task_description}
                      onChange={(e) => setFormData({ ...formData, task_description: e.target.value })}
                      className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                        formErrors.task_description ? 'border-red-500' : 'border-gray-300'
                      }`}
                      placeholder="e.g., File Written Statement, Submit Documents"
                    />
                    {formErrors.task_description && (
                      <p className="text-red-500 text-sm mt-1">{formErrors.task_description}</p>
                    )}
                  </div>

                  {/* Due Date */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <Calendar className="w-4 h-4 inline mr-1" />
                      Due Date *
                    </label>
                    <input
                      type="date"
                      value={formData.due_date}
                      onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                      className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                        formErrors.due_date ? 'border-red-500' : 'border-gray-300'
                      }`}
                      min={new Date().toISOString().split('T')[0]}
                    />
                    {formErrors.due_date && (
                      <p className="text-red-500 text-sm mt-1">{formErrors.due_date}</p>
                    )}
                  </div>

                  {/* Due Time */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <Clock className="w-4 h-4 inline mr-1" />
                      Due Time *
                    </label>
                    <input
                      type="time"
                      value={formData.due_time}
                      onChange={(e) => setFormData({ ...formData, due_time: e.target.value })}
                      className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                        formErrors.due_time ? 'border-red-500' : 'border-gray-300'
                      }`}
                    />
                    {formErrors.due_time && (
                      <p className="text-red-500 text-sm mt-1">{formErrors.due_time}</p>
                    )}
                  </div>

                  {/* Priority */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <AlertTriangle className="w-4 h-4 inline mr-1" />
                      Priority
                    </label>
                    <select
                      value={formData.priority}
                      onChange={(e) => setFormData({ ...formData, priority: e.target.value as any })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                      <option value="urgent">Urgent</option>
                    </select>
                  </div>

                  {/* Assigned To */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <User className="w-4 h-4 inline mr-1" />
                      Assigned To *
                    </label>
                    <input
                      type="text"
                      value={formData.assigned_to}
                      onChange={(e) => setFormData({ ...formData, assigned_to: e.target.value })}
                      className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                        formErrors.assigned_to ? 'border-red-500' : 'border-gray-300'
                      }`}
                      placeholder="e.g., John Doe, Jane Smith"
                    />
                    {formErrors.assigned_to && (
                      <p className="text-red-500 text-sm mt-1">{formErrors.assigned_to}</p>
                    )}
                  </div>

                  {/* Court Name */}
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <Building className="w-4 h-4 inline mr-1" />
                      Court Name *
                    </label>
                    <input
                      type="text"
                      value={formData.court_name}
                      onChange={(e) => setFormData({ ...formData, court_name: e.target.value })}
                      className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                        formErrors.court_name ? 'border-red-500' : 'border-gray-300'
                      }`}
                      placeholder="e.g., Supreme Court of India, High Court of Delhi"
                    />
                    {formErrors.court_name && (
                      <p className="text-red-500 text-sm mt-1">{formErrors.court_name}</p>
                    )}
                  </div>
                </div>

                <div className="flex justify-end gap-3 mt-6 pt-6 border-t border-gray-200">
                  <button
                    onClick={closeModals}
                    className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleAddDeadline}
                    className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <Save className="w-4 h-4 mr-2" />
                    Add Deadline
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Edit Deadline Modal */}
        {showEditModal && editingDeadline && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between p-6 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900 flex items-center">
                  <Edit className="w-5 h-5 mr-2" />
                  Edit Deadline
                </h2>
                <button
                  onClick={closeModals}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Case Name */}
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <FileText className="w-4 h-4 inline mr-1" />
                      Case Name *
                    </label>
                    <input
                      type="text"
                      value={formData.case_name}
                      onChange={(e) => setFormData({ ...formData, case_name: e.target.value })}
                      className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                        formErrors.case_name ? 'border-red-500' : 'border-gray-300'
                      }`}
                      placeholder="e.g., State vs. John Doe"
                    />
                    {formErrors.case_name && (
                      <p className="text-red-500 text-sm mt-1">{formErrors.case_name}</p>
                    )}
                  </div>

                  {/* Case Number */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Case Number *
                    </label>
                    <input
                      type="text"
                      value={formData.case_number}
                      onChange={(e) => setFormData({ ...formData, case_number: e.target.value })}
                      className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                        formErrors.case_number ? 'border-red-500' : 'border-gray-300'
                      }`}
                      placeholder="e.g., Civil Appeal No. 1234/2024"
                    />
                    {formErrors.case_number && (
                      <p className="text-red-500 text-sm mt-1">{formErrors.case_number}</p>
                    )}
                  </div>

                  {/* Case Type */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Case Type
                    </label>
                    <select
                      value={formData.case_type}
                      onChange={(e) => setFormData({ ...formData, case_type: e.target.value as any })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="civil">Civil</option>
                      <option value="criminal">Criminal</option>
                      <option value="commercial">Commercial</option>
                      <option value="family">Family</option>
                      <option value="other">Other</option>
                    </select>
                  </div>

                  {/* Task Description */}
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Task Description *
                    </label>
                    <input
                      type="text"
                      value={formData.task_description}
                      onChange={(e) => setFormData({ ...formData, task_description: e.target.value })}
                      className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                        formErrors.task_description ? 'border-red-500' : 'border-gray-300'
                      }`}
                      placeholder="e.g., File Written Statement, Submit Documents"
                    />
                    {formErrors.task_description && (
                      <p className="text-red-500 text-sm mt-1">{formErrors.task_description}</p>
                    )}
                  </div>

                  {/* Due Date */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <Calendar className="w-4 h-4 inline mr-1" />
                      Due Date *
                    </label>
                    <input
                      type="date"
                      value={formData.due_date}
                      onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                      className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                        formErrors.due_date ? 'border-red-500' : 'border-gray-300'
                      }`}
                    />
                    {formErrors.due_date && (
                      <p className="text-red-500 text-sm mt-1">{formErrors.due_date}</p>
                    )}
                  </div>

                  {/* Due Time */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <Clock className="w-4 h-4 inline mr-1" />
                      Due Time *
                    </label>
                    <input
                      type="time"
                      value={formData.due_time}
                      onChange={(e) => setFormData({ ...formData, due_time: e.target.value })}
                      className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                        formErrors.due_time ? 'border-red-500' : 'border-gray-300'
                      }`}
                    />
                    {formErrors.due_time && (
                      <p className="text-red-500 text-sm mt-1">{formErrors.due_time}</p>
                    )}
                  </div>

                  {/* Priority */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <AlertTriangle className="w-4 h-4 inline mr-1" />
                      Priority
                    </label>
                    <select
                      value={formData.priority}
                      onChange={(e) => setFormData({ ...formData, priority: e.target.value as any })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                      <option value="urgent">Urgent</option>
                    </select>
                  </div>

                  {/* Assigned To */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <User className="w-4 h-4 inline mr-1" />
                      Assigned To *
                    </label>
                    <input
                      type="text"
                      value={formData.assigned_to}
                      onChange={(e) => setFormData({ ...formData, assigned_to: e.target.value })}
                      className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                        formErrors.assigned_to ? 'border-red-500' : 'border-gray-300'
                      }`}
                      placeholder="e.g., John Doe, Jane Smith"
                    />
                    {formErrors.assigned_to && (
                      <p className="text-red-500 text-sm mt-1">{formErrors.assigned_to}</p>
                    )}
                  </div>

                  {/* Court Name */}
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <Building className="w-4 h-4 inline mr-1" />
                      Court Name *
                    </label>
                    <input
                      type="text"
                      value={formData.court_name}
                      onChange={(e) => setFormData({ ...formData, court_name: e.target.value })}
                      className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                        formErrors.court_name ? 'border-red-500' : 'border-gray-300'
                      }`}
                      placeholder="e.g., Supreme Court of India, High Court of Delhi"
                    />
                    {formErrors.court_name && (
                      <p className="text-red-500 text-sm mt-1">{formErrors.court_name}</p>
                    )}
                  </div>
                </div>

                <div className="flex justify-end gap-3 mt-6 pt-6 border-t border-gray-200">
                  <button
                    onClick={closeModals}
                    className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleEditDeadline}
                    className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <Save className="w-4 h-4 mr-2" />
                    Update Deadline
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
