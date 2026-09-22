from datetime import date
from unittest.mock import patch

import pytest

from src.scoring.decision import decide_paper


CURRENT_DATE = date(2026, 9, 22)
YEAR_LIMIT = CURRENT_DATE.year - 5


def make_paper(**overrides):
    paper = {
        "year": CURRENT_DATE.year,
        "venue_type": "journal",
        "mas": True,
        "scheduling": False,
        "llm": False,
        "mineria": False,
        "categoria": "MAS-SCHEDULING",
        "is_preprint": False,
    }
    paper.update(overrides)
    return paper


def decide(paper):
    with patch("src.scoring.decision.date") as mocked_date:
        mocked_date.today.return_value = CURRENT_DATE
        return decide_paper(paper)


def test_decide_paper_scores_only_true_classification_axes():
    result = decide(
        make_paper(mas=True, scheduling=True, llm=True, mineria=True)
    )

    assert result["relevance_score"] == 4
    assert result["decision"] == "incluido"


@pytest.mark.parametrize(
    "overrides, expected_reason",
    [
        ({"is_preprint": True}, "is_preprint=True"),
        ({"year": YEAR_LIMIT - 1}, f"year={YEAR_LIMIT - 1} < {YEAR_LIMIT}"),
        ({"mas": False}, "mas=False"),
    ],
)
def test_decide_paper_excludes_when_any_exclusion_rule_applies(
    overrides, expected_reason
):
    result = decide(make_paper(**overrides))

    assert result["decision"] == "excluido"
    assert expected_reason in result["justification"]


def test_decide_paper_exclusion_has_precedence_over_pending_rules():
    result = decide(
        make_paper(
            is_preprint=True,
            year=None,
            mas=False,
            venue_type="conference",
            categoria="NO_CLASIFICABLE",
        )
    )

    assert result["decision"] == "excluido"
    assert "is_preprint=True" in result["justification"]
    assert "mas=False" in result["justification"]
    assert "year=None" in result["justification"]


def test_decide_paper_exact_age_limit_is_not_excluded():
    result = decide(make_paper(year=YEAR_LIMIT))

    assert result["decision"] == "incluido"
    assert "antiguedad=dentro del limite o sin año" in result["justification"]


@pytest.mark.parametrize(
    "overrides, expected_reason",
    [
        ({"venue_type": "conference"}, "venue_type=conference"),
        ({"mas": None}, "mas=None"),
        ({"categoria": "NO_CLASIFICABLE"}, "categoria=NO_CLASIFICABLE"),
        ({"year": None}, "year=None"),
    ],
)
def test_decide_paper_marks_pending_when_information_is_incomplete(
    overrides, expected_reason
):
    result = decide(make_paper(**overrides))

    assert result["decision"] == "pendiente"
    assert expected_reason in result["justification"]


def test_decide_paper_returns_included_when_no_rule_blocks_inclusion():
    result = decide(make_paper())

    assert result["decision"] == "incluido"
    assert "incluido:" in result["justification"]


def test_decide_paper_justification_lists_all_evaluated_criteria():
    result = decide(make_paper())

    justification = result["justification"]
    for criterion in (
        "preprint=",
        "antiguedad=",
        "mas=",
        "venue_type=",
        "categoria=",
        "year=",
    ):
        assert criterion in justification, f"Missing criterion in justification: {criterion}"


def test_decide_paper_does_not_mutate_input_and_returns_only_new_fields():
    paper = make_paper(relevance_score=99, decision="original", justification="original")
    original = paper.copy()

    result = decide(paper)

    assert paper == original, "Decision must not mutate the input paper."
    assert set(result) == {"relevance_score", "decision", "justification"}