from backend.services.llm_registry import LLMProviderRegistry


def test_ollama_provider_reports_reachable_when_probe_succeeds(monkeypatch):
    monkeypatch.setenv("LOOPLAMP_ENABLE_OLLAMA", "true")
    registry = LLMProviderRegistry()
    monkeypatch.setattr(
        registry,
        "_fetch_json",
        lambda url, headers=None: {"models": [{"name": "llama3.1:8b"}]},
    )

    records = registry.list_provider_records()
    ollama = next(record for record in records if record.provider_id == "ollama")

    assert ollama.configured is True
    assert ollama.reachable is True
    assert "reachable" in ollama.health_message.lower()


def test_ollama_provider_uses_live_model_catalog(monkeypatch):
    monkeypatch.setenv("LOOPLAMP_ENABLE_OLLAMA", "true")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.1:8b")
    registry = LLMProviderRegistry()
    monkeypatch.setattr(
        registry,
        "_fetch_json",
        lambda url, headers=None: {"models": [{"name": "llama3.2"}, {"name": "qwen2.5:3b"}]},
    )

    records = registry.list_provider_records()
    ollama = next(record for record in records if record.provider_id == "ollama")

    assert ollama.reachable is True
    assert ollama.models == ["llama3.2", "qwen2.5:3b"]
    assert ollama.default_model == "llama3.2"
    assert "not installed" in ollama.health_message


def test_ollama_create_provider_uses_first_live_model_when_default_missing(monkeypatch):
    monkeypatch.setenv("LOOPLAMP_ENABLE_OLLAMA", "true")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.1:8b")
    registry = LLMProviderRegistry()
    monkeypatch.setattr(
        registry,
        "_fetch_json",
        lambda url, headers=None: {"models": [{"name": "llama3.2"}]},
    )

    provider = registry.create_provider(provider_id="ollama")

    assert provider.provider_id == "ollama"
    assert provider.model == "llama3.2"


def test_unconfigured_cloud_provider_reports_missing_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    registry = LLMProviderRegistry()

    records = registry.list_provider_records()
    openai = next(record for record in records if record.provider_id == "openai")

    assert openai.configured is False
    assert openai.reachable is False
    assert "Missing OPENAI_API_KEY" in openai.health_message
