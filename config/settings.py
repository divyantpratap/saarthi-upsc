"""
Configuration settings for UPSC RAG Chatbot
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EMBEDDINGS_DIR = DATA_DIR / "embeddings"

# Create directories if they don't exist
for dir_path in [RAW_DATA_DIR, PROCESSED_DATA_DIR, EMBEDDINGS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Gemini Configuration
GEMINI_MODEL = "gemini-2.0-flash-exp"
GEMINI_TEMPERATURE = 0.7
GEMINI_TOP_P = 0.95
GEMINI_TOP_K = 40
GEMINI_MAX_OUTPUT_TOKENS = 2048

# ChromaDB Configuration
CHROMA_DB_PATH = str(EMBEDDINGS_DIR / "chroma_db")
COLLECTION_NAME = "upsc_knowledge"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Fast and efficient
# Alternative: "all-mpnet-base-v2" for better quality

# Chunking Configuration
CHUNK_SIZE = 500  # tokens
CHUNK_OVERLAP = 50  # tokens
MAX_CHUNK_SIZE = 1000

# Retrieval Configuration
TOP_K_RESULTS = 5
SIMILARITY_THRESHOLD = 0.7
RERANK_TOP_K = 3

# PDF Processing Configuration
PDF_BATCH_SIZE = 10  # Process 10 PDFs in parallel
MAX_WORKERS = 4  # Number of parallel workers
PDF_TIMEOUT = 300  # 5 minutes per PDF

# Web Scraping Configuration
SCRAPING_DELAY = 1  # seconds between requests
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
REQUEST_TIMEOUT = 30

# Data Sources
WEB_SOURCES = {
    "insights_ias": "https://www.insightsonindia.com",
    "iasbaba": "https://iasbaba.com",
    "pib": "https://pib.gov.in"
}

# UPSC Topics
UPSC_TOPICS = [
    "History",
    "Geography",
    "Polity",
    "Economy",
    "Environment",
    "Science & Technology",
    "Current Affairs",
    "Ethics",
    "International Relations",
    "Internal Security"
]

# Prompt Templates
SYSTEM_PROMPT = """You are an expert UPSC mentor with deep knowledge of Indian civil services examination.
Your role is to provide accurate, exam-oriented answers based on the provided context.

Guidelines:
- Be precise and factual
- Include relevant dates, figures, and statistics
- Follow UPSC answer writing pattern
- Cite sources when available
- If information is not in context, clearly state that
- Structure answers with introduction, body, and conclusion for long answers
"""

QA_PROMPT_TEMPLATE = """Context from UPSC study materials:
{context}

Question: {question}

Provide a comprehensive answer following UPSC standards. Include:
1. Direct answer to the question
2. Relevant facts, figures, and examples
3. Multiple perspectives if applicable
4. Conclusion or way forward

Answer:"""

# Streamlit Configuration
APP_TITLE = "UPSC AI Mentor"
APP_ICON = "🎓"
PAGE_CONFIG = {
    "page_title": APP_TITLE,
    "page_icon": APP_ICON,
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
LOG_FILE = BASE_DIR / "logs" / "upsc_chatbot.log"

# Cache Configuration
ENABLE_CACHE = True
CACHE_TTL = 3600  # 1 hour

# Fine-tuning Configuration
FINE_TUNE_BATCH_SIZE = 16
FINE_TUNE_EPOCHS = 3
FINE_TUNE_LEARNING_RATE = 2e-5

