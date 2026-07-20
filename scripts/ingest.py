"""Alias: full rebuild = catalog + RAG."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
script = ROOT / "scripts" / "build_all.py"
sys.exit(subprocess.call([sys.executable, str(script)]))
