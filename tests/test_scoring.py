import copy

import pytest

from src.scoring.classifier import classify_paper


EXPECTED_FALSE_AXES = {
    "mas": False,
    "scheduling": False,
    "llm": False,
    "mineria": False,
    "categoria": "MAS-SCHEDULING",
}


@pytest.mark.parametrize(
    "keyword",
    [
        "multi-agent",
        "multiagent",
        "multi agent",
        "agent-based",
        "sistema multiagente",
        "sistemas multi-agente",
        "multiagente",
        "Multi-Agent Rescheduling Framework",
        "Multi-Agent Reinforcement Learning",
        "Priority-Driven Hierarchical Multi-Agent Systems",
    ],
)
def test_classify_paper_detects_each_mas_keyword(keyword):
    result = classify_paper({"title": keyword, "abstract": None})

    assert result["mas"] is True, "Each configured MAS keyword should be detected."
    assert result["scheduling"] is False
    assert result["categoria"] == "MAS-SCHEDULING"


@pytest.mark.parametrize(
    "keyword",
    [
        "scheduling",
        "dispatch",
        "dispatching",
        "job shop",
        "task allocation",
        "resource allocation",
    ],
)
def test_classify_paper_detects_each_scheduling_keyword(keyword):
    result = classify_paper({"title": None, "abstract": keyword})

    assert result["scheduling"] is True, "Each scheduling keyword should be detected."
    assert result["mas"] is False
    assert result["categoria"] == "MAS-SCHEDULING"


@pytest.mark.parametrize(
    ("paper", "expected"),
    [
        (
            {"title": "Large Language Model for scheduling", "abstract": None},
            {"mas": False, "scheduling": True, "llm": True, "mineria": False, "categoria": "MAS-LLM"},
        ),
        (
            {"title": "Mining dispatch optimization", "abstract": None},
            {"mas": False, "scheduling": True, "llm": False, "mineria": True, "categoria": "MAS-DESPACHO-MINERO"},
        ),
        (
            {"title": "GPT for mine dispatch", "abstract": None},
            {"mas": False, "scheduling": True, "llm": True, "mineria": True, "categoria": "MAS-DESPACHO-MINERO-LLM"},
        ),
    ],
)
def test_classify_paper_preserves_category_rules_for_llm_and_mining(paper, expected):
    assert classify_paper(paper) == expected


def test_classify_paper_is_case_and_accent_insensitive():
    result = classify_paper(
        {
            "title": "SISTEMAS MULTI-ÁGENTE para RESOURCE ALLOCATION",
            "abstract": "MODELO de LLM para DESPACHÓ MINERO",
        }
    )

    assert result == {
        "mas": True,
        "scheduling": True,
        "llm": True,
        "mineria": True,
        "categoria": "MAS-DESPACHO-MINERO-LLM",
    }


def test_classify_paper_returns_no_classifiable_for_missing_text():
    assert classify_paper({"title": None, "abstract": None}) == {
        "mas": None,
        "scheduling": None,
        "llm": None,
        "mineria": None,
        "categoria": "NO_CLASIFICABLE",
    }

    assert classify_paper({})["categoria"] == "NO_CLASIFICABLE"
    assert classify_paper({"title": "  ", "abstract": ""})["mas"] is None


def test_classify_paper_returns_false_axes_for_evaluable_unmatched_text():
    result = classify_paper(
        {"title": "Optimization study", "abstract": "A controlled unrelated topic."}
    )

    assert result == EXPECTED_FALSE_AXES


def test_mas_and_scheduling_do_not_change_category():
    mas_only = classify_paper({"title": "multi-agent system", "abstract": None})
    scheduling_only = classify_paper({"title": "job shop", "abstract": None})

    assert mas_only["mas"] is True
    assert mas_only["scheduling"] is False
    assert mas_only["categoria"] == "MAS-SCHEDULING"
    assert scheduling_only["mas"] is False
    assert scheduling_only["scheduling"] is True
    assert scheduling_only["categoria"] == "MAS-SCHEDULING"


def test_classify_paper_does_not_mutate_input():
    paper = {
        "title": "Foundation Model for task allocation",
        "abstract": "A multi-agent system for mining dispatch.",
        "llm": "original",
        "categoria": "original",
    }
    original = copy.deepcopy(paper)

    classify_paper(paper)

    assert paper == original, "Classification must not mutate the input paper."
