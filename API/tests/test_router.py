import pytest
from training.base import ModelStrategy
from training.router import ModelRouter


class MockDetector:
    def __init__(self, should_detect=False):
        self.should_detect = should_detect

    def detect(self, text):
        return self.should_detect


class MockStrategy(ModelStrategy):
    def __init__(self, name):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def preprocess(self, text: str) -> str:
        return f"processed_{text}"

    def predict(self, text: str) -> dict:
        return {"label": "POS", "score": 0.99, "segmented_text": self.preprocess(text)}


def test_router_selects_default_strategy():
    detector = MockDetector(should_detect=False)
    router = ModelRouter(detector)

    default_model = MockStrategy("default_model")
    teencode_model = MockStrategy("teencode_model")

    router.register("default_model", default_model)
    router.register("teencode_model", teencode_model)
    router.set_default("default_model")

    # Không phải teencode -> chọn default
    selected = router.select("xin chào")
    assert selected.name == "default_model"


def test_router_selects_teencode_strategy():
    detector = MockDetector(should_detect=True)
    router = ModelRouter(detector)

    default_model = MockStrategy("default_model")
    teencode_model = MockStrategy("teencode_model")

    router.register("default_model", default_model)
    router.register("teencode_model", teencode_model)
    router.set_default("default_model")

    # Có teencode -> chọn teencode_model
    selected = router.select("xin chào")
    assert selected.name == "teencode_model"


def test_router_predict_convenience_method():
    detector = MockDetector(should_detect=True)
    router = ModelRouter(detector)

    default_model = MockStrategy("default_model")
    teencode_model = MockStrategy("teencode_model")

    router.register("default_model", default_model)
    router.register("teencode_model", teencode_model)
    router.set_default("default_model")

    result = router.predict("text")
    assert result["model_used"] == "teencode_model"
    assert result["is_teencode"] is True
    assert result["label"] == "POS"
