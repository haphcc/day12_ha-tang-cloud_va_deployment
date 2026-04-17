"""Deterministic mock LLM for local and classroom testing."""

_RESPONSES = [
    "Container la cach dong goi app de chay o moi noi. Build once, run anywhere!",
    "Load balancing phan phoi request qua nhieu instance de tang do san sang.",
    "Redis thuong duoc dung de luu session, cache, va chia se state giua replicas.",
    "Health va readiness giup platform biet khi nao restart va khi nao route traffic.",
]


def ask(question: str) -> str:
    text = (question or "").strip()
    if not text:
        return "Vui long gui cau hoi hop le."
    idx = sum(ord(ch) for ch in text) % len(_RESPONSES)
    return _RESPONSES[idx]
