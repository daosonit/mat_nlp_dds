from core.base.base_data_processor import BaseDataProcessor



class PhoBertDataProcessor(BaseDataProcessor):
    """
    Xử lý dữ liệu cho PhoBERT.

    Kế thừa toàn bộ logic từ BaseDataProcessor.
    Chỉ override _preprocess_text() để tách từ bằng VnCoreNLP.
    """

    @property
    def _cache_prefix(self) -> str:
        return "phobert"

    def _preprocess_text(self, text: str, **kwargs) -> str:
        """Tách từ tiếng Việt bằng VnCoreNLP segmenter."""
        segmenter = kwargs.get("segmenter")
        if segmenter:
            sentences = segmenter.word_segment(text)
            return " ".join(sentences)
        return text
