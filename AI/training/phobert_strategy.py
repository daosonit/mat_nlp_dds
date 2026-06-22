import os
import logging

# pyrefly: ignore [missing-import]
import py_vncorenlp

# pyrefly: ignore [missing-import]
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

from training.base import ModelStrategy
from core.config import PHOBERT_MODEL_DIR, VNCORENLP_DIR

logger = logging.getLogger(__name__)


class PhoBertStrategy(ModelStrategy):
    """
    Strategy cho PhoBERT (vinai/phobert-base-v2).

    Đặc điểm:
    - Cần VnCoreNLP tách từ tiếng Việt trước khi đưa vào model.
    - Chuyên biệt cho văn bản tiếng Việt chuẩn (báo chí, review...).
    """

    def __init__(
        self,
        model_path: str = PHOBERT_MODEL_DIR,
        fallback_model: str = "vinai/phobert-base-v2",
        vncorenlp_dir: str = VNCORENLP_DIR,
        device: int = -1,
    ):
        self._model_path = model_path
        self._fallback_model = fallback_model
        self._device = device
        self._pipeline = None
        self._segmenter = None
        self._vncorenlp_dir = os.path.abspath(vncorenlp_dir)

    @property
    def name(self) -> str:
        return "phobert"

    def initialize(self):
        """Khởi tạo VnCoreNLP + Model pipeline (gọi 1 lần khi startup)."""
        self._init_vncorenlp()
        self._init_pipeline()
        logger.info("PhoBERT Strategy đã sẵn sàng.")

    def _init_vncorenlp(self):
        """Khởi tạo VnCoreNLP segmenter."""
        logger.info(f"Đang khởi tạo VnCoreNLP từ {self._vncorenlp_dir}...")
        try:
            self._segmenter = py_vncorenlp.VnCoreNLP(
                annotators=["wseg"], save_dir=self._vncorenlp_dir
            )
            logger.info("RDRSegmenter đã sẵn sàng.")
        except Exception as e:
            logger.error(f"Không thể khởi tạo VnCoreNLP: {e}", exc_info=True)
            self._segmenter = None

    def _init_pipeline(self):
        """Tải model PhoBERT và tạo HuggingFace pipeline."""
        model_path = self._model_path

        if not os.path.exists(model_path):
            logger.warning(
                f"Chưa tìm thấy model fine-tuned tại '{model_path}'. "
                f"Đang dùng model gốc: {self._fallback_model}"
            )
            model_path = self._fallback_model

        logger.info(f"Đang tải PhoBERT từ: {model_path}")
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForSequenceClassification.from_pretrained(model_path)

        self._pipeline = pipeline(
            "text-classification",
            model=model,
            tokenizer=tokenizer,
            device=self._device,
            batch_size=16,  # Bật cơ chế Batching
        )
        logger.info("PhoBERT pipeline đã khởi tạo thành công.")

    def preprocess(self, text: str) -> str:
        """Tách từ tiếng Việt bằng VnCoreNLP."""
        if self._segmenter:
            segmented_sentences = self._segmenter.word_segment(text)
            return " ".join(segmented_sentences)
        logger.warning("VnCoreNLP chưa sẵn sàng, trả về text gốc (fallback).")
        return text

    def predict(self, text: str) -> dict:
        """Tiền xử lý + suy luận bằng PhoBERT."""
        segmented_text = self.preprocess(text)
        result = self._pipeline(segmented_text)[0]
        return {
            "label": result["label"],
            "score": result["score"],
            "segmented_text": segmented_text,
        }

    def predict_batch(self, texts: list[str]) -> list[dict]:
        """Tiền xử lý + suy luận theo bó bằng PhoBERT."""
        segmented_texts = [self.preprocess(t) for t in texts]
        results = self._pipeline(segmented_texts)
        return [
            {
                "label": res["label"],
                "score": res["score"],
                "segmented_text": seg_t,
            }
            for res, seg_t in zip(results, segmented_texts)
        ]
