#!/bin/bash

# Verification script for MCP server setup

echo "=== Stock Analysis MCP Server Setup Verification ==="
echo ""

# Check Python version
echo "1. Checking Python version..."
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python 3 not found. Please install Python 3.11+"
    exit 1
fi
echo "✓ Python found"
echo ""

# Check if requirements file exists
echo "2. Checking requirements.txt..."
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found"
    exit 1
fi
echo "✓ requirements.txt found"
echo ""

# Check if server.py exists
echo "3. Checking server.py..."
if [ ! -f "server.py" ]; then
    echo "❌ server.py not found"
    exit 1
fi
echo "✓ server.py found"
echo ""

# Check if Dockerfile exists
echo "4. Checking Dockerfile..."
if [ ! -f "Dockerfile" ]; then
    echo "❌ Dockerfile not found"
    exit 1
fi
echo "✓ Dockerfile found"
echo ""

# Check if .env exists
echo "5. Checking .env configuration..."
if [ ! -f ".env" ]; then
    echo "⚠ .env not found. Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✓ .env created from .env.example"
    else
        echo "❌ .env.example not found"
        exit 1
    fi
else
    echo "✓ .env found"
fi
echo ""

# Check Docker (optional)
echo "6. Checking Docker (optional)..."
if command -v docker &> /dev/null; then
    docker --version
    echo "✓ Docker found"

    if command -v docker-compose &> /dev/null; then
        docker-compose --version
        echo "✓ Docker Compose found"
    else
        echo "⚠ Docker Compose not found (optional)"
    fi
else
    echo "⚠ Docker not found (optional for manual setup)"
fi
echo ""

# Check backend (if running locally)
echo "7. Checking backend availability..."
BACKEND_URL=${BACKEND_API_URL:-http://localhost:8000}
echo "Backend URL: $BACKEND_URL"

if command -v curl &> /dev/null; then
    if curl -s -f "$BACKEND_URL/" > /dev/null; then
        echo "✓ Backend is accessible"
    else
        echo "⚠ Backend not accessible (make sure it's running)"
    fi
else
    echo "⚠ curl not found, skipping backend check"
fi
echo ""

echo "=== Setup Verification Complete ==="
echo ""
echo "Next steps:"
echo "1. Make sure the backend is running (cd ../backend && uvicorn main:app)"
echo "2. Install dependencies: pip install -r requirements.txt"
echo "3. Run the MCP server: python server.py"
echo "   OR"
echo "   Use Docker: docker-compose up"
