import pandas as pd

from src.ui.app import filter_papers


FILTERS_WITHOUT_RESTRICTIONS = {
    "year_min": None,
    "year_max": None,
    "source": None,
    "llm": None,
    "mineria": None,
    "categoria": None,
    "venue_type": None,
}


PAPERS = [
    {
        "title": "Journal LLM mining",
        "year": 2024,
        "source": "semantic_scholar",
        "llm": True,
        "mineria": True,
        "categoria": "MAS-DESPACHO-MINERO-LLM",
        "venue_type": "journal",
    },
    {
        "title": "Conference scheduling",
        "year": 2022,
        "source": "scopus",
        "llm": False,
        "mineria": False,
        "categoria": "MAS-SCHEDULING",
        "venue_type": "conference",
    },
    {
        "title": "Missing year",
        "year": None,
        "source": "crossref",
        "llm": None,
        "mineria": None,
        "categoria": "NO_CLASIFICABLE",
        "venue_type": None,
    },
]


def test_filter_papers_with_all_none_returns_every_paper():
    assert filter_papers(PAPERS, FILTERS_WITHOUT_RESTRICTIONS) == PAPERS


def test_filter_papers_applies_inclusive_year_range():
    filters = {**FILTERS_WITHOUT_RESTRICTIONS, "year_min": 2022, "year_max": 2024}

    result = filter_papers(PAPERS, filters)

    assert [paper["title"] for paper in result] == [
        "Journal LLM mining",
        "Conference scheduling",
    ]


def test_filter_papers_applies_source_and_boolean_filters():
    filters = {
        **FILTERS_WITHOUT_RESTRICTIONS,
        "source": "semantic_scholar",
        "llm": True,
        "mineria": True,
    }

    result = filter_papers(PAPERS, filters)

    assert [paper["title"] for paper in result] == ["Journal LLM mining"]


def test_filter_papers_applies_category_and_venue_filters():
    filters = {
        **FILTERS_WITHOUT_RESTRICTIONS,
        "categoria": "MAS-SCHEDULING",
        "venue_type": "conference",
    }

    result = filter_papers(PAPERS, filters)

    assert [paper["title"] for paper in result] == ["Conference scheduling"]


def test_filter_papers_excludes_missing_year_when_year_filter_is_active():
    filters = {**FILTERS_WITHOUT_RESTRICTIONS, "year_min": 2021}

    result = filter_papers(PAPERS, filters)

    assert "Missing year" not in [paper["title"] for paper in result]


def test_filter_papers_does_not_mutate_input():
    original = [paper.copy() for paper in PAPERS]

    filter_papers(PAPERS, {**FILTERS_WITHOUT_RESTRICTIONS, "source": "scopus"})

    assert PAPERS == original
