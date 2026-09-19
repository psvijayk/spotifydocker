import re
from dataclasses import dataclass
from backend.config import settings


INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"reveal\s+(the\s+)?system\s+prompt",
    r"show\s+(me\s+)?your\s+system\s+instructions",
    r"developer\s+message",
    r"jailbreak",
    r"bypass\s+(the\s+)?guardrails",
]


@dataclass
class GuardrailResult:
    allowed: bool
    text: str
    flags: list[str]


class Guardrails:
    """Deterministic guardrail layer.

    This is deliberately dependency-light. It can later be replaced by
    Guardrails AI or NVIDIA NeMo Guardrails without changing the API layer.
    """

    def validate_input(self, question: str) -> GuardrailResult:
        flags = []
        q = question.strip()

        if not q:
            return GuardrailResult(False, q, ["empty_question"])

        if len(q) > settings.max_question_chars:
            return GuardrailResult(False, q, ["question_too_long"])

        lower = q.lower()
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, lower):
                flags.append("prompt_injection_detected")

        if flags:
            return GuardrailResult(False, q, flags)

        return GuardrailResult(True, q, [])

    def validate_context(self, vector_results: list[dict], graph_results: list[dict]):
        flags = []

        # Remove duplicate vector chunks.
        seen = set()
        deduped = []
        for item in vector_results:
            key = item.get("chunk_id") or item.get("text", "")[:100]
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)

        # Keep evidence bounded.
        total = 0
        bounded = []
        for item in deduped:
            size = len(item.get("text", ""))
            if total + size > settings.max_context_chars:
                break
            bounded.append(item)
            total += size

        if not bounded and not graph_results:
            flags.append("insufficient_retrieval_evidence")

        return bounded, graph_results, flags

    def validate_output(self, answer: str, has_evidence: bool) -> GuardrailResult:
        flags = []
        text = (answer or "").strip()

        if not text:
            return GuardrailResult(False, "", ["empty_model_output"])

        if len(text) > settings.max_answer_chars:
            text = text[:settings.max_answer_chars].rstrip() + "..."

        leakage = [
            "system prompt:",
            "developer message:",
            "internal instructions:",
            "ignore previous instructions",
        ]
        if any(x in text.lower() for x in leakage):
            return GuardrailResult(False, "", ["instruction_leakage"])

        if not has_evidence:
            return GuardrailResult(
                True,
                "I could not find sufficient evidence in the indexed documents or knowledge graph to answer that question.",
                ["insufficient_evidence"],
            )

        return GuardrailResult(True, text, flags)
