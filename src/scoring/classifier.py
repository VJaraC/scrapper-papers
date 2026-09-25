import unicodedata

from sentence_transformers import SentenceTransformer, util


MODEL_NAME = "all-MiniLM-L6-v2"
# Recalibrado contra los 148 papers reales del pool (data/papers.csv), no solo
# los 5 casos iniciales: con 0.15 el eje "mas" pasaba a True en ~93% del pool
# (vs. ~63% con las keywords viejas), incluyendo falsos positivos claros
# (p. ej. "The Bike Sharing Problem"). Subido a 0.30 para exigir mayor
# similitud semántica real.
MAS_THRESHOLD = 0.30
# Recalibrado contra el pool completo junto con MAS_THRESHOLD.
SCHEDULING_THRESHOLD = 0.28
# Recalibrado contra el pool completo junto con MAS_THRESHOLD.
LLM_THRESHOLD = 0.22
# Sin cambios: ya calibrado correctamente contra el pool completo de 148
# papers (proporción de True razonable, sin falsos positivos evidentes).
MINERIA_THRESHOLD = 0.35

REFERENCE_TEXTS = {
    "mas": (
        "a paper about multi-agent systems where multiple autonomous agents coordinate, negotiate, or interact",
        "research on autonomous software agents collaborating to solve a shared problem",
    ),
    "scheduling": (
        "a paper about scheduling, task allocation, resource allocation, or dispatching problems",
        "optimization of assigning tasks and resources over time under operational constraints",
    ),
    "llm": (
        "a paper about large language models (LLMs), such as GPT, ChatGPT, or foundation models for natural language processing",
        "research using neural language models to understand and generate human language",
    ),
    "mineria": (
        "a paper about mining operations, such as truck dispatch, fleet management, or open-pit or underground mining",
        "industrial extraction and haulage operations in surface or underground mines",
    ),
}

MODEL = SentenceTransformer(MODEL_NAME)
REFERENCE_EMBEDDINGS = {
    axis: MODEL.encode(references, convert_to_tensor=True)
    for axis, references in REFERENCE_TEXTS.items()
}


def classify_paper(paper: dict) -> dict:
    """Classify a paper using semantic similarity to reference descriptions."""
    text = _build_search_text(paper)
    if not text:
        return {
            "mas": None,
            "scheduling": None,
            "llm": None,
            "mineria": None,
            "mas_score": None,
            "scheduling_score": None,
            "llm_score": None,
            "mineria_score": None,
            "categoria": "NO_CLASIFICABLE",
        }

    paper_embedding = MODEL.encode(text, convert_to_tensor=True)
    scores = {
        axis: float(util.cos_sim(paper_embedding, reference_embeddings).max().item())
        for axis, reference_embeddings in REFERENCE_EMBEDDINGS.items()
    }
    mas_score = scores["mas"]
    scheduling_score = scores["scheduling"]
    llm_score = scores["llm"]
    mineria_score = scores["mineria"]
    mas = mas_score >= MAS_THRESHOLD
    scheduling = scheduling_score >= SCHEDULING_THRESHOLD
    llm = llm_score >= LLM_THRESHOLD
    mineria = mineria_score >= MINERIA_THRESHOLD

    return {
        "mas": mas,
        "scheduling": scheduling,
        "llm": llm,
        "mineria": mineria,
        "mas_score": mas_score,
        "scheduling_score": scheduling_score,
        "llm_score": llm_score,
        "mineria_score": mineria_score,
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
    """Normalize case and accents before embedding the paper text."""
    without_accents = unicodedata.normalize("NFKD", text)
    without_accents = "".join(
        character
        for character in without_accents
        if not unicodedata.combining(character)
    )
    return without_accents.casefold()


def _get_category(llm: bool, mineria: bool) -> str:
    """Map the two classification axes to the project category vocabulary."""
    if llm and mineria:
        return "MAS-DESPACHO-MINERO-LLM"
    if llm:
        return "MAS-LLM"
    if mineria:
        return "MAS-DESPACHO-MINERO"
    return "MAS-SCHEDULING"
