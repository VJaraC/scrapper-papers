from unittest.mock import patch

from src.collectors.errors import CollectorError
from src.pipeline import run_search


def make_paper(doi, title, abstract=None, venue_type=None):
    return {
        "title": title,
        "abstract": abstract,
        "doi": doi,
        "venue": None,
        "venue_type": venue_type,
        "year": 2024,
        "is_preprint": False,
    }


CLASSIFICATION = {
    "mas": True,
    "scheduling": True,
    "llm": False,
    "mineria": False,
    "categoria": "MAS-SCHEDULING",
}
DECISION = {
    "relevance_score": 2,
    "decision": "incluido",
    "justification": "Controlled decision",
}
COUNTS = {"nuevos": 2, "actualizados": 0, "protegidos": 0}


def test_run_search_returns_source_enrichment_and_upsert_results(tmp_path):
    semantic = make_paper("10.1234/example", "Semantic", None)
    scopus_duplicate = make_paper("10.1234/EXAMPLE", "Scopus", "Useful abstract")
    scopus_without_doi = make_paper(None, "No DOI", "Independent abstract", "journal")

    with patch("src.pipeline.semantic_scholar.collect_papers", return_value=[semantic]):
        with patch(
            "src.pipeline.scopus.collect_papers",
            return_value=[scopus_duplicate, scopus_without_doi],
        ):
            with patch("src.pipeline.wos.collect_papers", return_value=[]):
                with patch(
                    "src.pipeline.crossref.enrich_paper",
                    return_value={"venue": "Enriched Journal", "venue_type": "journal"},
                ) as enrich:
                    with patch("src.pipeline.classify_paper", return_value=CLASSIFICATION):
                        with patch("src.pipeline.decide_paper", return_value=DECISION):
                            with patch("src.pipeline.upsert_papers", return_value=COUNTS) as upsert:
                                result = run_search(
                                    "scheduling", 2022, 2025, 7, tmp_path / "papers.csv"
                                )

    assert result == {
        "sources": {
            "semantic_scholar": {"success": True, "count": 1, "error": None},
            "scopus": {"success": True, "count": 2, "error": None},
            "wos": {"success": True, "count": 0, "error": None},
        },
        "enrichment": {"crossref": {"attempted": 1, "succeeded": 1, "failed": 0}},
        "upsert": COUNTS,
    }, "Pipeline should return the complete public result schema."
    enrich.assert_called_once_with("10.1234/EXAMPLE")
    persisted = upsert.call_args.args[0]
    assert [paper["title"] for paper in persisted] == ["Scopus", "No DOI"]
    assert persisted[0]["venue"] == "Enriched Journal"


def test_run_search_treats_empty_sources_as_success(tmp_path):
    counts = {"nuevos": 0, "actualizados": 0, "protegidos": 0}

    with patch("src.pipeline.semantic_scholar.collect_papers", return_value=[]):
        with patch("src.pipeline.scopus.collect_papers", return_value=[]):
            with patch("src.pipeline.wos.collect_papers", return_value=[]):
                with patch("src.pipeline.upsert_papers", return_value=counts):
                    result = run_search("no results", csv_path=tmp_path / "papers.csv")

    assert result["sources"]["semantic_scholar"] == {
        "success": True,
        "count": 0,
        "error": None,
    }
    assert result["sources"]["scopus"] == {
        "success": True,
        "count": 0,
        "error": None,
    }
    assert result["sources"]["wos"] == {
        "success": True,
        "count": 0,
        "error": None,
    }
    assert result["enrichment"]["crossref"] == {
        "attempted": 0,
        "succeeded": 0,
        "failed": 0,
    }


def test_run_search_continues_after_one_source_fails(tmp_path):
    surviving_paper = make_paper("10.1234/survivor", "Survivor", "Abstract", "journal")
    counts = {"nuevos": 1, "actualizados": 0, "protegidos": 0}

    with patch(
        "src.pipeline.semantic_scholar.collect_papers",
        side_effect=CollectorError("semantic unavailable"),
    ):
        with patch("src.pipeline.scopus.collect_papers", return_value=[surviving_paper]):
            with patch(
                "src.pipeline.wos.collect_papers",
                side_effect=CollectorError("wos unavailable"),
            ):
                with patch("src.pipeline.classify_paper", return_value=CLASSIFICATION):
                    with patch("src.pipeline.upsert_papers", return_value=counts):
                        result = run_search("scheduling", csv_path=tmp_path / "papers.csv")

    assert result["sources"]["semantic_scholar"] == {
        "success": False,
        "count": 0,
        "error": "semantic unavailable",
    }
    assert result["sources"]["scopus"] == {
        "success": True,
        "count": 1,
        "error": None,
    }
    assert result["sources"]["wos"] == {
        "success": False,
        "count": 0,
        "error": "wos unavailable",
    }


def test_run_search_collects_wos_results(tmp_path):
    wos_paper = make_paper("10.1234/wos", "WOS paper", "Abstract", "journal")
    counts = {"nuevos": 1, "actualizados": 0, "protegidos": 0}

    with patch("src.pipeline.semantic_scholar.collect_papers", return_value=[]):
        with patch("src.pipeline.scopus.collect_papers", return_value=[]):
            with patch("src.pipeline.wos.collect_papers", return_value=[wos_paper]) as wos_collect:
                with patch("src.pipeline.classify_paper", return_value=CLASSIFICATION):
                    with patch("src.pipeline.upsert_papers", return_value=counts) as upsert:
                        result = run_search(
                            "scheduling", 2022, 2025, 7, tmp_path / "papers.csv"
                        )

    wos_collect.assert_called_once_with(
        "scheduling", year_from=2022, year_to=2025, limit=7
    )
    assert result["sources"]["wos"] == {
        "success": True,
        "count": 1,
        "error": None,
    }
    assert upsert.call_args.args[0][0]["title"] == "WOS paper"


def test_run_search_counts_crossref_404_as_attempt_without_failure(tmp_path):
    paper = make_paper("10.1234/missing", "Missing DOI")
    counts = {"nuevos": 1, "actualizados": 0, "protegidos": 0}

    with patch("src.pipeline.semantic_scholar.collect_papers", return_value=[paper]):
        with patch("src.pipeline.scopus.collect_papers", return_value=[]):
            with patch("src.pipeline.wos.collect_papers", return_value=[]):
                with patch("src.pipeline.crossref.enrich_paper", return_value=None):
                    with patch("src.pipeline.classify_paper", return_value=CLASSIFICATION):
                        with patch("src.pipeline.upsert_papers", return_value=counts):
                            result = run_search("scheduling", csv_path=tmp_path / "papers.csv")

    assert result["enrichment"]["crossref"] == {
        "attempted": 1,
        "succeeded": 0,
        "failed": 0,
    }


def test_run_search_counts_crossref_collector_error_as_failure(tmp_path):
    paper = make_paper("10.1234/failing", "Failing DOI")
    counts = {"nuevos": 1, "actualizados": 0, "protegidos": 0}

    with patch("src.pipeline.semantic_scholar.collect_papers", return_value=[paper]):
        with patch("src.pipeline.scopus.collect_papers", return_value=[]):
            with patch("src.pipeline.wos.collect_papers", return_value=[]):
                with patch(
                    "src.pipeline.crossref.enrich_paper",
                    side_effect=CollectorError("crossref unavailable"),
                ):
                    with patch("src.pipeline.classify_paper", return_value=CLASSIFICATION):
                        with patch("src.pipeline.upsert_papers", return_value=counts):
                            result = run_search("scheduling", csv_path=tmp_path / "papers.csv")

    assert result["enrichment"]["crossref"] == {
        "attempted": 1,
        "succeeded": 0,
        "failed": 1,
    }
