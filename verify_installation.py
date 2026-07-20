"""
Installation Verification Script
Run this to verify that everything is set up correctly
"""
import sys
from pathlib import Path
from typing import List, Tuple

def check_python_version() -> Tuple[bool, str]:
    """Check Python version"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        return True, f"✓ Python {version.major}.{version.minor}.{version.micro}"
    return False, f"✗ Python {version.major}.{version.minor} (Need 3.8+)"

def check_dependencies() -> Tuple[bool, List[str]]:
    """Check if required packages are installed"""
    required = [
        'google.generativeai',
        'chromadb',
        'streamlit',
        'sentence_transformers',
        'PyPDF2',
        'pdfplumber',
        'fitz',  # PyMuPDF
        'bs4',  # BeautifulSoup
        'requests',
        'pandas',
        'loguru',
        'dotenv'
    ]
    
    results = []
    all_ok = True
    
    for package in required:
        try:
            __import__(package)
            results.append(f"✓ {package}")
        except ImportError:
            results.append(f"✗ {package} (MISSING)")
            all_ok = False
    
    return all_ok, results

def check_directories() -> Tuple[bool, List[str]]:
    """Check if required directories exist"""
    required_dirs = [
        'config',
        'src/data_ingestion',
        'src/rag',
        'src/llm',
        'src/utils',
        'data/raw',
        'data/processed',
        'data/embeddings',
        'pages',
        'tests'
    ]
    
    results = []
    all_ok = True
    
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            results.append(f"✓ {dir_path}")
        else:
            results.append(f"✗ {dir_path} (MISSING)")
            all_ok = False
    
    return all_ok, results

def check_files() -> Tuple[bool, List[str]]:
    """Check if required files exist"""
    required_files = [
        'app.py',
        'ingest_data.py',
        'requirements.txt',
        'config/settings.py',
        'src/data_ingestion/pdf_parser.py',
        'src/data_ingestion/web_scraper.py',
        'src/rag/chroma_db.py',
        'src/rag/rag_pipeline.py',
        'src/llm/gemini_client.py',
        'README.md',
        'QUICKSTART.md'
    ]
    
    results = []
    all_ok = True
    
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            results.append(f"✓ {file_path}")
        else:
            results.append(f"✗ {file_path} (MISSING)")
            all_ok = False
    
    return all_ok, results

def check_env_file() -> Tuple[bool, str]:
    """Check if .env file exists"""
    env_path = Path('.env')
    if env_path.exists():
        # Check if API key is set
        content = env_path.read_text()
        if 'GEMINI_API_KEY' in content and 'your_' not in content:
            return True, "✓ .env file exists with API key"
        return False, "⚠ .env file exists but API key not configured"
    return False, "✗ .env file missing (copy from .env.example)"

def check_imports() -> Tuple[bool, List[str]]:
    """Check if project modules can be imported"""
    modules = [
        'config.settings',
        'src.data_ingestion.pdf_parser',
        'src.data_ingestion.web_scraper',
        'src.rag.chroma_db',
        'src.rag.rag_pipeline',
        'src.llm.gemini_client',
        'src.utils.helpers'
    ]
    
    results = []
    all_ok = True
    
    for module in modules:
        try:
            __import__(module)
            results.append(f"✓ {module}")
        except Exception as e:
            results.append(f"✗ {module} ({str(e)[:30]}...)")
            all_ok = False
    
    return all_ok, results

def main():
    """Run all verification checks"""
    print("="*60)
    print("UPSC AI MENTOR - INSTALLATION VERIFICATION")
    print("="*60)
    print()
    
    # Check Python version
    print("1. Python Version")
    print("-" * 60)
    ok, msg = check_python_version()
    print(msg)
    print()
    
    # Check dependencies
    print("2. Required Packages")
    print("-" * 60)
    ok, results = check_dependencies()
    for result in results:
        print(result)
    print()
    
    # Check directories
    print("3. Directory Structure")
    print("-" * 60)
    ok, results = check_directories()
    for result in results[:5]:  # Show first 5
        print(result)
    if len(results) > 5:
        print(f"... and {len(results) - 5} more")
    print()
    
    # Check files
    print("4. Required Files")
    print("-" * 60)
    ok, results = check_files()
    for result in results[:5]:  # Show first 5
        print(result)
    if len(results) > 5:
        print(f"... and {len(results) - 5} more")
    print()
    
    # Check .env
    print("5. Environment Configuration")
    print("-" * 60)
    ok, msg = check_env_file()
    print(msg)
    print()
    
    # Check imports
    print("6. Module Imports")
    print("-" * 60)
    ok, results = check_imports()
    for result in results:
        print(result)
    print()
    
    # Final summary
    print("="*60)
    print("VERIFICATION COMPLETE")
    print("="*60)
    print()
    
    env_ok, _ = check_env_file()
    deps_ok, _ = check_dependencies()
    imports_ok, _ = check_imports()
    
    if env_ok and deps_ok and imports_ok:
        print("✅ All checks passed! You're ready to go!")
        print()
        print("Next steps:")
        print("1. Add PDFs to data/raw/ directory")
        print("2. Run: python ingest_data.py --mode all")
        print("3. Run: streamlit run app.py")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        print()
        if not deps_ok:
            print("To install dependencies: pip install -r requirements.txt")
        if not env_ok:
            print("To setup environment: cp .env.example .env")
            print("Then edit .env and add your GEMINI_API_KEY")
    
    print()
    print("="*60)

if __name__ == "__main__":
    main()

