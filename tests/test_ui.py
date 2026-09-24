from unittest.mock import MagicMock, patch

import pandas as pd

from src.ui.app import _build_filters, build_result_messages, filter_papers, run_app


def test_build_result_messages_reports_successful_sources_and_crossref():
    result = {
        "sources": {
            "semantic_scholar": {"success": True, "count": 12, "error": None},
            "scopus": {"success": True, "count": 3, "error": None},
            "wos": {"success": True, "count": 4, "error": None},
        },
        "enrichment": {"crossref": {"attempted": 2, "succeeded": 2, "failed": 0}},
        "upsert": {"nuevos": 4, "actualizados": 1, "protegidos": 0},
    }

    assert build_result_messages(result) == [
        ("success", "Semantic Scholar: 12 papers"),
        ("success", "Scopus: 3 papers"),
        ("success", "Web of Science: 4 papers"),
        ("success", "CrossRef: 2 enriquecimientos"),
    ]


def test_build_result_messages_reports_source_failure_and_crossref_failure():
    result = {
        "sources": {
            "semantic_scholar": {
                "success": False,
                "count": 0,
                "error": "timeout",
            },
            "scopus": {"success": True, "count": 0, "error": None},
            "wos": {"success": False, "count": 0, "error": "wos timeout"},
        },
        "enrichment": {"crossref": {"attempted": 2, "succeeded": 0, "failed": 2}},
        "upsert": {"nuevos": 0, "actualizados": 0, "protegidos": 0},
    }

    assert build_result_messages(result) == [
        ("error", "Semantic Scholar: falló — timeout"),
        ("success", "Scopus: 0 papers"),
        ("error", "Web of Science: falló — wos timeout"),
        ("error", "CrossRef: fallaron 2 enriquecimientos"),
    ]


def test_build_result_messages_warns_for_crossref_404_attempts():
    result = {
        "sources": {},
        "enrichment": {"crossref": {"attempted": 3, "succeeded": 1, "failed": 0}},
        "upsert": {"nuevos": 0, "actualizados": 0, "protegidos": 0},
    }

    assert build_result_messages(result) == [
        ("warning", "CrossRef: 1 de 3 enriquecimientos completados"),
    ]


def test_build_filters_expands_slider_range_for_single_year():
    class SidebarStub:
        def __init__(self):
            self.slider_args = None

        def slider(self, *args):
            self.slider_args = args
            return args[3]

    sidebar = SidebarStub()
    frame = pd.DataFrame(
        {
            "year": [2024, 2024],
            "source": ["scopus", "scopus"],
            "llm": [False, False],
            "mineria": [False, False],
            "categoria": ["MAS-SCHEDULING", "MAS-SCHEDULING"],
            "venue_type": ["journal", "journal"],
            "decision": ["incluido", "incluido"],
        }
    )

    with patch("src.ui.app._select_filter", return_value=None):
        with patch("src.ui.app._select_boolean", return_value=None):
            filters = _build_filters(sidebar, frame)

    assert sidebar.slider_args == ("Año", 2023, 2025, (2024, 2024))
    assert filters["year_min"] == 2024
    assert filters["year_max"] == 2024


def test_filter_papers_by_decision_returns_only_matching_papers():
    papers = [
        {"title": "Included paper", "decision": "incluido"},
        {"title": "Excluded paper", "decision": "excluido"},
        {"title": "Pending paper", "decision": "pendiente"},
    ]

    filtered = filter_papers(papers, {"decision": "incluido"})

    assert filtered == [{"title": "Included paper", "decision": "incluido"}]


def test_run_app_skips_filters_and_table_when_pool_is_empty():
    streamlit = MagicMock()
    streamlit.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
    streamlit.button.return_value = False

    with patch("src.ui.app.st", streamlit):
        with patch("src.ui.app.load_pool", return_value=[]):
            with patch("src.ui.app._build_filters") as build_filters:
                run_app("empty.csv")

    streamlit.info.assert_called_once_with("No hay papers en el pool.")
    build_filters.assert_not_called()
    streamlit.data_editor.assert_not_called()
