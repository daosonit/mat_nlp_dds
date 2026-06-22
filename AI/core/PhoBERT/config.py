from dataclasses import dataclass
from core.base.base_config import BaseTrainConfig
from core.config import (
    PHOBERT_MODEL_DIR,
    PHOBERT_CHECKPOINT_DIR,
    PHOBERT_CACHE_DIR,
)


@dataclass
class PhoBertTrainConfig(BaseTrainConfig):
    """
    Cau hinh rieng cho PhoBERT (vinai/phobert-base-v2).

    Ke thua toan bo tham so tu BaseTrainConfig,
    chi override cac gia tri mac dinh dac trung cho PhoBERT.
    """

    output_dir: str = PHOBERT_MODEL_DIR
    checkpoint_dir: str = PHOBERT_CHECKPOINT_DIR
    cache_dir: str = PHOBERT_CACHE_DIR
    model_name: str = "vinai/phobert-base-v2"
    wandb_project: str = "phobert-sentiment"

    # PhoBERT gioi han kien truc 256 tokens
    max_length_limit: int = 256

# ==================================================================
# GIẢI THÍCH CÁC THƯ MỤC ĐƯỢC SINH RA KHI TRAIN:
# 1. cache_dir: Sinh ra TRƯỚC khi train. Lưu cache dữ liệu đã xử lý 
#               (tokenized) để chạy lại nhanh hơn, không phải load lại từ đầu.
# 2. checkpoint_dir: Sinh ra TRONG LÚC train. Chứa các bản sao lưu giữa chừng
#                    để nếu mất điện có thể train tiếp từ điểm dừng.
# 3. output_dir: Sinh ra SAU KHI train xong. Chứa mô hình (model) hoàn chỉnh 
#                nhất để mang ra sử dụng thực tế (như làm API).
# ==================================================================
