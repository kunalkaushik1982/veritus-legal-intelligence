# Checkpoint 2 Restore Script (Windows PowerShell)
# Restores the advanced collaborative editing features

Write-Host "🔄 Restoring Checkpoint 2 - Advanced Collaborative Editing..." -ForegroundColor Cyan

# Stop containers
Write-Host "⏹️ Stopping containers..." -ForegroundColor Yellow
docker-compose down

# Backup current state
$backupDir = "backup-$(Get-Date -Format 'yyyy-MM-dd-HH-mm-ss')"
Write-Host "💾 Creating backup: $backupDir" -ForegroundColor Yellow
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
Copy-Item -Path "backend/app/collab" -Destination "$backupDir/" -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item -Path "backend/app/simple_main.py" -Destination "$backupDir/" -Force -ErrorAction SilentlyContinue
Copy-Item -Path "frontend/pages/collaborative-editing.tsx" -Destination "$backupDir/" -Force -ErrorAction SilentlyContinue
Copy-Item -Path "frontend/components/collab" -Destination "$backupDir/" -Recurse -Force -ErrorAction SilentlyContinue

# Restore checkpoint files
Write-Host "📁 Restoring checkpoint files..." -ForegroundColor Yellow

# Backend files
Copy-Item -Path "checkpoint/checkpoint-2/collab" -Destination "backend/app/" -Recurse -Force
Copy-Item -Path "checkpoint/checkpoint-2/simple_main.py" -Destination "backend/app/" -Force
Copy-Item -Path "checkpoint/checkpoint-2/requirements.txt" -Destination "backend/" -Force

# Frontend files
Copy-Item -Path "checkpoint/checkpoint-2/frontend/collaborative-editing.tsx" -Destination "frontend/pages/" -Force
Copy-Item -Path "checkpoint/checkpoint-2/frontend/collab" -Destination "frontend/components/" -Recurse -Force
Copy-Item -Path "checkpoint/checkpoint-2/package.json" -Destination "frontend/" -Force

# Restart containers
Write-Host "🚀 Starting containers..." -ForegroundColor Yellow
docker-compose up -d --build

Write-Host "✅ Checkpoint 2 restored successfully!" -ForegroundColor Green
Write-Host "🌐 Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "🔧 Backend: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📝 Collaborative Editing: http://localhost:3000/collaborative-editing" -ForegroundColor Cyan

Write-Host "`n📋 Features Available:" -ForegroundColor White
Write-Host "  ✅ Real-time collaborative editing" -ForegroundColor Green
Write-Host "  ✅ User presence and cursors" -ForegroundColor Green
Write-Host "  ✅ Rich text formatting" -ForegroundColor Green
Write-Host "  ✅ Comments system" -ForegroundColor Green
Write-Host "  ✅ Document management" -ForegroundColor Green
Write-Host "  ✅ User attribution" -ForegroundColor Green
Write-Host "  ✅ Typing indicators" -ForegroundColor Green
