from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st

from src.cli import DEFAULT_CSV_PATH
from src.storage.csv_store import (
    CSV_COLUMNS,
    export_papers_to_excel,
    load_pool,
    save_pool,
)


def filter_papers(papers: list[dict], filters: dict) -> list[dict]:
    """Filter papers using None as the no-filter value for every criterion."""
    filtered = []
    for paper in papers:
        year = paper.get("year")
        if filters.get("year_min") is not None and (
            year is None or year < filters["year_min"]
        ):
            continue
        if filters.get("year_max") is not None and (
            year is None or year > filters["year_max"]
        ):
            continue
        if not _matches_filter(paper, "source", filters.get("source")):
            continue
        if not _matches_filter(paper, "llm", filters.get("llm")):
            continue
        if not _matches_filter(paper, "mineria", filters.get("mineria")):
            continue
        if not _matches_filter(paper, "categoria", filters.get("categoria")):
            continue
        if not _matches_filter(paper, "venue_type", filters.get("venue_type")):
            continue
        filtered.append(paper)
    return filtered


def _matches_filter(paper: dict, field: str, expected) -> bool:
    return expected is None or paper.get(field) == expected


def run_app(csv_path=DEFAULT_CSV_PATH):
    """Render the existing paper pool without triggering new searches."""
    st.set_page_config(page_title="Pool de papers", layout="wide")
    st.title("Pool de papers")

    pool_path = Path(csv_path)
    papers = load_pool(pool_path)
    if not papers:
        st.info("No hay papers en el pool.")
        return

    frame = pd.DataFrame(papers)
    sidebar = st.sidebar
    sidebar.header("Filtros")
    filters = _build_filters(sidebar, frame)
    filtered_papers = filter_papers(papers, filters)

    editable_frame = pd.DataFrame(filtered_papers)
    edited_frame = st.data_editor(
        editable_frame,
        column_config={"revisado": st.column_config.CheckboxColumn("Revisado")},
        disabled=[column for column in CSV_COLUMNS if column != "revisado"],
        hide_index=True,
        use_container_width=True,
        key="paper_editor",
    )
    _save_review_changes(papers, filtered_papers, edited_frame, pool_path)

    if st.button("Exportar filtrados a Excel"):
        export_path = pool_path.with_name("papers_filtrados.xlsx")
        export_papers_to_excel(filtered_papers, export_path)
        st.success(f"Exportado: {export_path}")


def _build_filters(sidebar, frame: pd.DataFrame) -> dict:
    years = [int(year) for year in frame["year"] if pd.notna(year)]
    year_min = min(years) if years else 2021
    year_max = max(years) if years else 2026
    selected_years = sidebar.slider("Año", year_min, year_max, (year_min, year_max))
    return {
        "year_min": selected_years[0],
        "year_max": selected_years[1],
        "source": _select_filter(sidebar, "Fuente", frame["source"]),
        "llm": _select_boolean(sidebar, "LLM"),
        "mineria": _select_boolean(sidebar, "Minería"),
        "categoria": _select_filter(sidebar, "Categoría", frame["categoria"]),
        "venue_type": _select_filter(sidebar, "Tipo de venue", frame["venue_type"]),
    }


def _select_filter(sidebar, label: str, values):
    options = [None] + sorted({value for value in values if value not in (None, "")})
    selected = sidebar.selectbox(label, options, format_func=lambda value: "Todos" if value is None else value)
    return selected


def _select_boolean(sidebar, label: str):
    selected = sidebar.selectbox(label, [None, True, False], format_func=lambda value: "Todos" if value is None else "Sí" if value else "No")
    return selected


def _save_review_changes(
    papers: list[dict],
    filtered_papers: list[dict],
    edited_frame: pd.DataFrame,
    csv_path: Path,
) -> None:
    """Persist edited review flags while retaining every unfiltered paper."""
    changed = False
    for row_index, paper in enumerate(filtered_papers):
        edited_value = bool(edited_frame.iloc[row_index]["revisado"])
        if paper.get("revisado") != edited_value:
            paper["revisado"] = edited_value
            changed = True

    if changed:
        save_pool(papers, csv_path)


if __name__ == "__main__":
    run_app()
