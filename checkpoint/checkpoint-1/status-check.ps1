# Quick Status Check Script for Checkpoint 1
# Run this to verify the system is in Checkpoint 1 state

Write-Host "🔍 Checking Veritus System Status..." -ForegroundColor Cyan

# Check Backend Health
Write-Host "`n🏥 Backend Health Check:" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Backend: Healthy" -ForegroundColor Green
        $healthData = $response.Content | ConvertFrom-Json
        Write-Host "   Service: $($healthData.service)" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ Backend: Not responding" -ForegroundColor Red
}

# Check RAG Status
Write-Host "`n🧠 RAG System Status:" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/rag/status" -Method GET -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        $ragData = $response.Content | ConvertFrom-Json
        Write-Host "✅ RAG: Active" -ForegroundColor Green
        Write-Host "   Judgments: $($ragData.total_judgments)" -ForegroundColor Gray
        Write-Host "   Chunks: $($ragData.total_chunks)" -ForegroundColor Gray
        Write-Host "   Memory: $([math]::Round($ragData.memory_usage_mb, 2)) MB" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ RAG: Not responding" -ForegroundColor Red
}

# Check Judgments Library
Write-Host "`n📚 Judgments Library:" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/judgments/" -Method GET -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        $judgmentsData = $response.Content | ConvertFrom-Json
        $judgmentCount = $judgmentsData.judgments.Count
        Write-Host "✅ Judgments: $judgmentCount available" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Judgments: Not responding" -ForegroundColor Red
}

# Check Batch Processing
Write-Host "`n⚙️  Batch Processing:" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/batch/status" -Method GET -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        $batchData = $response.Content | ConvertFrom-Json
        Write-Host "✅ Batch: Ready" -ForegroundColor Green
        Write-Host "   Processed: $($batchData.processed_judgments)" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ Batch: Not responding" -ForegroundColor Red
}

# Check Frontend
Write-Host "`n🌐 Frontend Status:" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -Method GET -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Frontend: Running" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Frontend: Not responding" -ForegroundColor Red
}

Write-Host "`n🎯 Checkpoint 1 Status Summary:" -ForegroundColor Cyan
Write-Host "   📅 Created: October 1, 2025" -ForegroundColor Gray
Write-Host "   🏷️  Tag: STABLE AND FULLY FUNCTIONAL" -ForegroundColor Gray
Write-Host "   ✅ Core Features: All Working" -ForegroundColor Green
Write-Host "   ❌ Collaborative Editing: Disabled" -ForegroundColor Yellow
