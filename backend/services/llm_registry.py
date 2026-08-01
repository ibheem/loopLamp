import logging
import os
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from backend.core.models import LLMProviderRecord
from backend.services.llm_provider import OpenAIResponsesReportProvider, ReportLLMProvider

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProviderSpec:
    provider_id: str
    label: str
    description: str
    default_model: str
    models: List[str] = field(default_factory=list)
    api_key_env: Optional[str] = None
    base_url: Optional[str] = None
    supports_custom_model: bool = True
    requires_api_key: bool = True
    enabled_flag_env: Optional[str] = None


class LLMProviderRegistry:
    def __init__(self):
        self._specs: Dict[str, ProviderSpec] = {
            "openai": ProviderSpec(
                provider_id="openai",
                label="OpenAI",
                description="Uses the native OpenAI Responses API integration.",
                default_model=os.getenv("OPENAI_MODEL", "gpt-5-mini"),
                models=["gpt-5-mini", "gpt-5.1", "gpt-4.1-mini"],
                api_key_env="OPENAI_API_KEY",
            ),
            "openrouter": ProviderSpec(
                provider_id="openrouter",
                label="OpenRouter",
                description="Uses an OpenAI-compatible endpoint through OpenRouter.",
                default_model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4.1-mini"),
                models=["openai/gpt-4.1-mini", "openai/gpt-5-mini", "anthropic/claude-3.7-sonnet"],
                api_key_env="OPENROUTER_API_KEY",
                base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            ),
            "groq": ProviderSpec(
                provider_id="groq",
                label="Groq",
                description="Uses Groq's OpenAI-compatible endpoint for fast inference.",
                default_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                models=["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
                api_key_env="GROQ_API_KEY",
                base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
            ),
            "together": ProviderSpec(
                provider_id="together",
                label="Together",
                description="Uses Together AI through an OpenAI-compatible endpoint.",
                default_model=os.getenv("TOGETHER_MODEL", "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"),
                models=[
                    "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
                    "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
                ],
                api_key_env="TOGETHER_API_KEY",
                base_url=os.getenv("TOGETHER_BASE_URL", "https://api.together.xyz/v1"),
            ),
            "ollama": ProviderSpec(
                provider_id="ollama",
                label="Ollama",
                description="Uses a local Ollama server through its OpenAI-compatible API.",
                default_model=os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
                models=["llama3.1:8b", "qwen2.5:7b", "mistral:7b"],
                base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1"),
                requires_api_key=False,
                enabled_flag_env="LOOPLAMP_ENABLE_OLLAMA",
            ),
        }

    def default_provider_id(self) -> str:
        return "auto"

    def resolve_auto_provider_id(self) -> str:
        for provider_id in ("openai", "openrouter", "groq", "together", "ollama"):
            if self.is_provider_available(provider_id):
                return provider_id
        return "openai"

    def is_provider_available(self, provider_id: str) -> bool:
        spec = self._specs.get(provider_id)
        if spec is None:
            return False
        if spec.enabled_flag_env:
            enabled_value = os.getenv(spec.enabled_flag_env, "").strip().lower()
            return enabled_value in {"1", "true", "yes", "on"}
        if spec.api_key_env:
            return bool(os.getenv(spec.api_key_env))
        return True

    def _is_provider_configured(self, provider_id: str) -> bool:
        return self.is_provider_available(provider_id)

    def _health_check(self, provider_id: str) -> Tuple[bool, str]:
        spec = self._specs.get(provider_id)
        if spec is None:
            return False, "Unknown provider."

        configured = self._is_provider_configured(provider_id)
        if not configured:
            if spec.enabled_flag_env:
                return False, f"Set {spec.enabled_flag_env}=true to enable this provider."
            if spec.api_key_env:
                return False, f"Missing {spec.api_key_env}."
            return False, "Provider is not configured."

        if provider_id == "ollama":
            base_url = (spec.base_url or "http://127.0.0.1:11434/v1").rstrip("/")
            root_url = base_url[:-3] if base_url.endswith("/v1") else base_url
            return self._probe_url(f"{root_url}/api/tags")

        base_url = (spec.base_url or "https://api.openai.com/v1").rstrip("/")
        headers = {}
        if spec.api_key_env:
            api_key = os.getenv(spec.api_key_env, "").strip()
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
        return self._probe_url(f"{base_url}/models", headers=headers)

    def _probe_url(self, url: str, headers: Optional[Dict[str, str]] = None) -> Tuple[bool, str]:
        request = Request(url, headers=headers or {}, method="GET")
        try:
            with urlopen(request, timeout=1.5) as response:
                status = getattr(response, "status", 200)
            if 200 <= status < 300:
                return True, "Provider responded to the health check."
            return False, f"Health check returned status {status}."
        except HTTPError as exc:
            if exc.code in {401, 403}:
                return False, f"Provider rejected credentials with status {exc.code}."
            return False, f"Health check returned status {exc.code}."
        except URLError as exc:
            reason = getattr(exc, "reason", exc)
            return False, f"Provider is unreachable: {reason}."
        except Exception as exc:
            return False, f"Provider health check failed: {exc.__class__.__name__}."

    def _fetch_json(self, url: str, headers: Optional[Dict[str, str]] = None) -> dict:
        request = Request(url, headers=headers or {}, method="GET")
        with urlopen(request, timeout=1.5) as response:
            payload = response.read().decode("utf-8")
        return json.loads(payload or "{}")

    def _resolve_ollama_runtime(self, spec: ProviderSpec) -> Tuple[bool, str, List[str], str]:
        configured = self._is_provider_configured(spec.provider_id)
        if not configured:
            return False, f"Set {spec.enabled_flag_env}=true to enable this provider.", [], spec.default_model

        base_url = (spec.base_url or "http://127.0.0.1:11434/v1").rstrip("/")
        root_url = base_url[:-3] if base_url.endswith("/v1") else base_url
        try:
            payload = self._fetch_json(f"{root_url}/api/tags")
        except HTTPError as exc:
            return False, f"Health check returned status {exc.code}.", [], spec.default_model
        except URLError as exc:
            reason = getattr(exc, "reason", exc)
            return False, f"Provider is unreachable: {reason}.", [], spec.default_model
        except Exception as exc:
            return False, f"Provider health check failed: {exc.__class__.__name__}.", [], spec.default_model

        models = sorted(
            {
                str(model.get("name", "")).strip()
                for model in payload.get("models", [])
                if str(model.get("name", "")).strip()
            }
        )
        if not models:
            return True, "Ollama is reachable, but no local models are installed.", [], spec.default_model

        effective_default = spec.default_model if spec.default_model in models else models[0]
        if spec.default_model and spec.default_model not in models:
            message = (
                f"Ollama is reachable with {len(models)} local model(s). "
                f"Configured default '{spec.default_model}' is not installed, so '{effective_default}' will be used by default."
            )
        else:
            message = f"Ollama is reachable with {len(models)} local model(s)."
        return True, message, models, effective_default

    def list_provider_records(self) -> List[LLMProviderRecord]:
        records = [
            LLMProviderRecord(
                provider_id="auto",
                label="Auto",
                description="Uses the first configured provider in the fallback chain.",
                available=True,
                configured=True,
                reachable=True,
                health_message="Automatic provider resolution is always available.",
                default_model="",
                models=[],
                supports_custom_model=False,
            )
        ]

        for spec in self._specs.values():
            configured = self._is_provider_configured(spec.provider_id)
            models = list(spec.models)
            default_model = spec.default_model
            if spec.provider_id == "ollama":
                reachable, health_message, models, default_model = self._resolve_ollama_runtime(spec)
            else:
                reachable, health_message = self._health_check(spec.provider_id)
            records.append(
                LLMProviderRecord(
                    provider_id=spec.provider_id,
                    label=spec.label,
                    description=spec.description,
                    available=configured,
                    configured=configured,
                    reachable=reachable,
                    health_message=health_message,
                    default_model=default_model,
                    models=models,
                    supports_custom_model=spec.supports_custom_model,
                )
            )

        return records

    def log_startup_health(self) -> None:
        for record in self.list_provider_records():
            if record.provider_id == "auto":
                continue
            if record.configured and not record.reachable:
                logger.warning(
                    f"llm_provider_unreachable provider={record.provider_id} message={record.health_message}"
                )

    def create_provider(self, provider_id: str = "auto", model_override: Optional[str] = None) -> ReportLLMProvider:
        selected_provider_id = provider_id or "auto"
        if selected_provider_id == "auto":
            selected_provider_id = self.resolve_auto_provider_id()

        spec = self._specs.get(selected_provider_id)
        if spec is None:
            supported = ", ".join(["auto", *sorted(self._specs.keys())])
            raise ValueError(
                f"Unsupported llm_provider '{provider_id}'. Supported providers: {supported}"
            )

        selected_model = (model_override or "").strip()
        if not selected_model:
            if spec.provider_id == "ollama":
                _, _, _, effective_default = self._resolve_ollama_runtime(spec)
                selected_model = effective_default.strip()
            else:
                selected_model = spec.default_model.strip()
        return OpenAIResponsesReportProvider(
            api_key=os.getenv(spec.api_key_env) if spec.api_key_env else None,
            model=selected_model,
            escalation_model=selected_model,
            provider_id=spec.provider_id,
            base_url=spec.base_url,
            requires_api_key=spec.requires_api_key,
        )
