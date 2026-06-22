import logging

from training.base import ModelStrategy
from libs.detection import TeencodeDetector

logger = logging.getLogger(__name__)


class ModelRouter:
    """
    Router Pattern — Chọn Strategy phù hợp dựa vào nội dung text.

    Luồng: Text → TeencodeDetector → Teencode? → ViSoBERT
                                    → Chuẩn?   → PhoBERT

    Khi thêm model mới, chỉ cần:
    1. Tạo class XyzStrategy(ModelStrategy)
    2. Đăng ký vào router.register("xyz", xyz_strategy)
    3. Cập nhật logic select() nếu cần
    """

    def __init__(self, detector: TeencodeDetector):
        self._detector = detector
        self._strategies: dict[str, ModelStrategy] = {}
        self._default_strategy_name: str = "phobert"

    def register(self, name: str, strategy: ModelStrategy):
        """Đăng ký một strategy mới vào router."""
        self._strategies[name] = strategy
        logger.info(f"Đã đăng ký model strategy: '{name}'")

    def set_default(self, name: str):
        """Đặt strategy mặc định (khi text không phải teencode)."""
        if name not in self._strategies:
            raise ValueError(f"Strategy '{name}' chưa được đăng ký.")
        self._default_strategy_name = name

    def select(self, text: str) -> ModelStrategy:
        """
        Chọn strategy phù hợp dựa vào nội dung text.

        Returns:
            ModelStrategy tương ứng (PhoBERT hoặc ViSoBERT).
        """
        if self._detector.detect(text):
            strategy = self._strategies.get("visobert")
            if strategy:
                return strategy
            logger.warning("ViSoBERT chưa đăng ký, fallback sang default.")

        return self._strategies[self._default_strategy_name]

    def predict(self, text: str) -> dict:
        """
        Convenience method: Chọn model + chạy predict trong 1 bước.

        Returns:
            dict với keys: label, score, segmented_text, model_used, is_teencode
        """
        is_tc = self._detector.detect(text)
        strategy = self.select(text)
        result = strategy.predict(text)

        return {
            **result,
            "model_used": strategy.name,
            "is_teencode": is_tc,
        }

    def predict_batch(self, payloads: list[dict]) -> list[dict]:
        """
        Xử lý bó các payloads từ RabbitMQ.
        Hàm sẽ nhóm các payload theo strategy, gọi batch inference,
        sau đó ráp kết quả lại đúng thứ tự ban đầu.
        """
        # 1. Phân loại
        phobert_items = []
        visobert_items = []

        for idx, payload in enumerate(payloads):
            text = payload.get("text", "")
            is_tc = self._detector.detect(text)
            strategy = self.select(text)

            item = {
                "original_index": idx,
                "payload": payload,
                "text": text,
                "is_tc": is_tc,
                "strategy": strategy,
                "result": None,
            }
            if strategy.name == "visobert":
                visobert_items.append(item)
            else:
                phobert_items.append(item)

        # 2. Suy luận theo nhóm
        if phobert_items:
            texts = [item["text"] for item in phobert_items]
            phobert_strategy = self._strategies.get(
                "phobert", self._strategies[self._default_strategy_name]
            )
            results = phobert_strategy.predict_batch(texts)
            for item, res in zip(phobert_items, results):
                item["result"] = res

        if visobert_items:
            texts = [item["text"] for item in visobert_items]
            visobert_strategy = self._strategies.get(
                "visobert", self._strategies[self._default_strategy_name]
            )
            results = visobert_strategy.predict_batch(texts)
            for item, res in zip(visobert_items, results):
                item["result"] = res

        # 3. Trả về đúng thứ tự ban đầu
        all_items = phobert_items + visobert_items
        all_items.sort(key=lambda x: x["original_index"])

        final_results = []
        for item in all_items:
            res = item["result"]
            final_results.append(
                {
                    "task_id": item["payload"].get("task_id", "unknown"),
                    "original_text": item["text"],
                    "ai_result": {
                        "label": res["label"],
                        "score": res["score"],
                        "segmented_text": res["segmented_text"],
                        "model_used": item["strategy"].name,
                        "is_teencode": item["is_tc"],
                    },
                    "client_id": item["payload"].get("client_id"),
                    "status": "success",
                }
            )

        return final_results
