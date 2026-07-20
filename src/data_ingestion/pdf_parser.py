"""
High-performance PDF parser with parallel processing
Optimized to process 100 pages in <2 minutes
"""
import os
import re
from pathlib import Path
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import PyPDF2
import pdfplumber
import fitz  # PyMuPDF
from tqdm import tqdm
from loguru import logger

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import (
    PDF_BATCH_SIZE, MAX_WORKERS, PDF_TIMEOUT,
    CHUNK_SIZE, CHUNK_OVERLAP, RAW_DATA_DIR, PROCESSED_DATA_DIR
)


class PDFParser:
    """Fast PDF parser with multiple extraction methods"""
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or PROCESSED_DATA_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def extract_text_pymupdf(self, pdf_path: Path) -> List[Dict]:
        """Fast extraction using PyMuPDF (fastest method)"""
        try:
            doc = fitz.open(pdf_path)
            pages_data = []
            
            for page_num, page in enumerate(doc, 1):
                text = page.get_text()
                if text.strip():
                    pages_data.append({
                        "page": page_num,
                        "text": text,
                        "source": pdf_path.name,
                        "method": "pymupdf"
                    })
            
            doc.close()
            return pages_data
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed for {pdf_path}: {e}")
            return []
    
    def extract_text_pdfplumber(self, pdf_path: Path) -> List[Dict]:
        """High-quality extraction using pdfplumber (fallback)"""
        try:
            pages_data = []
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text and text.strip():
                        pages_data.append({
                            "page": page_num,
                            "text": text,
                            "source": pdf_path.name,
                            "method": "pdfplumber"
                        })
            return pages_data
        except Exception as e:
            logger.error(f"pdfplumber extraction failed for {pdf_path}: {e}")
            return []
    
    def extract_text_pypdf2(self, pdf_path: Path) -> List[Dict]:
        """Basic extraction using PyPDF2 (last resort)"""
        try:
            pages_data = []
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    text = page.extract_text()
                    if text and text.strip():
                        pages_data.append({
                            "page": page_num,
                            "text": text,
                            "source": pdf_path.name,
                            "method": "pypdf2"
                        })
            return pages_data
        except Exception as e:
            logger.error(f"PyPDF2 extraction failed for {pdf_path}: {e}")
            return []
    
    def extract_text(self, pdf_path: Path) -> List[Dict]:
        """Extract text using best available method"""
        # Try methods in order of speed/quality
        for method in [self.extract_text_pymupdf, 
                      self.extract_text_pdfplumber, 
                      self.extract_text_pypdf2]:
            result = method(pdf_path)
            if result:
                logger.info(f"Successfully extracted {len(result)} pages from {pdf_path.name}")
                return result
        
        logger.warning(f"All extraction methods failed for {pdf_path}")
        return []
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s.,;:!?()\-\'\"]+', '', text)
        # Remove page numbers and headers/footers patterns
        text = re.sub(r'\b\d+\s*\|\s*Page\b', '', text, flags=re.IGNORECASE)
        return text.strip()

    def chunk_text(self, text: str, chunk_size: int = CHUNK_SIZE,
                   overlap: int = CHUNK_OVERLAP) -> List[str]:
        """Split text into overlapping chunks by tokens (words)"""
        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)

            # Break if we've reached the end
            if i + chunk_size >= len(words):
                break

        return chunks

    def extract_metadata(self, pdf_path: Path) -> Dict:
        """Extract metadata from PDF"""
        try:
            doc = fitz.open(pdf_path)
            metadata = doc.metadata
            doc.close()

            # Infer topic from filename
            filename = pdf_path.stem.lower()
            topic = self._infer_topic(filename)

            return {
                "title": metadata.get("title", pdf_path.stem),
                "author": metadata.get("author", "Unknown"),
                "subject": metadata.get("subject", ""),
                "topic": topic,
                "filename": pdf_path.name,
                "pages": len(list(fitz.open(pdf_path)))
            }
        except Exception as e:
            logger.error(f"Metadata extraction failed for {pdf_path}: {e}")
            return {
                "title": pdf_path.stem,
                "topic": self._infer_topic(pdf_path.stem.lower()),
                "filename": pdf_path.name
            }

    def _infer_topic(self, text: str) -> str:
        """Infer UPSC topic from text"""
        topic_keywords = {
            "History": ["history", "ancient", "medieval", "modern", "freedom", "struggle"],
            "Geography": ["geography", "climate", "map", "physical", "economic"],
            "Polity": ["polity", "constitution", "governance", "parliament", "laxmikanth"],
            "Economy": ["economy", "economic", "finance", "budget", "gdp"],
            "Environment": ["environment", "ecology", "biodiversity", "climate change"],
            "Science & Technology": ["science", "technology", "innovation", "research"],
            "Current Affairs": ["current", "affairs", "news", "daily", "monthly"],
            "Ethics": ["ethics", "integrity", "values", "case study"],
            "International Relations": ["international", "foreign", "diplomacy", "global"],
            "Internal Security": ["security", "defense", "terrorism", "naxalism"]
        }

        for topic, keywords in topic_keywords.items():
            if any(keyword in text for keyword in keywords):
                return topic

        return "General"

    def process_single_pdf(self, pdf_path: Path) -> Dict:
        """Process a single PDF file"""
        try:
            logger.info(f"Processing: {pdf_path.name}")

            # Extract metadata
            metadata = self.extract_metadata(pdf_path)

            # Extract text from all pages
            pages_data = self.extract_text(pdf_path)

            if not pages_data:
                return {"status": "failed", "file": pdf_path.name, "error": "No text extracted"}

            # Combine all pages and clean
            full_text = " ".join([page["text"] for page in pages_data])
            cleaned_text = self.clean_text(full_text)

            # Create chunks
            chunks = self.chunk_text(cleaned_text)

            # Prepare documents with metadata
            documents = []
            for idx, chunk in enumerate(chunks):
                doc = {
                    "text": chunk,
                    "chunk_id": idx,
                    "source": pdf_path.name,
                    "topic": metadata["topic"],
                    "title": metadata["title"],
                    "total_chunks": len(chunks)
                }
                documents.append(doc)

            logger.success(f"✓ Processed {pdf_path.name}: {len(chunks)} chunks from {len(pages_data)} pages")

            return {
                "status": "success",
                "file": pdf_path.name,
                "pages": len(pages_data),
                "chunks": len(chunks),
                "documents": documents,
                "metadata": metadata
            }

        except Exception as e:
            logger.error(f"Failed to process {pdf_path.name}: {e}")
            return {"status": "failed", "file": pdf_path.name, "error": str(e)}

    def process_pdfs_parallel(self, pdf_dir: Optional[Path] = None,
                             max_workers: int = MAX_WORKERS) -> List[Dict]:
        """Process multiple PDFs in parallel - OPTIMIZED FOR SPEED"""
        pdf_dir = pdf_dir or RAW_DATA_DIR
        pdf_files = list(pdf_dir.glob("*.pdf"))

        if not pdf_files:
            logger.warning(f"No PDF files found in {pdf_dir}")
            return []

        logger.info(f"Found {len(pdf_files)} PDF files. Processing with {max_workers} workers...")

        all_documents = []
        results = []

        # Process in parallel with progress bar
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_pdf = {
                executor.submit(self.process_single_pdf, pdf_path): pdf_path
                for pdf_path in pdf_files
            }

            # Collect results with progress bar
            with tqdm(total=len(pdf_files), desc="Processing PDFs") as pbar:
                for future in as_completed(future_to_pdf):
                    result = future.result()
                    results.append(result)

                    if result["status"] == "success":
                        all_documents.extend(result["documents"])

                    pbar.update(1)

        # Summary
        successful = sum(1 for r in results if r["status"] == "success")
        failed = len(results) - successful
        total_chunks = len(all_documents)

        logger.info(f"""
        ╔══════════════════════════════════════╗
        ║     PDF Processing Complete          ║
        ╠══════════════════════════════════════╣
        ║  Total PDFs: {len(pdf_files):<23} ║
        ║  Successful: {successful:<23} ║
        ║  Failed: {failed:<27} ║
        ║  Total Chunks: {total_chunks:<21} ║
        ╚══════════════════════════════════════╝
        """)

        return all_documents


def main():
    """Test the PDF parser"""
    from loguru import logger

    # Configure logger
    logger.add("pdf_parser.log", rotation="10 MB")

    parser = PDFParser()

    # Process all PDFs in the raw data directory
    documents = parser.process_pdfs_parallel()

    if documents:
        logger.success(f"Successfully processed {len(documents)} document chunks")

        # Save sample output
        import json
        sample_output = documents[:5]  # First 5 chunks
        with open(PROCESSED_DATA_DIR / "sample_output.json", "w", encoding="utf-8") as f:
            json.dump(sample_output, f, indent=2, ensure_ascii=False)

        logger.info(f"Sample output saved to {PROCESSED_DATA_DIR / 'sample_output.json'}")
    else:
        logger.warning("No documents processed")


if __name__ == "__main__":
    main()

