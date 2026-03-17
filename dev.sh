#!/bin/bash

# Quant Master - fast dev startup (no dependency install)

set -e

echo "Starting Quant Master (dev mode)..."
echo ""

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cleanup() {
    echo ""
    echo "Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

echo -e "${BLUE}Starting Backend Server...${NC}"
cd "$SCRIPT_DIR/backend"

if [ ! -d "venv" ]; then
    echo "Missing backend venv. Run ./bootstrap.sh first."
    exit 1
fi

source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload --reload-dir . --reload-dir ../core &
BACKEND_PID=$!
echo -e "${GREEN}Backend started on http://localhost:8000${NC}"
echo ""

sleep 2

echo -e "${BLUE}Starting Frontend Server...${NC}"
cd "$SCRIPT_DIR/frontend"

if [ ! -d "node_modules" ]; then
    echo "Missing frontend dependencies. Run ./bootstrap.sh first."
    exit 1
fi

npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}Frontend started on http://localhost:5173${NC}"
echo ""

echo "Press Ctrl+C to stop all servers"

wait
