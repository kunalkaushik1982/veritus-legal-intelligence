#!/bin/bash

# Veritus Setup Script
# This script sets up the Veritus development environment

set -e

echo "🚀 Setting up Veritus Legal Intelligence Platform..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please edit .env file with your API keys before continuing."
    echo "   Required: OPENAI_API_KEY"
    echo "   Optional: PINECONE_API_KEY, PINECONE_ENVIRONMENT"
    read -p "Press Enter when you've updated the .env file..."
fi

# Build and start services
echo "🔨 Building Docker images..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
echo "🔍 Checking service health..."

# Check PostgreSQL
if docker-compose exec postgres pg_isready -U veritus_user -d veritus; then
    echo "✅ PostgreSQL is ready"
else
    echo "❌ PostgreSQL is not ready"
fi

# Check Redis
if docker-compose exec redis redis-cli ping | grep -q PONG; then
    echo "✅ Redis is ready"
else
    echo "❌ Redis is not ready"
fi

# Check Backend
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend API is ready"
else
    echo "❌ Backend API is not ready"
fi

# Check Frontend
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is ready"
else
    echo "❌ Frontend is not ready"
fi

echo ""
echo "🎉 Veritus is now running!"
echo ""
echo "📱 Access your application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Documentation: http://localhost:8000/docs"
echo ""
echo "🔧 Useful commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop services: docker-compose down"
echo "   Restart services: docker-compose restart"
echo "   Update services: docker-compose pull && docker-compose up -d"
echo ""
echo "📚 Next steps:"
echo "   1. Register a new account at http://localhost:3000/register"
echo "   2. Start asking legal questions in the dashboard"
echo "   3. Explore the API documentation at http://localhost:8000/docs"
echo ""
echo "Happy coding! 🎯"
