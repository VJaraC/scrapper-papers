import logging
from pathlib import Path

from src.collectors import crossref, scopus, semantic_scholar, wos
from src.collectors.errors import CollectorError
from src.scoring.classifier import classify_paper
from src.scoring.decision import decide_paper
from src.storage.csv_store import upsert_papers


LOGGER = logging.getLogger(__name__)


def run_search(
    query: str,
    year_from: int = 2021,
    year_to: int = 2026,
    limit: int = 20,
    csv_path="data/papers.csv",
) -> dict:
    """Collect, classify, decide, and persist papers from all search sources."""
    collected = []
    source_results = {}
    for source_name, collector in (
        ("semantic_scholar", semantic_scholar.collect_papers),
        ("scopus", scopus.collect_papers),
        ("wos", wos.collect_papers),
    ):
        try:
            papers = collector(query, year_from=year_from, year_to=year_to, limit=limit)
        except Exception as error:
            LOGGER.error("Collector %s failed: %s", source_name, error)
            source_results[source_name] = {
                "success": False,
                "count": 0,
                "error": str(error),
            }
            continue

        source_results[source_name] = {
            "success": True,
            "count": len(papers),
            "error": None,
        }
        collected.extend(papers)

    papers = _deduplicate_by_doi(collected)
    processed_papers = []
    enrichment_result = {"attempted": 0, "succeeded": 0, "failed": 0}
    for paper in papers:
        processed_paper = dict(paper)
        _enrich_with_crossref(processed_paper, enrichment_result)
        processed_paper.update(classify_paper(processed_paper))
        processed_paper.update(decide_paper(processed_paper))
        processed_papers.append(processed_paper)

    csv_file = Path(csv_path)
    csv_file.parent.mkdir(parents=True, exist_ok=True)
    counts = upsert_papers(processed_papers, csv_file)
    return {
        "sources": source_results,
        "enrichment": {"crossref": enrichment_result},
        "upsert": counts,
    }


def _deduplicate_by_doi(papers: list[dict]) -> list[dict]:
    """Deduplicate one batch by DOI, preferring a paper with useful abstract."""
    deduplicated = []
    doi_indexes = {}
    for paper in papers:
        doi = _normalize_doi(paper.get("doi"))
        if doi is None:
            deduplicated.append(paper)
            continue

        existing_index = doi_indexes.get(doi)
        if existing_index is None:
            doi_indexes[doi] = len(deduplicated)
            deduplicated.append(paper)
            continue

        existing_paper = deduplicated[existing_index]
        if not _has_abstract(existing_paper) and _has_abstract(paper):
            deduplicated[existing_index] = paper

    return deduplicated


def _has_abstract(paper: dict) -> bool:
    abstract = paper.get("abstract")
    return abstract is not None and bool(abstract.strip())


def _enrich_with_crossref(paper: dict, result: dict) -> None:
    if paper.get("venue_type") is not None or not paper.get("doi"):
        return

    result["attempted"] += 1
    try:
        enrichment = crossref.enrich_paper(paper["doi"])
    except CollectorError as error:
        LOGGER.error("Collector crossref enrichment failed: %s", error)
        result["failed"] += 1
        return

    if not enrichment:
        return
    result["succeeded"] += 1
    for field, value in enrichment.items():
        if value is not None:
            paper[field] = value


def _normalize_doi(doi) -> str | None:
    if doi is None:
        return None
    normalized = str(doi).strip().casefold()
    return normalized or None