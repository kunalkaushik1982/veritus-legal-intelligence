@echo off
REM Veritus Setup Script for Windows
REM This script sets up the Veritus development environment

echo 🚀 Setting up Veritus Legal Intelligence Platform...

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    echo    Download from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

REM Create .env file if it doesn't exist
if not exist .env (
    echo 📝 Creating .env file from template...
    copy env.example .env
    echo ⚠️  Please edit .env file with your API keys before continuing.
    echo    Required: OPENAI_API_KEY
    echo    Optional: PINECONE_API_KEY, PINECONE_ENVIRONMENT
    echo.
    echo Press any key when you've updated the .env file...
    pause >nul
)

REM Build and start services
echo 🔨 Building Docker images...
docker-compose build

echo 🚀 Starting services...
docker-compose up -d

REM Wait for services to be ready
echo ⏳ Waiting for services to be ready...
timeout /t 15 /nobreak >nul

REM Check if services are running
echo 🔍 Checking service health...

REM Check PostgreSQL
docker-compose exec postgres pg_isready -U veritus_user -d veritus >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ PostgreSQL is ready
) else (
    echo ❌ PostgreSQL is not ready
)

REM Check Redis
docker-compose exec redis redis-cli ping >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Redis is ready
) else (
    echo ❌ Redis is not ready
)

REM Check Backend
curl -f http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Backend API is ready
) else (
    echo ❌ Backend API is not ready
)

REM Check Frontend
curl -f http://localhost:3000 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Frontend is ready
) else (
    echo ❌ Frontend is not ready
)

echo.
echo 🎉 Veritus is now running!
echo.
echo 📱 Access your application:
echo    Frontend: http://localhost:3000
echo    Backend API: http://localhost:8000
echo    API Documentation: http://localhost:8000/docs
echo.
echo 🔧 Useful commands:
echo    View logs: docker-compose logs -f
echo    Stop services: docker-compose down
echo    Restart services: docker-compose restart
echo    Update services: docker-compose pull ^&^& docker-compose up -d
echo.
echo 📚 Next steps:
echo    1. Register a new account at http://localhost:3000/register
echo    2. Start asking legal questions in the dashboard
echo    3. Explore the API documentation at http://localhost:8000/docs
echo.
echo Happy coding! 🎯
pause
