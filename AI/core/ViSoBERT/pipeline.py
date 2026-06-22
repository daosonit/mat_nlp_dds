import logging

# pyrefly: ignore [missing-import]
from transformers import AutoTokenizer

from core.base.base_pipeline import BaseTrainingPipeline
from core.ViSoBERT.config import ViSoBertTrainConfig
from core.ViSoBERT.data_processor import ViSoBertDataProcessor
from core.ViSoBERT.model_builder import ViSoBertModelBuilder

logger = logging.getLogger(__name__)


class ViSoBertTrainingPipeline(BaseTrainingPipeline):
    """
    Training Pipeline cho ViSoBERT.

    Kế thừa toàn bộ logic từ BaseTrainingPipeline (build_model, train_and_save...).
    Chỉ override prepare_data() vì ViSoBERT KHÔNG cần VnCoreNLP.
    """

    def __init__(self, config: ViSoBertTrainConfig):
        super().__init__(config)
        self.data_processor = ViSoBertDataProcessor(config)
        self.model_builder = ViSoBertModelBuilder(config)

    def prepare_data(self, raw_data: list):
        """Tokenize thẳng, KHÔNG cần VnCoreNLP."""
        logger.info("--- BƯỚC 1: CHUẨN BỊ DỮ LIỆU (ViSoBERT) ---")

        # ViSoBERT có tokenizer riêng, tải sẵn để tokenize
        temp_tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)

        # Chạy pipeline xử lý dữ liệu (KHÔNG có segmenter)
        self.tokenized_datasets = self.data_processor.process(
            raw_data=raw_data,
            tokenizer=temp_tokenizer,
        )
        logger.info("Hoàn tất chuẩn bị dữ liệu ViSoBERT!")
