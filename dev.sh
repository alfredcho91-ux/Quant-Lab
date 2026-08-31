#!/bin/bash

# Quant Master - fast dev startup (no dependency install)

set -e

echo "Starting Quant Master (dev mode)..."
echo ""

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
QUANT_MASTER_HOST="${QUANT_MASTER_HOST:-127.0.0.1}"
if [ -z "${NODE_BIN:-}" ]; then
    NODE_BIN="$(command -v node 2>/dev/null || true)"
fi
if [ -x "/Users/geunwoocho/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node" ] && ! "$NODE_BIN" --version >/dev/null 2>&1; then
    NODE_BIN="/Users/geunwoocho/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
fi
if [ -z "$NODE_BIN" ]; then
    echo "Node.js was not found. Install Node.js or set NODE_BIN before starting Quant-Lab."
    exit 1
fi

stop_existing_project_server() {
    local port="$1"
    local pid command
    while read -r pid; do
        [ -z "$pid" ] && continue
        command="$(ps -p "$pid" -o command= 2>/dev/null || true)"
        case "$command" in
            *"$SCRIPT_DIR/frontend"*|*"$SCRIPT_DIR/backend"*|*"backend.main:app"*)
                echo "Stopping previous Quant-Lab process $pid on port $port"
                kill "$pid" 2>/dev/null || true
                ;;
        esac
    done < <(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)
}

if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "$SCRIPT_DIR/.env"
    set +a
fi

cleanup() {
    status=$?
    trap - EXIT SIGINT SIGTERM
    echo ""
    echo "Shutting down servers..."
    [ -n "${BACKEND_PID:-}" ] && kill "$BACKEND_PID" 2>/dev/null || true
    [ -n "${FRONTEND_PID:-}" ] && kill "$FRONTEND_PID" 2>/dev/null || true
    stop_existing_project_server 8000
    stop_existing_project_server 5173
    wait 2>/dev/null || true
    exit "$status"
}

trap cleanup EXIT SIGINT SIGTERM

echo -e "${BLUE}Starting Backend Server...${NC}"
cd "$SCRIPT_DIR"

stop_existing_project_server 8000
stop_existing_project_server 5173

if [ ! -d "backend/venv" ]; then
    echo "Missing backend venv. Run ./bootstrap.sh first."
    exit 1
fi

"$SCRIPT_DIR/backend/venv/bin/python" -m uvicorn backend.main:app \
    --host "$QUANT_MASTER_HOST" \
    --port 8000 \
    --reload \
    --reload-dir backend \
    --reload-dir core &
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

"$NODE_BIN" "$SCRIPT_DIR/frontend/node_modules/vite/bin/vite.js" --host "$QUANT_MASTER_HOST" --port 5173 &
FRONTEND_PID=$!
echo -e "${GREEN}Frontend started on http://localhost:5173${NC}"
echo ""

echo "Press Ctrl+C to stop all servers"

wait
