"""
AI-powered document classifier using OpenAI GPT-4
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
import pdfplumber
from pathlib import Path

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
        print(f"Error extracting text from {pdf_path}: {e}")
    return text.strip()


def classify_document(pdf_path: str) -> dict:
    """
    Classify a document using GPT-4

    Returns:
        dict with:
            - document_type: str (purchase_order, invoice, goods_received_note, unknown)
            - confidence: float (0-1)
            - reasoning: str
    """
    # Extract text from PDF
    text = extract_text_from_pdf(pdf_path)

    if not text:
        return {
            "document_type": "unknown",
            "confidence": 0.0,
            "reasoning": "No text could be extracted from PDF"
        }

    # Limit text to first 2000 characters for classification
    text_sample = text[:2000]

    classification_prompt = f"""
Analyze this document and classify it into ONE of these categories:
1. purchase_order - A purchase order from a buyer to a vendor
2. invoice - A bill/invoice from a vendor requesting payment
3. goods_received_note - A document confirming receipt of goods
4. unknown - If it doesn't fit any category

Document text:
{text_sample}

Respond in JSON format with:
- document_type: one of the categories above
- confidence: a number between 0 and 1
- reasoning: brief explanation of classification

Example:
{{"document_type": "invoice", "confidence": 0.95, "reasoning": "Contains invoice number, amount due, and payment terms"}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a document classification expert. Analyze documents and classify them accurately."
                },
                {
                    "role": "user",
                    "content": classification_prompt
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )

        import json
        result = json.loads(response.choices[0].message.content)

        # Validate response
        valid_types = ["purchase_order", "invoice", "goods_received_note", "unknown"]
        if result.get("document_type") not in valid_types:
            result["document_type"] = "unknown"
            result["confidence"] = 0.5

        return result

    except Exception as e:
        print(f"Error classifying document: {e}")
        return {
            "document_type": "unknown",
            "confidence": 0.0,
            "reasoning": f"Classification error: {str(e)}"
        }


if __name__ == "__main__":
    # Test the classifier
    test_pdf = "data/synthetic/pdfs/PO-2024-01001.pdf"
    if os.path.exists(test_pdf):
        result = classify_document(test_pdf)
        print(f"\nClassification Result:")
        print(f"  Type: {result['document_type']}")
        print(f"  Confidence: {result['confidence']:.2%}")
        print(f"  Reasoning: {result['reasoning']}")
    else:
        print("Test PDF not found. Please run generate_pdf_documents.py first.")
