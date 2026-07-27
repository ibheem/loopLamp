from dataclasses import dataclass
from typing import Callable, List

from backend.core.documents import Document


@dataclass
class GuardedExecutionResult:
    answer: str
    attempts: int
    used_reflection: bool
    sources: List[Document]


def _answer_is_grounded(answer: str, sources: List[Document]) -> bool:
    lowered = answer.lower()
    return any(token in lowered for token in ("based on the retrieved context", "retrieved context")) and bool(sources)


def run_with_reflection(
    generate: Callable[[List[Document]], str],
    retrieve: Callable[[int], List[Document]],
    initial_k: int,
    max_attempts: int = 2,
) -> GuardedExecutionResult:
    used_reflection = False
    last_answer = ""
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
