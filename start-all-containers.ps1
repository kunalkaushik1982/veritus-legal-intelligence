# Veritus - Complete Container Startup Script
# This script starts all containers with proper configuration

Write-Host "🚀 Starting Veritus - Complete Container Setup" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green

# Check if Docker is running
try {
    docker version | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Create necessary directories
Write-Host "📁 Creating necessary directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "logs" | Out-Null
New-Item -ItemType Directory -Force -Path "nginx" | Out-Null
New-Item -ItemType Directory -Force -Path "nginx/ssl" | Out-Null

# Stop any existing containers
Write-Host "🛑 Stopping existing containers..." -ForegroundColor Yellow
docker-compose -f docker-compose.full.yml down

# Remove old containers and images (optional)
$cleanup = Read-Host "Do you want to remove old containers and images? (y/n)"
if ($cleanup -eq "y" -or $cleanup -eq "Y") {
    Write-Host "🧹 Cleaning up old containers and images..." -ForegroundColor Yellow
    docker-compose -f docker-compose.full.yml down --volumes --remove-orphans
    docker system prune -f
}

# Build fresh images
Write-Host "🔨 Building fresh images..." -ForegroundColor Yellow
docker-compose -f docker-compose.full.yml build --no-cache

# Start core services
Write-Host "🚀 Starting core services..." -ForegroundColor Green
docker-compose -f docker-compose.full.yml up -d postgres redis

# Wait for database to be ready
Write-Host "⏳ Waiting for database to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Start backend
Write-Host "🔧 Starting backend service..." -ForegroundColor Green
docker-compose -f docker-compose.full.yml up -d backend

# Wait for backend to be ready
Write-Host "⏳ Waiting for backend to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Start frontend
Write-Host "🎨 Starting frontend service..." -ForegroundColor Green
docker-compose -f docker-compose.full.yml up -d frontend

# Check if user wants admin tools
$admin = Read-Host "Do you want to start admin tools (pgAdmin, Redis Commander)? (y/n)"
if ($admin -eq "y" -or $admin -eq "Y") {
    Write-Host "🛠️ Starting admin tools..." -ForegroundColor Green
    docker-compose -f docker-compose.full.yml --profile admin up -d
}

# Check if user wants nginx proxy
$nginx = Read-Host "Do you want to start nginx reverse proxy? (y/n)"
if ($nginx -eq "y" -or $nginx -eq "Y") {
    Write-Host "🌐 Starting nginx reverse proxy..." -ForegroundColor Green
    docker-compose -f docker-compose.full.yml --profile production up -d nginx
}

# Show container status
Write-Host "📊 Container Status:" -ForegroundColor Green
docker-compose -f docker-compose.full.yml ps

# Show logs
Write-Host "📋 Recent logs:" -ForegroundColor Green
docker-compose -f docker-compose.full.yml logs --tail=10

# Show access URLs
Write-Host "`n🌐 Access URLs:" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "Database: localhost:5432" -ForegroundColor White
Write-Host "Redis: localhost:6379" -ForegroundColor White

if ($admin -eq "y" -or $admin -eq "Y") {
    Write-Host "pgAdmin: http://localhost:5050 (admin@veritus.com / admin123)" -ForegroundColor White
    Write-Host "Redis Commander: http://localhost:8081" -ForegroundColor White
}

if ($nginx -eq "y" -or $nginx -eq "Y") {
    Write-Host "Nginx Proxy: http://localhost:80" -ForegroundColor White
}

Write-Host "`n✅ All containers started successfully!" -ForegroundColor Green
Write-Host "Use 'docker-compose -f docker-compose.full.yml logs -f' to follow logs" -ForegroundColor Yellow
