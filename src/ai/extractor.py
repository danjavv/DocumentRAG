"""
AI-powered data extraction from classified documents
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
import pdfplumber
import json

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text content from PDF"""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error extracting text: {e}")
    return text.strip()


def get_extraction_schema(document_type: str) -> dict:
    """Get the expected schema for each document type"""
    schemas = {
        "purchase_order": {
            "po_number": "string",
            "po_date": "YYYY-MM-DD",
            "vendor_name": "string",
            "vendor_id": "string or null",
            "buyer_name": "string or null",
            "department": "string or null",
            "line_items": [
                {
                    "item_code": "string",
                    "description": "string",
                    "quantity": "number",
                    "unit_price": "number",
                    "total": "number"
                }
            ],
            "subtotal": "number",
            "tax": "number",
            "total_amount": "number",
            "currency": "string",
            "delivery_address": "string or null",
            "delivery_date": "YYYY-MM-DD or null"
        },
        "invoice": {
            "invoice_number": "string",
            "invoice_date": "YYYY-MM-DD",
            "po_reference": "string or null",
            "vendor_name": "string",
            "vendor_id": "string or null",
            "line_items": [
                {
                    "item_code": "string",
                    "description": "string",
                    "quantity": "number",
                    "unit_price": "number",
                    "total": "number"
                }
            ],
            "subtotal": "number",
            "tax": "number",
            "total_amount": "number",
            "currency": "string",
            "payment_terms": "string or null",
            "due_date": "YYYY-MM-DD or null"
        },
        "goods_received_note": {
            "grn_number": "string",
            "grn_date": "YYYY-MM-DD",
            "po_reference": "string or null",
            "vendor_name": "string",
            "received_by": "string or null",
            "warehouse": "string or null",
            "line_items": [
                {
                    "item_code": "string",
                    "description": "string",
                    "quantity_received": "number",
                    "quantity_rejected": "number",
                    "condition": "string"
                }
            ]
        }
    }
    return schemas.get(document_type, {})


def extract_data(pdf_path: str, document_type: str) -> dict:
    """
    Extract structured data from a document

    Args:
        pdf_path: Path to PDF file
        document_type: Type of document (purchase_order, invoice, goods_received_note)

    Returns:
        dict: Extracted structured data
    """
    # Extract text from PDF
    text = extract_text_from_pdf(pdf_path)

    if not text:
        return {"error": "No text could be extracted from PDF"}

    # Get schema for this document type
    schema = get_extraction_schema(document_type)

    if not schema:
        return {"error": f"Unknown document type: {document_type}"}

    # Create extraction prompt
    extraction_prompt = f"""
Extract structured data from this {document_type.replace('_', ' ')} document.

Expected output schema:
{json.dumps(schema, indent=2)}

Document text:
{text}

Instructions:
1. Extract ALL fields that are present in the document
2. Use null for fields that are not found
3. For dates, use YYYY-MM-DD format
4. For numbers, use numeric values (not strings)
5. Be precise with amounts and calculations
6. Extract ALL line items, don't skip any

Return ONLY valid JSON matching the schema above.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a data extraction expert. Extract information accurately from documents and return structured JSON."
                },
                {
                    "role": "user",
                    "content": extraction_prompt
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )

        extracted_data = json.loads(response.choices[0].message.content)

        # Add metadata
        extracted_data["_metadata"] = {
            "extraction_model": "gpt-4-turbo-preview",
            "source_file": os.path.basename(pdf_path),
            "document_type": document_type
        }

        return extracted_data

    except Exception as e:
        print(f"Error extracting data: {e}")
        return {"error": f"Extraction failed: {str(e)}"}


if __name__ == "__main__":
    # Test the extractor
    test_cases = [
        ("data/synthetic/pdfs/PO-2024-01001.pdf", "purchase_order"),
        ("data/synthetic/pdfs/INV-005001.pdf", "invoice"),
        ("data/synthetic/pdfs/GRN-08001.pdf", "goods_received_note")
    ]

    for pdf_path, doc_type in test_cases:
        if os.path.exists(pdf_path):
            print(f"\n{'='*70}")
            print(f"Testing: {os.path.basename(pdf_path)} ({doc_type})")
            print('='*70)

            result = extract_data(pdf_path, doc_type)

            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                # Pretty print key fields
                if doc_type == "purchase_order":
                    print(f"PO Number: {result.get('po_number')}")
                    print(f"Vendor: {result.get('vendor_name')}")
                    print(f"Total: ${result.get('total_amount', 0):.2f}")
                    print(f"Line Items: {len(result.get('line_items', []))}")
                elif doc_type == "invoice":
                    print(f"Invoice Number: {result.get('invoice_number')}")
                    print(f"PO Reference: {result.get('po_reference')}")
                    print(f"Total: ${result.get('total_amount', 0):.2f}")
                elif doc_type == "goods_received_note":
                    print(f"GRN Number: {result.get('grn_number')}")
                    print(f"PO Reference: {result.get('po_reference')}")
                    print(f"Items: {len(result.get('line_items', []))}")
        else:
            print(f"File not found: {pdf_path}")
