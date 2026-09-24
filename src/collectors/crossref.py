import logging

import requests

from src.collectors.errors import CollectorError


LOGGER = logging.getLogger(__name__)
CROSSREF_WORKS_URL = "https://api.crossref.org/works"


def enrich_paper(doi: str) -> dict | None:
    """Look up and normalize enrichment metadata for one DOI."""
    try:
        response = requests.get(f"{CROSSREF_WORKS_URL}/{doi}", timeout=10)
        response.raise_for_status()
    except requests.RequestException as error:
        LOGGER.error("CrossRef request failed: %s", error)
        if error.response is not None and error.response.status_code == 404:
            return None
        raise CollectorError(str(error)) from error

    response_data = response.json()
    paper = response_data.get("message")
    if not isinstance(paper, dict):
        return None

    return _normalize_enrichment(paper)


def _normalize_paper(paper: dict) -> dict:
    """Convert a CrossRef result to the project metadata schema."""
    title = paper.get("title") or []
    venue = paper.get("container-title") or []
    authors = paper.get("author") or []

    return {
        "title": title[0] if isinstance(title, list) and title else None,
        "authors": [_normalize_author(author) for author in authors],
        "year": _extract_year(paper),
        "venue": venue[0] if isinstance(venue, list) and venue else None,
        "venue_type": _get_venue_type(paper.get("type")),
        "doi": paper.get("DOI"),
        "abstract": None,
        "source": "crossref",
        "is_preprint": False,
        "llm": None,
        "revisado": False,
        "mineria": None,
        "categoria": None,
        "relevance_score": None,
        "decision": None,
        "justification": None,
    }


def _normalize_enrichment(paper: dict) -> dict:
    """Convert CrossRef data to the fields used to enrich an existing paper."""
    venue = paper.get("container-title") or []

    return {
        "venue": venue[0] if isinstance(venue, list) and venue else None,
        "venue_type": _get_venue_type(paper.get("type")),
        "doi": paper.get("DOI"),
    }


def _normalize_author(author: dict) -> str | None:
    """Normalize author names from CrossRef."""
    if not isinstance(author, dict):
        return None

    family_name = author.get("family")
    given_name = author.get("given")
    if family_name and given_name:
        return f"{given_name} {family_name}"
    if family_name:
        return family_name
    if given_name:
        return given_name
    return author.get("name")


def _get_venue_type(paper_type: str | None) -> str | None:
    """Map CrossRef article types to the project venue-type vocabulary."""
    if paper_type == "journal-article":
        return "journal"
    if paper_type == "proceedings-article":
        return "conference"
    return None


def _extract_year(paper: dict) -> int | None:
    """Extract publication year from the first available CrossRef date field."""
    for key in ("published-print", "published-online", "created", "deposited"):
        date_value = paper.get(key)
        if not isinstance(date_value, dict):
            continue

        date_parts = date_value.get("date-parts") or []
        if not date_parts:
            continue

        year = date_parts[0][0] if isinstance(date_parts[0], list) and date_parts[0] else None
        if year is not None:
            return year

    return None
