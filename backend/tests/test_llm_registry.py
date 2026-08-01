from backend.services.llm_registry import LLMProviderRegistry


def test_ollama_provider_reports_reachable_when_probe_succeeds(monkeypatch):
    monkeypatch.setenv("LOOPLAMP_ENABLE_OLLAMA", "true")
    registry = LLMProviderRegistry()
    monkeypatch.setattr(registry, "_probe_url", lambda url, headers=None: (True, "Provider responded to the health check."))

    records = registry.list_provider_records()
    ollama = next(record for record in records if record.provider_id == "ollama")

    assert ollama.configured is True
    assert ollama.reachable is True
    assert "responded" in ollama.health_message


def test_unconfigured_cloud_provider_reports_missing_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    registry = LLMProviderRegistry()

    records = registry.list_provider_records()
    openai = next(record for record in records if record.provider_id == "openai")

    assert openai.configured is False
    assert openai.reachable is False
    assert "Missing OPENAI_API_KEY" in openai.health_message
