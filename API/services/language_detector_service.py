import os
import fasttext
import re
from libs.detection import TeencodeDetector


def clean_text(text: str) -> str:
    """
    Làm sạch văn bản cơ bản:
    - Loại bỏ các khoảng trắng thừa.
    - Xóa khoảng trắng đầu/cuối.
    """
    if not text:
        return ""
    text = re.sub(r"\s+", " ", str(text))
    return text.strip()


class VietnameseDetector:
    """
    Bộ lọc Tiếng Việt 2 lớp (Hoàn toàn Offline).
    - Lớp 1: Dùng TeencodeDetector để bắt tiếng lóng/teencode.
    - Lớp 2: Dùng mô hình FastText (lid.176.ftz) để nhận diện ngôn ngữ.
    """

    def __init__(self, teencode_dict_path: str = None, fasttext_model_path: str = None):
        base_dir = os.path.dirname(os.path.dirname(__file__))

        # Định tuyến file Local (Tuyệt đối không tải từ Internet)
        if not teencode_dict_path:
            teencode_dict_path = os.path.join(
                base_dir, "libs", "teencode_dictionary.json"
            )

        if not fasttext_model_path:
            fasttext_model_path = os.path.join(
                base_dir, "libs", "detection", "models", "lid.176.ftz"
            )

        if not os.path.exists(fasttext_model_path):
            raise FileNotFoundError(
                f"Không tìm thấy model FastText tại {fasttext_model_path}. Hãy đảm bảo đã tải file lid.176.ftz vào đúng thư mục."
            )

        # 1. Load Teencode Detector
        self.teencode_detector = TeencodeDetector(dictionary_path=teencode_dict_path)

        # 2. Load FastText Model
        fasttext.FastText.eprint = lambda x: None  # Ẩn các warning của FastText
        self.ft_model = fasttext.load_model(fasttext_model_path)

        # 3. Regex kiểm tra nguyên âm
        self.vowel_pattern = re.compile(
            r"[aeiouyăâêôơưàáãạảằắẵặẳầấẫậẩèéẽẹẻềếễệểìíĩịỉòóõọỏồốỗộổờớỡợởùúũụủừứữựửỳýỹỵỷ]"
        )

    def is_vietnamese(self, text: str) -> dict:
        """
        Kiểm tra văn bản có phải Tiếng Việt (hoặc Teencode) có ý nghĩa hay không.
        """
        text = clean_text(text).lower()
        if not text:
            return {"is_vietnamese": False, "reason": "empty_string"}

        words = text.split()

        # ---------------------------------------------
        # BƯỚC 1: Lọc bằng Teencode & Cấu trúc chữ
        # ---------------------------------------------
        teencode_details = self.teencode_detector.get_details(text)
        teencode_count = teencode_details["teencode_count"]

        # Đếm số từ có chứa ít nhất 1 nguyên âm
        vowel_words_count = sum(1 for w in words if self.vowel_pattern.search(w))
        valid_ratio = (teencode_count + vowel_words_count) / len(words)

        # ---------------------------------------------
        # BƯỚC 2: AI FastText
        # ---------------------------------------------
        text_ft = text.replace("\n", " ")
        predictions, scores = self.ft_model.predict(text_ft)

        lang = predictions[0].replace("__label__", "")
        ft_score = float(scores[0])

        # ---------------------------------------------
        # LUẬT QUYẾT ĐỊNH (DECISION RULES)
        # ---------------------------------------------
        is_vi = False
        reason = ""

        # Luật 1: FastText tự tin cao (>40%) là tiếng Việt
        if lang == "vi" and ft_score > 0.4:
            is_vi = True
            reason = "fasttext_confident"

        # Luật 2: FastText không tự tin do "không dấu", nhưng chứa Teencode quen thuộc
        elif teencode_count > 0 and valid_ratio > 0.5:
            is_vi = True
            reason = "teencode_detected"

        # Luật 3: Rõ ràng là tiếng Anh hoặc ngôn ngữ khác
        elif lang != "vi" and ft_score > 0.6:
            is_vi = False
            reason = f"detected_foreign_language_{lang}"

        # Luật 4: Chữ gõ bừa (không có teencode, không có nguyên âm hợp lệ)
        elif valid_ratio < 0.3:
            is_vi = False
            reason = "gibberish"

        # Luật 5: Tiếng Việt gõ không dấu.
        # Nếu mô hình đoán ngoại ngữ nhưng độ tin cậy thấp (< 30%) và câu có nhiều nguyên âm chuẩn (> 70%)
        elif lang != "vi" and ft_score < 0.3 and valid_ratio > 0.7:
            is_vi = True
            reason = "unaccented_vietnamese_guess"

        # Cuối cùng: Phó mặc cho phán đoán của FastText
        else:
            is_vi = lang == "vi"
            reason = "fasttext_fallback"

        return {
            "text": text,
            "is_vietnamese": bool(is_vi),
            "reason": str(reason),
            "fasttext_lang": str(lang),
            "fasttext_confidence": float(round(ft_score * 100, 2)),
            "teencode_ratio": float(round(teencode_details["ratio"], 2)),
        }
