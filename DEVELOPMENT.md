# 🚀 Veritus Development Setup

## 📋 Quick Start (Recommended)

### Option 1: Automated Script (Easiest)
```bash
# Windows PowerShell
.\dev-start.ps1

# Linux/Mac
chmod +x dev-start.sh
./dev-start.sh
```

### Option 2: Manual Setup
```bash
# 1. Start backend services only
docker-compose up -d postgres redis backend

# 2. Wait for backend to be ready (check http://localhost:8000/health)

# 3. Start frontend locally
cd frontend
npm install
npm run dev
```

## 🔄 Development Workflow

### ✅ What Works with Hot Reload:
- **Backend Python files**: Changes in `backend/app/` are automatically reloaded
- **Frontend React files**: Changes in `frontend/` are automatically reloaded
- **Database/Redis**: Persistent data across restarts

### 🐳 Docker Services Running:
- **PostgreSQL**: `localhost:5432`
- **Redis**: `localhost:6379`
- **Backend API**: `localhost:8000`
- **API Documentation**: `localhost:8000/docs`

### 🎨 Local Services Running:
- **Frontend**: `localhost:3000` (with hot reload)

## 🛠️ Available Commands

### Development
```bash
# Start development environment
.\dev-start.ps1                    # Windows
./dev-start.sh                     # Linux/Mac

# Start backend services only
docker-compose up -d postgres redis backend

# Start frontend locally
cd frontend && npm run dev
```

### Production
```bash
# Start all services in production mode
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Or use the development override
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### Debugging
```bash
# View backend logs
docker-compose logs -f backend

# View all logs
docker-compose logs -f

# Stop all services
docker-compose down
```

## 🔧 Troubleshooting

### Backend Changes Not Reflecting
1. Check if backend container is running: `docker-compose ps`
2. Check backend logs: `docker-compose logs backend`
3. Restart backend: `docker-compose restart backend`

### Frontend Changes Not Reflecting
1. Check if frontend is running locally: `http://localhost:3000`
2. Hard refresh browser: `Ctrl+F5` or `Cmd+Shift+R`
3. Clear browser cache

### Port Conflicts
- Backend (8000): Change in `docker-compose.yml`
- Frontend (3000): Change in `frontend/package.json`

## 📁 Project Structure
```
veritus/
├── backend/           # Python FastAPI backend
├── frontend/          # Next.js React frontend
├── pdfs/             # PDF files storage
├── docker-compose.yml # Main docker configuration
├── docker-compose.dev.yml # Development overrides
├── docker-compose.prod.yml # Production overrides
├── dev-start.ps1     # Windows development script
└── dev-start.sh      # Linux/Mac development script
```

## 🎯 Benefits of This Setup

1. **Fast Development**: No need to rebuild Docker images for code changes
2. **Hot Reload**: Both frontend and backend reload automatically
3. **Isolated Services**: Database and Redis run in containers
4. **Production Ready**: Separate production configuration
5. **Easy Debugging**: Direct access to logs and processes
