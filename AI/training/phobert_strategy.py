import os

# pyrefly: ignore [missing-import]
import py_vncorenlp

# pyrefly: ignore [missing-import]
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

from training.base import ModelStrategy
from core.config import PHOBERT_MODEL_DIR, VNCORENLP_DIR


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
        device: str = "cpu",
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

    def _init_vncorenlp(self):
        """Khởi tạo VnCoreNLP segmenter."""
        try:
            self._segmenter = py_vncorenlp.VnCoreNLP(
                annotators=["wseg"], save_dir=self._vncorenlp_dir
            )
        except Exception as e:
            self._segmenter = None

    def _init_pipeline(self):
        """Tải model PhoBERT và tạo HuggingFace pipeline."""
        model_path = self._model_path

        if not os.path.exists(model_path):
            model_path = self._fallback_model
        # use_fast=False? Tokenizer của PhoBERT sử dụng Byte-Pair Encoding (BPE) truyền thống, tương thích hoàn hảo 100% với phiên bản Fast (Rust) của thư viện Tokenizers. Nên bạn có thể để mặc định (nó sẽ tự chọn bản Fast để có tốc độ cao nhất) mà không lo lỗi.
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForSequenceClassification.from_pretrained(model_path)

        self._pipeline = pipeline(
            "text-classification",
            model=model,
            tokenizer=tokenizer,
            device=self._device,
            batch_size=16,  # Bật cơ chế Batching
        )

    def preprocess(self, text: str) -> str:
        """Tách từ tiếng Việt bằng VnCoreNLP."""
        if self._segmenter:
            segmented_sentences = self._segmenter.word_segment(text)
            return " ".join(segmented_sentences)
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
