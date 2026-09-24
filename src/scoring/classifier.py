import re
import unicodedata


LLM_KEYWORDS = (
    "large language model",
    "llm",
    "gpt",
    "chatgpt",
    "generative pre-trained transformer",
    "foundation model",
)
MINING_KEYWORDS = (
    "mining dispatch",
    "mine dispatch",
    "truck dispatch",
    "haul truck",
    "mining fleet",
    "open-pit mining",
    "underground mining",
    "despacho minero",
)
MAS_KEYWORDS = (
    "multi-agent",
    "multiagent",
    "multi agent",
    "agent-based",
    "sistema multiagente",
    "sistemas multi-agente",
    "multiagente",
)
SCHEDULING_KEYWORDS = (
    "scheduling",
    "dispatch",
    "dispatching",
    "job shop",
    "task allocation",
    "resource allocation",
)


def classify_paper(paper: dict) -> dict:
    """Classify a paper using explicit LLM and mining keyword rules."""
    text = _build_search_text(paper)
    if not text:
        return {
            "mas": None,
            "scheduling": None,
            "llm": None,
            "mineria": None,
            "categoria": "NO_CLASIFICABLE",
        }

    mas = _contains_keyword(text, MAS_KEYWORDS)
    scheduling = _contains_keyword(text, SCHEDULING_KEYWORDS)
    llm = _contains_keyword(text, LLM_KEYWORDS)
    mineria = _contains_keyword(text, MINING_KEYWORDS)

    return {
        "mas": mas,
        "scheduling": scheduling,
        "llm": llm,
        "mineria": mineria,
        "categoria": _get_category(llm, mineria),
    }


def _build_search_text(paper: dict) -> str:
    """Combine and normalize the title and abstract available for evaluation."""
    text_parts = [paper.get("title"), paper.get("abstract")]
    usable_parts = [part for part in text_parts if isinstance(part, str) and part.strip()]
    if not usable_parts:
        return ""
    return _normalize_text(" ".join(usable_parts))


def _normalize_text(text: str) -> str:
    """Normalize case, accents, and punctuation for keyword matching."""
    without_accents = unicodedata.normalize("NFKD", text)
    without_accents = "".join(
        character for character in without_accents
        if not unicodedata.combining(character)
    )
    return without_accents.casefold()


def _contains_keyword(text: str, keywords: tuple[str, ...]) -> bool:
    """Return whether any keyword appears as a complete text token sequence."""
    return any(re.search(rf"\b{re.escape(_normalize_text(keyword))}\b", text) for keyword in keywords)


def _get_category(llm: bool, mineria: bool) -> str:
    """Map the two classification axes to the project category vocabulary."""
    if llm and mineria:
        return "MAS-DESPACHO-MINERO-LLM"
    if llm:
        return "MAS-LLM"
    if mineria:
        return "MAS-DESPACHO-MINERO"
    return "MAS-SCHEDULING"
