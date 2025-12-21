"""
Configuration Management
Loads settings from environment variables with fallback defaults
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """Application configuration"""

    # Google Gemini API
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/procurement.db')

    # Vector Store
    VECTOR_STORE_PATH = os.getenv('VECTOR_STORE_PATH', 'data/vector_store')
    CHROMA_PERSIST_DIR = os.getenv('CHROMA_PERSIST_DIR', 'data/vector_store')

    # File Paths
    PDF_DIR = Path(os.getenv('PDF_DIR', 'data/synthetic/pdfs_alternative'))
    PROCESSED_DIR = Path(os.getenv('PROCESSED_DIR', 'data/processed'))
    INGESTION_LOG = Path(os.getenv('INGESTION_LOG', 'data/ingestion_log.json'))

    # API Configuration
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', '8000'))

    # Cache
    CACHE_TTL = int(os.getenv('CACHE_TTL', '300'))

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY not found in environment variables. "
                "Please set it in .env file or as environment variable."
            )

    @classmethod
    def display(cls):
        """Display configuration (hiding sensitive data)"""
        print("📋 Configuration:")
        print(f"   GEMINI_API_KEY: {'*' * 20}{cls.GEMINI_API_KEY[-4:] if cls.GEMINI_API_KEY else 'NOT SET'}")
        print(f"   DATABASE_URL: {cls.DATABASE_URL}")
        print(f"   VECTOR_STORE_PATH: {cls.VECTOR_STORE_PATH}")
        print(f"   PDF_DIR: {cls.PDF_DIR}")
        print(f"   API_PORT: {cls.API_PORT}")
        print(f"   CACHE_TTL: {cls.CACHE_TTL}s")
        print(f"   LOG_LEVEL: {cls.LOG_LEVEL}")


# Singleton instance
config = Config()
