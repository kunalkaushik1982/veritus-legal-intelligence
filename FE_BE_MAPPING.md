# 🗺️ Veritus Frontend-Backend Mapping Documentation

## 📋 Overview

This comprehensive documentation maps out all Frontend (FE) code connections to Backend (BE) code, providing a complete understanding of how the Veritus Legal Intelligence Platform works. This serves as a mindmap for developers to understand the overall functionality and data flow.

---

## 🏗️ Architecture Overview

```
┌─────────────────┐    HTTP/WebSocket    ┌─────────────────┐
│   Frontend      │◄────────────────────►│   Backend       │
│   (Next.js)     │                      │   (FastAPI)     │
├─────────────────┤                      ├─────────────────┤
│ • React Pages   │                      │ • API Endpoints │
│ • Components    │                      │ • Services      │
│ • State Mgmt    │                      │ • Database      │
│ • WebSocket     │                      │ • WebSocket     │
└─────────────────┘                      └─────────────────┘
```

---

## 📱 Frontend Structure

### **Core Pages**
| Page | File | Purpose |
|------|------|---------|
| **Home/Landing** | `pages/index.tsx` | Marketing page with feature overview |
| **Dashboard** | `pages/dashboard.tsx` | Main user dashboard with navigation |
| **Login** | `pages/login.tsx` | User authentication |
| **Register** | `pages/register.tsx` | User registration |
| **Judgments Library** | `pages/judgments-library.tsx` | Main judgments management |
| **Citation Analysis** | `pages/citation-analysis.tsx` | Citation analysis and network visualization |
| **Deadline Tracker** | `pages/deadline-tracker.tsx` | Deadline management (Frontend-only) |
| **Batch Process** | `pages/batch-process.tsx` | Batch processing interface |
| **Collaborative Editing** | `pages/collaborative-editing.tsx` | Real-time collaborative editing |

### **Components**
| Component | File | Purpose |
|-----------|------|---------|
| **CollaborativeEditor** | `components/collab/CollaborativeEditor.tsx` | Real-time text editing |
| **CommentsSidebar** | `components/collab/CommentsSidebar.tsx` | Document comments |
| **DocumentManager** | `components/collab/DocumentManager.tsx` | Document CRUD operations |
| **CursorOverlay** | `components/collab/CursorOverlay.tsx` | User cursor visualization |

---

## 🔌 Backend Structure

### **API Endpoints (simple_main.py)**
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Root health check |
| `/health` | GET | Service health status |
| `/api/test` | GET | Test endpoint |
| `/api/auth/login` | POST | User authentication |
| `/api/auth/register` | POST | User registration |
| `/api/upload/pdf` | POST | PDF upload and processing |
| `/api/judgments/` | GET | List all judgments |
| `/api/judgments/{id}/view` | GET | View judgment PDF |
| `/api/judgments/{id}/download` | GET | Download judgment PDF |
| `/api/judgments/{id}/text` | GET | Get judgment text |
| `/api/batch/process-existing` | POST | Batch process judgments |
| `/api/citations/sample` | GET | Sample citation data |
| `/api/citations/analyze` | POST | Analyze citation strength |
| `/api/citations/network/{id}` | GET | Citation network visualization |
| `/api/citations/strength-ranking` | GET | Citation strength ranking |
| `/api/timeline/{id}` | GET | Extract timeline from judgment |
| `/api/summary/{id}` | POST | AI case summarization |
| `/api/chatbot/query` | POST | AI chatbot queries |

### **Modular API Routes**
| Router | File | Endpoints |
|--------|------|-----------|
| **Authentication** | `api/auth.py` | `/api/auth/*` |
| **Users** | `api/users.py` | `/api/users/*` |
| **Judgments** | `api/judgments.py` | `/api/judgments/*` |
| **Citations** | `api/citations.py` | `/api/citations/*` |
| **Timelines** | `api/timelines.py` | `/api/timelines/*` |
| **Batch Processing** | `api/batch_processing.py` | `/api/batch/*` |
| **Collaborative** | `collab/routes.py` | `/collab/*` |

### **WebSocket Endpoints**
| Endpoint | Purpose |
|----------|---------|
| `/ws/docs/{document_id}` | Real-time collaborative editing |

---

## 🔄 Feature-by-Feature Mapping

## 1. 🏠 **Home Page** (`pages/index.tsx`)
```
Frontend: pages/index.tsx
├── Static Content (No BE calls)
├── Navigation Links
│   ├── /login → login.tsx
│   └── /register → register.tsx
└── Feature Showcase (Static)
```

**Backend Connection:** ❌ No direct backend calls

---

## 2. 🔐 **Authentication** (`pages/login.tsx`, `pages/register.tsx`)

### **Login Flow**
```
Frontend: pages/login.tsx
├── loginMutation.useMutation()
│   └── fetch('/api/auth/login', { method: 'POST' })
│       └── Backend: simple_main.py
│           └── @app.post("/api/auth/login")
│               ├── Parse form data
│               ├── Generate user ID from username hash
│               └── Return JWT token + user data
├── Store token in localStorage
├── Redirect to /dashboard
└── Error handling with toast notifications
```

### **Registration Flow**
```
Frontend: pages/register.tsx
├── registerMutation.useMutation()
│   └── fetch('/api/auth/register', { method: 'POST' })
│       └── Backend: simple_main.py
│           └── @app.post("/api/auth/register")
│               ├── Return demo token
│               └── Return user data
├── Store token in localStorage
├── Redirect to /dashboard
└── Error handling with toast notifications
```

---

## 3. 📊 **Dashboard** (`pages/dashboard.tsx`)

### **Dashboard Features**
```
Frontend: pages/dashboard.tsx
├── Navigation Menu
│   ├── Search Judgments → /judgments-library
│   ├── Citation Analysis → /citation-analysis
│   ├── Deadline Tracker → /deadline-tracker
│   └── Collaborative Editing → /collaborative-editing
├── AI Chatbot (chatMutation)
│   └── fetch('/api/chatbot/query', { method: 'POST' })
│       └── Backend: simple_main.py
│           └── @app.post("/api/chatbot/query")
│               ├── Process query with AI service
│               ├── Generate response
│               └── Return AI response
├── Batch Processing (batchMutation)
│   └── fetch('/api/batch/process-existing', { method: 'POST' })
│       └── Backend: simple_main.py
│           └── @app.post("/api/batch/process-existing")
│               ├── Start background processing
│               ├── Process PDFs
│               └── Return processing status
└── User Statistics Display
```

---

## 4. 📚 **Judgments Library** (`pages/judgments-library.tsx`)

### **Core Functionality**
```
Frontend: pages/judgments-library.tsx
├── Data Loading (useEffect)
│   └── fetch('/api/judgments/')
│       └── Backend: simple_main.py
│           └── @app.get("/api/judgments/")
│               ├── Load sample judgments
│               ├── Add metadata (petitioner, respondent, etc.)
│               └── Return judgment list
├── Search & Filter (Client-side)
│   ├── Filter by petitioner, respondent, case_number, filename
│   ├── Sort by date, title, case number
│   └── Pagination (5, 10, 20, 50, 100 items)
├── AI Summary (handleSummarizeCase)
│   └── fetch(`/api/summary/${judgment.id}`, { method: 'POST' })
│       └── Backend: simple_main.py
│           └── @app.post("/api/summary/{judgment_id}")
│               ├── CaseSummarizer.generate_summary()
│               ├── OpenAI API call
│               ├── Cache result
│               └── Return summary
├── View PDF (handleViewPDF)
│   └── fetch(`/api/judgments/${judgment.id}/view`)
│       └── Backend: simple_main.py
│           └── @app.get("/api/judgments/{judgment_id}/view")
│               ├── Check file existence
│               └── Return PDF file
├── Download PDF (handleDownloadPDF)
│   └── fetch(`/api/judgments/${judgment.id}/download`)
│       └── Backend: simple_main.py
│           └── @app.get("/api/judgments/{judgment_id}/download")
│               ├── Check file existence
│               └── Return PDF download
├── View Text (handleViewText)
│   └── fetch(`/api/judgments/${judgment.id}/text`)
│       └── Backend: simple_main.py
│           └── @app.get("/api/judgments/{judgment_id}/text")
│               ├── Extract text from PDF
│               └── Return judgment text
└── Timeline Extraction (handleViewTimeline)
    └── fetch(`/api/timeline/${judgment.id}`)
        └── Backend: simple_main.py
            └── @app.get("/api/timeline/{judgment_id}")
                ├── TimelineExtractor.extract_timeline()
                ├── Process judgment text
                └── Return timeline events
```

### **State Management**
```typescript
// Frontend State
const [judgments, setJudgments] = useState<Judgment[]>([]);
const [filteredJudgments, setFilteredJudgments] = useState<Judgment[]>([]);
const [searchTerm, setSearchTerm] = useState('');
const [sortBy, setSortBy] = useState<'date' | 'title' | 'case_number'>('date');
const [currentPage, setCurrentPage] = useState(1);
const [itemsPerPage, setItemsPerPage] = useState(10);
```

---

## 5. 🔍 **Citation Analysis** (`pages/citation-analysis.tsx`)

### **Multi-Tab Interface**
```
Frontend: pages/citation-analysis.tsx
├── Tab: Browse Judgments
│   ├── Load judgments: fetch('/api/judgments/')
│   ├── PDF Upload: fetch('/api/upload/pdf', { method: 'POST' })
│   │   └── Backend: simple_main.py
│   │       └── @app.post("/api/upload/pdf")
│   │           ├── Save uploaded file
│   │           ├── Process PDF
│   │           ├── Extract metadata
│   │           └── Return processed data
│   └── Select source/target judgments
├── Tab: Analyze Citation
│   ├── Citation Analysis Form
│   └── fetch('/api/citations/analyze', { method: 'POST' })
│       └── Backend: simple_main.py
│           └── @app.post("/api/citations/analyze")
│               ├── CitationAnalyzer.analyze_citation()
│               ├── Process source/target/context
│               ├── Calculate strength score
│               └── Return analysis result
├── Tab: Network Analysis
│   └── fetch(`/api/citations/network/${networkJudgmentId}`)
│       └── Backend: simple_main.py
│           └── @app.get("/api/citations/network/{judgment_id}")
│               ├── Build citation network
│               ├── Calculate connections
│               └── Return network data
└── Tab: Precedent Ranking
    └── fetch(`/api/citations/strength-ranking?limit=${rankingLimit}`)
        └── Backend: simple_main.py
            └── @app.get("/api/citations/strength-ranking")
                ├── Calculate citation strength
                ├── Rank precedents
                └── Return ranking list
```

---

## 6. ⏰ **Deadline Tracker** (`pages/deadline-tracker.tsx`)

### **Frontend-Only Feature**
```
Frontend: pages/deadline-tracker.tsx
├── Sample Data (No BE calls)
│   ├── Sample deadlines array
│   ├── Stats calculation (client-side)
│   └── CRUD operations (local state)
├── Add Deadline Modal
│   ├── Form validation (client-side)
│   ├── Add to local state
│   └── Update stats
├── Edit Deadline Modal
│   ├── Pre-populate form
│   ├── Update local state
│   └── Update stats
├── Filter & Pagination (client-side)
└── Actions (client-side)
    ├── Mark completed
    └── Delete deadline
```

**Backend Connection:** ❌ No backend calls (Frontend-only feature)

---

## 7. 🔄 **Batch Processing** (`pages/batch-process.tsx`)

### **Batch Processing Flow**
```
Frontend: pages/batch-process.tsx
├── Start Processing Button
│   └── fetch('/api/batch/process-existing', { method: 'POST' })
│       └── Backend: simple_main.py
│           └── @app.post("/api/batch/process-existing")
│               ├── Start background task
│               ├── Process existing PDFs
│               ├── Extract metadata
│               ├── Update database
│               └── Return processing status
├── Progress Display
│   ├── Processing status
│   ├── Files processed count
│   └── Error handling
└── Results Summary
```

---

## 8. 🤝 **Collaborative Editing** (`pages/collaborative-editing.tsx`)

### **Real-time Collaboration**
```
Frontend: components/collab/CollaborativeEditor.tsx
├── WebSocket Connection
│   ├── wsUrl = 'ws://localhost:8000/ws/docs/{documentId}'
│   ├── WebSocket connection management
│   ├── Auto-reconnect logic
│   └── Connection status tracking
├── Document Operations
│   ├── Load document: fetch(`/collab/documents/${documentId}/state`)
│   ├── Save document: fetch(`/collab/documents/${documentId}/save`)
│   └── Real-time updates via WebSocket
├── User Presence
│   ├── Cursor position sharing
│   ├── User list display
│   └── Real-time cursor overlay
└── Text Operations
    ├── Y.js integration
    ├── Operational transforms
    └── Conflict resolution
```

### **Backend WebSocket Handler**
```
Backend: collab/routes.py
├── WebSocket Endpoint: /ws/docs/{document_id}
│   ├── Accept WebSocket connection
│   ├── Authenticate user
│   ├── Join document room
│   └── Handle real-time messages
├── Message Types
│   ├── auth: User authentication
│   ├── text_op: Text operations
│   ├── cursor_update: Cursor position
│   ├── selection_update: Text selection
│   └── ping/pong: Keep-alive
├── Broadcast System
│   ├── Send to all users in document
│   ├── Exclude sender
│   └── Handle disconnections
└── Document Persistence
    ├── Save document state
    ├── Load document state
    └── Version control
```

### **Comments System**
```
Frontend: components/collab/CommentsSidebar.tsx
├── Load Comments: fetch(`/collab/documents/${documentId}/comments`)
├── Add Comment: fetch(`/collab/documents/${documentId}/comments`, { method: 'POST' })
├── Update Comment: fetch(`/collab/documents/${documentId}/comments/${commentId}`, { method: 'PUT' })
└── Delete Comment: fetch(`/collab/documents/${documentId}/comments/${commentId}`, { method: 'DELETE' })
    └── Backend: collab/routes.py
        └── Comment CRUD endpoints
            ├── GET /collab/documents/{doc_id}/comments
            ├── POST /collab/documents/{doc_id}/comments
            ├── PUT /collab/documents/{doc_id}/comments/{comment_id}
            └── DELETE /collab/documents/{doc_id}/comments/{comment_id}
```

---

## 🔧 **Services & Utilities**

### **Frontend Services**
| Service | File | Purpose |
|---------|------|---------|
| **API Config** | `utils/config.ts` | API endpoint configuration |
| **WebSocket Config** | `utils/config.ts` | WebSocket URL configuration |

### **Backend Services**
| Service | File | Purpose |
|---------|------|---------|
| **PDF Processor** | `services/pdf_processor.py` | PDF text extraction |
| **Metadata Extractor** | `services/pdf_metadata_extractor.py` | PDF metadata extraction |
| **Citation Analyzer** | `services/citation_analyzer.py` | Citation analysis |
| **Timeline Extractor** | `services/timeline_extractor.py` | Timeline extraction |
| **Case Summarizer** | `services/case_summarizer.py` | AI case summarization |
| **AI Service** | `services/ai_service.py` | OpenAI integration |
| **WebSocket Manager** | `collab/websocket_manager.py` | WebSocket connection management |

---

## 📊 **Data Flow Patterns**

### **1. Standard CRUD Flow**
```
Frontend Component → API Call → Backend Endpoint → Service Layer → Database
                  ← Response ← ← Response ← ← Response ←
```

### **2. Real-time WebSocket Flow**
```
Frontend Component → WebSocket Message → Backend WebSocket Handler → Broadcast to All Users
                  ← WebSocket Response ← ← WebSocket Response ←
```

### **3. File Upload Flow**
```
Frontend → File Upload → Backend → File Processing → Database Storage → Response
       ← Progress Updates ← ← Processing Status ←
```

### **4. AI Processing Flow**
```
Frontend → AI Request → Backend → OpenAI API → AI Response → Cache → Frontend
       ← Loading State ← ← Processing ← ← Response ←
```

---

## 🔐 **Authentication & Authorization**

### **Token Management**
```
Frontend:
├── Login → Store JWT in localStorage
├── API calls → Include Bearer token
├── Token validation → Check expiry
└── Auto-logout → Clear token on expiry

Backend:
├── JWT validation → Verify token
├── User context → Extract user info
├── Authorization → Check permissions
└── Rate limiting → Prevent abuse
```

### **Protected Routes**
```
Frontend Protected Pages:
├── /dashboard
├── /judgments-library
├── /citation-analysis
├── /deadline-tracker
├── /batch-process
└── /collaborative-editing

Backend Protected Endpoints:
├── All /api/* endpoints
├── All /collab/* endpoints
└── WebSocket connections
```

---

## 🚨 **Error Handling**

### **Frontend Error Handling**
```typescript
// API Error Handling
try {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  const data = await response.json();
} catch (error) {
  toast.error(`Error: ${error.message}`);
  console.error('API Error:', error);
}

// WebSocket Error Handling
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
  toast.error('Connection error. Attempting to reconnect...');
};

// Form Validation
const validateForm = (data) => {
  const errors = {};
  if (!data.required_field) {
    errors.required_field = 'This field is required';
  }
  return errors;
};
```

### **Backend Error Handling**
```python
# FastAPI Error Handling
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Service Error Handling
try:
    result = await service.process_data(data)
    return {"success": True, "data": result}
except Exception as e:
    logger.error(f"Service error: {str(e)}")
    raise HTTPException(status_code=500, detail=str(e))
```

---

## 📈 **Performance Optimizations**

### **Frontend Optimizations**
- **React Query**: Caching API responses
- **Pagination**: Limit data loading
- **Debounced Search**: Reduce API calls
- **Lazy Loading**: Load components on demand
- **Memoization**: Prevent unnecessary re-renders

### **Backend Optimizations**
- **Connection Pooling**: Database connections
- **Caching**: Redis for frequent data
- **Background Tasks**: Async processing
- **Rate Limiting**: Prevent abuse
- **Compression**: Gzip responses

---

## 🔄 **State Management**

### **Frontend State**
```typescript
// React State
const [data, setData] = useState([]);
const [loading, setLoading] = useState(false);
const [error, setError] = useState(null);

// React Query (Server State)
const { data, isLoading, error } = useQuery(
  'judgments',
  () => fetchJudgments()
);

// Local Storage (Persistent State)
localStorage.setItem('access_token', token);
```

### **Backend State**
```python
# Database State (PostgreSQL)
class Judgment(Base):
    __tablename__ = "judgments"
    id = Column(Integer, primary_key=True)
    # ... other fields

# Cache State (Redis)
redis.set("user_session", session_data, ex=3600)
```

---

## 🌐 **API Configuration**

### **Frontend Configuration**
```typescript
// utils/config.ts
export const API_CONFIG = {
  BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  WS_URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000',
  
  getApiUrl: (endpoint: string) => `${API_CONFIG.BASE_URL}${endpoint}`,
  getWsUrl: (endpoint: string) => `${API_CONFIG.WS_URL}${endpoint}`,
};
```

### **Backend Configuration**
```python
# Environment Variables
DATABASE_URL = "postgresql://user:pass@localhost:5432/veritus"
REDIS_URL = "redis://localhost:6379"
OPENAI_API_KEY = "sk-..."
CORS_ORIGINS = ["http://localhost:3000"]

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📝 **Development Workflow**

### **Frontend Development**
1. **Component Creation** → `pages/` or `components/`
2. **API Integration** → `fetch()` calls with error handling
3. **State Management** → React hooks or React Query
4. **Styling** → Tailwind CSS classes
5. **Testing** → Component testing

### **Backend Development**
1. **Endpoint Creation** → `@app.get/post/put/delete()`
2. **Service Integration** → Service layer calls
3. **Database Operations** → SQLAlchemy ORM
4. **Error Handling** → HTTPException with proper status codes
5. **Testing** → API endpoint testing

---

## 🚀 **Deployment Architecture**

### **Container Setup**
```
Docker Compose:
├── Frontend Container (Next.js)
├── Backend Container (FastAPI)
├── PostgreSQL Container
├── Redis Container
└── Nginx Container (Optional)
```

### **Environment Variables**
```bash
# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Backend (.env)
DATABASE_URL=postgresql://user:pass@postgres:5432/veritus
REDIS_URL=redis://redis:6379
OPENAI_API_KEY=sk-...
```

---

## 📚 **Key Integration Points**

### **1. Authentication Flow**
```
Login Page → Auth API → JWT Token → Dashboard
```

### **2. Judgments Management**
```
Judgments Library → Judgments API → PDF Processing → Database
```

### **3. AI Integration**
```
Citation Analysis → AI Service → OpenAI API → Cached Results
```

### **4. Real-time Collaboration**
```
Collaborative Editor → WebSocket → Real-time Updates → All Users
```

### **5. File Processing**
```
PDF Upload → Processing Pipeline → Metadata Extraction → Storage
```

---

## 🔍 **Debugging Guide**

### **Frontend Debugging**
```typescript
// Console Logging
console.log('API Response:', response);
console.log('Component State:', state);

// React DevTools
// - Component tree inspection
// - State and props debugging
// - Performance profiling

// Network Tab
// - API call monitoring
// - Request/response inspection
// - WebSocket message tracking
```

### **Backend Debugging**
```python
# Logging
logger.info(f"Processing request: {request_data}")
logger.error(f"Error occurred: {str(e)}")

# FastAPI Docs
# - http://localhost:8000/docs
# - Interactive API testing
# - Schema validation

# Database Queries
# - SQLAlchemy query logging
# - Database connection monitoring
```

---

## 📋 **Summary**

This documentation provides a comprehensive mapping of how the Veritus Legal Intelligence Platform connects Frontend and Backend components. Key takeaways:

1. **Modular Architecture**: Clear separation between FE and BE with well-defined interfaces
2. **Real-time Features**: WebSocket-based collaborative editing
3. **AI Integration**: OpenAI-powered case summarization and analysis
4. **File Processing**: Comprehensive PDF processing pipeline
5. **Authentication**: JWT-based user management
6. **Error Handling**: Robust error handling at all levels
7. **Performance**: Optimized for scalability and user experience

**This mapping serves as a complete reference for developers to understand the system architecture and implement new features effectively.**
