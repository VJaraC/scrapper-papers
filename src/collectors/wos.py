import logging
import os

import requests

from src.collectors.errors import CollectorError


LOGGER = logging.getLogger(__name__)
SEARCH_URL = "https://api.clarivate.com/apis/wos-starter/v2/documents"
MAX_PAGE_SIZE = 50


def collect_papers(
    query: str,
    year_from: int = None,
    year_to: int = None,
    limit: int = 20,
) -> list[dict]:
    """Collect and normalize papers returned by Web of Science Starter API."""
    api_key = os.getenv("WOS_API_KEY")
    if not api_key:
        error = "WOS_API_KEY environment variable is missing"
        LOGGER.error(error)
        raise CollectorError(error)

    page_size = min(limit, MAX_PAGE_SIZE)
    params = {
        "db": "WOS",
        "q": _build_query(query),
        "limit": page_size,
        "page": 1,
    }
    if year_from is not None and year_to is not None:
        params["publishTimeSpan"] = f"{year_from}-01-01+{year_to}-12-31"

    headers = {"X-ApiKey": api_key}
    collected = []
    page = 1
    total = None
    while len(collected) < limit and (total is None or len(collected) < total):
        params["page"] = page
        response = _request(params, headers)
        response_data = response.json()
        hits = response_data.get("hits") or []
        if total is None:
            total = _get_total(response_data)
        if not hits:
            break

        collected.extend(_normalize_paper(hit) for hit in hits)
        page += 1

    return collected[:limit]


def _request(params: dict, headers: dict):
    try:
        response = requests.get(SEARCH_URL, params=params, headers=headers)
        response.raise_for_status()
    except requests.RequestException as error:
        LOGGER.error("Web of Science request failed: %s", error)
        raise CollectorError(str(error)) from error
    return response


def _build_query(query: str) -> str:
    terms = query.split()
    return f"TS=({' AND '.join(terms)})"


def _get_total(response_data: dict) -> int:
    metadata = response_data.get("metadata") or {}
    total = metadata.get("total", 0)
    return total if isinstance(total, int) else 0


def _normalize_paper(paper: dict) -> dict:
    names = paper.get("names") or {}
    authors = names.get("authors") or []
    source = paper.get("source") or {}
    identifiers = paper.get("identifiers") or {}
    types = paper.get("types") or []

    return {
        "title": paper.get("title"),
        "authors": [author.get("displayName") for author in authors],
        "year": source.get("publishYear"),
        "venue": source.get("sourceTitle"),
        "venue_type": _get_venue_type(types),
        "doi": identifiers.get("doi"),
        "abstract": None,
        "source": "wos",
        "is_preprint": False,
        "llm": None,
        "revisado": False,
        "mineria": None,
        "categoria": None,
        "relevance_score": None,
        "decision": None,
        "justification": None,
    }


def _get_venue_type(types: list) -> str | None:
    if types and types[0] == "Article":
        return "journal"
    return None