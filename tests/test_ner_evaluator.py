import pytest
from greenprompt.evaluators import NERExtractionEvaluator, get_evaluator


@pytest.fixture
def evaluator():
    return NERExtractionEvaluator()


class TestNERExtractionEvaluator:
    def test_perfect_match(self, evaluator):
        response = '{"PERSON": ["John Smith"], "ORG": ["Google"], "LOC": ["New York"]}'
        gt = '{"PERSON": ["John Smith"], "ORG": ["Google"], "LOC": ["New York"]}'
        quality, completed = evaluator.evaluate(response, gt)
        assert quality == 1.0
        assert completed is True

    def test_partial_match(self, evaluator):
        response = '{"PERSON": ["John Smith"], "ORG": ["Google"]}'
        gt = '{"PERSON": ["John Smith"], "ORG": ["Google"], "LOC": ["New York"]}'
        quality, completed = evaluator.evaluate(response, gt)
        assert 0.0 < quality < 1.0
        assert completed is True

    def test_wrong_entities(self, evaluator):
        response = '{"PERSON": ["Jane Doe"], "ORG": ["Apple"]}'
        gt = '{"PERSON": ["John Smith"], "ORG": ["Google"], "LOC": ["New York"]}'
        quality, completed = evaluator.evaluate(response, gt)
        assert quality == 0.0

    def test_empty_response(self, evaluator):
        quality, completed = evaluator.evaluate("", '{"PERSON": ["John"]}')
        assert quality == 0.0
        assert completed is False

    def test_no_ground_truth(self, evaluator):
        quality, completed = evaluator.evaluate("some response", None)
        assert quality == 0.0
        assert completed is False

    def test_json_in_markdown_block(self, evaluator):
        response = '```json\n{"PERSON": ["John Smith"], "ORG": ["Google"]}\n```'
        gt = '{"PERSON": ["John Smith"], "ORG": ["Google"]}'
        quality, completed = evaluator.evaluate(response, gt)
        assert quality == 1.0

    def test_case_insensitive_entities(self, evaluator):
        response = '{"PERSON": ["john smith"], "ORG": ["google"]}'
        gt = '{"PERSON": ["John Smith"], "ORG": ["Google"]}'
        quality, completed = evaluator.evaluate(response, gt)
        assert quality == 1.0

    def test_extra_entities_penalized(self, evaluator):
        response = '{"PERSON": ["John Smith", "Jane Doe"], "ORG": ["Google"]}'
        gt = '{"PERSON": ["John Smith"], "ORG": ["Google"]}'
        quality, completed = evaluator.evaluate(response, gt)
        assert quality < 1.0

    def test_get_evaluator_returns_ner(self):
        ev = get_evaluator("ner")
        assert isinstance(ev, NERExtractionEvaluator)
