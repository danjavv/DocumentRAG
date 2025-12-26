#!/usr/bin/env python3
"""
FastAPI Backend for RAG System
Serves the procurement document RAG system via REST API
"""

import sys
import os
import threading
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn

# Import configuration
from config import config

# Import RAG system and file watcher
from rag_system import RAGSystem, DocumentLoader
from pdf_watcher import PDFAutoIngestion, start_watcher
from invoice_po_matcher import InvoicePOMatcher

# Configuration from environment
PDF_WATCH_DIR = config.PDF_DIR
PROCESSED_DIR = config.PROCESSED_DIR

# Initialize FastAPI app
app = FastAPI(
    title="Procurement RAG API",
    description="Intelligent document search and Q&A for procurement documents",
    version="1.0.0"
)

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip compression middleware - compress responses > 1KB
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Global instances
rag_system: Optional[RAGSystem] = None
auto_ingestion: Optional[PDFAutoIngestion] = None
watcher_thread: Optional[threading.Thread] = None
invoice_matcher: Optional[InvoicePOMatcher] = None


# Request/Response Models
class QueryRequest(BaseModel):
    question: str
    n_results: int = 5
    filter_type: Optional[str] = None
    filter_vendor: Optional[str] = None
    filter_min_amount: Optional[float] = None
    filter_max_amount: Optional[float] = None


class SourceDocument(BaseModel):
    doc_id: str
    doc_type: str
    vendor: str
    amount: Optional[float]
    date: str
    relevance: float
    excerpt: str


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[SourceDocument]
    timestamp: str


class StatsResponse(BaseModel):
    total_documents: int
    purchase_orders: int
    invoices: int
    grns: int
    total_value: float
    status: str


def on_new_pdf_callback(pdf_path: str):
    """Callback when new PDF is detected"""
    global rag_system, auto_ingestion

    if not rag_system or not auto_ingestion:
        return

    # Process the PDF
    result = auto_ingestion.process_pdf(pdf_path)

    if result:
        # Add to RAG system
        doc_type_map = {
            'purchase_order': 'purchase_orders',
            'invoice': 'invoices',
            'grn': 'grns'
        }

        doc_type = result['doc_type']
        doc_data = result['doc_data']

        # Add to RAG system dynamically
        rag_system.add_new_document(doc_data, doc_type_map[doc_type])

        print(f"    Document {result['doc_id']} added to RAG system and ready for queries!")


@app.on_event("startup")
async def startup_event():
    """Initialize RAG system and file watcher on startup"""
    global rag_system, auto_ingestion, watcher_thread, invoice_matcher

    print("\n" + "="*80)
    print("Starting Procurement RAG API Server")
    print("="*80)

    try:
        # Validate configuration
        config.validate()

        # Initialize RAG system
        print("\n Initializing RAG System with Gemini 2.5 Flash...")
        rag_system = RAGSystem(gemini_api_key=config.GEMINI_API_KEY)
        rag_system.initialize()

        print("\n RAG System Ready!")

        # Initialize Invoice-PO Matcher
        print("\n Initializing Invoice-PO Matcher...")
        try:
            invoice_matcher = InvoicePOMatcher()
            print(f" Invoice-PO Matcher Ready!")
        except Exception as e:
            print(f" Warning: Could not initialize Invoice-PO Matcher: {e}")
            print(" Mismatch detection will be unavailable.")

        # Initialize auto-ingestion with callback
        print("\n Initializing PDF Auto-Ingestion...")
        auto_ingestion = PDFAutoIngestion(
            watch_dir=PDF_WATCH_DIR,
            processed_dir=PROCESSED_DIR
        )

        # Create a custom watcher function
        def watcher_with_rag():
            from watchdog.observers import Observer
            from pdf_watcher import PDFWatcherHandler

            event_handler = PDFWatcherHandler(callback=on_new_pdf_callback)
            observer = Observer()
            observer.schedule(event_handler, str(PDF_WATCH_DIR), recursive=False)
            observer.start()

            print("👀 PDF Watcher started in background!")
            print(f"   Monitoring: {PDF_WATCH_DIR}\n")

            try:
                import time
                while True:
                    time.sleep(1)
            except:
                observer.stop()
            observer.join()

        # Start watcher in background thread
        watcher_thread = threading.Thread(target=watcher_with_rag, daemon=True)
        watcher_thread.start()

        print("Auto-ingestion active")
        print("="*80)

    except Exception as e:
        print(f"\n Error initializing systems: {e}")
        raise


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Procurement RAG API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "query": "/api/query",
            "stats": "/api/stats",
            "health": "/api/health"
        }
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    if rag_system is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")

    return {
        "status": "healthy",
        "rag_system": "ready",
        "llm": "gemini-2.5-flash",
        "auto_ingestion": "active" if auto_ingestion else "inactive"
    }


@app.get("/api/stats")
async def get_stats() -> StatsResponse:
    """Get system statistics"""
    if rag_system is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")

    try:
        # Load documents to get counts
        docs = DocumentLoader.load_all_documents()

        # Calculate totals (handle None values)
        total_po_value = sum(po.get('total_amount') or 0 for po in docs['purchase_orders'])
        total_inv_value = sum(inv.get('total_amount') or 0 for inv in docs['invoices'])

        return StatsResponse(
            total_documents=len(docs['purchase_orders']) + len(docs['invoices']) + len(docs['grns']),
            purchase_orders=len(docs['purchase_orders']),
            invoices=len(docs['invoices']),
            grns=len(docs['grns']),
            total_value=total_po_value + total_inv_value,
            status="operational"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")


@app.get("/api/watcher/status")
async def get_watcher_status():
    """Get PDF watcher status"""
    if auto_ingestion is None:
        return {
            "status": "inactive",
            "watcher_running": False
        }

    stats = auto_ingestion.get_stats()
    return {
        "status": "active",
        "watcher_running": True,
        "watch_directory": str(PDF_WATCH_DIR),
        "ingestion_stats": stats
    }


def is_mismatch_query(question: str) -> bool:
    """Detect if the query is about invoice-PO matching/mismatching"""
    question_lower = question.lower()

    # Match/mismatch-related keywords
    match_keywords = [
        'mismatch', 'mismatched',
        'discrepan', 'difference', 'differ',
        'not match', 'doesn\'t match', 'don\'t match',
        'incorrect', 'wrong',
        'variance', 'vary',
        'invoice.*(?:vs|versus|compared to).*po',
        'po.*(?:vs|versus|compared to).*invoice',
        'invoice.*not.*purchase order',
        'purchase order.*not.*invoice',
        'match.*invoice.*po', 'match.*po.*invoice',
        'invoice.*match.*purchase order',
        'purchase order.*match.*invoice',
        'accurately match', 'exact match'
    ]

    import re
    for keyword in match_keywords:
        if re.search(keyword, question_lower):
            return True

    return False


def parse_query_filters(question: str, request: QueryRequest):
    """Extract filters from natural language query"""
    import re

    question_lower = question.lower()

    # Auto-detect vendor name if not provided
    vendor = request.filter_vendor
    if not vendor:
        # Common vendor detection patterns
        vendors = [
            "Global Tech Solutions", "Nordic Supplies AB", "Pacific Traders",
            "Quality Manufacturing", "Premier Office Equipment", "CloudTech Innovations Inc",
            "Industrial Components Inc", "Advanced Tech Solutions Ltd"
        ]
        for v in vendors:
            if v.lower() in question_lower:
                vendor = v
                break

    # Auto-detect amount filters
    min_amount = request.filter_min_amount
    max_amount = request.filter_max_amount

    # Detect "over $X" or "above $X"
    over_match = re.search(r'(?:over|above|more than|greater than)\s*\$?\s*([\d,]+)', question_lower)
    if over_match and not min_amount:
        min_amount = float(over_match.group(1).replace(',', ''))
    # Detect "under $X" or "below $X"
    under_match = re.search(r'(?:under|below|less than)\s*\$?\s*([\d,]+)', question_lower)
    if under_match and not max_amount:
        max_amount = float(under_match.group(1).replace(',', ''))
    # Detect "between $X and $Y"
    between_match = re.search(r'between\s*\$?\s*([\d,]+)\s*and\s*\$?\s*([\d,]+)', question_lower)
    if between_match:
        min_amount = float(between_match.group(1).replace(',', ''))
        max_amount = float(between_match.group(2).replace(',', ''))
        print(f"    Auto-detected amount range: ${min_amount} - ${max_amount}")

    # Auto-increase n_results for "all" or "show me all" queries
    n_results = request.n_results
    if any(phrase in question_lower for phrase in ['all', 'every', 'complete list']):
        n_results = max(50, n_results)  # Increase to 50 for "all" queries
    return vendor, min_amount, max_amount, n_results


def handle_mismatch_query(question: str, vendor_filter: Optional[str] = None) -> Dict[str, Any]:
    """Handle queries about invoice-PO matching/mismatching"""
    if invoice_matcher is None:
        raise HTTPException(status_code=503, detail="Invoice-PO matcher not initialized")

    # Detect if user is asking for matched or mismatched invoices
    import re
    question_lower = question.lower()
    show_matched = bool(re.search(r'\b(matched|match|accurately match|exact match|correct)\b', question_lower) and
                       not re.search(r'\b(mismatch|not match|don\'t match|doesn\'t match)\b', question_lower))

    # Get all results
    all_results = invoice_matcher.find_all_mismatches()

    # Choose which set to show
    if show_matched:
        target_list = all_results['matched']
        target_type = "matched"
    else:
        target_list = all_results['mismatched']
        target_type = "mismatched"

    # Apply vendor filter if specified
    if vendor_filter:
        target_list = [m for m in target_list if m['vendor_name'].lower() == vendor_filter.lower()]

    # Generate answer text
    summary = all_results['summary']
    answer_parts = []

    if show_matched:
        answer_parts.append(f"**Invoice-PO Match Analysis**\n")
        answer_parts.append(f"I found **{summary['total_matched']} perfectly matched invoices** out of {all_results['total_invoices']} total invoices analyzed.\n")
    else:
        answer_parts.append(f"**Invoice-PO Mismatch Analysis**\n")
        answer_parts.append(f"I found **{summary['total_mismatched']} mismatched invoices** out of {all_results['total_invoices']} total invoices analyzed.\n")

    if vendor_filter:
        answer_parts.append(f"\n**Filtered by vendor: {vendor_filter}**")
        answer_parts.append(f"Found {len(target_list)} {target_type} invoices for this vendor.\n")

    if show_matched:
        # Show matched invoices
        if len(target_list) > 0:
            answer_parts.append(f"\n**These invoices perfectly match their reference purchase orders:**\n")
            for idx, match in enumerate(target_list, 1):
                answer_parts.append(
                    f"{idx}. **{match['invoice_number']}** → PO {match['po_reference']} ✓\n"
                    f"   - Vendor: {match['vendor_name']}\n"
                    f"   - Amount: ${match['invoice_total']:,.2f}\n"
                    f"   - All details match perfectly\n"
                )
        else:
            answer_parts.append(f"\n**No perfectly matched invoices found.** All invoices have some discrepancies with their referenced POs.")
    else:
        # Show mismatched invoices
        if summary['total_mismatched'] > 0:
            answer_parts.append(f"\n**Summary:**")
            answer_parts.append(f"- Total amount variance: ${summary['total_amount_variance']:,.2f}")
            answer_parts.append(f"- High severity issues: {summary['high_severity_issues']}")
            answer_parts.append(f"- Medium severity issues: {summary['medium_severity_issues']}\n")

            # Show ALL mismatches
            answer_parts.append(f"\n**All Mismatched Invoices ({len(target_list)}):**\n")
            for idx, mismatch in enumerate(target_list, 1):
                variance = abs(mismatch['invoice_total'] - mismatch['po_total'])
                answer_parts.append(
                    f"{idx}. **{mismatch['invoice_number']}** → PO {mismatch['po_reference']}\n"
                    f"   - Vendor: {mismatch['vendor_name']}\n"
                    f"   - Invoice Total: ${mismatch['invoice_total']:,.2f} | PO Total: ${mismatch['po_total']:,.2f}\n"
                    f"   - Variance: ${variance:,.2f}\n"
                    f"   - Issues: {mismatch['total_issues']}\n"
                )

                # Show specific issues
                if mismatch['header_issues']:
                    for issue in mismatch['header_issues'][:3]:  # Show top 3 issues per invoice
                        field = issue['field']
                        if 'difference' in issue:
                            diff = issue['difference']
                            answer_parts.append(f"     • {field}: ${diff:+,.2f} difference\n")
                        else:
                            answer_parts.append(f"     • {field}: mismatch detected\n")
        else:
            answer_parts.append(f"\n**Great news!** All invoices match their referenced purchase orders perfectly. ✓")

    answer = "\n".join(answer_parts)

    # Create source documents
    sources = []
    for item in target_list[:5]:  # Top 5 as sources
        if show_matched:
            excerpt = f"Invoice {item['invoice_number']} references PO {item['po_reference']}. "
            excerpt += f"Invoice total: ${item['invoice_total']:,.2f}, PO total: ${item['po_total']:,.2f}. "
            excerpt += f"All details match perfectly."
        else:
            excerpt = f"Invoice {item['invoice_number']} references PO {item['po_reference']}. "
            excerpt += f"Invoice total: ${item['invoice_total']:,.2f}, PO total: ${item['po_total']:,.2f}. "
            excerpt += f"Found {item['total_issues']} issues."

        sources.append({
            'doc_id': item['invoice_number'],
            'doc_type': 'Invoice',
            'vendor': item['vendor_name'],
            'amount': item['invoice_total'],
            'date': item.get('invoice_date', 'Unknown'),
            'relevance': 1.0,  # Exact match
            'excerpt': excerpt
        })

    return {
        'answer': answer,
        'sources': sources,
        'metadata': all_results
    }


@app.post("/api/query")
async def query_documents(request: QueryRequest) -> QueryResponse:
    """Query the RAG system"""
    if rag_system is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")

    if not request.question or len(request.question.strip()) == 0:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        # Check if this is a mismatch query
        if is_mismatch_query(request.question):
            print(f"\n [MISMATCH QUERY DETECTED] Routing to Invoice-PO matcher")

            # Parse vendor filter if any
            vendor, _, _, _ = parse_query_filters(request.question, request)

            # Handle mismatch query
            result = handle_mismatch_query(request.question, vendor)

            # Format sources
            sources = [
                SourceDocument(
                    doc_id=src['doc_id'],
                    doc_type=src['doc_type'],
                    vendor=src['vendor'],
                    amount=src['amount'],
                    date=src['date'],
                    relevance=src['relevance'],
                    excerpt=src['excerpt']
                )
                for src in result['sources']
            ]

            from datetime import datetime

            return QueryResponse(
                question=request.question,
                answer=result['answer'],
                sources=sources,
                timestamp=datetime.now().isoformat()
            )

        # Normal RAG query
        # Parse query for filters
        vendor, min_amount, max_amount, n_results = parse_query_filters(request.question, request)

        # Query RAG system
        result = rag_system.query(
            question=request.question,
            n_results=n_results,
            filter_type=request.filter_type,
            filter_vendor=vendor,
            filter_min_amount=min_amount,
            filter_max_amount=max_amount
        )

        # Debug logging
        print(f"\n Query: {request.question}")
        print(f"   Requested n_results: {request.n_results}")
        print(f"   Returned documents: {len(result['source_documents'])}")
        print(f"   Document IDs: {[m.get('doc_id') for m in result['metadata']]}")

        # Format sources
        sources = []
        for i, (meta, dist, doc) in enumerate(zip(
            result['metadata'],
            result['distances'],
            result['source_documents']
        )):
            sources.append(SourceDocument(
                doc_id=meta.get('doc_id', 'Unknown'),
                doc_type=meta.get('document_type', 'unknown').replace('_', ' ').title(),
                vendor=meta.get('vendor', 'Unknown'),
                amount=meta.get('amount'),
                date=meta.get('date', 'Unknown'),
                relevance=round(1 - dist, 2),
                excerpt=doc[:200] + "..." if len(doc) > 200 else doc
            ))

        from datetime import datetime

        return QueryResponse(
            question=request.question,
            answer=result['answer'],
            sources=sources,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.get("/api/suggestions")
async def get_suggestions():
    """Get suggested queries"""
    return {
        "suggestions": [
            "What is the total value of all purchase orders?",
            "Show me all invoices from Global Tech Solutions",
            "Show me all documents over $10,000",
            "Show me mismatched invoices and purchase orders",
            "Which invoices don't match their purchase orders?",
            "Tell me about purchase order PO-2024-01006",
            "Show me all documents from Nordic Supplies AB",
            "Find invoice-PO discrepancies"
        ]
    }


if __name__ == "__main__":
    print("""

                                                                          
              PROCUREMENT RAG API SERVER                                  
                                                                          
   FastAPI backend for Next.js chat interface                            
                                                                          

""")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
