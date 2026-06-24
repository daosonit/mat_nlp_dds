import re
from core.base.base_data_processor import BaseDataProcessor



class ViSoBertDataProcessor(BaseDataProcessor):
    """
    Xử lý dữ liệu cho ViSoBERT.

    Kế thừa toàn bộ logic từ BaseDataProcessor.
    Override _preprocess_text() để chuẩn hoá social media text
    (ViSoBERT không cần VnCoreNLP, nhưng cần normalize URL, mention, hashtag).
    """

    @property
    def _cache_prefix(self) -> str:
        return "visobert"

    def _preprocess_text(self, text: str, **kwargs) -> str:
        """
        Chuẩn hoá text social media trước khi đưa vào ViSoBERT.
        ViSoBERT KHÔNG cần tách từ, nhưng cần loại bỏ nhiễu.
        """
        text = re.sub(r"https?://\S+", "", text)  # Xóa URL
        text = re.sub(r"#(\w+)", r"\1", text)  # #hashtag → hashtag
        text = re.sub(r"@\w+", "", text)  # Xóa @mention
        text = re.sub(r"\s+", " ", text).strip()  # Chuẩn hóa khoảng trắng
        return text
