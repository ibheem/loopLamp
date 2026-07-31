from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

from backend.core.documents import Document
from backend.core.models import DomainReport


@dataclass
class GuardedExecutionResult:
    answer: DomainReport
    attempts: int
    used_reflection: bool
    sources: List[Document]
    runtime_metadata: Dict[str, Any] = field(default_factory=dict)


def _answer_is_grounded(answer: DomainReport, sources: List[Document]) -> bool:
    lowered = answer.summary.lower()
    return any(token in lowered for token in ("based on the retrieved context", "retrieved context")) and bool(sources)


def run_with_reflection(
    generate: Callable[[List[Document]], DomainReport],
    retrieve: Callable[[int], List[Document]],
    initial_k: int,
    max_attempts: int = 2,
) -> GuardedExecutionResult:
    used_reflection = False
    last_answer = DomainReport(domain="unknown", summary="No answer generated")
    last_sources: List[Document] = []

    for attempt in range(1, max_attempts + 1):
        k = initial_k + (attempt - 1)
        sources = retrieve(k)
        answer = generate(sources)
        last_answer = answer
        last_sources = sources
        if _answer_is_grounded(answer, sources):
            return GuardedExecutionResult(
                answer=answer,
                attempts=attempt,
                used_reflection=used_reflection,
                sources=sources,
            )
        used_reflection = True

    return GuardedExecutionResult(
        answer=last_answer,
        attempts=max_attempts,
        used_reflection=used_reflection,
        sources=last_sources,
    )
