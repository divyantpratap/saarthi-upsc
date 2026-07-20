import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.references.catalog import build_catalog

if __name__ == "__main__":
    build_catalog()
