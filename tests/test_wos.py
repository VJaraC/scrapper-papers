from unittest.mock import MagicMock, patch

import pytest
import requests

from src.collectors.errors import CollectorError
from src.collectors.wos import SEARCH_URL, collect_papers


def make_response(payload):
    response = MagicMock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def hit(title="WOS paper", types=None):
    return {
        "title": title,
        "names": {"authors": [{"displayName": "Ada Lovelace"}]},
        "source": {"publishYear": 2024, "sourceTitle": "Example Journal"},
        "identifiers": {"doi": "10.1234/example"},
        "types": ["Article"] if types is None else types,
    }


def test_collect_papers_builds_wos_query_and_normalizes_response():
    response = make_response({"metadata": {"total": 1}, "hits": [hit()]})

    with patch.dict("os.environ", {"WOS_API_KEY": "test-wos-key"}):
        with patch("src.collectors.wos.requests.get", return_value=response) as get:
            papers = collect_papers(
                "multi-agent system", year_from=2021, year_to=2026, limit=20
            )

    assert papers == [
        {
            "title": "WOS paper",
            "authors": ["Ada Lovelace"],
            "year": 2024,
            "venue": "Example Journal",
            "venue_type": "journal",
            "doi": "10.1234/example",
            "abstract": None,
            "source": "wos",
            "is_preprint": False,
            "llm": None,
            "revisado": False,
            "mineria": None,
            "categoria": None,
            "relevance_score": None,
            "decision": None,
            "justification": None,
        }
    ]
    get.assert_called_once_with(
        SEARCH_URL,
        params={
            "db": "WOS",
            "q": "TS=(multi-agent AND system)",
            "limit": 20,
            "page": 1,
            "publishTimeSpan": "2021-01-01+2026-12-31",
        },
        headers={"X-ApiKey": "test-wos-key"},
    )


def test_collect_papers_omits_year_span_when_range_is_incomplete():
    response = make_response({"metadata": {"total": 0}, "hits": []})

    with patch.dict("os.environ", {"WOS_API_KEY": "test-wos-key"}):
        with patch("src.collectors.wos.requests.get", return_value=response) as get:
            papers = collect_papers("scheduling", year_from=2021)

    assert papers == []
    assert "publishTimeSpan" not in get.call_args.kwargs["params"]


def test_collect_papers_paginates_in_pages_of_fifty_until_limit():
    first_page = {"metadata": {"total": 120}, "hits": [hit(f"Paper {i}") for i in range(50)]}
    second_page = {"metadata": {"total": 120}, "hits": [hit(f"Paper {i}") for i in range(50, 100)]}
    third_page = {"metadata": {"total": 120}, "hits": [hit(f"Paper {i}") for i in range(100, 120)]}

    requested_pages = []

    def request_side_effect(url, params, headers):
        requested_pages.append(params["page"])
        return [
            make_response(first_page),
            make_response(second_page),
            make_response(third_page),
        ][params["page"] - 1]

    with patch.dict("os.environ", {"WOS_API_KEY": "test-wos-key"}):
        with patch(
            "src.collectors.wos.requests.get",
            side_effect=request_side_effect,
        ) as get:
            papers = collect_papers("scheduling", limit=120)

    assert len(papers) == 120
    assert requested_pages == [1, 2, 3]
    assert all(call.kwargs["params"]["limit"] == 50 for call in get.call_args_list)


def test_collect_papers_stops_at_total_when_total_is_below_requested_limit():
    response = make_response({"metadata": {"total": 1}, "hits": [hit()]})

    with patch.dict("os.environ", {"WOS_API_KEY": "test-wos-key"}):
        with patch("src.collectors.wos.requests.get", return_value=response) as get:
            papers = collect_papers("scheduling", limit=50)

    assert len(papers) == 1
    get.assert_called_once()


def test_collect_papers_handles_missing_optional_fields():
    response = make_response(
        {
            "metadata": {"total": 1},
            "hits": [{"title": "Incomplete paper"}],
        }
    )

    with patch.dict("os.environ", {"WOS_API_KEY": "test-wos-key"}):
        with patch("src.collectors.wos.requests.get", return_value=response):
            papers = collect_papers("scheduling")

    assert papers[0]["title"] == "Incomplete paper"
    assert papers[0]["authors"] == []
    assert papers[0]["year"] is None
    assert papers[0]["venue"] is None
    assert papers[0]["doi"] is None
    assert papers[0]["venue_type"] is None
    assert papers[0]["abstract"] is None


@pytest.mark.parametrize("types, expected", [(["Article"], "journal"), (["Proceedings Paper"], None), ([], None)])
def test_collect_papers_maps_only_article_type(types, expected):
    response = make_response({"metadata": {"total": 1}, "hits": [hit(types=types)]})

    with patch.dict("os.environ", {"WOS_API_KEY": "test-wos-key"}):
        with patch("src.collectors.wos.requests.get", return_value=response):
            papers = collect_papers("scheduling")

    assert papers[0]["venue_type"] == expected


def test_collect_papers_rejects_limit_above_zero_without_api_key():
    with patch.dict("os.environ", {}, clear=True):
        with patch("src.collectors.wos.requests.get") as get:
            with pytest.raises(CollectorError, match="WOS_API_KEY environment variable is missing"):
                collect_papers("scheduling")

    get.assert_not_called()


def test_collect_papers_raises_collector_error_for_request_failure(caplog):
    request_error = requests.HTTPError("controlled WOS failure")

    with patch.dict("os.environ", {"WOS_API_KEY": "test-wos-key"}):
        with patch("src.collectors.wos.requests.get", side_effect=request_error):
            with caplog.at_level("ERROR"):
                with pytest.raises(CollectorError, match="controlled WOS failure"):
                    collect_papers("scheduling")

    assert "Web of Science request failed" in caplog.text


def test_collect_papers_returns_empty_for_empty_response():
    response = make_response({"metadata": {"total": 0}, "hits": []})

    with patch.dict("os.environ", {"WOS_API_KEY": "test-wos-key"}):
        with patch("src.collectors.wos.requests.get", return_value=response):
            papers = collect_papers("query with no results")

    assert papers == []
