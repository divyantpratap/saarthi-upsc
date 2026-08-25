from __future__ import annotations

import os

from src.core.gemini import get_client


def test_user_key_is_not_copied_to_environment(monkeypatch):
    captured = {}

    def fake_client(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr("src.core.gemini.genai.Client", fake_client)
    get_client("session-only-test-key")

    assert captured["api_key"] == "session-only-test-key"
    assert "GEMINI_API_KEY" not in os.environ
