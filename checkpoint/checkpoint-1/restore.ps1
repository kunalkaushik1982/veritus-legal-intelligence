# Veritus Legal Intelligence Platform - Checkpoint 1 Restore Script (PowerShell)
# This script restores the system to Checkpoint 1 state

Write-Host "🔄 Restoring Veritus to Checkpoint 1..." -ForegroundColor Cyan

# Stop current containers
Write-Host "⏹️  Stopping current containers..." -ForegroundColor Yellow
docker-compose down

# Backup current state (optional)
Write-Host "💾 Creating backup of current state..." -ForegroundColor Yellow
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
New-Item -ItemType Directory -Path "backup_$timestamp" -Force | Out-Null
Copy-Item -Path "backend" -Destination "backup_$timestamp/" -Recurse -ErrorAction SilentlyContinue
Copy-Item -Path "frontend" -Destination "backup_$timestamp/" -Recurse -ErrorAction SilentlyContinue
Copy-Item -Path "docker-compose.yml" -Destination "backup_$timestamp/" -ErrorAction SilentlyContinue

# Restore from checkpoint
Write-Host "🔄 Restoring from Checkpoint 1..." -ForegroundColor Yellow
Remove-Item -Path "backend" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "frontend" -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item -Path "checkpoint/checkpoint-1/backend" -Destination "./backend" -Recurse
Copy-Item -Path "checkpoint/checkpoint-1/frontend" -Destination "./frontend" -Recurse
Copy-Item -Path "checkpoint/checkpoint-1/docker-compose.yml" -Destination "./docker-compose.yml"

# Start containers
Write-Host "🚀 Starting containers..." -ForegroundColor Yellow
docker-compose up -d

# Wait for services to start
Write-Host "⏳ Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Test health
Write-Host "🏥 Testing health..." -ForegroundColor Yellow
try {
    $backendHealth = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 5
    if ($backendHealth.StatusCode -eq 200) {
        Write-Host "✅ Backend is healthy!" -ForegroundColor Green
    } else {
        Write-Host "❌ Backend health check failed" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Backend health check failed" -ForegroundColor Red
}

try {
    $frontendHealth = Invoke-WebRequest -Uri "http://localhost:3000" -Method GET -TimeoutSec 5
    if ($frontendHealth.StatusCode -eq 200) {
        Write-Host "✅ Frontend is healthy!" -ForegroundColor Green
    } else {
        Write-Host "❌ Frontend health check failed" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Frontend health check failed" -ForegroundColor Red
}

Write-Host "🎉 Restore complete! System restored to Checkpoint 1 state." -ForegroundColor Green
Write-Host "📋 Current backup saved as: backup_$timestamp" -ForegroundColor Cyan
