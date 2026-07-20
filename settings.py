"""Central configuration — override via environment variables."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Data paths
DATA_DIR = ROOT / "data"
PDF_DIR = DATA_DIR / "pdfs"
SCRAPED_DIR = DATA_DIR / "scraped"
SAMPLE_URLS_FILE = DATA_DIR / "sample_urls.txt"
REFERENCES_DIR = DATA_DIR / "references"
CATALOG_FILE = REFERENCES_DIR / "catalog.json"
ANSWER_EXAMPLES_FILE = REFERENCES_DIR / "answer_examples.json"
LOG_DIR = ROOT / "logs"

# Vector store
CHROMA_DIR = ROOT / "chroma_db"
COLLECTION_NAME = "upsc_knowledge"

# RAG
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "120"))
TOP_K_RAG = int(os.getenv("TOP_K_RAG", "6"))
TOP_K_DIRECT = int(os.getenv("TOP_K_DIRECT", "3"))
RAG_MAX_DISTANCE = float(os.getenv("RAG_MAX_DISTANCE", "0.72"))  # cosine distance; lower = better

# Context limits (prevent empty/truncated Gemini responses)
MAX_CONTEXT_CHARS = int(os.getenv("MAX_CONTEXT_CHARS", "14000"))
MAX_CONTEXT_DIRECT = int(os.getenv("MAX_CONTEXT_DIRECT", "10000"))
MAX_CONTEXT_RAG = int(os.getenv("MAX_CONTEXT_RAG", "12000"))
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "4096"))
DIRECT_EXCERPT_CHARS = int(os.getenv("DIRECT_EXCERPT_CHARS", "3500"))

# PDF ingestion
MAX_PAGES_FULL = int(os.getenv("MAX_PAGES_FULL", "150"))
MAX_PAGES_PREVIEW = int(os.getenv("MAX_PAGES_PREVIEW", "8"))
MIN_CHARS_PER_PDF = int(os.getenv("MIN_CHARS_PER_PDF", "200"))

# Gemini — favour the low-latency stable endpoint for an interactive tutor.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_MODEL_FALLBACK = os.getenv("GEMINI_MODEL_FALLBACK", "gemini-3.5-flash")
GEMINI_TIMEOUT_MS = int(os.getenv("GEMINI_TIMEOUT_MS", "12000"))
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")

# Embeddings: local (recommended) | gemini
EMBEDDING_BACKEND = os.getenv("EMBEDDING_BACKEND", "local")
LOCAL_EMBED_MODEL = os.getenv("LOCAL_EMBED_MODEL", "all-MiniLM-L6-v2")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
