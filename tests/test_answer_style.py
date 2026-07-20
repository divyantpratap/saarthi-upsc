import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.references.answer_style import get_answer_examples


def test_definition_example_selected():
    ex = get_answer_examples("What is Article 32?", mode="direct")
    assert "Article 32" in ex
    assert "Prelims" in ex or "prelims" in ex.lower()


def test_compare_example_selected():
    ex = get_answer_examples("Compare FR and DPSP", mode="rag")
    assert "DPSP" in ex or "Fundamental Rights" in ex
