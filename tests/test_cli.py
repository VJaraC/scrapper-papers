from unittest.mock import patch

from src.cli import DEFAULT_CSV_PATH, build_parser, buscar


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


def test_buscar_delegates_to_shared_pipeline_and_returns_full_result(tmp_path, capsys):
    result = {
        "sources": {
            "semantic_scholar": {"success": True, "count": 2, "error": None},
            "scopus": {"success": True, "count": 1, "error": None},
        },
        "enrichment": {"crossref": {"attempted": 1, "succeeded": 1, "failed": 0}},
        "upsert": {"nuevos": 2, "actualizados": 0, "protegidos": 0},
    }

    with patch("src.cli.run_search", return_value=result) as run_search:
        returned = buscar(
            "scheduling",
            year_from=2022,
            year_to=2025,
            limit=7,
            csv_path=tmp_path / "papers.csv",
        )

    assert returned == result, "CLI should expose the complete pipeline result."
    run_search.assert_called_once_with(
        "scheduling", 2022, 2025, 7, tmp_path / "papers.csv"
    )
    assert "nuevos=2" in capsys.readouterr().out
