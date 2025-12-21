#!/usr/bin/env python3
"""
PDF Directory Watcher
Monitors PDF directory for new files and automatically ingests them into the RAG system
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Install watchdog if not available
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileCreatedEvent
except ImportError:
    print("Installing watchdog library...")
    import subprocess
    subprocess.check_call(["pip3", "install", "--break-system-packages", "watchdog"])
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileCreatedEvent

# Import configuration
from config import config

# Import existing scripts
from pdf_ingestion_pipeline import PDFExtractor, DocumentClassifier, DataExtractor, LLMDataExtractor

# Configuration from environment
PDF_WATCH_DIR = config.PDF_DIR
PROCESSED_DIR = config.PROCESSED_DIR
INGESTION_LOG = config.INGESTION_LOG

# Ensure directories exist
PDF_WATCH_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


class IngestionLog:
    """Manage ingestion log for tracking processed files"""

    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.log_data = self._load_log()

    def _load_log(self) -> Dict[str, Any]:
        """Load existing log or create new one"""
        if self.log_file.exists():
            with open(self.log_file, 'r') as f:
                return json.load(f)
        return {
            "processed_files": {},
            "total_processed": 0,
            "last_updated": None
        }

    def _save_log(self):
        """Save log to file"""
        with open(self.log_file, 'w') as f:
            json.dump(self.log_data, f, indent=2)

    def is_processed(self, filename: str) -> bool:
        """Check if file has been processed"""
        return filename in self.log_data["processed_files"]

    def mark_processed(self, filename: str, doc_type: str, doc_id: str):
        """Mark file as processed"""
        self.log_data["processed_files"][filename] = {
            "doc_type": doc_type,
            "doc_id": doc_id,
            "processed_at": datetime.now().isoformat()
        }
        self.log_data["total_processed"] = len(self.log_data["processed_files"])
        self.log_data["last_updated"] = datetime.now().isoformat()
        self._save_log()


class PDFWatcherHandler(FileSystemEventHandler):
    """Handle file system events for PDF directory"""

    def __init__(self, callback):
        self.callback = callback
        self.processing = set()  # Track files being processed

    def on_created(self, event):
        """Called when a file is created"""
        if event.is_directory:
            return

        # Only process PDF files
        if not event.src_path.endswith('.pdf'):
            return

        # Avoid duplicate processing
        if event.src_path in self.processing:
            return

        self.processing.add(event.src_path)

        # Wait a bit to ensure file is fully written
        time.sleep(1)

        try:
            self.callback(event.src_path)
        finally:
            self.processing.discard(event.src_path)


class PDFAutoIngestion:
    """Automatic PDF ingestion system"""

    def __init__(self, watch_dir: Path, processed_dir: Path):
        self.watch_dir = watch_dir
        self.processed_dir = processed_dir

        # Initialize components
        self.extractor = PDFExtractor()
        self.classifier = DocumentClassifier()
        self.data_extractor = DataExtractor()
        self.llm_extractor = LLMDataExtractor(config.GEMINI_API_KEY)
        self.log = IngestionLog(INGESTION_LOG)

        # Document storage
        self.documents = self._load_existing_documents()

        print("=" * 80)
        print("PDF Auto-Ingestion System")
        print("="*80)
        print(f"   Watch Directory: {self.watch_dir}")
        print(f"   Processed Directory: {self.processed_dir}")
        print(f"   Total files already processed: {self.log.log_data['total_processed']}")
        print("="*80 + "\n")

    def _load_existing_documents(self) -> Dict[str, list]:
        """Load existing processed documents"""
        documents = {
            'purchase_orders': [],
            'invoices': [],
            'grns': []
        }

        # Load purchase orders
        po_file = self.processed_dir / "purchase_orders.json"
        if po_file.exists():
            with open(po_file, 'r') as f:
                documents['purchase_orders'] = json.load(f)

        # Load invoices
        inv_file = self.processed_dir / "invoices.json"
        if inv_file.exists():
            with open(inv_file, 'r') as f:
                documents['invoices'] = json.load(f)

        # Load GRNs
        grn_file = self.processed_dir / "grns.json"
        if grn_file.exists():
            with open(grn_file, 'r') as f:
                documents['grns'] = json.load(f)

        return documents

    def _save_documents(self):
        """Save all documents to JSON files"""
        # Save purchase orders
        with open(self.processed_dir / "purchase_orders.json", 'w') as f:
            json.dump(self.documents['purchase_orders'], f, indent=2)

        # Save invoices
        with open(self.processed_dir / "invoices.json", 'w') as f:
            json.dump(self.documents['invoices'], f, indent=2)

        # Save GRNs
        with open(self.processed_dir / "grns.json", 'w') as f:
            json.dump(self.documents['grns'], f, indent=2)

        # Save combined
        all_docs = (
            self.documents['purchase_orders'] +
            self.documents['invoices'] +
            self.documents['grns']
        )
        with open(self.processed_dir / "all_documents.json", 'w') as f:
            json.dump(all_docs, f, indent=2)

    def process_pdf(self, pdf_path: str) -> Optional[Dict[str, Any]]:
        """Process a single PDF file"""
        filename = Path(pdf_path).name

        # Check if already processed
        if self.log.is_processed(filename):
            print(f"     Skipping {filename} (already processed)")
            return None

        print(f"\n{'='*80}")
        print(f"Processing: {filename}")
        print("=" * 80)

        try:
            # Extract text
            print(f"    Extracting text...")
            text = self.extractor.extract_text(pdf_path)

            if not text or len(text.strip()) < 50:
                print(f"     Insufficient text extracted from {filename}")
                return None

            # Classify document
            print(f"     Classifying document...")
            doc_type = self.classifier.classify(text, filename)

            if doc_type == 'unknown':
                print(f"     Could not classify {filename}")
                return None

            print(f"    Classified as: {doc_type.upper()}")

            # Extract structured data with LLM first, fallback to regex
            
            doc_data = None
            extraction_method = 'regex'

            # Try LLM extraction first
            if self.llm_extractor and self.llm_extractor.enabled:
                
                if doc_type == 'purchase_order':
                    doc_data = self.llm_extractor.extract_purchase_order(text)
                elif doc_type == 'invoice':
                    doc_data = self.llm_extractor.extract_invoice(text)
                elif doc_type == 'grn':
                    doc_data = self.llm_extractor.extract_grn(text)

                if doc_data:
                    extraction_method = 'llm'

            # Fallback to regex if LLM failed
            if not doc_data:
                
                doc_data = self.data_extractor.extract(text, doc_type, filename)

            if not doc_data:
                print(f"     Could not extract data from {filename}")
                return None

            # Add metadata to document
            doc_data['metadata'] = {
                'filename': filename,
                'file_size': Path(pdf_path).stat().st_size,
                'layout_style': 'unknown',  # Can't determine from watcher
                'processed_at': datetime.now().isoformat(),
                'extraction_method': extraction_method,
                'extraction_confidence': 'high' if doc_data.get('po_number') or doc_data.get('invoice_number') or doc_data.get('grn_number') else 'low'
            }

            # Add to appropriate collection
            doc_id = doc_data.get('po_number') or doc_data.get('invoice_number') or doc_data.get('grn_number')

            if doc_type == 'purchase_order':
                self.documents['purchase_orders'].append(doc_data)
            elif doc_type == 'invoice':
                self.documents['invoices'].append(doc_data)
            elif doc_type == 'grn':
                self.documents['grns'].append(doc_data)

            # Save updated documents
            self._save_documents()

            # Mark as processed
            self.log.mark_processed(filename, doc_type, doc_id)

            print(f"    Successfully processed {filename}")
            print(f"    Document ID: {doc_id}")
            print(f"    Saved to {doc_type}.json")
            print(f"{'='*80}\n")

            return {
                'filename': filename,
                'doc_type': doc_type,
                'doc_id': doc_id,
                'doc_data': doc_data
            }

        except Exception as e:
            print(f"    Error processing {filename}: {e}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """Get ingestion statistics"""
        return {
            'total_purchase_orders': len(self.documents['purchase_orders']),
            'total_invoices': len(self.documents['invoices']),
            'total_grns': len(self.documents['grns']),
            'total_documents': sum([
                len(self.documents['purchase_orders']),
                len(self.documents['invoices']),
                len(self.documents['grns'])
            ]),
            'files_processed': self.log.log_data['total_processed'],
            'last_updated': self.log.log_data['last_updated']
        }


def start_watcher(watch_dir: Path, auto_ingestion: PDFAutoIngestion):
    """Start the file watcher"""
    event_handler = PDFWatcherHandler(callback=auto_ingestion.process_pdf)
    observer = Observer()
    observer.schedule(event_handler, str(watch_dir), recursive=False)
    observer.start()

    print("👀 PDF Watcher started!")
    print(f"   Monitoring: {watch_dir}")
    print(f"   Press Ctrl+C to stop\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n Stopping PDF Watcher...")
        observer.stop()

    observer.join()
    print(" PDF Watcher stopped")


if __name__ == "__main__":
    # Initialize auto-ingestion
    auto_ingestion = PDFAutoIngestion(
        watch_dir=PDF_WATCH_DIR,
        processed_dir=PROCESSED_DIR
    )

    # Start watching
    start_watcher(PDF_WATCH_DIR, auto_ingestion)
