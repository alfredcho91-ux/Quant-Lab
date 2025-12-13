#!/bin/bash

# WolGem Quant Master - Development Startup Script
# This script starts both the backend and frontend servers

echo "🚀 Starting WolGem Quant Master..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start Backend
echo -e "${BLUE}Starting Backend Server...${NC}"
cd "$SCRIPT_DIR/backend"

# Check if venv exists, if not create it
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate venv and install dependencies
source venv/bin/activate
pip install -q -r requirements.txt

# Start backend server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend started on http://localhost:8000${NC}"
echo ""

# Wait for backend to start
sleep 2

# Start Frontend
echo -e "${BLUE}Starting Frontend Server...${NC}"
cd "$SCRIPT_DIR/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
fi

# Start frontend server
npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}✓ Frontend started on http://localhost:5173${NC}"
echo ""

echo "========================================="
echo -e "${GREEN}🎉 WolGem Quant Master is running!${NC}"
echo ""
echo "  📡 Backend API:  http://localhost:8000"
echo "  🌐 Frontend App: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop all servers"
echo "========================================="

# Wait for both processes
wait

