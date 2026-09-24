import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.collectors.crossref import CROSSREF_WORKS_URL, enrich_paper
from src.collectors.errors import CollectorError
from src.collectors.scopus import SEARCH_URL as SCOPUS_SEARCH_URL
from src.collectors.scopus import collect_papers as scopus_collect_papers
from src.collectors.semantic_scholar import SEARCH_URL, collect_papers


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "semantic_scholar_response.json"
SCOPUS_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "scopus_response.json"


def load_fixture():
    with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def load_scopus_fixture():
    with SCOPUS_FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def make_response(payload):
    response = MagicMock()
    response.json.return_value = payload
    return response


def test_collect_papers_normalizes_complete_response_and_request_options():
    response = make_response(load_fixture())
    response.raise_for_status.return_value = None

    with patch.dict("os.environ", {}, clear=True):
        with patch("src.collectors.semantic_scholar.requests.get", return_value=response) as get:
            papers = collect_papers(
                "multi-agent scheduling",
                year_from=2021,
                year_to=2026,
                limit=10,
            )

    assert papers == [
        {
            "title": "Multi-agent scheduling with language models",
            "authors": ["Ada Lovelace", "Alan Turing"],
            "year": 2024,
            "venue": "Example Journal",
            "venue_type": "journal",
            "doi": "10.1234/example",
            "abstract": "A controlled fixture abstract.",
            "source": "semantic_scholar",
            "is_preprint": False,
            "revisado": False,
            "llm": None,
            "mineria": None,
            "categoria": None,
            "relevance_score": None,
            "decision": None,
            "justification": None,
        }
    ], "The complete response should be normalized to project metadata."

    get.assert_called_once_with(
        SEARCH_URL,
        params={
            "query": "multi-agent scheduling",
            "limit": 10,
            "fields": (
                "title,abstract,year,venue,publicationVenue,journal,authors,"
                "externalIds,publicationTypes"
            ),
            "publicationTypes": "JournalArticle",
            "year": "2021-2026",
        },
        headers={},
    )


def test_collect_papers_omits_api_key_header_when_key_is_absent():
    response = make_response({"data": []})
    response.raise_for_status.return_value = None

    with patch.dict("os.environ", {}, clear=True):
        with patch("src.collectors.semantic_scholar.requests.get", return_value=response) as get:
            collect_papers("scheduling")

    assert get.call_args.kwargs["headers"] == {}, "No header should be added without an API key."


def test_collect_papers_adds_api_key_header_when_key_is_configured():
    response = make_response({"data": []})
    response.raise_for_status.return_value = None

    with patch.dict("os.environ", {"SEMANTIC_SCHOLAR_API_KEY": "test-key"}):
        with patch("src.collectors.semantic_scholar.requests.get", return_value=response) as get:
            collect_papers("scheduling")

    assert get.call_args.kwargs["headers"] == {"x-api-key": "test-key"}, (
        "The configured API key should be sent as an optional request header."
    )


def test_collect_papers_normalizes_missing_fields_without_failing():
    response = make_response(
        {
            "data": [
                {
                    "title": "Paper without optional metadata",
                    "authors": [{}],
                    "publicationTypes": ["UnknownType"],
                }
            ]
        }
    )
    response.raise_for_status.return_value = None

    with patch("src.collectors.semantic_scholar.requests.get", return_value=response):
        papers = collect_papers("scheduling")

    assert papers[0]["title"] == "Paper without optional metadata"
    assert papers[0]["authors"] == [None], "Missing author names should remain explicit."
    assert papers[0]["year"] is None
    assert papers[0]["doi"] is None
    assert papers[0]["abstract"] is None
    assert papers[0]["venue_type"] is None


def test_collect_papers_returns_empty_list_for_empty_response():
    response = make_response({"data": []})
    response.raise_for_status.return_value = None

    with patch("src.collectors.semantic_scholar.requests.get", return_value=response):
        papers = collect_papers("query with no results")

    assert papers == [], "An empty API result should produce an empty paper list."


def test_collect_papers_raises_collector_error_and_logs_request_error(caplog):
    request_error = requests.HTTPError("controlled HTTP failure")

    with patch(
        "src.collectors.semantic_scholar.requests.get",
        side_effect=request_error,
    ):
        with caplog.at_level("ERROR"):
            with pytest.raises(CollectorError, match="controlled HTTP failure"):
                collect_papers("scheduling")

    assert "Semantic Scholar request failed" in caplog.text
    assert "controlled HTTP failure" in caplog.text


def test_crossref_enrich_paper_normalizes_metadata_and_uses_direct_doi_lookup():
    response = make_response(
        {
            "message": {
                "container-title": ["Example Journal"],
                "DOI": "10.1234/example-confirmed",
                "type": "journal-article",
            }
        }
    )
    response.raise_for_status.return_value = None

    with patch("src.collectors.crossref.requests.get", return_value=response) as get:
        enrichment = enrich_paper("10.1234/example")

    assert enrichment == {
        "venue": "Example Journal",
        "venue_type": "journal",
        "doi": "10.1234/example-confirmed",
    }, "CrossRef should return only metadata used to enrich the existing paper."

    get.assert_called_once_with(
        f"{CROSSREF_WORKS_URL}/10.1234/example",
        timeout=10,
    )


def test_crossref_enrich_paper_handles_missing_enrichment_fields():
    response = make_response({"message": {"type": "unknown-type"}})
    response.raise_for_status.return_value = None

    with patch("src.collectors.crossref.requests.get", return_value=response):
        enrichment = enrich_paper("10.1234/missing-fields")

    assert enrichment == {
        "venue": None,
        "venue_type": None,
        "doi": None,
    }, "Missing CrossRef fields should remain explicit without failing."


def test_crossref_enrich_paper_returns_none_for_empty_response():
    response = make_response({})
    response.raise_for_status.return_value = None

    with patch("src.collectors.crossref.requests.get", return_value=response):
        enrichment = enrich_paper("10.1234/not-found")

    assert enrichment is None, "A response without a CrossRef paper should return None."


def test_crossref_enrich_paper_raises_collector_error_for_request_error(caplog):
    request_error = requests.HTTPError("controlled CrossRef failure")

    with patch("src.collectors.crossref.requests.get", side_effect=request_error):
        with caplog.at_level("ERROR"):
            with pytest.raises(CollectorError, match="controlled CrossRef failure"):
                enrich_paper("10.1234/failing")

    assert "CrossRef request failed" in caplog.text
    assert "controlled CrossRef failure" in caplog.text


def test_crossref_enrich_paper_returns_none_for_http_404(caplog):
    response = make_response({})
    response.raise_for_status.side_effect = requests.HTTPError("controlled HTTP 404 failure")
    response.raise_for_status.side_effect.response = response
    response.status_code = 404

    with patch("src.collectors.crossref.requests.get", return_value=response):
        with caplog.at_level("ERROR"):
            enrichment = enrich_paper("10.1234/http-404")

    assert enrichment is None, "A missing DOI should not count as a CrossRef failure."
    assert "controlled HTTP 404 failure" in caplog.text


def test_crossref_enrich_paper_raises_for_non_404_http_status(caplog):
    response = make_response({})
    response.raise_for_status.side_effect = requests.HTTPError("controlled HTTP 500 failure")
    response.raise_for_status.side_effect.response = response
    response.status_code = 500

    with patch("src.collectors.crossref.requests.get", return_value=response):
        with caplog.at_level("ERROR"):
            with pytest.raises(CollectorError, match="controlled HTTP 500 failure"):
                enrich_paper("10.1234/http-500")

    assert "CrossRef request failed" in caplog.text


def test_crossref_enrich_paper_maps_only_real_crossref_venue_types():
    journal_response = make_response(
        {"message": {"container-title": ["Journal"], "type": "journal-article", "DOI": "10/journal"}}
    )
    journal_response.raise_for_status.return_value = None
    conference_response = make_response(
        {"message": {"container-title": ["Proceedings"], "type": "proceedings-article", "DOI": "10/conference"}}
    )
    conference_response.raise_for_status.return_value = None

    with patch(
        "src.collectors.crossref.requests.get",
        side_effect=[journal_response, conference_response],
    ):
        journal = enrich_paper("10/journal")
        conference = enrich_paper("10/conference")

    assert journal["venue_type"] == "journal"
    assert conference["venue_type"] == "conference"


def test_crossref_enrich_paper_rejects_non_crossref_type_aliases():
    response = make_response(
        {"message": {"type": "article-journal", "DOI": "10/alias"}}
    )
    response.raise_for_status.return_value = None

    with patch("src.collectors.crossref.requests.get", return_value=response):
        enrichment = enrich_paper("10/alias")

    assert enrichment["venue_type"] is None, "Unsupported type aliases must not be classified."


def test_scopus_collect_papers_normalizes_standard_response_and_request_options():
    response = make_response(load_scopus_fixture())
    response.raise_for_status.return_value = None

    with patch.dict("os.environ", {"SCOPUS_API_KEY": "test-scopus-key"}):
        with patch("src.collectors.scopus.requests.get", return_value=response) as get:
            papers = scopus_collect_papers(
                "multi-agent scheduling",
                year_from=2021,
                year_to=2026,
                limit=10,
            )

    assert papers == [
        {
            "title": "Multi-agent scheduling with language models",
            "authors": ["Ada Lovelace"],
            "year": 2024,
            "venue": "Example Journal",
            "venue_type": "journal",
            "doi": "10.1234/scopus-example",
            "abstract": None,
            "source": "scopus",
            "is_preprint": False,
            "revisado": False,
            "llm": None,
            "mineria": None,
            "categoria": None,
            "relevance_score": None,
            "decision": None,
            "justification": None,
        },
        {
            "title": "Mining dispatch conference study",
            "authors": ["Alan Turing"],
            "year": 2023,
            "venue": "Example Proceedings",
            "venue_type": "conference",
            "doi": "10.1234/scopus-conference",
            "abstract": None,
            "source": "scopus",
            "is_preprint": False,
            "revisado": False,
            "llm": None,
            "mineria": None,
            "categoria": None,
            "relevance_score": None,
            "decision": None,
            "justification": None,
        },
    ], "STANDARD metadata should be normalized to the project schema."

    get.assert_called_once_with(
        SCOPUS_SEARCH_URL,
        params={
            "query": (
                "TITLE-ABS-KEY(multi-agent AND scheduling) AND PUBYEAR > 2020 "
                "AND PUBYEAR < 2027"
            ),
            "count": 10,
            "start": 0,
            "view": "STANDARD",
        },
        headers={"X-ELS-APIKey": "test-scopus-key"},
    )


def test_scopus_collect_papers_omits_year_filter_when_year_range_is_incomplete():
    response = make_response({"search-results": {"entry": []}})
    response.raise_for_status.return_value = None

    with patch.dict("os.environ", {"SCOPUS_API_KEY": "test-scopus-key"}):
        with patch("src.collectors.scopus.requests.get", return_value=response) as get:
            papers = scopus_collect_papers("scheduling", year_from=2021)

    assert papers == [], "An incomplete year range should not add a partial filter."
    assert get.call_args.kwargs["params"]["query"] == "TITLE-ABS-KEY(scheduling)"


def test_scopus_collect_papers_joins_query_terms_with_explicit_and():
    response = make_response({"search-results": {"entry": []}})
    response.raise_for_status.return_value = None

    with patch.dict("os.environ", {"SCOPUS_API_KEY": "test-scopus-key"}):
        with patch("src.collectors.scopus.requests.get", return_value=response) as get:
            scopus_collect_papers("multi-agent system mining dispatch scheduling")

    assert get.call_args.kwargs["params"]["query"] == (
        "TITLE-ABS-KEY(multi-agent AND system AND mining AND dispatch AND scheduling)"
    ), "Each query term should be ANDed explicitly, matching the WoS collector's pattern."


def test_scopus_collect_papers_handles_missing_standard_fields():
    response = make_response(
        {
            "search-results": {
                "entry": [
                    {
                        "dc:title": "Paper without optional metadata",
                        "subtypeDescription": "Book",
                    }
                ]
            }
        }
    )
    response.raise_for_status.return_value = None

    with patch.dict("os.environ", {"SCOPUS_API_KEY": "test-scopus-key"}):
        with patch("src.collectors.scopus.requests.get", return_value=response):
            papers = scopus_collect_papers("scheduling")

    assert papers[0]["title"] == "Paper without optional metadata"
    assert papers[0]["authors"] == [], "Missing dc:creator should produce no authors."
    assert papers[0]["year"] is None
    assert papers[0]["venue"] is None
    assert papers[0]["venue_type"] is None
    assert papers[0]["doi"] is None
    assert papers[0]["abstract"] is None


def test_scopus_collect_papers_returns_empty_list_without_api_key(caplog):
    with patch.dict("os.environ", {}, clear=True):
        with patch("src.collectors.scopus.requests.get") as get:
            with caplog.at_level("ERROR"):
                papers = scopus_collect_papers("scheduling")

    assert papers == [], "Missing credentials should prevent the request."
    get.assert_not_called()
    assert "SCOPUS_API_KEY environment variable is missing" in caplog.text


def test_scopus_collect_papers_returns_empty_list_for_empty_response():
    response = make_response({"search-results": {"entry": []}})
    response.raise_for_status.return_value = None

    with patch.dict("os.environ", {"SCOPUS_API_KEY": "test-scopus-key"}):
        with patch("src.collectors.scopus.requests.get", return_value=response):
            papers = scopus_collect_papers("query with no results")

    assert papers == [], "An empty Scopus result should produce an empty paper list."


def test_scopus_collect_papers_raises_collector_error_and_logs_request_error(caplog):
    request_error = requests.HTTPError("controlled Scopus failure")

    with patch.dict("os.environ", {"SCOPUS_API_KEY": "test-scopus-key"}):
        with patch(
            "src.collectors.scopus.requests.get",
            side_effect=request_error,
        ):
            with caplog.at_level("ERROR"):
                with pytest.raises(CollectorError, match="controlled Scopus failure"):
                    scopus_collect_papers("scheduling")

    assert "Scopus request failed" in caplog.text
    assert "controlled Scopus failure" in caplog.text
