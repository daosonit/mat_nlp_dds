import logging

# pyrefly: ignore [missing-import]
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from core.base.base_config import BaseTrainConfig

logger = logging.getLogger(__name__)


class BaseModelBuilder:
    """
    Lớp khởi tạo mô hình cơ sở (Builder/Factory Pattern).

    Chứa logic dùng chung: tải Tokenizer + Model từ HuggingFace.
    Lớp con (PhoBERT) có thể thêm method riêng (build_vncorenlp).
    """

    def __init__(self, config: BaseTrainConfig):
        self.config = config
        self.tokenizer = None
        self.model = None

    def build_model(self, num_labels: int, label2id: dict, id2label: dict):
        """Tải Tokenizer và mô hình từ HuggingFace."""
        model_name = self.config.model_name

        logger.info(f"Dang tai Tokenizer tu: {model_name}...")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        except Exception as e:
            raise RuntimeError(
                f"Khong the tai Tokenizer tu '{model_name}'.\n"
                f"Chi tiet: {e}"
            )

        logger.info(f"Dang tai Model tu: {model_name}...")
        try:
            self.model = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                num_labels=num_labels,
                id2label=id2label,
                label2id=label2id,
                ignore_mismatched_sizes=True,
            )
        except Exception as e:
            raise RuntimeError(
                f"Khong the tai Model tu '{model_name}'.\nChi tiet: {e}"
            )

        logger.info(f"Model da san sang voi {num_labels} nhan.")
        return self.tokenizer, self.model
