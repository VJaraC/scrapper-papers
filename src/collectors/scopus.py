import logging
import os

import requests

from src.collectors.errors import CollectorError


LOGGER = logging.getLogger(__name__)
SEARCH_URL = "https://api.elsevier.com/content/search/scopus"


def collect_papers(
    query: str,
    year_from: int = None,
    year_to: int = None,
    limit: int = 20,
) -> list[dict]:
    """Collect and normalize papers returned by Scopus."""
    api_key = os.getenv("SCOPUS_API_KEY")
    if not api_key:
        LOGGER.error("SCOPUS_API_KEY environment variable is missing")
        return []

    scopus_query = f"TITLE-ABS-KEY({_build_query(query)})"
    if year_from is not None and year_to is not None:
        scopus_query += (
            f" AND PUBYEAR > {year_from - 1}"
            f" AND PUBYEAR < {year_to + 1}"
        )

    params = {
        "query": scopus_query,
        "count": limit,
        "start": 0,
        "view": "STANDARD",
    }
    headers = {"X-ELS-APIKey": api_key}

    try:
        response = requests.get(SEARCH_URL, params=params, headers=headers)
        response.raise_for_status()
    except requests.RequestException as error:
        LOGGER.error("Scopus request failed: %s", error)
        raise CollectorError(str(error)) from error

    response_data = response.json()
    entries = response_data.get("search-results", {}).get("entry", [])
    return [_normalize_paper(entry) for entry in entries]


def _build_query(query: str) -> str:
    terms = query.split()
    return " AND ".join(terms)


def _normalize_paper(paper: dict) -> dict:
    """Convert a Scopus result to the project metadata schema."""
    return {
        "title": paper.get("dc:title"),
        "authors": _normalize_authors(paper.get("dc:creator")),
        "year": _extract_year(paper.get("prism:coverDate")),
        "venue": paper.get("prism:publicationName"),
        "venue_type": _get_venue_type(paper.get("subtypeDescription")),
        "doi": paper.get("prism:doi"),
        "abstract": None,
        "source": "scopus",
        "is_preprint": False,
        "llm": None,
        "revisado": False,
        "mineria": None,
        "categoria": None,
        "relevance_score": None,
        "decision": None,
        "justification": None,
    }


def _normalize_authors(creator: str | None) -> list[str]:
    """Normalize the single author value available in STANDARD results."""
    return [creator] if creator else []


def _get_venue_type(subtype_description: str | None) -> str | None:
    """Map Scopus subtype descriptions to the project venue vocabulary."""
    if subtype_description == "Article":
        return "journal"
    if subtype_description == "Conference Paper":
        return "conference"
    return None


def _extract_year(cover_date: str | None) -> int | None:
    """Extract a publication year from a YYYY-MM-DD cover date."""
    if not isinstance(cover_date, str) or len(cover_date) < 4:
        return None

    year_text = cover_date[:4]
    if not year_text.isdigit():
        return None
    return int(year_text)
