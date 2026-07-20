"""Exit 0 if system healthy (for Docker / CI)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv()

from src.core.health import check_health

if __name__ == "__main__":
    report = check_health()
    print(report.to_dict())
    sys.exit(0 if report.ok else 1)
