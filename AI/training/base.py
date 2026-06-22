from abc import ABC, abstractmethod


class ModelStrategy(ABC):
    """
    Strategy Pattern — Interface chung cho mọi mô hình NLP.

    Mỗi model (PhoBERT, ViSoBERT, BARTPho...) chỉ cần implement 3 method:
    - name: Tên model (dùng trong response)
    - preprocess: Tiền xử lý text (tách từ hoặc không)
    - predict: Chạy suy luận

    Khi thêm model mới, chỉ cần tạo class mới implement interface này,
    KHÔNG cần sửa serve.py hay bất kỳ file nào khác (Open/Closed Principle).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Tên định danh của model (ví dụ: 'phobert', 'visobert')."""
        ...

    @abstractmethod
    def preprocess(self, text: str) -> str:
        """
        Tiền xử lý text trước khi đưa vào model.
        Ví dụ: PhoBERT cần tách từ VnCoreNLP, ViSoBERT thì không.
        """
        ...

    @abstractmethod
    def predict(self, text: str) -> dict:
        """
        Chạy suy luận (inference) và trả về kết quả.
        Returns: {"label": str, "score": float, "segmented_text": str}
        """
        ...

    @abstractmethod
    def predict_batch(self, texts: list[str]) -> list[dict]:
        """
        Chạy suy luận theo bó (batch inference).
        Returns: Danh sách các dict [{"label": str, "score": float, "segmented_text": str}, ...]
        """
        ...
