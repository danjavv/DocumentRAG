#!/bin/bash

echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                          ║"
echo "║              STARTING PROCUREMENT RAG FRONTEND                           ║"
echo "║                                                                          ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    cd frontend && npm install
    cd ..
fi

# Start Next.js development server
echo ""
echo "🚀 Starting Next.js server on http://localhost:3000"
echo ""

cd frontend && npm run dev
