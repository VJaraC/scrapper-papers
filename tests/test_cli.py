from unittest.mock import patch

from src.cli import (
    DEFAULT_CSV_PATH,
    _deduplicate_by_doi,
    build_parser,
    buscar,
)


def paper(doi, title, abstract=None, venue_type="journal"):
    return {
        "title": title,
        "abstract": abstract,
        "doi": doi,
        "venue": None,
        "venue_type": venue_type,
        "year": 2024,
        "is_preprint": False,
        "revisado": False,
    }


def test_deduplicate_prefers_abstract_over_none_empty_and_whitespace():
    cases = [None, "", "   "]
    for missing_abstract in cases:
        result = _deduplicate_by_doi(
            [
                paper("10.1234/example", "Without abstract", missing_abstract),
                paper("10.1234/EXAMPLE", "With abstract", "Useful abstract"),
            ]
        )

        assert [item["title"] for item in result] == ["With abstract"]


def test_deduplicate_keeps_first_when_both_have_or_lack_abstract():
    for first_abstract, second_abstract in [("First abstract", "Second abstract"), (None, " ")]:
        result = _deduplicate_by_doi(
            [
                paper("10.1234/example", "First", first_abstract),
                paper("10.1234/EXAMPLE", "Second", second_abstract),
            ]
        )

        assert [item["title"] for item in result] == ["First"]


def test_deduplicate_keeps_all_papers_without_doi():
    result = _deduplicate_by_doi(
        [paper(None, "First"), paper("", "Second"), paper(None, "Third")]
    )

    assert [item["title"] for item in result] == ["First", "Second", "Third"]


def test_build_parser_uses_required_defaults():
    args = build_parser().parse_args(["buscar", "scheduling"])

    assert args.year_from == 2021
    assert args.year_to == 2026
    assert args.limit == 20
    assert args.csv_path == str(DEFAULT_CSV_PATH)


def test_build_parser_accepts_overrides():
    args = build_parser().parse_args(
        [
            "buscar",
            "multi-agent scheduling",
            "--year-from",
            "2022",
            "--year-to",
            "2025",
            "--limit",
            "7",
            "--csv-path",
            "custom/papers.csv",
        ]
    )

    assert (args.year_from, args.year_to, args.limit) == (2022, 2025, 7)
    assert args.csv_path == "custom/papers.csv"


def test_buscar_runs_pipeline_deduplicates_enriches_and_persists(tmp_path, capsys):
    semantic_paper = paper("10.1234/example", "Semantic", None, None)
    scopus_duplicate = paper("10.1234/EXAMPLE", "Scopus", "Scopus abstract", None)
    scopus_without_doi = paper(None, "No DOI", "Independent abstract")
    counts = {"nuevos": 2, "actualizados": 0, "protegidos": 0}

    with patch(
        "src.cli.semantic_scholar.collect_papers", return_value=[semantic_paper]
    ) as semantic_collect:
        with patch(
            "src.cli.scopus.collect_papers", return_value=[scopus_duplicate, scopus_without_doi]
        ) as scopus_collect:
            with patch(
                "src.cli.crossref.enrich_paper",
                return_value={"venue": "Enriched Journal", "venue_type": "journal"},
            ) as enrich:
                with patch("src.cli.classify_paper", return_value={
                    "mas": True,
                    "scheduling": False,
                    "llm": False,
                    "mineria": False,
                    "categoria": "MAS-SCHEDULING",
                }) as classify:
                    with patch("src.cli.decide_paper", return_value={
                        "relevance_score": 1,
                        "decision": "incluido",
                        "justification": "Controlled decision",
                    }) as decide:
                        with patch("src.cli.upsert_papers", return_value=counts) as upsert:
                            result = buscar(
                                "scheduling",
                                year_from=2022,
                                year_to=2025,
                                limit=7,
                                csv_path=tmp_path / "papers.csv",
                            )

    assert result == counts
    semantic_collect.assert_called_once_with(
        "scheduling", year_from=2022, year_to=2025, limit=7
    )
    scopus_collect.assert_called_once_with(
        "scheduling", year_from=2022, year_to=2025, limit=7
    )
    enrich.assert_called_once_with("10.1234/EXAMPLE")
    assert classify.call_count == 2
    assert decide.call_count == 2
    upsert.assert_called_once()
    persisted = upsert.call_args.args[0]
    assert [item["title"] for item in persisted] == ["Scopus", "No DOI"]
    assert persisted[0]["venue"] == "Enriched Journal"
    assert "nuevos=2" in capsys.readouterr().out


def test_buscar_continues_when_one_collector_fails(tmp_path, caplog):
    surviving_paper = paper("10.1234/survivor", "Survivor", "Abstract")
    counts = {"nuevos": 1, "actualizados": 0, "protegidos": 0}

    with patch(
        "src.cli.semantic_scholar.collect_papers",
        side_effect=RuntimeError("controlled failure"),
    ):
        with patch("src.cli.scopus.collect_papers", return_value=[surviving_paper]):
            with patch("src.cli.classify_paper", return_value={
                "mas": True,
                "scheduling": False,
                "llm": False,
                "mineria": False,
                "categoria": "MAS-SCHEDULING",
            }):
                with patch("src.cli.decide_paper", return_value={
                    "relevance_score": 1,
                    "decision": "incluido",
                    "justification": "Controlled decision",
                }):
                    with patch("src.cli.upsert_papers", return_value=counts) as upsert:
                        result = buscar("scheduling", csv_path=tmp_path / "papers.csv")

    assert result == counts
    assert "Collector semantic_scholar failed" in caplog.text
    assert upsert.call_args.args[0][0]["title"] == "Survivor"


def test_crossref_failure_keeps_original_paper_and_persists_it(tmp_path, caplog):
    original = paper("10.1234/example", "Original", "Abstract", None)
    counts = {"nuevos": 1, "actualizados": 0, "protegidos": 0}

    with patch("src.cli.semantic_scholar.collect_papers", return_value=[original]):
        with patch("src.cli.scopus.collect_papers", return_value=[]):
            with patch(
                "src.cli.crossref.enrich_paper",
                side_effect=RuntimeError("crossref unavailable"),
            ):
                with patch("src.cli.classify_paper", return_value={
                    "mas": True,
                    "scheduling": False,
                    "llm": False,
                    "mineria": False,
                    "categoria": "MAS-SCHEDULING",
                }):
                    with patch("src.cli.decide_paper", return_value={
                        "relevance_score": 1,
                        "decision": "incluido",
                        "justification": "Controlled decision",
                    }):
                        with patch("src.cli.upsert_papers", return_value=counts) as upsert:
                            buscar("scheduling", csv_path=tmp_path / "papers.csv")

    persisted = upsert.call_args.args[0][0]
    assert persisted["venue"] is None
    assert persisted["title"] == "Original"
    assert "crossref enrichment failed" in caplog.text
