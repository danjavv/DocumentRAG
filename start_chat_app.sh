#!/bin/bash

echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                          ║"
echo "║              PROCUREMENT RAG CHAT APPLICATION                            ║"
echo "║                                                                          ║"
echo "║   Starting Backend (FastAPI) and Frontend (Next.js)                     ║"
echo "║                                                                          ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend in background
echo "🚀 Starting Backend API Server (Port 8000)..."
./run_backend.sh > backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to start
echo "⏳ Waiting for backend to initialize (this may take 10-15 seconds)..."
sleep 3

# Wait for backend to be ready (with retries)
MAX_RETRIES=10
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        break
    fi
    echo "   ⏳ Still initializing... ($((RETRY_COUNT + 1))/$MAX_RETRIES)"
    sleep 2
    RETRY_COUNT=$((RETRY_COUNT + 1))
done

# Check if backend is running
if ! curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "❌ Backend failed to start. Check backend.log for details."
    tail -30 backend.log
    exit 1
fi

echo "✅ Backend is running!"
echo ""

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing Frontend dependencies (first time only)..."
    cd frontend && npm install && cd ..
fi

# Start frontend in background
echo "🚀 Starting Frontend Server (Port 3000)..."
./run_frontend.sh > frontend.log 2>&1 &
FRONTEND_PID=$!

echo "⏳ Waiting for frontend to start..."
sleep 8

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                          ║"
echo "║                    ✅ APPLICATION IS READY! ✅                           ║"
echo "║                                                                          ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 Open in your browser:"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "💡 Tips:"
echo "   • Ask questions about Purchase Orders, Invoices, and GRNs"
echo "   • Click on suggested questions in the sidebar"
echo "   • View source documents for each answer"
echo ""
echo "📝 Logs:"
echo "   Backend:  tail -f backend.log"
echo "   Frontend: tail -f frontend.log"
echo ""
echo "Press Ctrl+C to stop both servers..."
echo ""

# Wait for either process to exit
wait $BACKEND_PID $FRONTEND_PID
