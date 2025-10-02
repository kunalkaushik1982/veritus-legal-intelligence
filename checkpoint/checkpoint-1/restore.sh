#!/bin/bash

# Veritus Legal Intelligence Platform - Checkpoint 1 Restore Script
# This script restores the system to Checkpoint 1 state

echo "🔄 Restoring Veritus to Checkpoint 1..."

# Stop current containers
echo "⏹️  Stopping current containers..."
docker-compose down

# Backup current state (optional)
echo "💾 Creating backup of current state..."
timestamp=$(date +"%Y%m%d_%H%M%S")
mkdir -p "backup_$timestamp"
cp -r backend "backup_$timestamp/" 2>/dev/null || true
cp -r frontend "backup_$timestamp/" 2>/dev/null || true
cp docker-compose.yml "backup_$timestamp/" 2>/dev/null || true

# Restore from checkpoint
echo "🔄 Restoring from Checkpoint 1..."
cp -r checkpoint/checkpoint-1/backend ./
cp -r checkpoint/checkpoint-1/frontend ./
cp checkpoint/checkpoint-1/docker-compose.yml ./

# Start containers
echo "🚀 Starting containers..."
docker-compose up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Test health
echo "🏥 Testing health..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is healthy!"
else
    echo "❌ Backend health check failed"
fi

if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend is healthy!"
else
    echo "❌ Frontend health check failed"
fi

echo "🎉 Restore complete! System restored to Checkpoint 1 state."
echo "📋 Current backup saved as: backup_$timestamp"
