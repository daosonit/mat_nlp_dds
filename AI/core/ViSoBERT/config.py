from dataclasses import dataclass
from core.base.base_config import BaseTrainConfig
from core.config import (
    VISOBERT_MODEL_DIR,
    VISOBERT_CHECKPOINT_DIR,
    VISOBERT_CACHE_DIR,
)


@dataclass
class ViSoBertTrainConfig(BaseTrainConfig):
    """
    Cau hinh rieng cho ViSoBERT (uitnlp/visobert).

    Ke thua toan bo tham so tu BaseTrainConfig,
    chi override cac gia tri mac dinh dac trung cho ViSoBERT.

    Dac diem:
    - Kien truc XLM-RoBERTa, ho tro toi da 512 tokens.
    - Co tokenizer rieng, KHONG can VnCoreNLP tach tu.
    - Chuyen biet cho van ban mang xa hoi (teencode, emoji, viet tat).
    """

    model_name: str = "uitnlp/visobert"
    output_dir: str = VISOBERT_MODEL_DIR
    checkpoint_dir: str = VISOBERT_CHECKPOINT_DIR
    cache_dir: str = VISOBERT_CACHE_DIR
    wandb_project: str = "visobert-sentiment"

    # XLM-RoBERTa ho tro toi da 512 tokens
    max_length_limit: int = 512


# ==================================================================
# GIẢI THÍCH CÁC THƯ MỤC ĐƯỢC SINH RA KHI TRAIN:
# 1. cache_dir: Sinh ra TRƯỚC khi train. Lưu cache dữ liệu đã xử lý
#               (tokenized) để chạy lại nhanh hơn, không phải load lại từ đầu.
# 2. checkpoint_dir: Sinh ra TRONG LÚC train. Chứa các bản sao lưu giữa chừng
#                    để nếu mất điện có thể train tiếp từ điểm dừng.
# 3. output_dir: Sinh ra SAU KHI train xong. Chứa mô hình (model) hoàn chỉnh
#                nhất để mang ra sử dụng thực tế (như làm API).
# ==================================================================
