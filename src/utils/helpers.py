"""
Utility functions for UPSC chatbot
"""
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from loguru import logger


def save_json(data: Any, filepath: Path, indent: int = 2):
    """Save data to JSON file"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        logger.info(f"Saved data to {filepath}")
        return True
    except Exception as e:
        logger.error(f"Failed to save JSON: {e}")
        return False


def load_json(filepath: Path) -> Any:
    """Load data from JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Loaded data from {filepath}")
        return data
    except Exception as e:
        logger.error(f"Failed to load JSON: {e}")
        return None


def format_timestamp(dt: datetime = None) -> str:
    """Format timestamp for logging"""
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to max length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def count_tokens(text: str) -> int:
    """Approximate token count (rough estimate)"""
    # Simple approximation: ~4 characters per token
    return len(text) // 4


def batch_list(items: List, batch_size: int) -> List[List]:
    """Split list into batches"""
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]


def merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """Merge two dictionaries"""
    result = dict1.copy()
    result.update(dict2)
    return result


def clean_filename(filename: str) -> str:
    """Clean filename for safe file operations"""
    import re
    # Remove invalid characters
    cleaned = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace spaces with underscores
    cleaned = cleaned.replace(' ', '_')
    return cleaned


def get_file_size(filepath: Path) -> str:
    """Get human-readable file size"""
    size_bytes = filepath.stat().st_size
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.2f} TB"


def validate_pdf(filepath: Path) -> bool:
    """Validate if file is a valid PDF"""
    try:
        with open(filepath, 'rb') as f:
            header = f.read(4)
            return header == b'%PDF'
    except:
        return False


def create_backup(filepath: Path) -> Path:
    """Create backup of a file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = filepath.parent / f"{filepath.stem}_backup_{timestamp}{filepath.suffix}"
    
    try:
        import shutil
        shutil.copy2(filepath, backup_path)
        logger.info(f"Created backup: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        return None


def ensure_dir(directory: Path) -> Path:
    """Ensure directory exists"""
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def get_project_root() -> Path:
    """Get project root directory"""
    return Path(__file__).parent.parent.parent


def format_sources(sources: List[Dict]) -> str:
    """Format sources for display"""
    if not sources:
        return "No sources available"
    
    formatted = []
    for i, source in enumerate(sources, 1):
        source_text = f"{i}. {source.get('source', 'Unknown')}"
        if source.get('topic'):
            source_text += f" (Topic: {source['topic']})"
        if source.get('relevance'):
            source_text += f" - Relevance: {source['relevance']:.2%}"
        formatted.append(source_text)
    
    return "\n".join(formatted)


def extract_keywords(text: str, top_n: int = 10) -> List[str]:
    """Extract top keywords from text (simple implementation)"""
    import re
    from collections import Counter
    
    # Remove special characters and convert to lowercase
    words = re.findall(r'\b[a-z]{4,}\b', text.lower())
    
    # Common stop words
    stop_words = {'that', 'this', 'with', 'from', 'have', 'been', 'were', 
                  'their', 'there', 'which', 'would', 'about', 'other'}
    
    # Filter stop words
    words = [w for w in words if w not in stop_words]
    
    # Count and return top N
    counter = Counter(words)
    return [word for word, _ in counter.most_common(top_n)]


def calculate_reading_time(text: str, wpm: int = 200) -> str:
    """Calculate estimated reading time"""
    word_count = len(text.split())
    minutes = word_count / wpm
    
    if minutes < 1:
        return "< 1 minute"
    elif minutes < 60:
        return f"{int(minutes)} minutes"
    else:
        hours = minutes / 60
        return f"{hours:.1f} hours"


if __name__ == "__main__":
    # Test utilities
    print("Testing utilities...")
    
    test_text = "This is a sample text for testing the utility functions."
    print(f"Token count: {count_tokens(test_text)}")
    print(f"Truncated: {truncate_text(test_text, 20)}")
    print(f"Reading time: {calculate_reading_time(test_text)}")
    print(f"Keywords: {extract_keywords(test_text)}")

