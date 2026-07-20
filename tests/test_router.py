import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.rag.router import route_question


def test_direct_routing():
    assert route_question("What is Article 32?", True) == "direct"
    assert route_question("Define Panchayati Raj", True) == "direct"


def test_rag_routing():
    assert route_question("Compare FR and DPSP in detail", True) == "rag"
    assert route_question("Critically analyze federalism", True) == "rag"


def test_no_rag_fallback():
    assert route_question("What is GDP?", False) == "direct"
