import os
import json
import logging
import argparse

# pyrefly: ignore [missing-import]
from transformers import set_seed

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def train_phobert(raw_data: list, **kwargs):
    """Huấn luyện mô hình PhoBERT (cho văn bản tiếng Việt chuẩn)."""
    from core.PhoBERT.config import PhoBertTrainConfig
    from core.PhoBERT.pipeline import PhoBertTrainingPipeline

    config = PhoBertTrainConfig(**kwargs)
    config.validate()
    set_seed(config.seed)
    logger.info(f"Khởi động PhoBERT Pipeline. Seed={config.seed}")

    pipeline = PhoBertTrainingPipeline(config)
    pipeline.prepare_data(raw_data)
    pipeline.build_model()
    pipeline.train_and_save()


def train_visobert(raw_data: list, **kwargs):
    """Huấn luyện mô hình ViSoBERT (cho văn bản social media / teencode)."""
    from core.ViSoBERT.config import ViSoBertTrainConfig
    from core.ViSoBERT.pipeline import ViSoBertTrainingPipeline

    config = ViSoBertTrainConfig(**kwargs)
    config.validate()
    set_seed(config.seed)
    logger.info(f"Khởi động ViSoBERT Pipeline. Seed={config.seed}")

    pipeline = ViSoBertTrainingPipeline(config)
    pipeline.prepare_data(raw_data)
    pipeline.build_model()
    pipeline.train_and_save()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Huấn luyện mô hình NLP (PhoBERT hoặc ViSoBERT)"
    )
    parser.add_argument(
        "--model",
        type=str,
        choices=["phobert", "visobert", "both"],
        default="both",
        help="Chọn mô hình cần train: 'phobert', 'visobert', hoặc 'both' (mặc định)",
    )
    parser.add_argument(
        "--data",
        type=str,
        default="./car_sentiment_mock_data.json",
        help="Đường dẫn tới file dữ liệu JSON",
    )
    parser.add_argument(
        "--epochs", type=int, default=5, help="Số vòng huấn luyện (mặc định: 5)"
    )
    parser.add_argument(
        "--fp16",
        action="store_true",
        default=True,
        help="Bật Mixed Precision FP16 (mặc định: True)",
    )
    parser.add_argument(
        "--no-fp16",
        action="store_true",
        help="Tắt Mixed Precision FP16 (dùng khi chạy CPU)",
    )
    parser.add_argument(
        "--grad-accum",
        type=int,
        default=4,
        help="Gradient Accumulation Steps (mặc định: 4)",
    )
    parser.add_argument(
        "--wandb",
        action="store_true",
        default=False,
        help="Bật Weights & Biases logging",
    )

    args = parser.parse_args()

    # Đọc dữ liệu
    if not os.path.exists(args.data):
        logger.error(
            f"Không tìm thấy file dữ liệu huấn luyện '{args.data}'. Vui lòng cung cấp file JSON hợp lệ qua tham số --data."
        )
        exit(1)

    with open(args.data, "r", encoding="utf-8") as f:
        sample_data = json.load(f)

    use_fp16 = not args.no_fp16

    # Gọi hàm train tương ứng
    train_kwargs = {
        "epochs": args.epochs,
        "use_fp16": use_fp16,
        "gradient_accumulation_steps": args.grad_accum,
        "use_wandb": args.wandb,
    }

    if args.model in ["phobert", "both"]:
        logger.info("=" * 50)
        logger.info("  HUẤN LUYỆN MÔ HÌNH: PhoBERT")
        logger.info("  (Chuyên biệt cho văn bản tiếng Việt chuẩn)")
        logger.info("=" * 50)
        train_phobert(raw_data=sample_data, **train_kwargs)

    if args.model in ["visobert", "both"]:
        logger.info("=" * 50)
        logger.info("  HUẤN LUYỆN MÔ HÌNH: ViSoBERT")
        logger.info("  (Chuyên biệt cho social media / teencode)")
        logger.info("=" * 50)
        train_visobert(raw_data=sample_data, **train_kwargs)
