# Development startup script for Windows PowerShell
# This script starts the backend services in Docker and frontend locally

Write-Host "🚀 Starting Veritus Development Environment..." -ForegroundColor Green

# Stop any existing containers
Write-Host "📦 Stopping existing containers..." -ForegroundColor Yellow
docker-compose down

# Start backend services (postgres, redis, backend) without frontend
Write-Host "🐳 Starting backend services..." -ForegroundColor Yellow
docker-compose up -d postgres redis backend

# Wait for services to be ready
Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep 15

# Check if backend is ready
Write-Host "🔍 Checking backend health..." -ForegroundColor Yellow
$backendReady = $false
for ($i = 0; $i -lt 10; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            $backendReady = $true
            break
        }
    }
    catch {
        Write-Host "Backend not ready yet, waiting..." -ForegroundColor Yellow
        Start-Sleep 5
    }
}

if ($backendReady) {
    Write-Host "✅ Backend services are ready!" -ForegroundColor Green
    Write-Host "🌐 Backend API: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "📊 API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
    
    # Start frontend locally
    Write-Host "🎨 Starting frontend locally..." -ForegroundColor Yellow
    Set-Location frontend
    Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
    npm install
    
    Write-Host "🚀 Starting Next.js development server..." -ForegroundColor Yellow
    Write-Host "🌐 Frontend will be available at: http://localhost:3000" -ForegroundColor Cyan
    Write-Host "🔄 Hot reload is enabled for both frontend and backend!" -ForegroundColor Green
    
    npm run dev
}
else {
    Write-Host "❌ Backend services failed to start. Check logs with: docker-compose logs backend" -ForegroundColor Red
}
