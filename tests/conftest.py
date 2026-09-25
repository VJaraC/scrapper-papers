import sys
import types


class FakeSentenceTransformer:
    def __init__(self, model_name):
        self.model_name = model_name

    def encode(self, values, convert_to_tensor=True):
        return values


class FakeUtil:
    @staticmethod
    def cos_sim(*args, **kwargs):
        raise AssertionError("Tests must provide their cosine similarity mock.")


sys.modules.setdefault(
    "sentence_transformers",
    types.SimpleNamespace(SentenceTransformer=FakeSentenceTransformer, util=FakeUtil),
)
