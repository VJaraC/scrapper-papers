from pathlib import Path

import pandas as pd

from src.storage.csv_store import (
    CSV_COLUMNS,
    export_papers_to_excel,
    export_to_excel,
    load_pool,
    save_pool,
    upsert_papers,
)


def make_paper(**overrides):
    paper = {
        "title": "Paper title",
        "authors": ["Ada Lovelace"],
        "year": 2024,
        "venue": "Example Journal",
        "venue_type": "journal",
        "doi": "10.1234/example",
        "abstract": "An abstract with, commas, quotes \"and\nline breaks.",
        "source": "semantic_scholar",
        "is_preprint": False,
        "revisado": False,
        "mas": True,
        "scheduling": True,
        "llm": False,
        "mineria": False,
        "categoria": "MAS-SCHEDULING",
        "relevance_score": 2,
        "decision": "pendiente",
        "justification": "Controlled justification",
    }
    paper.update(overrides)
    return paper


def test_load_pool_returns_empty_list_when_file_does_not_exist(tmp_path):
    assert load_pool(tmp_path / "missing.csv") == []


def test_authors_round_trip_as_list_with_semicolon_separator(tmp_path):
    csv_path = tmp_path / "pool.csv"
    paper = make_paper(authors=["Ada Lovelace", "Alan Turing"])

    save_pool([paper], csv_path)

    assert pd.read_csv(csv_path).loc[0, "authors"] == "Ada Lovelace; Alan Turing"
    assert load_pool(csv_path)[0]["authors"] == ["Ada Lovelace", "Alan Turing"]


def test_save_pool_overwrites_complete_csv_without_merge(tmp_path):
    csv_path = tmp_path / "pool.csv"
    save_pool([make_paper(title="First")], csv_path)

    save_pool([make_paper(title="Replacement")], csv_path)

    loaded = load_pool(csv_path)
    assert [paper["title"] for paper in loaded] == ["Replacement"]


def test_export_papers_to_excel_exports_in_memory_list(tmp_path):
    xlsx_path = tmp_path / "filtered.xlsx"

    export_papers_to_excel([make_paper(title="Filtered")], xlsx_path)

    exported = pd.read_excel(xlsx_path, engine="openpyxl")
    assert list(exported.columns) == CSV_COLUMNS
    assert exported.loc[0, "title"] == "Filtered"
    assert exported.loc[0, "authors"] == "Ada Lovelace"


def test_upsert_papers_writes_complete_schema_and_defaults_revisado_false(tmp_path):
    csv_path = tmp_path / "pool.csv"

    paper = make_paper(revisado=True)
    counts = upsert_papers([paper], csv_path)

    loaded = load_pool(csv_path)
    assert counts == {"nuevos": 1, "actualizados": 0, "protegidos": 0}
    assert list(pd.read_csv(csv_path).columns) == CSV_COLUMNS
    assert loaded[0]["revisado"] is False, "Storage must not create reviewed rows."
    assert loaded[0]["title"] == paper["title"]
    assert loaded[0]["doi"] == paper["doi"]


def test_upsert_updates_existing_unreviewed_paper_regardless_of_decision(tmp_path):
    csv_path = tmp_path / "pool.csv"
    first_counts = upsert_papers(
        [make_paper(decision="incluido", title="Old title")], csv_path
    )

    second_counts = upsert_papers(
        [make_paper(title="Recalculated title", decision="excluido", relevance_score=0)],
        csv_path,
    )

    loaded = load_pool(csv_path)
    assert first_counts == {"nuevos": 1, "actualizados": 0, "protegidos": 0}
    assert second_counts == {"nuevos": 0, "actualizados": 1, "protegidos": 0}
    assert len(loaded) == 1
    assert loaded[0]["title"] == "Recalculated title"
    assert loaded[0]["decision"] == "excluido"
    assert loaded[0]["relevance_score"] == 0
    assert loaded[0]["revisado"] is False


def test_upsert_preserves_existing_reviewed_row_without_modification(tmp_path):
    csv_path = tmp_path / "pool.csv"
    original = make_paper(
        title="Human-reviewed title",
        decision="excluido",
        revisado=False,
    )
    upsert_papers([original], csv_path)
    frame = pd.read_csv(csv_path)
    frame.loc[0, "revisado"] = True
    frame.to_csv(csv_path, index=False)

    counts = upsert_papers(
        [make_paper(title="Automated replacement", decision="incluido", revisado=False)],
        csv_path,
    )

    loaded = load_pool(csv_path)
    assert counts == {"nuevos": 0, "actualizados": 0, "protegidos": 1}
    assert loaded[0]["title"] == "Human-reviewed title"
    assert loaded[0]["decision"] == "excluido"
    assert loaded[0]["revisado"] is True


def test_load_pool_treats_missing_or_empty_revisado_as_false(tmp_path):
    csv_path = tmp_path / "pool.csv"
    pd.DataFrame(
        [{"doi": "10.1234/missing"}, {"doi": "10.1234/empty", "revisado": ""}]
    ).to_csv(csv_path, index=False)

    loaded = load_pool(csv_path)

    assert [paper["revisado"] for paper in loaded] == [False, False]


def test_upsert_matches_doi_case_insensitively(tmp_path):
    csv_path = tmp_path / "pool.csv"
    upsert_papers([make_paper(doi="10.1234/EXAMPLE", title="Old")], csv_path)

    upsert_papers([make_paper(doi="10.1234/example", title="Updated")], csv_path)

    loaded = load_pool(csv_path)
    assert len(loaded) == 1
    assert loaded[0]["title"] == "Updated"
    assert loaded[0]["doi"] == "10.1234/example"


def test_upsert_treats_papers_without_doi_as_new_even_when_titles_match(tmp_path):
    csv_path = tmp_path / "pool.csv"
    upsert_papers([make_paper(doi="", title="Same title")], csv_path)
    upsert_papers([make_paper(doi=None, title="Same title")], csv_path)

    loaded = load_pool(csv_path)
    assert len(loaded) == 2
    assert all(paper["title"] == "Same title" for paper in loaded)


def test_export_to_excel_preserves_csv_rows_and_columns(tmp_path):
    csv_path = tmp_path / "pool.csv"
    xlsx_path = tmp_path / "pool.xlsx"
    upsert_papers([make_paper()], csv_path)

    export_to_excel(csv_path, xlsx_path)

    exported = pd.read_excel(xlsx_path, engine="openpyxl")
    assert list(exported.columns) == CSV_COLUMNS
    assert exported.loc[0, "title"] == "Paper title"
    assert exported.loc[0, "abstract"] == "An abstract with, commas, quotes \"and\nline breaks."
