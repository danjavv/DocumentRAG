#!/usr/bin/env python3
"""
RAG System for Procurement Document Analysis
Uses structured JSON data to build a retrieval-augmented generation system
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Install required packages
required_packages = [
    "chromadb",
    "sentence-transformers",
    "google-generativeai"
]
for package in required_packages:
    try:
        if package == "google-generativeai":
            import google.generativeai as genai
        else:
            __import__(package.replace("-", "_"))
    except ImportError:
        import subprocess
        subprocess.check_call(["pip3", "install", "--break-system-packages", package])

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# Configuration
PROCESSED_DIR = Path("data/processed")
VECTOR_DB_DIR = Path("data/vector_store")
VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)


class DocumentLoader:
    """Load and prepare structured JSON documents"""

    @staticmethod
    def load_all_documents() -> Dict[str, List[Dict[str, Any]]]:
        """Load all processed documents"""
        print("\n Loading structured documents...")

        documents = {
            'purchase_orders': [],
            'invoices': [],
            'grns': []
        }

        # Load Purchase Orders
        po_file = PROCESSED_DIR / "purchase_orders.json"
        if po_file.exists():
            with open(po_file) as f:
                documents['purchase_orders'] = json.load(f)
            print(f"    Loaded {len(documents['purchase_orders'])} Purchase Orders")

        # Load Invoices
        inv_file = PROCESSED_DIR / "invoices.json"
        if inv_file.exists():
            with open(inv_file) as f:
                documents['invoices'] = json.load(f)
            print(f"    Loaded {len(documents['invoices'])} Invoices")

        # Load GRNs
        grn_file = PROCESSED_DIR / "grns.json"
        if grn_file.exists():
            with open(grn_file) as f:
                documents['grns'] = json.load(f)
            print(f"    Loaded {len(documents['grns'])} GRNs")

        total = sum(len(docs) for docs in documents.values())
        print(f"    Total documents loaded: {total}\n")

        return documents

    @staticmethod
    def create_text_representation(doc: Dict[str, Any]) -> str:
        """Create a searchable text representation of a document"""
        doc_type = doc.get('document_type', 'unknown')

        if doc_type == 'purchase_order':
            return DocumentLoader._create_po_text(doc)
        elif doc_type == 'invoice':
            return DocumentLoader._create_invoice_text(doc)
        elif doc_type == 'grn':
            return DocumentLoader._create_grn_text(doc)
        else:
            return json.dumps(doc)

    @staticmethod
    def _create_po_text(po: Dict[str, Any]) -> str:
        """Create searchable text for Purchase Order"""
        parts = [
            f"Purchase Order {po.get('po_number', 'N/A')}",
            f"Document Type: Purchase Order",
        ]

        if po.get('po_date'):
            parts.append(f"Order Date: {po['po_date']}")

        if po.get('vendor_name'):
            parts.append(f"Vendor: {po['vendor_name']}")

        if po.get('vendor_id'):
            parts.append(f"Vendor ID: {po['vendor_id']}")

        if po.get('buyer_name'):
            parts.append(f"Buyer: {po['buyer_name']}")

        if po.get('department'):
            parts.append(f"Department: {po['department']}")

        if po.get('delivery_date'):
            parts.append(f"Delivery Date: {po['delivery_date']}")

        if po.get('total_amount'):
            parts.append(f"Total Amount: ${po['total_amount']:.2f}")

        if po.get('currency'):
            parts.append(f"Currency: {po['currency']}")

        if po.get('subtotal'):
            parts.append(f"Subtotal: ${po['subtotal']:.2f}")

        if po.get('tax'):
            parts.append(f"Tax: ${po['tax']:.2f}")

        # Add line items if available
        if po.get('line_items'):
            parts.append("Items:")
            for item in po['line_items']:
                parts.append(f"  - {item.get('description', 'Item')}: {item.get('quantity', 0)} units at ${item.get('unit_price', 0):.2f}")

        # Add metadata
        if po.get('metadata'):
            parts.append(f"Layout Style: {po['metadata'].get('layout_style', 'unknown')}")

        return "\n".join(parts)

    @staticmethod
    def _create_invoice_text(inv: Dict[str, Any]) -> str:
        """Create searchable text for Invoice"""
        parts = [
            f"Invoice {inv.get('invoice_number', 'N/A')}",
            f"Document Type: Invoice",
        ]

        if inv.get('invoice_date'):
            parts.append(f"Invoice Date: {inv['invoice_date']}")

        if inv.get('due_date'):
            parts.append(f"Due Date: {inv['due_date']}")

        if inv.get('vendor_name'):
            parts.append(f"Vendor: {inv['vendor_name']}")

        if inv.get('vendor_id'):
            parts.append(f"Vendor ID: {inv['vendor_id']}")

        if inv.get('po_reference'):
            parts.append(f"PO Reference: {inv['po_reference']}")

        if inv.get('payment_terms'):
            parts.append(f"Payment Terms: {inv['payment_terms']}")

        if inv.get('total_amount'):
            parts.append(f"Amount Due: ${inv['total_amount']:.2f}")

        if inv.get('currency'):
            parts.append(f"Currency: {inv['currency']}")

        if inv.get('subtotal'):
            parts.append(f"Subtotal: ${inv['subtotal']:.2f}")

        if inv.get('tax'):
            parts.append(f"Tax: ${inv['tax']:.2f}")

        # Add line items if available
        if inv.get('line_items'):
            parts.append("Items:")
            for item in inv['line_items']:
                parts.append(f"  - {item.get('description', 'Item')}: {item.get('quantity', 0)} units at ${item.get('unit_price', 0):.2f}")

        # Add metadata
        if inv.get('metadata'):
            parts.append(f"Layout Style: {inv['metadata'].get('layout_style', 'unknown')}")

        return "\n".join(parts)

    @staticmethod
    def _create_grn_text(grn: Dict[str, Any]) -> str:
        """Create searchable text for GRN"""
        parts = [
            f"Goods Received Note {grn.get('grn_number', 'N/A')}",
            f"Document Type: Goods Received Note",
        ]

        if grn.get('grn_date'):
            parts.append(f"Receipt Date: {grn['grn_date']}")

        if grn.get('vendor_name'):
            parts.append(f"Vendor: {grn['vendor_name']}")

        if grn.get('po_reference'):
            parts.append(f"PO Reference: {grn['po_reference']}")

        if grn.get('received_by'):
            parts.append(f"Received By: {grn['received_by']}")

        if grn.get('warehouse'):
            parts.append(f"Warehouse: {grn['warehouse']}")

        if grn.get('total_received') is not None:
            parts.append(f"Total Items Received: {grn['total_received']}")

        if grn.get('total_rejected') is not None:
            parts.append(f"Total Items Rejected: {grn['total_rejected']}")

        if grn.get('acceptance_rate') is not None:
            parts.append(f"Acceptance Rate: {grn['acceptance_rate']:.1f}%")

        # Add received items if available
        if grn.get('received_items'):
            parts.append("Received Items:")
            for item in grn['received_items']:
                condition = item.get('condition', 'Unknown')
                parts.append(f"  - {item.get('description', 'Item')}: {item.get('quantity_received', 0)} received, "
                           f"{item.get('quantity_rejected', 0)} rejected ({condition})")

        # Add metadata
        if grn.get('metadata'):
            parts.append(f"Layout Style: {grn['metadata'].get('layout_style', 'unknown')}")

        return "\n".join(parts)

    @staticmethod
    def create_metadata(doc: Dict[str, Any]) -> Dict[str, Any]:
        """Create metadata for vector store (ChromaDB requires non-None values)"""
        metadata = {
            'document_type': doc.get('document_type', 'unknown'),
            'filename': doc.get('metadata', {}).get('filename', 'unknown'),
            'layout_style': doc.get('metadata', {}).get('layout_style', 'unknown'),
        }

        # Add type-specific identifiers
        if doc.get('po_number'):
            metadata['doc_id'] = str(doc['po_number'])
            metadata['vendor'] = str(doc.get('vendor_name') or 'Unknown')
            metadata['amount'] = float(doc.get('total_amount') or 0)
            metadata['date'] = str(doc.get('po_date') or 'Unknown')
        elif doc.get('invoice_number'):
            metadata['doc_id'] = str(doc['invoice_number'])
            metadata['vendor'] = str(doc.get('vendor_name') or 'Unknown')
            metadata['amount'] = float(doc.get('total_amount') or 0)
            metadata['date'] = str(doc.get('invoice_date') or 'Unknown')
        elif doc.get('grn_number'):
            metadata['doc_id'] = str(doc['grn_number'])
            metadata['vendor'] = str(doc.get('vendor_name') or 'Unknown')
            metadata['date'] = str(doc.get('grn_date') or 'Unknown')
            metadata['amount'] = 0.0  # GRNs don't have amounts

        # Ensure all values are non-None (ChromaDB requirement)
        metadata = {k: (v if v is not None else 'Unknown') for k, v in metadata.items()}

        return metadata


class VectorStore:
    """Manage vector embeddings and retrieval"""

    def __init__(self, collection_name: str = "procurement_docs", reset: bool = False):
        """Initialize vector store"""
        print("\n Initializing Vector Store...")

        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))
        self.collection_name = collection_name
        self.doc_counter = 0

        # Delete existing collection if reset=True
        if reset:
            try:
                self.client.delete_collection(name=collection_name)
            except:
                pass

        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            self.doc_counter = self.collection.count()
            print(f"    Loaded existing collection with {self.doc_counter} documents")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Procurement documents - POs, Invoices, GRNs"}
            )
        # Initialize embedding model
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        print("    Vector store initialized\n")

    def add_documents(self, documents: Dict[str, List[Dict[str, Any]]]):
        """Add documents to vector store"""
        print("Building vector index...")

        all_texts = []
        all_metadatas = []
        all_ids = []

        doc_count = 0
        for doc_type, docs in documents.items():
            for doc in docs:
                # Create text representation
                text = DocumentLoader.create_text_representation(doc)
                metadata = DocumentLoader.create_metadata(doc)

                # Create unique ID
                doc_id = f"{doc_type}_{self.doc_counter + doc_count}"

                all_texts.append(text)
                all_metadatas.append(metadata)
                all_ids.append(doc_id)

                doc_count += 1

        # Create embeddings
        embeddings = self.embedder.encode(all_texts, show_progress_bar=True)

        # Add to ChromaDB
        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=all_texts,
            metadatas=all_metadatas,
            ids=all_ids
        )

        self.doc_counter += len(all_texts)
        print(f"    Added {len(all_texts)} documents to vector store\n")

    def add_single_document(self, doc: Dict[str, Any], doc_type: str) -> bool:
        """Add a single document to vector store dynamically"""
        try:
            # Create text representation
            text = DocumentLoader.create_text_representation(doc)
            metadata = DocumentLoader.create_metadata(doc)

            # Create unique ID
            doc_id = f"{doc_type}_{self.doc_counter}"

            # Create embedding
            embedding = self.embedder.encode([text])[0]

            # Add to ChromaDB
            self.collection.add(
                embeddings=[embedding.tolist()],
                documents=[text],
                metadatas=[metadata],
                ids=[doc_id]
            )

            self.doc_counter += 1
            return True

        except Exception as e:
            print(f"    Error adding document: {e}")
            return False

    def search(self, query: str, n_results: int = 5, filter_dict: Optional[Dict] = None) -> Dict[str, Any]:
        """Search for relevant documents"""
        # Create query embedding
        query_embedding = self.embedder.encode([query])[0]

        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results,
            where=filter_dict
        )

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        count = self.collection.count()
        return {
            'total_documents': count,
            'collection_name': self.collection.name
        }


class RAGSystem:
    """Complete RAG system with LLM integration"""

    def __init__(self, gemini_api_key: Optional[str] = None):
        """Initialize RAG system"""
        self.vector_store = None
        self.use_gemini = False
        self.gemini_model = None

        # Initialize Gemini if API key provided
        if gemini_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=gemini_api_key)
                self.gemini_model = genai.GenerativeModel('gemini-2.5-flash')
                self.use_gemini = True
                print("    Gemini 2.5 Flash client initialized")
            except Exception as e:
                print(f"     Could not initialize Gemini: {e}")
                print(f"   Using local template-based generation")
                self.use_gemini = False

    def initialize(self):
        """Initialize the RAG system"""
        print("\n" + "="*80)
        print(" INITIALIZING RAG SYSTEM")
        print("="*80)

        # Load documents
        documents = DocumentLoader.load_all_documents()

        # Initialize vector store
        self.vector_store = VectorStore()

        # Only add documents if collection is empty or newly created
        current_count = self.vector_store.collection.count()
        if current_count == 0:
            print(f"    Collection is empty, adding {sum(len(docs) for docs in documents.values())} documents...")
            # Add documents to vector store
            self.vector_store.add_documents(documents)
        else:
            print(f"    Collection already contains {current_count} documents, skipping initial load")
            print(f"    To reset the collection, delete the vector store directory: {VECTOR_DB_DIR}")

        # Print stats
        stats = self.vector_store.get_stats()
        print("="*80)
        print(f" RAG System Ready!")
        print(f"   Total documents indexed: {stats['total_documents']}")
        print(f"   LLM Mode: {'Gemini 2.5 Flash' if self.use_gemini else 'Local (template-based)'}")
        print("="*80)

    def query(self, question: str, n_results: int = 5, filter_type: Optional[str] = None,
              filter_vendor: Optional[str] = None, filter_min_amount: Optional[float] = None,
              filter_max_amount: Optional[float] = None) -> Dict[str, Any]:
        """Query the RAG system with metadata filtering"""
        import re

        # Check if question contains specific document IDs
        doc_id_patterns = [
            r'PO-\d{4}-\d{5}',      # Purchase Orders
            r'INV-\d{6}',            # Invoices
            r'GRN-\d{5}'             # GRNs
        ]

        specific_doc_id = None
        for pattern in doc_id_patterns:
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                specific_doc_id = match.group(0).upper()
                break

        # Build metadata filter
        filter_dict = None
        filter_conditions = []

        if specific_doc_id:
            # Filter by specific document ID
            filter_conditions.append({"doc_id": specific_doc_id})
            # Increase results to ensure we find the document
            n_results = min(n_results * 3, 15)

        if filter_type:
            filter_conditions.append({"document_type": filter_type})

        if filter_vendor:
            filter_conditions.append({"vendor": filter_vendor})

        if filter_min_amount is not None or filter_max_amount is not None:
            amount_filter = {}
            if filter_min_amount is not None:
                amount_filter["$gte"] = filter_min_amount
            if filter_max_amount is not None:
                amount_filter["$lte"] = filter_max_amount
            filter_conditions.append({"amount": amount_filter})

        # Combine filters with $and if multiple conditions
        if len(filter_conditions) > 1:
            filter_dict = {"$and": filter_conditions}
        elif len(filter_conditions) == 1:
            filter_dict = filter_conditions[0]

        # Retrieve relevant documents
        results = self.vector_store.search(question, n_results=n_results, filter_dict=filter_dict)

        # Generate answer
        if self.use_gemini:
            answer = self._generate_answer_gemini(question, results)
        else:
            answer = self._generate_answer_local(question, results)

        return {
            'question': question,
            'answer': answer,
            'source_documents': results['documents'][0],
            'metadata': results['metadatas'][0],
            'distances': results['distances'][0]
        }

    def _generate_answer_gemini(self, question: str, results: Dict[str, Any]) -> str:
        """Generate answer using Gemini"""
        # Prepare context from retrieved documents
        context = "\n\n---\n\n".join(results['documents'][0])

        # Create prompt
        prompt = f"""You are a helpful assistant that answers questions about procurement documents (Purchase Orders, Invoices, and Goods Received Notes).

Based on the following document excerpts, answer the user's question. Be specific and cite document numbers when relevant.

Context:
{context}

Question: {question}

Answer: """

        try:
            response = self.gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating answer with Gemini: {e}\n\nFalling back to retrieved documents:\n{results['documents'][0][0][:500]}..."

    def _generate_answer_local(self, question: str, results: Dict[str, Any]) -> str:
        """Generate answer using local template-based approach"""
        if not results['documents'][0]:
            return "No relevant documents found for your query."

        # Get top result
        top_doc = results['documents'][0][0]
        top_metadata = results['metadatas'][0][0]
        distance = results['distances'][0][0]

        # Extract key information
        answer_parts = [
            f"Based on the retrieved documents (relevance score: {1 - distance:.2f}):\n"
        ]

        # Add document summary
        doc_type = top_metadata.get('document_type', 'unknown').replace('_', ' ').title()
        doc_id = top_metadata.get('doc_id', 'N/A')

        answer_parts.append(f" Most Relevant Document: {doc_type} {doc_id}")

        # Parse and extract relevant info based on question
        question_lower = question.lower()

        if 'vendor' in question_lower or 'supplier' in question_lower:
            vendor = top_metadata.get('vendor', 'Unknown')
            answer_parts.append(f"Vendor: {vendor}")

        if 'amount' in question_lower or 'total' in question_lower or 'value' in question_lower or 'cost' in question_lower:
            amount = top_metadata.get('amount', 0)
            if amount:
                answer_parts.append(f"Amount: ${amount:,.2f}")

        if 'date' in question_lower or 'when' in question_lower:
            date = top_metadata.get('date', 'Unknown')
            answer_parts.append(f"Date: {date}")

        # Add document excerpt
        answer_parts.append(f"\n Document Details:")
        answer_parts.append(top_doc[:500] + "..." if len(top_doc) > 500 else top_doc)

        return "\n".join(answer_parts)

    def add_new_document(self, doc_data: Dict[str, Any], doc_type: str) -> bool:
        """Add a new document to the RAG system dynamically"""
        if not self.vector_store:
            print("    Vector store not initialized")
            return False

        try:
            # Add to vector store
            success = self.vector_store.add_single_document(doc_data, doc_type)

            if success:
                stats = self.vector_store.get_stats()
                doc_id = doc_data.get('po_number') or doc_data.get('invoice_number') or doc_data.get('grn_number')
                print(f"    Added {doc_type} {doc_id} to RAG system")
                print(f"    Total documents: {stats['total_documents']}")

            return success

        except Exception as e:
            print(f"    Error adding document to RAG: {e}")
            return False

    def reload_all_documents(self):
        """Reload all documents from JSON files"""
        print("\n Reloading all documents...")

        # Load documents
        documents = DocumentLoader.load_all_documents()

        # Reinitialize vector store with reset
        self.vector_store = VectorStore(reset=True)

        # Add documents
        self.vector_store.add_documents(documents)

        # Print stats
        stats = self.vector_store.get_stats()
        print(f" Reloaded {stats['total_documents']} documents\n")

    def interactive_mode(self):
        """Interactive query mode"""
        print("\n" + "="*80)
        print("💬 INTERACTIVE RAG SYSTEM")
        print("="*80)
        print("\nAsk questions about procurement documents!")
        print("Commands:")
        print("  - Type your question to search")
        print("  - 'filter:po', 'filter:invoice', 'filter:grn' to filter by type")
        print("  - 'stats' to see system statistics")
        print("  - 'quit' or 'exit' to exit")
        print("\n" + "="*80 + "\n")

        current_filter = None

        while True:
            try:
                query = input("\n Your question: ").strip()

                if not query:
                    continue

                if query.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!")
                    break

                if query.lower() == 'stats':
                    stats = self.vector_store.get_stats()
                    print(f"\n System Statistics:")
                    print(f"   Total documents: {stats['total_documents']}")
                    print(f"   Current filter: {current_filter or 'None'}")
                    continue

                if query.lower().startswith('filter:'):
                    filter_type = query.split(':')[1].strip()
                    if filter_type in ['po', 'purchase_order']:
                        current_filter = 'purchase_order'
                        print(f"    Filter set to: Purchase Orders")
                    elif filter_type in ['inv', 'invoice']:
                        current_filter = 'invoice'
                        print(f"    Filter set to: Invoices")
                    elif filter_type in ['grn']:
                        current_filter = 'grn'
                        print(f"    Filter set to: GRNs")
                    elif filter_type in ['none', 'clear']:
                        current_filter = None
                        print(f"    Filter cleared")
                    continue

                # Process query
                print("\n Searching...")
                result = self.query(query, filter_type=current_filter)

                print("\n" + "-"*80)
                print(" Answer:")
                print("-"*80)
                print(result['answer'])

                print("\n" + "-"*80)
                print(f"📚 Sources ({len(result['source_documents'])} documents):")
                print("-"*80)
                for i, (doc, meta, dist) in enumerate(zip(
                    result['source_documents'][:3],
                    result['metadata'][:3],
                    result['distances'][:3]
                ), 1):
                    print(f"\n{i}. {meta.get('doc_id', 'N/A')} (relevance: {1-dist:.2f})")
                    print(f"   {doc[:150]}...")

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n Error: {e}")


def demo_queries(rag_system: RAGSystem):
    """Run demo queries"""
    print("\n" + "="*80)
    print(" DEMO QUERIES")
    print("="*80)

    demo_questions = [
        "What is the total value of all purchase orders?",
        "Show me invoices from Global Tech Solutions",
        "Which warehouse received the most goods?",
        "What are the largest purchase orders?",
        "Show me all documents related to vendor V-1002",
        "What invoices are due soon?",
        "Tell me about purchase order PO-2024-01006"
    ]

    for i, question in enumerate(demo_questions, 1):
        print(f"\n{'='*80}")
        print(f"Demo Query {i}/{len(demo_questions)}")
        print(f"{'='*80}")
        print(f"❓ Question: {question}")
        print("-"*80)

        result = rag_system.query(question, n_results=3)

        print(" Answer:")
        print(result['answer'])

        print(f"\n📚 Top Sources:")
        for j, (meta, dist) in enumerate(zip(result['metadata'][:2], result['distances'][:2]), 1):
            print(f"   {j}. {meta.get('doc_id', 'N/A')} (relevance: {1-dist:.2f})")

        if i < len(demo_questions):
            input("\n⏎ Press Enter for next query...")


def main():
    """Main entry point"""
    print("""

                                                                          
              RAG SYSTEM FOR PROCUREMENT DOCUMENTS                        
                                                                          
   Retrieval-Augmented Generation for Purchase Orders, Invoices & GRNs   
                                                                          

""")

    # Check for Gemini API key
    gemini_api_key = os.getenv('GEMINI_API_KEY')

    # Initialize RAG system
    rag = RAGSystem(gemini_api_key=gemini_api_key)
    rag.initialize()

    # Run demo queries
    print("\n" + "="*80)
    print("Choose mode:")
    print("  1. Demo mode (pre-defined queries)")
    print("  2. Interactive mode (ask your own questions)")
    print("="*80)

    choice = input("\nEnter choice (1 or 2): ").strip()

    if choice == "1":
        demo_queries(rag)
    else:
        rag.interactive_mode()

    print("\n" + "="*80)
    print(" RAG SYSTEM SESSION COMPLETE")
    print("="*80)
    print(f"\n Vector store saved to: {VECTOR_DB_DIR}")
    print("\n Next Steps:")
    print("   1. Try different queries in interactive mode")
    print("   2. Set GEMINI_API_KEY environment variable for Gemini 2.5 Flash integration")
    print("   3. Extend with more sophisticated retrieval strategies")
    print("   4. Add multi-hop reasoning for complex queries")
    print()


if __name__ == "__main__":
    main()
