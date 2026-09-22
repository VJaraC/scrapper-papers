import argparse
import logging
from pathlib import Path

from dotenv import load_dotenv

from src.collectors import crossref, scopus, semantic_scholar
from src.scoring.classifier import classify_paper
from src.scoring.decision import decide_paper
from src.storage.csv_store import upsert_papers


load_dotenv()

LOGGER = logging.getLogger(__name__)
DEFAULT_CSV_PATH = Path("data/papers.csv")


def buscar(
    query: str,
    year_from: int = 2021,
    year_to: int = 2026,
    limit: int = 20,
    csv_path=DEFAULT_CSV_PATH,
) -> dict:
    """Run the collection, scoring, decision, and persistence pipeline."""
    collected = []
    for collector_name, collector in (
        ("semantic_scholar", semantic_scholar.collect_papers),
        ("scopus", scopus.collect_papers),
    ):
        try:
            papers = collector(query, year_from=year_from, year_to=year_to, limit=limit)
        except Exception as error:
            LOGGER.error("Collector %s failed: %s", collector_name, error)
            continue
        if papers:
            collected.extend(papers)

    papers = _deduplicate_by_doi(collected)
    processed_papers = []
    for paper in papers:
        processed_paper = dict(paper)
        _enrich_with_crossref(processed_paper)
        processed_paper.update(classify_paper(processed_paper))
        processed_paper.update(decide_paper(processed_paper))
        processed_papers.append(processed_paper)

    csv_file = Path(csv_path)
    csv_file.parent.mkdir(parents=True, exist_ok=True)
    counts = upsert_papers(processed_papers, csv_file)
    print(
        "Resumen: "
        f"nuevos={counts['nuevos']}, "
        f"actualizados={counts['actualizados']}, "
        f"protegidos={counts['protegidos']}"
    )
    return counts


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
    """Return whether an abstract contains non-whitespace text."""
    abstract = paper.get("abstract")
    return abstract is not None and bool(abstract.strip())


def _enrich_with_crossref(paper: dict) -> None:
    """Enrich only papers lacking venue type and having a DOI."""
    if paper.get("venue_type") is not None or not paper.get("doi"):
        return

    try:
        enrichment = crossref.enrich_paper(paper["doi"])
    except Exception as error:
        LOGGER.error("Collector crossref enrichment failed: %s", error)
        return

    if not enrichment:
        return
    for field, value in enrichment.items():
        if value is not None:
            paper[field] = value


def _normalize_doi(doi) -> str | None:
    if doi is None:
        return None
    normalized = str(doi).strip().casefold()
    return normalized or None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Collect and curate papers.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    buscar_parser = subparsers.add_parser("buscar", help="Search for papers.")
    buscar_parser.add_argument("query", help="Plain-text search query.")
    buscar_parser.add_argument("--year-from", type=int, default=2021)
    buscar_parser.add_argument("--year-to", type=int, default=2026)
    buscar_parser.add_argument("--limit", type=int, default=20)
    buscar_parser.add_argument("--csv-path", default=str(DEFAULT_CSV_PATH))
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "buscar":
        buscar(
            args.query,
            year_from=args.year_from,
            year_to=args.year_to,
            limit=args.limit,
            csv_path=args.csv_path,
        )
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())