import copy
from types import SimpleNamespace

import pytest

from src.scoring import classifier


class FakeScore:
    def __init__(self, value):
        self.value = value

    def max(self):
        return self

    def item(self):
        return self.value


@pytest.fixture(autouse=True)
def mock_embedding_model(monkeypatch):
    model = SimpleNamespace(encode=lambda text, convert_to_tensor=True: text)
    scores = {axis: 0.1 for axis in classifier.REFERENCE_TEXTS}

    def cosine_similarity(paper_embedding, reference_embeddings):
        return FakeScore(scores[reference_embeddings])

    monkeypatch.setattr(classifier, "MODEL", model)
    monkeypatch.setattr(
        classifier,
        "REFERENCE_EMBEDDINGS",
        {axis: axis for axis in classifier.REFERENCE_TEXTS},
    )
    monkeypatch.setattr(classifier.util, "cos_sim", cosine_similarity)
    return scores


def test_classify_paper_uses_maximum_similarity_and_independent_thresholds(
    mock_embedding_model,
):
    mock_embedding_model.update(
        mas=0.31,
        scheduling=0.27,
        llm=0.23,
        mineria=0.30,
    )

    result = classifier.classify_paper({"title": "Controlled paper", "abstract": None})

    assert result["mas"] is True
    assert result["scheduling"] is False
    assert result["llm"] is True
    assert result["mineria"] is False
    assert result["mas_score"] == 0.31
    assert result["scheduling_score"] == 0.27
    assert result["llm_score"] == 0.23
    assert result["mineria_score"] == 0.30
    assert result["categoria"] == "MAS-LLM"


@pytest.mark.parametrize(
    ("title", "scores", "expected"),
    [
        (
            "Automated Daily Production Report Generation for Coal Mine Dispatch Rooms Based on Distil-LLM and Autogen Agents",
            {"mas": 0.8, "mineria": 0.8, "llm": 0.8, "scheduling": 0.8},
            {"mas": True, "mineria": True, "llm": True, "scheduling": True},
        ),
        (
            "Real-time multi-agent fleet management strategy for autonomous underground mines vehicles",
            {"mas": 0.8, "mineria": 0.8, "llm": 0.1, "scheduling": 0.1},
            {"mas": True, "mineria": True},
        ),
        (
            "Proceedings of 2024 International Conference on Big Data Mining and Information Processing",
            {"mas": 0.1, "mineria": 0.2, "llm": 0.1, "scheduling": 0.1},
            {"mineria": False},
        ),
        (
            "Multi-agent Scheduling to Minimize Total Completion Times",
            {"mas": 0.8, "mineria": 0.1, "llm": 0.1, "scheduling": 0.8},
            {"mas": True, "scheduling": True, "llm": False},
        ),
        (
            "Testing Access Control List Policies in a Hadoop Environment",
            {"mas": 0.1, "mineria": 0.1, "llm": 0.1, "scheduling": 0.1},
            {"mas": False, "llm": False, "scheduling": False, "mineria": False},
        ),
    ],
)
def test_validation_titles_use_mocked_semantic_scores(
    title, mock_embedding_model, scores, expected
):
    mock_embedding_model.update(scores)

    result = classifier.classify_paper({"title": title, "abstract": None})

    for axis, expected_value in expected.items():
        assert result[axis] is expected_value


def test_classify_paper_returns_none_scores_without_text():
    result = classifier.classify_paper({"title": None, "abstract": None})

    assert result == {
        "mas": None,
        "scheduling": None,
        "llm": None,
        "mineria": None,
        "mas_score": None,
        "scheduling_score": None,
        "llm_score": None,
        "mineria_score": None,
        "categoria": "NO_CLASIFICABLE",
    }


def test_classify_paper_does_not_mutate_input():
    paper = {"title": "Controlled paper", "abstract": "An abstract"}
    original = copy.deepcopy(paper)

    classifier.classify_paper(paper)

    assert paper == original
