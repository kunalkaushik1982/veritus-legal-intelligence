#!/bin/bash

# Veritus - Complete Container Startup Script
# This script starts all containers with proper configuration

echo "🚀 Starting Veritus - Complete Container Setup"
echo "================================================"

# Check if Docker is running
if ! docker version > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi
echo "✅ Docker is running"

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs
mkdir -p nginx/ssl

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.full.yml down

# Remove old containers and images (optional)
read -p "Do you want to remove old containers and images? (y/n): " cleanup
if [[ $cleanup == "y" || $cleanup == "Y" ]]; then
    echo "🧹 Cleaning up old containers and images..."
    docker-compose -f docker-compose.full.yml down --volumes --remove-orphans
    docker system prune -f
fi

# Build fresh images
echo "🔨 Building fresh images..."
docker-compose -f docker-compose.full.yml build --no-cache

# Start core services
echo "🚀 Starting core services..."
docker-compose -f docker-compose.full.yml up -d postgres redis

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Start backend
echo "🔧 Starting backend service..."
docker-compose -f docker-compose.full.yml up -d backend

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
sleep 15

# Start frontend
echo "🎨 Starting frontend service..."
docker-compose -f docker-compose.full.yml up -d frontend

# Check if user wants admin tools
read -p "Do you want to start admin tools (pgAdmin, Redis Commander)? (y/n): " admin
if [[ $admin == "y" || $admin == "Y" ]]; then
    echo "🛠️ Starting admin tools..."
    docker-compose -f docker-compose.full.yml --profile admin up -d
fi

# Check if user wants nginx proxy
read -p "Do you want to start nginx reverse proxy? (y/n): " nginx
if [[ $nginx == "y" || $nginx == "Y" ]]; then
    echo "🌐 Starting nginx reverse proxy..."
    docker-compose -f docker-compose.full.yml --profile production up -d nginx
fi

# Show container status
echo "📊 Container Status:"
docker-compose -f docker-compose.full.yml ps

# Show logs
echo "📋 Recent logs:"
docker-compose -f docker-compose.full.yml logs --tail=10

# Show access URLs
echo ""
echo "🌐 Access URLs:"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "Database: localhost:5432"
echo "Redis: localhost:6379"

if [[ $admin == "y" || $admin == "Y" ]]; then
    echo "pgAdmin: http://localhost:5050 (admin@veritus.com / admin123)"
    echo "Redis Commander: http://localhost:8081"
fi

if [[ $nginx == "y" || $nginx == "Y" ]]; then
    echo "Nginx Proxy: http://localhost:80"
fi

echo ""
echo "✅ All containers started successfully!"
echo "Use 'docker-compose -f docker-compose.full.yml logs -f' to follow logs"
