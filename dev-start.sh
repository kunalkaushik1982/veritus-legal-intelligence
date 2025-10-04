#!/bin/bash
# Development startup script for Linux/Mac
# This script starts the backend services in Docker and frontend locally

echo "🚀 Starting Veritus Development Environment..."

# Stop any existing containers
echo "📦 Stopping existing containers..."
docker-compose down

# Start backend services (postgres, redis, backend) without frontend
echo "🐳 Starting backend services..."
docker-compose up -d postgres redis backend

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 15

# Check if backend is ready
echo "🔍 Checking backend health..."
backend_ready=false
for i in {1..10}; do
    if curl -s http://localhost:8000/health > /dev/null; then
        backend_ready=true
        break
    else
        echo "Backend not ready yet, waiting..."
        sleep 5
    fi
done

if [ "$backend_ready" = true ]; then
    echo "✅ Backend services are ready!"
    echo "🌐 Backend API: http://localhost:8000"
    echo "📊 API Docs: http://localhost:8000/docs"
    
    # Start frontend locally
    echo "🎨 Starting frontend locally..."
    cd frontend
    echo "📦 Installing dependencies..."
    npm install
    
    echo "🚀 Starting Next.js development server..."
    echo "🌐 Frontend will be available at: http://localhost:3000"
    echo "🔄 Hot reload is enabled for both frontend and backend!"
    
    npm run dev
else
    echo "❌ Backend services failed to start. Check logs with: docker-compose logs backend"
fi
