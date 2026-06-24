
# pyrefly: ignore [missing-import]
from transformers import AutoTokenizer

from core.base.base_pipeline import BaseTrainingPipeline
from core.PhoBERT.config import PhoBertTrainConfig
from core.PhoBERT.data_processor import PhoBertDataProcessor
from core.PhoBERT.model_builder import PhoBertModelBuilder



class PhoBertTrainingPipeline(BaseTrainingPipeline):
    """
    Training Pipeline cho PhoBERT.

    Kế thừa toàn bộ logic từ BaseTrainingPipeline (build_model, train_and_save...).
    Chỉ override prepare_data() vì PhoBERT cần VnCoreNLP tách từ.
    """

    def __init__(self, config: PhoBertTrainConfig):
        super().__init__(config)
        self.data_processor = PhoBertDataProcessor(config)
        self.model_builder = PhoBertModelBuilder(config)

    def prepare_data(self, raw_data: list):
        """Khởi động VnCoreNLP → tách từ → tokenize."""

        # PhoBERT cần VnCoreNLP để tách từ tiếng Việt
        segmenter = self.model_builder.build_vncorenlp()

        # Tải tokenizer để mã hoá
        temp_tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)

        # Chạy pipeline xử lý dữ liệu (truyền segmenter qua kwargs)
        self.tokenized_datasets = self.data_processor.process(
            raw_data=raw_data,
            tokenizer=temp_tokenizer,
            segmenter=segmenter,
        )
