#!/bin/bash

# LinkedIn Automation MVP - Full Stack Startup Script
set -e

echo "🚀 Starting LinkedIn Automation MVP..."

# Function to check if service is ready
wait_for_service() {
    local service_name=$1
    local url=$2
    local max_attempts=30
    local attempt=0
    
    echo "Waiting for $service_name to be ready..."
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s $url > /dev/null 2>&1; then
            echo "✅ $service_name is ready!"
            return 0
        fi
        
        echo "⏳ Waiting for $service_name... (attempt $((attempt + 1))/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service_name failed to start after $max_attempts attempts"
    return 1
}

# Create frontend directory if it doesn't exist
if [ ! -d "frontend" ]; then
    echo "📁 Creating frontend directory..."
    mkdir -p frontend
fi

# Copy frontend files
# echo "📄 Setting up frontend files..."
# cp frontend_files/index.html frontend/
# cp frontend_files/nginx.conf frontend/
# cp frontend_files/Dockerfile frontend/
# cp frontend_files/config.js frontend/

# Start all services
echo "🐳 Starting Docker services..."
docker-compose down -v  # Clean start
docker-compose up -d --build

# Wait for services to be ready
echo "🔍 Checking service health..."

wait_for_service "Database" "http://localhost:5432" || exit 1
wait_for_service "Redis" "http://localhost:6379" || exit 1
wait_for_service "Backend API" "http://localhost:8000/health" || exit 1
wait_for_service "Frontend" "http://localhost" || exit 1

# Run backend tests
echo "🧪 Running backend tests..."
python test_mvp.py

# Run frontend tests (optional, requires ChromeDriver)
if command -v google-chrome &> /dev/null; then
    echo "🌐 Running frontend tests..."
    python test_frontend.py
else
    echo "⚠️  Chrome not found, skipping frontend tests"
    echo "   Install Chrome and ChromeDriver to run frontend tests"
fi

echo ""
echo "🎉 LinkedIn Automation MVP is ready!"
echo ""
echo "🌐 Frontend: http://localhost"
echo "🔧 Backend API: http://localhost:8000"
echo "📊 API Docs: http://localhost:8000/docs"
echo "🔍 Health Check: http://localhost:8000/health"
echo ""
echo "📋 Test the MVP user journeys:"
echo "1. Register a new user at http://localhost"
echo "2. Add a content source (try: https://feeds.feedburner.com/oreilly/radar)"
echo "3. View the content feed"
echo "4. Generate and edit post drafts"
echo "5. Publish posts (simulated)"
echo ""
echo "📁 View logs with: docker-compose logs -f"
echo "🛑 Stop services with: docker-compose down"