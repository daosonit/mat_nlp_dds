import os
import logging

# pyrefly: ignore [missing-import]
from transformers import AutoModelForSequenceClassification, XLMRobertaTokenizer, pipeline

from training.base import ModelStrategy
from core.config import VISOBERT_MODEL_DIR

logger = logging.getLogger(__name__)


class ViSoBertStrategy(ModelStrategy):
    """
    Strategy cho ViSoBERT (uitnlp/visobert).

    Đặc điểm:
    - KHÔNG cần VnCoreNLP tách từ (ViSoBERT tự xử lý social media text).
    - Chuyên biệt cho văn bản mạng xã hội (teencode, emoji, viết tắt).
    - Kiến trúc XLM-RoBERTa với tokenizer riêng.
    """

    def __init__(
        self,
        model_path: str = VISOBERT_MODEL_DIR,
        fallback_model: str = "uitnlp/visobert",
        device: int = -1,
    ):
        self._model_path = model_path
        self._fallback_model = fallback_model
        self._device = device
        self._pipeline = None

    @property
    def name(self) -> str:
        return "visobert"

    def initialize(self):
        """Khởi tạo Model pipeline (gọi 1 lần khi startup)."""
        self._init_pipeline()
        logger.info("ViSoBERT Strategy đã sẵn sàng.")

    def _init_pipeline(self):
        """Tải model ViSoBERT và tạo HuggingFace pipeline."""
        model_path = self._model_path

        if not os.path.exists(model_path):
            logger.warning(
                f"Chưa tìm thấy model fine-tuned tại '{model_path}'. "
                f"Đang dùng model gốc: {self._fallback_model}"
            )
            model_path = self._fallback_model

        logger.info(f"Đang tải ViSoBERT từ: {model_path}")
        tokenizer = XLMRobertaTokenizer.from_pretrained(
            model_path, local_files_only=True
        )
        model = AutoModelForSequenceClassification.from_pretrained(
            model_path, local_files_only=True
        )

        self._pipeline = pipeline(
            "text-classification",
            model=model,
            tokenizer=tokenizer,
            device=self._device,
            batch_size=16,  # Bật cơ chế Batching
        )
        logger.info("ViSoBERT pipeline đã khởi tạo thành công.")

    def preprocess(self, text: str) -> str:
        """ViSoBERT không cần tiền xử lý, trả về text gốc."""
        return text

    def predict(self, text: str) -> dict:
        """Suy luận trực tiếp bằng ViSoBERT (không cần tách từ)."""
        result = self._pipeline(text)[0]
        return {
            "label": result["label"],
            "score": result["score"],
            "segmented_text": text,
        }

    def predict_batch(self, texts: list[str]) -> list[dict]:
        """Suy luận theo bó bằng ViSoBERT."""
        results = self._pipeline(texts)
        return [
            {
                "label": res["label"],
                "score": res["score"],
                "segmented_text": t,
            }
            for res, t in zip(results, texts)
        ]
