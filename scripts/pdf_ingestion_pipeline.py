#!/usr/bin/env python3
"""
PDF Data Ingestion Pipeline
Scans PDFs, classifies them, extracts structured data, and stores as JSON
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Install required packages
try:
    import pdfplumber
except ImportError:
    print("Installing pdfplumber...")
    import subprocess
    subprocess.check_call(["pip3", "install", "--break-system-packages", "pdfplumber"])
    import pdfplumber

try:
    import google.generativeai as genai
except ImportError:
    print("Installing google-generativeai...")
    import subprocess
    subprocess.check_call(["pip3", "install", "--break-system-packages", "google-generativeai"])
    import google.generativeai as genai

# Import configuration
from config import config

# Configuration from environment
PDF_DIR = config.PDF_DIR
OUTPUT_DIR = config.PROCESSED_DIR
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class PDFExtractor:
    """Extract text from PDF files"""

    @staticmethod
    def extract_text(pdf_path: str) -> str:
        """Extract all text from a PDF"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                return text
        except Exception as e:
            print(f"     Error extracting {pdf_path}: {e}")
            return ""


class DocumentClassifier:
    """Classify documents based on content"""

    # Keywords for classification
    CLASSIFICATION_RULES = {
        'purchase_order': [
            r'\bPURCHASE\s+ORDER\b',
            r'\bPO\s+NUMBER\b',
            r'\bPO:\s*PO-',
            r'\bORDER\s+DATE\b',
            r'\bDELIVERY\s+DATE\b',
            r'\bBUYER\b'
        ],
        'invoice': [
            r'\bINVOICE\b',
            r'\bTAX\s+INVOICE\b',
            r'\bINVOICE\s+NUMBER\b',
            r'\bINVOICE\s+DATE\b',
            r'\bAMOUNT\s+DUE\b',
            r'\bDUE\s+DATE\b',
            r'\bPAYMENT\s+TERMS\b'
        ],
        'grn': [
            r'\bGOODS\s+RECEIVED\b',
            r'\bGOODS\s+RECEIPT\b',
            r'\bGRN\s+NUMBER\b',
            r'\bGRN:\s*GRN-',
            r'\bRECEIVED\s+BY\b',
            r'\bWAREHOUSE\b',
            r'\bQUANTITY\s+RECEIVED\b'
        ]
    }

    @staticmethod
    def classify(text: str, filename: str) -> str:
        """Classify document type based on content and filename"""
        text_upper = text.upper()

        # First, try filename-based classification
        if filename.startswith('PO-'):
            return 'purchase_order'
        elif filename.startswith('INV-'):
            return 'invoice'
        elif filename.startswith('GRN-'):
            return 'grn'

        # Content-based classification with scoring
        scores = defaultdict(int)

        for doc_type, patterns in DocumentClassifier.CLASSIFICATION_RULES.items():
            for pattern in patterns:
                if re.search(pattern, text_upper):
                    scores[doc_type] += 1

        # Return type with highest score
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]

        return 'unknown'


class DataExtractor:
    """Extract structured data from classified documents"""

    @staticmethod
    def extract(text: str, doc_type: str, filename: str) -> Optional[Dict[str, Any]]:
        """Main extraction method that routes to specific extractors"""
        if doc_type == 'purchase_order':
            data = DataExtractor.extract_purchase_order(text)
        elif doc_type == 'invoice':
            data = DataExtractor.extract_invoice(text)
        elif doc_type == 'grn':
            data = DataExtractor.extract_grn(text)
        else:
            return None

        # Add source file information
        if data:
            data['source_file'] = filename
            data['extraction_timestamp'] = datetime.now().isoformat()

        return data

    @staticmethod
    def extract_purchase_order(text: str) -> Dict[str, Any]:
        """Extract PO data"""
        data = {
            'document_type': 'purchase_order',
            'po_number': DataExtractor._extract_pattern(text, [
                r'PO\s+NUMBER:?\s*([A-Z0-9-]+)',
                r'PO:\s*([A-Z0-9-]+)',
                r'PURCHASE\s+ORDER\s*\n+([A-Z0-9-]+)'
            ]),
            'po_date': DataExtractor._extract_date(text, [
                r'ORDER\s+DATE:?\s*(\d{4}-\d{2}-\d{2})',
                r'PO\s+DATE:?\s*(\d{4}-\d{2}-\d{2})',
                r'DATE:?\s*(\d{4}-\d{2}-\d{2})'
            ]),
            'vendor_name': DataExtractor._extract_pattern(text, [
                r'VENDOR:?\s*\n*([A-Za-z\s&.,]+?)(?:\n|Vendor ID)',
                r'VENDOR:?\s*([A-Za-z\s&.,]+?)(?:\s{2,}|\n)'
            ]),
            'vendor_id': DataExtractor._extract_pattern(text, [
                r'VENDOR\s+ID:?\s*([A-Z0-9-]+)',
                r'Vendor ID:?\s*([A-Z0-9-]+)'
            ]),
            'buyer_name': DataExtractor._extract_pattern(text, [
                r'BUYER:?\s*\n*([A-Za-z\s.]+?)(?:\n|DEPARTMENT)',
                r'BUYER:?\s*([A-Za-z\s.]+?)(?:\s{2,}|\n)'
            ]),
            'department': DataExtractor._extract_pattern(text, [
                r'DEPARTMENT:?\s*\n*([A-Za-z\s&]+?)(?:\n|\s{2,})',
            ]),
            'delivery_date': DataExtractor._extract_date(text, [
                r'DELIVERY\s+DATE:?\s*(\d{4}-\d{2}-\d{2})',
            ]),
            'currency': DataExtractor._extract_pattern(text, [
                r'CURRENCY:?\s*([A-Z]{3})',
            ]),
            'total_amount': DataExtractor._extract_amount(text, [
                r'TOTAL:?\s*\$?([\d,]+\.?\d*)',
                r'GRAND\s+TOTAL:?\s*\$?([\d,]+\.?\d*)',
            ]),
            'subtotal': DataExtractor._extract_amount(text, [
                r'SUBTOTAL:?\s*\$?([\d,]+\.?\d*)',
                r'Subtotal:?\s*\$?([\d,]+\.?\d*)',
            ]),
            'tax': DataExtractor._extract_amount(text, [
                r'TAX:?\s*\$?([\d,]+\.?\d*)',
                r'Tax:?\s*\$?([\d,]+\.?\d*)',
            ]),
        }

        # Extract line items
        data['line_items'] = DataExtractor._extract_line_items(text)
        data['item_count'] = len(data['line_items'])

        return data

    @staticmethod
    def extract_invoice(text: str) -> Dict[str, Any]:
        """Extract Invoice data"""
        data = {
            'document_type': 'invoice',
            'invoice_number': DataExtractor._extract_pattern(text, [
                r'INVOICE\s+NUMBER:?\s*([A-Z0-9-]+)',
                r'INVOICE\s*\n+([A-Z0-9-]+)',
                r'Invoice\s*\n+([A-Z0-9-]+)'
            ]),
            'invoice_date': DataExtractor._extract_date(text, [
                r'INVOICE\s+DATE:?\s*(\d{4}-\d{2}-\d{2})',
                r'DATE:?\s*(\d{4}-\d{2}-\d{2})'
            ]),
            'due_date': DataExtractor._extract_date(text, [
                r'DUE\s+DATE:?\s*(\d{4}-\d{2}-\d{2})',
            ]),
            'vendor_name': DataExtractor._extract_pattern(text, [
                r'FROM:?\s*\n*([A-Za-z\s&.,]+?)(?:\n|Vendor ID)',
                r'FROM:?\s*([A-Za-z\s&.,]+?)(?:\s{2,}|\n)'
            ]),
            'vendor_id': DataExtractor._extract_pattern(text, [
                r'VENDOR\s+ID:?\s*([A-Z0-9-]+)',
                r'Vendor ID:?\s*([A-Z0-9-]+)'
            ]),
            'po_reference': DataExtractor._extract_pattern(text, [
                r'PO\s+REFERENCE:?\s*([A-Z0-9-]+)',
                r'PO Reference:?\s*([A-Z0-9-]+)'
            ]),
            'payment_terms': DataExtractor._extract_pattern(text, [
                r'PAYMENT\s+TERMS:?\s*\n*([A-Za-z0-9\s]+?)(?:\n|\s{2,})',
            ]),
            'currency': DataExtractor._extract_pattern(text, [
                r'CURRENCY:?\s*([A-Z]{3})',
            ]),
            'total_amount': DataExtractor._extract_amount(text, [
                r'AMOUNT\s+DUE:?\s*\$?([\d,]+\.?\d*)',
                r'TOTAL:?\s*\$?([\d,]+\.?\d*)',
            ]),
            'subtotal': DataExtractor._extract_amount(text, [
                r'SUBTOTAL:?\s*\$?([\d,]+\.?\d*)',
                r'Subtotal:?\s*\$?([\d,]+\.?\d*)',
            ]),
            'tax': DataExtractor._extract_amount(text, [
                r'TAX:?\s*\$?([\d,]+\.?\d*)',
                r'Tax:?\s*\$?([\d,]+\.?\d*)',
            ]),
        }

        # Extract line items
        data['line_items'] = DataExtractor._extract_line_items(text)
        data['item_count'] = len(data['line_items'])

        return data

    @staticmethod
    def extract_grn(text: str) -> Dict[str, Any]:
        """Extract GRN data"""
        data = {
            'document_type': 'grn',
            'grn_number': DataExtractor._extract_pattern(text, [
                r'GRN\s+NUMBER:?\s*([A-Z0-9-]+)',
                r'GRN:\s*([A-Z0-9-]+)',
                r'GOODS\s+RECEIVED\s*\n+([A-Z0-9-]+)'
            ]),
            'grn_date': DataExtractor._extract_date(text, [
                r'RECEIPT\s+DATE:?\s*(\d{4}-\d{2}-\d{2})',
                r'GRN\s+DATE:?\s*(\d{4}-\d{2}-\d{2})',
                r'DATE:?\s*(\d{4}-\d{2}-\d{2})'
            ]),
            'vendor_name': DataExtractor._extract_pattern(text, [
                r'VENDOR:?\s*\n*([A-Za-z\s&.,]+?)(?:\n|RECEIVED)',
                r'VENDOR:?\s*([A-Za-z\s&.,]+?)(?:\s{2,}|\n)'
            ]),
            'po_reference': DataExtractor._extract_pattern(text, [
                r'PO\s+REFERENCE:?\s*([A-Z0-9-]+)',
                r'PO Reference:?\s*([A-Z0-9-]+)'
            ]),
            'received_by': DataExtractor._extract_pattern(text, [
                r'RECEIVED\s+BY:?\s*\n*([A-Za-z\s.]+?)(?:\n|\s{2,})',
            ]),
            'warehouse': DataExtractor._extract_pattern(text, [
                r'WAREHOUSE:?\s*\n*([A-Za-z0-9\s-]+?)(?:\n|\s{2,})',
            ]),
        }

        # Extract received items
        data['received_items'] = DataExtractor._extract_grn_items(text)
        data['item_count'] = len(data['received_items'])

        # Calculate totals
        total_received = sum(item.get('quantity_received', 0) for item in data['received_items'])
        total_rejected = sum(item.get('quantity_rejected', 0) for item in data['received_items'])

        data['total_received'] = total_received
        data['total_rejected'] = total_rejected
        data['acceptance_rate'] = round((total_received / (total_received + total_rejected) * 100), 2) if (total_received + total_rejected) > 0 else 100.0

        return data

    @staticmethod
    def _extract_pattern(text: str, patterns: List[str]) -> Optional[str]:
        """Extract first match from multiple patterns"""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                result = match.group(1).strip()
                # Clean up common artifacts
                result = re.sub(r'\s+', ' ', result)
                return result
        return None

    @staticmethod
    def _extract_date(text: str, patterns: List[str]) -> Optional[str]:
        """Extract date"""
        date_str = DataExtractor._extract_pattern(text, patterns)
        if date_str:
            # Validate date format
            try:
                datetime.strptime(date_str, '%Y-%m-%d')
                return date_str
            except ValueError:
                pass
        return None

    @staticmethod
    def _extract_amount(text: str, patterns: List[str]) -> Optional[float]:
        """Extract monetary amount"""
        amount_str = DataExtractor._extract_pattern(text, patterns)
        if amount_str:
            # Remove commas and convert to float
            try:
                return float(amount_str.replace(',', ''))
            except ValueError:
                pass
        return None

    @staticmethod
    def _extract_line_items(text: str) -> List[Dict[str, Any]]:
        """Extract line items from PO/Invoice"""
        items = []

        # Look for item patterns in the text
        # Pattern: Item Code | Description | Quantity | Price | Total
        item_pattern = r'([A-Z]{3}-\d{3})\s+([A-Za-z\s\-&]+?)\s+(\d+)\s+\$?([\d,]+\.?\d*)\s+\$?([\d,]+\.?\d*)'

        matches = re.finditer(item_pattern, text)
        for match in matches:
            try:
                items.append({
                    'item_code': match.group(1).strip(),
                    'description': match.group(2).strip(),
                    'quantity': int(match.group(3)),
                    'unit_price': float(match.group(4).replace(',', '')),
                    'total': float(match.group(5).replace(',', ''))
                })
            except (ValueError, IndexError):
                continue

        return items

    @staticmethod
    def _extract_grn_items(text: str) -> List[Dict[str, Any]]:
        """Extract received items from GRN"""
        items = []

        # Pattern for GRN items: Item Code | Description | Received | Rejected | Status
        # Try multiple patterns for different layouts
        patterns = [
            r'([A-Z]{3}-\d{3})\s+([A-Za-z\s\-&]+?)\s+(\d+)\s+(\d+)\s+(OK|Issue|Good|Damaged)',
            r'([A-Z]{3}-\d{3})\s+([A-Za-z\s\-&]+?)\s+(\d+)\s+(\d+)\s+\s*OK',
            r'([A-Z]{3}-\d{3})\s+([A-Za-z\s\-&]+?)\s+(\d+)\s+(\d+)\s+✗\s*Issue',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    item_code = match.group(1).strip()
                    # Skip if already added
                    if any(item['item_code'] == item_code for item in items):
                        continue

                    received = int(match.group(3))
                    rejected = int(match.group(4))

                    items.append({
                        'item_code': item_code,
                        'description': match.group(2).strip(),
                        'quantity_received': received,
                        'quantity_rejected': rejected,
                        'condition': 'Good' if rejected == 0 else 'Damaged'
                    })
                except (ValueError, IndexError):
                    continue

        return items


class LLMDataExtractor:
    """Enhanced data extraction using Gemini 2.5 Flash LLM"""

    def __init__(self, api_key: str):
        """Initialize LLM extractor"""
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            self.enabled = True
        except Exception as e:
            print(f"     Could not initialize Gemini: {e}")
            self.enabled = False

    def extract_purchase_order(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract PO data using LLM"""
        if not self.enabled:
            return None

        prompt = f"""Extract structured data from this Purchase Order document. Return ONLY a valid JSON object with no additional text or markdown formatting.

Document Text:
{text}

Extract the following fields and return as JSON:
{{
  "po_number": "The purchase order number (e.g., PO-2024-01037)",
  "po_date": "The order date in YYYY-MM-DD format or null",
  "vendor_name": "The vendor/supplier company name",
  "vendor_id": "The vendor ID code or null",
  "buyer_name": "The buyer's name",
  "department": "The department name",
  "delivery_date": "The delivery date in YYYY-MM-DD format or null",
  "currency": "The currency code (e.g., USD, EUR) or null",
  "total_amount": The total amount as a number or null,
  "subtotal": The subtotal amount as a number or null,
  "tax": The tax amount as a number or null,
  "line_items": [
    {{
      "item_code": "Item code",
      "description": "Item description",
      "quantity": Quantity as integer,
      "unit_price": Unit price as number,
      "total": Line total as number
    }}
  ]
}}

Important:
- Return ONLY the JSON object, no markdown code blocks or explanations
- Use null for missing values, not empty strings
- Ensure all numbers are numeric types, not strings
- Be very careful to extract actual values, NOT field labels
- If you see "ORDER DATE" followed by a date, extract the date, not "ORDER DATE"
- If you see "VENDOR:" followed by a company name, extract the company name, not "VENDOR"
"""

        try:
            response = self.model.generate_content(prompt)
            # Clean the response to extract just the JSON
            response_text = response.text.strip()
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            data = json.loads(response_text)
            data['document_type'] = 'purchase_order'
            data['item_count'] = len(data.get('line_items', []))
            return data
        except Exception as e:
            print(f"     LLM extraction failed: {e}")
            return None

    def extract_invoice(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract Invoice data using LLM"""
        if not self.enabled:
            return None

        prompt = f"""Extract structured data from this Invoice document. Return ONLY a valid JSON object with no additional text or markdown formatting.

Document Text:
{text}

Extract the following fields and return as JSON:
{{
  "invoice_number": "The invoice number (e.g., INV-123456)",
  "invoice_date": "The invoice date in YYYY-MM-DD format or null",
  "due_date": "The payment due date in YYYY-MM-DD format or null",
  "vendor_name": "The vendor/supplier company name",
  "vendor_id": "The vendor ID code or null",
  "po_reference": "The referenced PO number or null",
  "payment_terms": "The payment terms (e.g., Net 30) or null",
  "currency": "The currency code (e.g., USD, EUR) or null",
  "total_amount": The total amount due as a number or null,
  "subtotal": The subtotal amount as a number or null,
  "tax": The tax amount as a number or null,
  "line_items": [
    {{
      "item_code": "Item code",
      "description": "Item description",
      "quantity": Quantity as integer,
      "unit_price": Unit price as number,
      "total": Line total as number
    }}
  ]
}}

Important:
- Return ONLY the JSON object, no markdown code blocks or explanations
- Use null for missing values, not empty strings
- Ensure all numbers are numeric types, not strings
- Be very careful to extract actual values, NOT field labels
"""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            data = json.loads(response_text)
            data['document_type'] = 'invoice'
            data['item_count'] = len(data.get('line_items', []))
            return data
        except Exception as e:
            print(f"     LLM extraction failed: {e}")
            return None

    def extract_grn(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract GRN data using LLM"""
        if not self.enabled:
            return None

        prompt = f"""Extract structured data from this Goods Received Note (GRN) document. Return ONLY a valid JSON object with no additional text or markdown formatting.

Document Text:
{text}

Extract the following fields and return as JSON:
{{
  "grn_number": "The GRN number (e.g., GRN-12345)",
  "grn_date": "The receipt date in YYYY-MM-DD format or null",
  "vendor_name": "The vendor/supplier company name",
  "po_reference": "The referenced PO number or null",
  "received_by": "Name of person who received the goods",
  "warehouse": "The warehouse name or location",
  "received_items": [
    {{
      "item_code": "Item code",
      "description": "Item description",
      "quantity_received": Quantity received as integer,
      "quantity_rejected": Quantity rejected as integer,
      "condition": "Good or Damaged"
    }}
  ]
}}

Important:
- Return ONLY the JSON object, no markdown code blocks or explanations
- Use null for missing values, not empty strings
- Ensure all numbers are numeric types, not strings
- Be very careful to extract actual values, NOT field labels
"""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            data = json.loads(response_text)
            data['document_type'] = 'grn'
            data['item_count'] = len(data.get('received_items', []))

            # Calculate totals
            received_items = data.get('received_items', [])
            total_received = sum(item.get('quantity_received', 0) for item in received_items)
            total_rejected = sum(item.get('quantity_rejected', 0) for item in received_items)

            data['total_received'] = total_received
            data['total_rejected'] = total_rejected
            data['acceptance_rate'] = round((total_received / (total_received + total_rejected) * 100), 2) if (total_received + total_rejected) > 0 else 100.0

            return data
        except Exception as e:
            print(f"     LLM extraction failed: {e}")
            return None


class IngestionPipeline:
    """Main pipeline orchestrator"""

    # Field labels that indicate erroneous extraction
    ERRONEOUS_VALUES = [
        'ORDER DATE', 'DELIVERY DATE', 'CURRENCY', 'VENDOR', 'BUYER',
        'DEPARTMENT', 'INVOICE DATE', 'DUE DATE', 'PAYMENT TERMS',
        'RECEIPT DATE', 'WAREHOUSE', 'RECEIVED BY'
    ]

    def __init__(self, pdf_directory: Path, use_llm: bool = True, fix_mode: bool = False):
        self.pdf_directory = pdf_directory
        self.extractor = PDFExtractor()
        self.classifier = DocumentClassifier()
        self.data_extractor = DataExtractor()
        self.llm_extractor = LLMDataExtractor(config.GEMINI_API_KEY) if use_llm else None
        self.fix_mode = fix_mode

        self.stats = {
            'total_files': 0,
            'processed': 0,
            'failed': 0,
            'by_type': defaultdict(int),
            'by_layout': defaultdict(int),
            'llm_extractions': 0,
            'regex_extractions': 0,
            'fixed': 0,
            'skipped_good': 0
        }

        self.results = {
            'purchase_orders': [],
            'invoices': [],
            'grns': [],
            'unknown': []
        }

        # Load existing documents if in fix mode
        if self.fix_mode:
            self._load_existing_documents()

    def _load_existing_documents(self):
        """Load existing processed documents"""
        print("\n Loading existing documents...")

        for doc_type in ['purchase_orders', 'invoices', 'grns']:
            file_path = OUTPUT_DIR / f"{doc_type}.json"
            if file_path.exists():
                with open(file_path, 'r') as f:
                    self.results[doc_type] = json.load(f)

    def _is_problematic_document(self, doc: Dict[str, Any], doc_type: str) -> tuple[bool, List[str]]:
        """Check if a document has null or erroneous values"""
        issues = []

        if doc_type == 'purchase_order':
            if not doc.get('po_number'):
                issues.append('Missing PO number')
            if not doc.get('po_date'):
                issues.append('Missing PO date')
            if not doc.get('vendor_name') or doc.get('vendor_name') in self.ERRONEOUS_VALUES:
                issues.append(f"Invalid vendor: {doc.get('vendor_name')}")
            if not doc.get('buyer_name') or doc.get('buyer_name') in self.ERRONEOUS_VALUES:
                issues.append(f"Invalid buyer: {doc.get('buyer_name')}")
            if not doc.get('department') or doc.get('department') in self.ERRONEOUS_VALUES:
                issues.append(f"Invalid department: {doc.get('department')}")
            if not doc.get('delivery_date'):
                issues.append('Missing delivery date')
            if not doc.get('currency'):
                issues.append('Missing currency')

        elif doc_type == 'invoice':
            if not doc.get('invoice_number'):
                issues.append('Missing invoice number')
            if not doc.get('invoice_date'):
                issues.append('Missing invoice date')
            if not doc.get('vendor_name') or doc.get('vendor_name') in self.ERRONEOUS_VALUES:
                issues.append(f"Invalid vendor: {doc.get('vendor_name')}")
            if not doc.get('due_date'):
                issues.append('Missing due date')

        elif doc_type == 'grn':
            if not doc.get('grn_number'):
                issues.append('Missing GRN number')
            if not doc.get('grn_date'):
                issues.append('Missing GRN date')
            if not doc.get('vendor_name') or doc.get('vendor_name') in self.ERRONEOUS_VALUES:
                issues.append(f"Invalid vendor: {doc.get('vendor_name')}")

        return len(issues) > 0, issues

    def _find_existing_document(self, filename: str) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Find existing document by filename"""
        for doc_type in ['purchase_orders', 'invoices', 'grns']:
            for doc in self.results[doc_type]:
                if doc.get('metadata', {}).get('filename') == filename:
                    return doc, doc_type
        return None, None

    def process_pdf(self, pdf_path: Path) -> Optional[Dict[str, Any]]:
        """Process a single PDF"""
        try:
            # In fix mode, check if this document needs fixing
            if self.fix_mode:
                existing_doc, existing_type = self._find_existing_document(pdf_path.name)

                if existing_doc:
                    is_prob, issues = self._is_problematic_document(existing_doc, existing_type)

                    if not is_prob:
                        # Document is fine, skip it
                        self.stats['skipped_good'] += 1
                        return None
                    else:
                        # Document is problematic, will re-extract with LLM
                        print(f"\n     Problematic: {pdf_path.name}")
                        print(f"       Issues: {', '.join(issues)}")
                        print(f"       Re-extracting with LLM...")

            # Extract text
            text = self.extractor.extract_text(str(pdf_path))
            if not text:
                return None

            # Classify document
            doc_type = self.classifier.classify(text, pdf_path.name)

            # Extract layout from filename
            layout = 'unknown'
            if '_modern.pdf' in pdf_path.name:
                layout = 'modern'
            elif '_classic.pdf' in pdf_path.name:
                layout = 'classic'
            elif '_creative.pdf' in pdf_path.name:
                layout = 'creative'

            # Try regex extraction first
            data = None
            extraction_method = 'regex'

            # First attempt: regex extraction
            if doc_type == 'purchase_order':
                data = self.data_extractor.extract_purchase_order(text)
            elif doc_type == 'invoice':
                data = self.data_extractor.extract_invoice(text)
            elif doc_type == 'grn':
                data = self.data_extractor.extract_grn(text)
            else:
                data = {'document_type': 'unknown'}

            # Check if regex result is problematic
            if data and doc_type in ['purchase_order', 'invoice', 'grn']:
                is_prob, issues = self._is_problematic_document(data, doc_type)

                # If problematic and LLM is available, retry with LLM
                if is_prob and self.llm_extractor and self.llm_extractor.enabled:
                    print(f"     Regex extraction issues for {pdf_path.name}: {', '.join(issues[:2])}")
                    print(f"    Re-extracting with LLM...")

                    llm_data = None
                    if doc_type == 'purchase_order':
                        llm_data = self.llm_extractor.extract_purchase_order(text)
                    elif doc_type == 'invoice':
                        llm_data = self.llm_extractor.extract_invoice(text)
                    elif doc_type == 'grn':
                        llm_data = self.llm_extractor.extract_grn(text)

                    if llm_data:
                        data = llm_data
                        extraction_method = 'llm'
                        self.stats['llm_extractions'] += 1
                    else:
                        self.stats['regex_extractions'] += 1
                else:
                    self.stats['regex_extractions'] += 1
            else:
                self.stats['regex_extractions'] += 1

            # Add metadata
            data['metadata'] = {
                'filename': pdf_path.name,
                'file_size': pdf_path.stat().st_size,
                'layout_style': layout,
                'processed_at': datetime.now().isoformat(),
                'extraction_method': extraction_method,
                'extraction_confidence': 'high' if data.get('po_number') or data.get('invoice_number') or data.get('grn_number') else 'low'
            }

            # Mark as re-extracted if in fix mode
            if self.fix_mode:
                data['metadata']['re_extracted'] = True
                self.stats['fixed'] += 1

            # Update stats
            self.stats['by_type'][doc_type] += 1
            self.stats['by_layout'][layout] += 1

            return data

        except Exception as e:
            print(f"     Error processing {pdf_path.name}: {e}")
            self.stats['failed'] += 1
            return None

    def run(self) -> Dict[str, Any]:
        """Run the ingestion pipeline"""
        print("=" * 80)
        if self.fix_mode:
            print(" PDF FIX MODE - Re-extracting Problematic Documents")
        else:
            print(" PDF DATA INGESTION PIPELINE")
        print("=" * 80)

        # Get all PDFs
        pdf_files = sorted(self.pdf_directory.glob("*.pdf"))
        self.stats['total_files'] = len(pdf_files)

        print(f"\n Found {len(pdf_files)} PDF files in {self.pdf_directory}")
        if self.fix_mode:
            pass
        print("\n Processing documents...")

        # Process each PDF
        for i, pdf_path in enumerate(pdf_files, 1):
            data = self.process_pdf(pdf_path)

            if data:
                doc_type = data['document_type']

                # In fix mode, update existing document instead of appending
                if self.fix_mode:
                    filename = pdf_path.name
                    updated = False

                    # Find and replace the document
                    for idx, doc in enumerate(self.results[f"{doc_type}s"]):
                        if doc.get('metadata', {}).get('filename') == filename:
                            self.results[f"{doc_type}s"][idx] = data
                            updated = True
                            break

                    if not updated:
                        # If not found, append (shouldn't happen but just in case)
                        self.results[f"{doc_type}s"].append(data)
                else:
                    # Normal mode: append new documents
                    if doc_type == 'purchase_order':
                        self.results['purchase_orders'].append(data)
                    elif doc_type == 'invoice':
                        self.results['invoices'].append(data)
                    elif doc_type == 'grn':
                        self.results['grns'].append(data)
                    else:
                        self.results['unknown'].append(data)

                self.stats['processed'] += 1

            # Progress indicator
            if i % 25 == 0:
                print(f"    Processed {i}/{len(pdf_files)} files...")

        print(f"    Processing complete!")

        return self.results

    def save_results(self, output_dir: Path):
        """Save extracted data to JSON files"""
        print("\n Saving results...")

        # Save each document type separately
        for doc_type, documents in self.results.items():
            if documents:
                output_file = output_dir / f"{doc_type}.json"
                with open(output_file, 'w') as f:
                    json.dump(documents, f, indent=2)
                print(f"    Saved {len(documents)} {doc_type} to {output_file}")

        # Save combined results
        combined_file = output_dir / "all_documents.json"
        with open(combined_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"    Saved combined data to {combined_file}")

        # Save statistics
        stats_file = output_dir / "ingestion_stats.json"
        stats_data = {
            'summary': dict(self.stats),
            'details': {
                'total_files': self.stats['total_files'],
                'successfully_processed': self.stats['processed'],
                'failed': self.stats['failed'],
                'success_rate': round(self.stats['processed'] / self.stats['total_files'] * 100, 2) if self.stats['total_files'] > 0 else 0
            },
            'breakdown': {
                'by_document_type': dict(self.stats['by_type']),
                'by_layout_style': dict(self.stats['by_layout'])
            },
            'timestamp': datetime.now().isoformat()
        }

        with open(stats_file, 'w') as f:
            json.dump(stats_data, f, indent=2)
        print(f"    Saved statistics to {stats_file}")

    def print_summary(self):
        """Print pipeline summary"""
        print("=" * 80)
        print(" INGESTION SUMMARY")
        print("=" * 80)

        print(f"\n Overall Statistics:")
        print(f"   • Total Files: {self.stats['total_files']}")
        print(f"   • Successfully Processed: {self.stats['processed']}")
        print(f"   • Failed: {self.stats['failed']}")
        success_rate = (self.stats['processed'] / self.stats['total_files'] * 100) if self.stats['total_files'] > 0 else 0
        print(f"   • Success Rate: {success_rate:.1f}%")

        print(f"\n Extraction Method:")
        print(f"   • LLM (Gemini 2.5 Flash): {self.stats['llm_extractions']}")
        print(f"   • Regex (Fallback): {self.stats['regex_extractions']}")

        if self.fix_mode:
            print(f"\n Fix Mode Statistics:")
            print(f"   • Documents Fixed: {self.stats['fixed']}")
            print(f"   • Skipped (Already Good): {self.stats['skipped_good']}")

        print(f"\n By Document Type:")
        for doc_type, count in sorted(self.stats['by_type'].items()):
            print(f"   • {doc_type.replace('_', ' ').title()}: {count}")

        print(f"\n By Layout Style:")
        for layout, count in sorted(self.stats['by_layout'].items()):
            print(f"   • {layout.title()}: {count}")

        print(f"\n Extracted Documents:")
        print(f"   • Purchase Orders: {len(self.results['purchase_orders'])}")
        print(f"   • Invoices: {len(self.results['invoices'])}")
        print(f"   • GRNs: {len(self.results['grns'])}")
        print(f"   • Unknown: {len(self.results['unknown'])}")

        # Sample data
        if self.results['purchase_orders']:
            print(f"\n Sample Purchase Order:")
            sample = self.results['purchase_orders'][0]
            print(f"   • PO Number: {sample.get('po_number', 'N/A')}")
            print(f"   • Vendor: {sample.get('vendor_name', 'N/A')}")
            print(f"   • Total: ${sample.get('total_amount', 0):.2f}")
            print(f"   • Items: {sample.get('item_count', 0)}")
            print(f"   • Layout: {sample['metadata']['layout_style']}")

        if self.results['invoices']:
            print(f"\n Sample Invoice:")
            sample = self.results['invoices'][0]
            print(f"   • Invoice Number: {sample.get('invoice_number', 'N/A')}")
            print(f"   • Vendor: {sample.get('vendor_name', 'N/A')}")
            print(f"   • Amount Due: ${sample.get('total_amount', 0):.2f}")
            print(f"   • Items: {sample.get('item_count', 0)}")
            print(f"   • Layout: {sample['metadata']['layout_style']}")

        if self.results['grns']:
            print(f"\n Sample GRN:")
            sample = self.results['grns'][0]
            print(f"   • GRN Number: {sample.get('grn_number', 'N/A')}")
            print(f"   • Vendor: {sample.get('vendor_name', 'N/A')}")
            print(f"   • Total Received: {sample.get('total_received', 0)}")
            print(f"   • Total Rejected: {sample.get('total_rejected', 0)}")
            print(f"   • Acceptance Rate: {sample.get('acceptance_rate', 0):.1f}%")
            print(f"   • Layout: {sample['metadata']['layout_style']}")


def main():
    """Main entry point"""
    import sys

    # Check for fix mode flag
    fix_mode = '--fix' in sys.argv or '-f' in sys.argv

    if fix_mode:
        print("""

                                                                          
              PDF FIX MODE - Re-extract Problematic Documents             
                                                                          
   Using Gemini 2.5 Flash to fix PDFs with null/erroneous values         
                                                                          

""")
    else:
        print("""

                                                                          
              PDF DATA INGESTION PIPELINE                                 
                                                                          
   Automated extraction and classification of PDF documents              
                                                                          

""")

    # Initialize and run pipeline
    pipeline = IngestionPipeline(PDF_DIR, use_llm=True, fix_mode=fix_mode)
    results = pipeline.run()

    # Save results
    pipeline.save_results(OUTPUT_DIR)

    # Print summary
    pipeline.print_summary()

    print("=" * 80)
    print(" PIPELINE COMPLETE!")
    print("=" * 80)
    print(f"\n Output Directory: {OUTPUT_DIR}")

    if fix_mode:
        print(f"\n Next Steps:")
        print(f"   1. Clear vector store: rm -rf data/vector_store/*")
        print(f"   2. Restart backend to rebuild with fixed data")
    else:
        print(f"\n Next Steps:")
        print(f"   1. Review extracted data: cat {OUTPUT_DIR}/ingestion_stats.json")
        print(f"   2. To fix problematic PDFs, run: python3 scripts/pdf_ingestion_pipeline.py --fix")
    print()


if __name__ == "__main__":
    main()
