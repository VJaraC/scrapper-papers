from pathlib import Path

import pandas as pd


CSV_COLUMNS = [
    "title",
    "authors",
    "year",
    "venue",
    "venue_type",
    "doi",
    "abstract",
    "source",
    "is_preprint",
    "revisado",
    "mas",
    "scheduling",
    "llm",
    "mineria",
    "categoria",
    "relevance_score",
    "decision",
    "justification",
]


def load_pool(path) -> list[dict]:
    """Load the paper pool from CSV, returning an empty list if absent."""
    csv_path = Path(path)
    if not csv_path.exists():
        return []

    frame = pd.read_csv(csv_path, keep_default_na=False)
    frame = _ensure_columns(frame)
    frame["authors"] = frame["authors"].map(_deserialize_authors)
    frame["revisado"] = frame["revisado"].map(_to_bool)
    return frame.to_dict(orient="records")


def upsert_papers(new_papers: list[dict], path) -> dict:
    """Insert or refresh papers, preserving externally reviewed rows."""
    csv_path = Path(path)
    existing_papers = load_pool(csv_path)
    counts = {"nuevos": 0, "actualizados": 0, "protegidos": 0}
    doi_indexes = {
        normalized_doi: index
        for index, paper in enumerate(existing_papers)
        if (normalized_doi := _normalize_doi(paper.get("doi"))) is not None
    }

    for paper in new_papers:
        normalized_paper = _normalize_paper(paper)
        normalized_doi = _normalize_doi(normalized_paper.get("doi"))
        existing_index = doi_indexes.get(normalized_doi) if normalized_doi else None

        if existing_index is not None:
            if existing_papers[existing_index].get("revisado") is True:
                counts["protegidos"] += 1
                continue
            counts["actualizados"] += 1
            existing_papers[existing_index] = normalized_paper
            continue

        counts["nuevos"] += 1
        existing_papers.append(normalized_paper)
        if normalized_doi is not None:
            doi_indexes[normalized_doi] = len(existing_papers) - 1

    _write_pool(existing_papers, csv_path)
    return counts


def export_to_excel(csv_path, xlsx_path) -> None:
    """Export the complete CSV pool to an Excel workbook."""
    export_papers_to_excel(load_pool(csv_path), xlsx_path)


def save_pool(papers: list[dict], path) -> None:
    """Overwrite the complete CSV pool without merging or deduplicating."""
    _write_pool(papers, Path(path))


def export_papers_to_excel(papers: list[dict], xlsx_path: str) -> None:
    """Export an in-memory paper list directly to Excel."""
    frame = _papers_to_frame(papers)
    frame.to_excel(Path(xlsx_path), index=False, engine="openpyxl")


def _normalize_paper(paper: dict) -> dict:
    """Keep the common schema and never create a reviewed row."""
    normalized = {column: paper.get(column, "") for column in CSV_COLUMNS}
    normalized["revisado"] = False
    return normalized


def _ensure_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Add missing schema columns and return columns in the canonical order."""
    for column in CSV_COLUMNS:
        if column not in frame:
            frame[column] = ""
    return frame[CSV_COLUMNS]


def _to_bool(value) -> bool:
    """Interpret only an explicit true value as reviewed."""
    return value is True or str(value).strip().casefold() == "true"


def _write_pool(papers: list[dict], path: Path) -> None:
    """Write normalized papers using the canonical CSV schema."""
    frame = _papers_to_frame(papers)
    frame.to_csv(path, index=False)


def _papers_to_frame(papers: list[dict]) -> pd.DataFrame:
    """Prepare papers for CSV or Excel while preserving the schema order."""
    frame = _ensure_columns(pd.DataFrame(papers))
    frame["authors"] = frame["authors"].map(_serialize_authors)
    return frame


def _serialize_authors(authors) -> str:
    if isinstance(authors, list):
        return "; ".join(str(author) for author in authors)
    if authors is None:
        return ""
    return str(authors)


def _deserialize_authors(authors) -> list[str]:
    if not authors:
        return []
    return str(authors).split("; ")


def _normalize_doi(doi) -> str | None:
    """Normalize DOI only for case-insensitive matching."""
    if doi is None:
        return None
    normalized = str(doi).strip().casefold()
    return normalized or None
