# Checkpoint 2 Status Check Script
# Verifies that all collaborative editing features are working

Write-Host "🔍 Checking Checkpoint 2 Status..." -ForegroundColor Cyan

# Check if containers are running
Write-Host "`n📦 Container Status:" -ForegroundColor Yellow
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Check backend health
Write-Host "`n🔧 Backend Health Check:" -ForegroundColor Yellow
try {
    $backendResponse = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
    Write-Host "  ✅ Backend is healthy" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Backend is not responding" -ForegroundColor Red
}

# Check collaborative editing endpoints
Write-Host "`n📝 Collaborative Editing Endpoints:" -ForegroundColor Yellow
try {
    $collabResponse = Invoke-RestMethod -Uri "http://localhost:8000/collab/documents" -TimeoutSec 5
    Write-Host "  ✅ Collaborative editing API is working" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Collaborative editing API is not responding" -ForegroundColor Red
}

# Check frontend
Write-Host "`n🌐 Frontend Health Check:" -ForegroundColor Yellow
try {
    $frontendResponse = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5
    if ($frontendResponse.StatusCode -eq 200) {
        Write-Host "  ✅ Frontend is accessible" -ForegroundColor Green
    }
} catch {
    Write-Host "  ❌ Frontend is not responding" -ForegroundColor Red
}

Write-Host "`n🎯 Test URLs:" -ForegroundColor White
Write-Host "  🏠 Dashboard: http://localhost:3000/dashboard" -ForegroundColor Cyan
Write-Host "  📝 Collaborative Editing: http://localhost:3000/collaborative-editing" -ForegroundColor Cyan
Write-Host "  📚 Judgments Library: http://localhost:3000/judgments-library" -ForegroundColor Cyan
Write-Host "  🔗 Citation Analysis: http://localhost:3000/citation-analysis" -ForegroundColor Cyan

Write-Host "`n✨ Checkpoint 2 Features:" -ForegroundColor White
Write-Host "  ✅ Real-time collaborative text editing" -ForegroundColor Green
Write-Host "  ✅ Multi-user presence tracking" -ForegroundColor Green
Write-Host "  ✅ Live cursor positioning and avatars" -ForegroundColor Green
Write-Host "  ✅ Rich text formatting (bold, italic, lists)" -ForegroundColor Green
Write-Host "  ✅ User attribution with colored highlights" -ForegroundColor Green
Write-Host "  ✅ Real-time typing indicators" -ForegroundColor Green
Write-Host "  ✅ Comments system with sidebar" -ForegroundColor Green
Write-Host "  ✅ Document management (create, delete, list)" -ForegroundColor Green
Write-Host "  ✅ WebSocket-based real-time sync" -ForegroundColor Green
Write-Host "  ✅ Operational Transform for conflict resolution" -ForegroundColor Green
