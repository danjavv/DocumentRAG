#!/bin/bash

echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                          ║"
echo "║              STARTING PROCUREMENT RAG BACKEND                            ║"
echo "║                                                                          ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""

# Install required packages
echo "📦 Installing Python dependencies..."
pip3 install --break-system-packages fastapi uvicorn pydantic 2>/dev/null

# Start FastAPI backend
echo ""
echo "🚀 Starting FastAPI server on http://localhost:8000"
echo "   API Documentation: http://localhost:8000/docs"
echo ""

python3 backend/api.py
