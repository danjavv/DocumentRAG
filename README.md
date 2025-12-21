# AI-Powered Procurement Document Management System

## RAG-based Chat Interface for Procurement Documents

A complete end-to-end solution for intelligent document processing with semantic search capabilities, powered by Google Gemini AI and ChromaDB vector database.

Steps:-

1. Process the pdfs to convert them into structured jsons (It is regex pattern based extraction of useful fields and if there is some error in it, then LLM is utitlized for extracting info from the pdfs).
Since it uses LLMs and LLMs have a per minute limit, therefore this step takes much time for the first time

2. Convert the structured jsons into a vector store by the RAG system. The documents are now ready to be searched in natural language

3. Add a new pdf in the data/synthetic/pdfs_alternative directory and it will be automatically be ingested, processed and added to the RAG vector store in about 30 seconds. You can refresh the frontend to see the stats update in real time.

### First-Time Setup

If PDFs haven't been processed yet, run these commands **in order**:

```bash
# 1. Set up environment variables (IMPORTANT!)
cp .env.example .env
# Then edit .env and add your Gemini API key:
# GEMINI_API_KEY=your_actual_api_key_here

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Process all PDFs and extract structured data
python3 scripts/pdf_ingestion_pipeline.py

# 4. Build the vector database for RAG
python3 scripts/rag_system.py

# 5. Install frontend dependencies
cd frontend
npm install
cd ..

# 6. Start the full application (backend + frontend)
./start_chat_app.sh
```

Access the chat interface at: **http://localhost:3000**

**Note:** The `.env` file contains your API keys and should NEVER be committed to git. It's already in `.gitignore`.

### Running the Application (After Initial Setup)

```bash
# Start both backend and frontend
./start_chat_app.sh

# Or run separately:
./run_backend.sh    # Backend on http://localhost:8000
./run_frontend.sh   # Frontend on http://localhost:3000
```

### Auto-Process New PDFs

Place new PDFs in `data/synthetic/pdfs_alternative/` and they'll be automatically ingested.
When you run either:
  - ./start_chat_app.sh (which calls run_backend.sh), or
  - ./run_backend.sh directly

  The backend automatically:
  1. Initializes the RAG system
  2. Initializes PDF auto-ingestion
  3. Starts the PDF watcher in a background thread (line 172)

Or you can run 
```bash
# Start the PDF watcher to automatically process new documents
./start_watcher_standalone.sh
```
but its not needed actually

## Architecture Overview

### Document Processing Pipeline

```
PDF Files
   ↓
Text Extraction (pdfplumber)
   ↓
Classification (Rule-based + Regex)
   ↓
Data Extraction (Gemini LLM + Regex Fallback)
   ↓
JSON Storage (data/processed/)
   ↓
Vector Embeddings (Sentence-Transformers)
   ↓
ChromaDB Vector Store
```

### RAG Query Flow

```
User Query
   ↓
Embedding Generation
   ↓
Vector Similarity Search (Top-5)
   ↓
Context Assembly
   ↓
Gemini 2.5 Flash (Answer Generation)
   ↓
Response + Source Attribution
```