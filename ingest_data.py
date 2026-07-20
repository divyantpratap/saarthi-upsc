"""
Data Ingestion Script
Run this script to process PDFs and web content and add them to ChromaDB
"""
import sys
from pathlib import Path
from loguru import logger
import argparse

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.data_ingestion.pdf_parser import PDFParser
from src.data_ingestion.web_scraper import WebScraper
from src.rag.chroma_db import ChromaDBManager
from config.settings import RAW_DATA_DIR, PROCESSED_DATA_DIR


def setup_logging():
    """Setup logging configuration"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger.add(
        log_dir / "ingestion_{time}.log",
        rotation="10 MB",
        retention="7 days",
        level="INFO"
    )


def ingest_pdfs(db_manager: ChromaDBManager, pdf_dir: Path = None):
    """Ingest PDFs into the knowledge base"""
    logger.info("="*60)
    logger.info("STARTING PDF INGESTION")
    logger.info("="*60)
    
    pdf_dir = pdf_dir or RAW_DATA_DIR
    
    # Check if PDFs exist
    pdf_files = list(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDF files found in {pdf_dir}")
        logger.info("Please add PDF files to the data/raw/ directory")
        return 0
    
    logger.info(f"Found {len(pdf_files)} PDF files")
    
    # Process PDFs
    parser = PDFParser()
    documents = parser.process_pdfs_parallel()
    
    if not documents:
        logger.error("Failed to process PDFs")
        return 0
    
    # Add to ChromaDB
    logger.info(f"Adding {len(documents)} document chunks to ChromaDB...")
    db_manager.add_documents(documents)
    
    logger.success(f"✓ Successfully ingested {len(documents)} chunks from {len(pdf_files)} PDFs")
    return len(documents)


def ingest_web_content(db_manager: ChromaDBManager, articles_per_source: int = 30):
    """Scrape and ingest web content"""
    logger.info("="*60)
    logger.info("STARTING WEB SCRAPING")
    logger.info("="*60)
    
    scraper = WebScraper()
    
    # Scrape all sources
    articles = scraper.scrape_all(articles_per_source=articles_per_source)
    
    if not articles:
        logger.warning("No articles scraped")
        return 0
    
    # Save articles
    scraper.save_articles(articles)
    
    # Add to ChromaDB
    logger.info(f"Adding {len(articles)} articles to ChromaDB...")
    db_manager.add_documents(articles)
    
    logger.success(f"✓ Successfully ingested {len(articles)} web articles")
    return len(articles)


def main():
    """Main ingestion pipeline"""
    parser = argparse.ArgumentParser(description="UPSC Chatbot Data Ingestion")
    parser.add_argument(
        '--mode',
        choices=['pdf', 'web', 'all'],
        default='all',
        help='Ingestion mode: pdf, web, or all'
    )
    parser.add_argument(
        '--articles',
        type=int,
        default=30,
        help='Number of articles to scrape per source (for web mode)'
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset database before ingestion'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    logger.info("="*60)
    logger.info("UPSC CHATBOT - DATA INGESTION")
    logger.info("="*60)
    
    # Initialize ChromaDB
    db_manager = ChromaDBManager()
    
    # Reset database if requested
    if args.reset:
        logger.warning("Resetting database...")
        db_manager.reset_collection()
    
    # Show initial stats
    initial_stats = db_manager.get_stats()
    logger.info(f"Initial document count: {initial_stats['total_documents']}")
    
    total_added = 0
    
    # Ingest based on mode
    if args.mode in ['pdf', 'all']:
        pdf_count = ingest_pdfs(db_manager)
        total_added += pdf_count
    
    if args.mode in ['web', 'all']:
        web_count = ingest_web_content(db_manager, args.articles)
        total_added += web_count
    
    # Show final stats
    logger.info("="*60)
    logger.info("INGESTION COMPLETE")
    logger.info("="*60)
    
    final_stats = db_manager.get_stats()
    logger.info(f"Final document count: {final_stats['total_documents']}")
    logger.info(f"Documents added: {total_added}")
    
    # Print detailed stats
    db_manager.print_stats()
    
    logger.success("✅ Data ingestion completed successfully!")
    
    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("1. Run the Streamlit app: streamlit run app.py")
    print("2. Start asking questions about UPSC topics")
    print("3. Add more PDFs to data/raw/ and run this script again")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

