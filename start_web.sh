#!/bin/bash

# Start the Gold Sentiment Index web dashboard (Backend + Frontend)

BACKEND_PORT=${GSI_BACKEND_PORT:-22226}
FRONTEND_PORT=${GSI_FRONTEND_PORT:-22265}

echo "=========================================="
echo "  Gold Sentiment Index Web Dashboard"
echo "=========================================="
echo ""
echo "Backend Port:  $BACKEND_PORT"
echo "Frontend Port: $FRONTEND_PORT"
echo ""
echo "API Docs:  http://localhost:$BACKEND_PORT/docs"
echo "Frontend:  http://localhost:$FRONTEND_PORT"
echo ""

BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    echo ""
    echo "Shutting down Gold Sentiment Index web..."

    if [ -n "$BACKEND_PID" ]; then
        echo "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null
    fi

    if [ -n "$FRONTEND_PID" ]; then
        echo "Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null
    fi

    kill $(lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t) 2>/dev/null
    kill $(lsof -Pi :$FRONTEND_PORT -sTCP:LISTEN -t) 2>/dev/null

    echo "System stopped"
    exit
}
trap cleanup EXIT INT TERM

cd "$(dirname "$0")" || exit 1

# Check and clear ports if needed
for PORT in $BACKEND_PORT $FRONTEND_PORT; do
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "Port $PORT is already in use"
        lsof -Pi :$PORT -sTCP:LISTEN
        echo ""
        read -p "Kill existing processes on port $PORT? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Killing processes on port $PORT..."
            kill -9 $(lsof -Pi :$PORT -sTCP:LISTEN -t) 2>/dev/null
            sleep 1
        else
            echo "Cannot start - port $PORT is busy"
            exit 1
        fi
    fi
done

echo ""
echo "Starting backend server..."
python3 -m uvicorn api.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload &
BACKEND_PID=$!
echo "Backend started (PID: $BACKEND_PID)"

echo "Waiting for backend to initialize..."
sleep 3

echo ""
echo "Starting frontend server..."
cd web && npm run dev &
FRONTEND_PID=$!
echo "Frontend started (PID: $FRONTEND_PID)"

cd ..

echo ""
echo "=========================================="
echo "  System is running!"
echo "=========================================="
echo "  Press Ctrl+C to stop all services"
echo "=========================================="
echo ""

wait
