import logging
import os

import requests

from src.collectors.errors import CollectorError


LOGGER = logging.getLogger(__name__)
SEARCH_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
PAPER_FIELDS = (
    "title,abstract,year,venue,publicationVenue,journal,authors,"
    "externalIds,publicationTypes"
)


def collect_papers(
    query: str,
    year_from: int = None,
    year_to: int = None,
    limit: int = 20,
) -> list[dict]:
    """Collect and normalize papers returned by Semantic Scholar."""
    params = {
        "query": query,
        "limit": limit,
        "fields": PAPER_FIELDS,
    }

    if year_from is not None and year_to is not None:
        params["year"] = f"{year_from}-{year_to}"

    headers = {}
    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    if api_key:
        headers["x-api-key"] = api_key

    try:
        response = requests.get(SEARCH_URL, params=params, headers=headers)
        response.raise_for_status()
    except requests.RequestException as error:
        LOGGER.error("Semantic Scholar request failed: %s", error)
        raise CollectorError(str(error)) from error

    response_data = response.json()
    papers = response_data.get("data", [])
    return [_normalize_paper(paper) for paper in papers]


def _normalize_paper(paper: dict) -> dict:
    """Convert a Semantic Scholar paper to the project metadata schema."""
    publication_types = paper.get("publicationTypes") or []
    venue_type = _get_venue_type(publication_types)
    external_ids = paper.get("externalIds") or {}
    authors = paper.get("authors") or []
    # This is an approximate heuristic, not a perfect preprint detector.
    is_preprint = (
        bool(external_ids.get("ArXiv"))
        and not set(publication_types).intersection(
            {"JournalArticle", "Conference", "ConferencePaper", "Review"}
        )
    )

    return {
        "title": paper.get("title"),
        "authors": [author.get("name") for author in authors],
        "year": paper.get("year"),
        "venue": paper.get("venue"),
        "venue_type": venue_type,
        "doi": external_ids.get("DOI"),
        "abstract": paper.get("abstract"),
        "source": "semantic_scholar",
        "is_preprint": is_preprint,
        "llm": None,
        "revisado": False,
        "mineria": None,
        "categoria": None,
        "relevance_score": None,
        "decision": None,
        "justification": None,
    }


def _get_venue_type(publication_types: list) -> str | None:
    """Map the first recognized Semantic Scholar publication type."""
    for publication_type in publication_types:
        if publication_type == "JournalArticle":
            return "journal"
        if publication_type in {"Conference", "ConferencePaper"}:
            return "conference"
    return None
