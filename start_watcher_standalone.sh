#!/bin/bash

echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                          ║"
echo "║              PDF AUTO-INGESTION WATCHER (STANDALONE)                    ║"
echo "║                                                                          ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "This watcher will monitor data/synthetic/pdfs_alternative/ for new PDFs"
echo "and automatically process them."
echo ""
echo "Press Ctrl+C to stop the watcher"
echo ""

python3 scripts/pdf_watcher.py
