# Veritus - Container Management Script
# This script provides easy management of all Veritus containers

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("start", "stop", "restart", "status", "logs", "clean", "build", "shell", "backup", "restore")]
    [string]$Action,
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("all", "frontend", "backend", "postgres", "redis", "nginx", "admin")]
    [string]$Service = "all"
)

function Show-Header {
    Write-Host "🐳 Veritus Container Manager" -ForegroundColor Cyan
    Write-Host "=============================" -ForegroundColor Cyan
}

function Start-Containers {
    param([string]$TargetService)
    
    Write-Host "🚀 Starting containers..." -ForegroundColor Green
    
    switch ($TargetService) {
        "all" {
            docker-compose -f docker-compose.full.yml up -d
        }
        "frontend" {
            docker-compose -f docker-compose.full.yml up -d frontend
        }
        "backend" {
            docker-compose -f docker-compose.full.yml up -d backend
        }
        "postgres" {
            docker-compose -f docker-compose.full.yml up -d postgres
        }
        "redis" {
            docker-compose -f docker-compose.full.yml up -d redis
        }
        "nginx" {
            docker-compose -f docker-compose.full.yml --profile production up -d nginx
        }
        "admin" {
            docker-compose -f docker-compose.full.yml --profile admin up -d
        }
    }
}

function Stop-Containers {
    param([string]$TargetService)
    
    Write-Host "🛑 Stopping containers..." -ForegroundColor Yellow
    
    switch ($TargetService) {
        "all" {
            docker-compose -f docker-compose.full.yml down
        }
        "frontend" {
            docker-compose -f docker-compose.full.yml stop frontend
        }
        "backend" {
            docker-compose -f docker-compose.full.yml stop backend
        }
        "postgres" {
            docker-compose -f docker-compose.full.yml stop postgres
        }
        "redis" {
            docker-compose -f docker-compose.full.yml stop redis
        }
        "nginx" {
            docker-compose -f docker-compose.full.yml stop nginx
        }
        "admin" {
            docker-compose -f docker-compose.full.yml --profile admin stop
        }
    }
}

function Restart-Containers {
    param([string]$TargetService)
    
    Write-Host "🔄 Restarting containers..." -ForegroundColor Blue
    Stop-Containers -TargetService $TargetService
    Start-Sleep -Seconds 3
    Start-Containers -TargetService $TargetService
}

function Show-Status {
    Write-Host "📊 Container Status:" -ForegroundColor Green
    docker-compose -f docker-compose.full.yml ps
    
    Write-Host "`n💾 Disk Usage:" -ForegroundColor Green
    docker system df
    
    Write-Host "`n🌐 Port Usage:" -ForegroundColor Green
    netstat -an | Select-String ":3000|:8000|:5432|:6379|:80|:443|:5050|:8081"
}

function Show-Logs {
    param([string]$TargetService)
    
    Write-Host "📋 Showing logs for $TargetService..." -ForegroundColor Green
    
    switch ($TargetService) {
        "all" {
            docker-compose -f docker-compose.full.yml logs -f
        }
        "frontend" {
            docker-compose -f docker-compose.full.yml logs -f frontend
        }
        "backend" {
            docker-compose -f docker-compose.full.yml logs -f backend
        }
        "postgres" {
            docker-compose -f docker-compose.full.yml logs -f postgres
        }
        "redis" {
            docker-compose -f docker-compose.full.yml logs -f redis
        }
        "nginx" {
            docker-compose -f docker-compose.full.yml logs -f nginx
        }
    }
}

function Clean-Containers {
    Write-Host "🧹 Cleaning up containers..." -ForegroundColor Yellow
    
    $confirm = Read-Host "This will remove all containers, images, and volumes. Continue? (y/n)"
    if ($confirm -eq "y" -or $confirm -eq "Y") {
        docker-compose -f docker-compose.full.yml down --volumes --remove-orphans
        docker system prune -af
        docker volume prune -f
        Write-Host "✅ Cleanup completed" -ForegroundColor Green
    } else {
        Write-Host "❌ Cleanup cancelled" -ForegroundColor Red
    }
}

function Build-Containers {
    param([string]$TargetService)
    
    Write-Host "🔨 Building containers..." -ForegroundColor Blue
    
    switch ($TargetService) {
        "all" {
            docker-compose -f docker-compose.full.yml build --no-cache
        }
        "frontend" {
            docker-compose -f docker-compose.full.yml build --no-cache frontend
        }
        "backend" {
            docker-compose -f docker-compose.full.yml build --no-cache backend
        }
    }
}

function Open-Shell {
    param([string]$TargetService)
    
    Write-Host "🐚 Opening shell for $TargetService..." -ForegroundColor Green
    
    switch ($TargetService) {
        "frontend" {
            docker-compose -f docker-compose.full.yml exec frontend sh
        }
        "backend" {
            docker-compose -f docker-compose.full.yml exec backend bash
        }
        "postgres" {
            docker-compose -f docker-compose.full.yml exec postgres psql -U veritus_user -d veritus
        }
        "redis" {
            docker-compose -f docker-compose.full.yml exec redis redis-cli
        }
    }
}

function Backup-Data {
    Write-Host "💾 Creating backup..." -ForegroundColor Green
    
    $timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
    $backupDir = "backups/$timestamp"
    
    New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
    
    # Backup database
    docker-compose -f docker-compose.full.yml exec -T postgres pg_dump -U veritus_user veritus > "$backupDir/database.sql"
    
    # Backup volumes
    docker run --rm -v veritus_postgres_data:/data -v "${PWD}/$backupDir":/backup alpine tar czf /backup/postgres_data.tar.gz -C /data .
    
    Write-Host "✅ Backup created in $backupDir" -ForegroundColor Green
}

function Restore-Data {
    Write-Host "📥 Restoring data..." -ForegroundColor Green
    
    $backupDir = Read-Host "Enter backup directory path (e.g., backups/2024-01-15_10-30-00)"
    
    if (Test-Path $backupDir) {
        # Restore database
        Get-Content "$backupDir/database.sql" | docker-compose -f docker-compose.full.yml exec -T postgres psql -U veritus_user -d veritus
        
        # Restore volumes
        docker run --rm -v veritus_postgres_data:/data -v "${PWD}/$backupDir":/backup alpine tar xzf /backup/postgres_data.tar.gz -C /data
        
        Write-Host "✅ Data restored from $backupDir" -ForegroundColor Green
    } else {
        Write-Host "❌ Backup directory not found: $backupDir" -ForegroundColor Red
    }
}

# Main execution
Show-Header

switch ($Action) {
    "start" { Start-Containers -TargetService $Service }
    "stop" { Stop-Containers -TargetService $Service }
    "restart" { Restart-Containers -TargetService $Service }
    "status" { Show-Status }
    "logs" { Show-Logs -TargetService $Service }
    "clean" { Clean-Containers }
    "build" { Build-Containers -TargetService $Service }
    "shell" { Open-Shell -TargetService $Service }
    "backup" { Backup-Data }
    "restore" { Restore-Data }
}

Write-Host "`n✅ Operation completed!" -ForegroundColor Green
