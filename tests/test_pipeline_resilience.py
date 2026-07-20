from src.core.gemini import GeminiError
from src.rag.pipeline import UPSCChatbot


def test_model_outage_returns_source_notes(monkeypatch):
    monkeypatch.setattr("src.rag.pipeline.route_question", lambda question, has_rag: "direct")
    monkeypatch.setattr(
        "src.rag.pipeline.lookup_direct",
        lambda question, top_k: [
            {"text": "Article 32 provides the right to constitutional remedies.", "source": "notes:polity.txt", "subject": "Polity"}
        ],
    )
    monkeypatch.setattr("src.rag.pipeline.generate_answer", lambda *args, **kwargs: (_ for _ in ()).throw(GeminiError("503 busy")))
    monkeypatch.setattr(UPSCChatbot, "_has_rag", lambda self: False)

    result = UPSCChatbot().ask("What is Article 32?")

    assert result["error"] is None
    assert result["mode"] == "direct"
    assert "Source notes" in result["answer"]
    assert "Article 32" in result["answer"]
    assert result["sources"]
