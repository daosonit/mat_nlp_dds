import json
import logging
import os
from typing import Set

logger = logging.getLogger(__name__)

# Danh sách từ 1 ký tự quá phổ biến trong tiếng Việt thông thường.
# Loại khỏi detection để tránh false positive.
_AMBIGUOUS_SINGLE_CHARS = {"a", "b", "e", "m", "o", "r", "s", "t", "v", "h", "j", "q"}


class TeencodeDetector:
    """
    Phát hiện teencode trong text tiếng Việt.

    Cải tiến so với phiên bản cũ:
    - Loại bỏ các từ 1 ký tự quá phổ biến (a, b, e, m...) khỏi detection set
      để giảm false positive.
    - Hỗ trợ 2 chế độ: match ≥ N từ HOẶC tỷ lệ ≥ threshold.
    - Trả về chi tiết (từ nào bị match, tỷ lệ) để dễ debug.
    """

    def __init__(
        self,
        dictionary_path: str,
        min_matches: int = 1,
        ratio_threshold: float = 0.0,
    ):
        """
        Args:
            dictionary_path: Đường dẫn đến file teencode_dictionary.json.
            min_matches: Số từ teencode tối thiểu để coi là teencode (mặc định: 1).
            ratio_threshold: Tỷ lệ từ teencode / tổng số từ (0.0 = tắt, 0.3 = 30%).
        """
        self._dictionary = {}
        self._strong_set: Set[str] = set()
        self._min_matches = min_matches
        self._ratio_threshold = ratio_threshold

        self._load_dictionary(dictionary_path)

    def _load_dictionary(self, path: str):
        """Tải dictionary và lọc bỏ các từ 1 ký tự gây nhiễu."""
        if not os.path.exists(path):
            logger.error(f"Không tìm thấy teencode dictionary: {path}")
            return

        with open(path, "r", encoding="utf-8") as f:
            self._dictionary = json.load(f)

        # Chỉ giữ lại các từ teencode "mạnh" (loại bỏ từ 1 ký tự gây false positive)
        self._strong_set = {
            word
            for word in self._dictionary.keys()
            if word not in _AMBIGUOUS_SINGLE_CHARS
        }

        logger.info(
            f"Đã tải teencode dictionary: {len(self._dictionary)} tổng, "
            f"{len(self._strong_set)} từ mạnh (đã loại {len(_AMBIGUOUS_SINGLE_CHARS)} từ gây nhiễu)."
        )

    def detect(self, text: str) -> bool:
        """
        Kiểm tra xem text có phải teencode không.

        Logic:
        1. Nếu tỷ lệ teencode >= ratio_threshold → True (nếu ratio_threshold > 0)
        2. Nếu số từ teencode >= min_matches → True
        3. Ngược lại → False
        """
        words = text.lower().split()
        if not words:
            return False

        matched = [w for w in words if w in self._strong_set]
        count = len(matched)

        # Kiểm tra tỷ lệ (nếu bật)
        if self._ratio_threshold > 0:
            ratio = count / len(words)
            if ratio >= self._ratio_threshold:
                return True

        # Kiểm tra số lượng tối thiểu
        return count >= self._min_matches

    def get_details(self, text: str) -> dict:
        """
        Trả về chi tiết phân tích teencode (dùng cho debug/logging).
        """
        words = text.lower().split()
        matched = [w for w in words if w in self._strong_set]
        return {
            "total_words": len(words),
            "teencode_count": len(matched),
            "teencode_words": matched,
            "ratio": len(matched) / len(words) if words else 0,
            "is_teencode": self.detect(text),
        }
