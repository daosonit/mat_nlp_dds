import os
import json
import hashlib
import logging
from abc import ABC, abstractmethod

# pyrefly: ignore [missing-import]
from datasets import Dataset
from tqdm import tqdm
from core.base.base_config import BaseTrainConfig

logger = logging.getLogger(__name__)


class BaseDataProcessor(ABC):
    """
    Lớp xử lý dữ liệu cơ sở (Template Method Pattern).

    Chứa toàn bộ logic dùng chung:
    - Lọc dữ liệu (_clean_and_validate)
    - Xây dựng label maps (_build_label_maps)
    - Cache management (_compute_data_hash)
    - Chia Train/Test
    - Tokenize

    Lớp con chỉ cần override 1 method duy nhất:
    - _preprocess_text(): PhoBERT tách từ VnCoreNLP, ViSoBERT trả thẳng.
    """

    def __init__(self, config: BaseTrainConfig):
        self.config = config
        self.label2id = {}
        self.id2label = {}
        self.num_labels = 0

    @abstractmethod
    def _preprocess_text(self, text: str, **kwargs) -> str:
        """
        Điểm khác biệt DUY NHẤT giữa các model.
        - PhoBERT: tách từ bằng VnCoreNLP segmenter
        - ViSoBERT: trả thẳng text gốc (model tự xử lý)
        """
        ...

    @property
    def _cache_prefix(self) -> str:
        """Prefix cho file cache, override nếu cần."""
        return "base"

    def _build_label_maps(self, clean_data: list):
        """Xây dựng bản đồ nhãn động từ dữ liệu đã lọc."""
        unique_labels = sorted(
            list(set(item["label"] for item in clean_data if "label" in item))
        )

        if len(unique_labels) < 2:
            raise ValueError(
                f"Du lieu phai co it nhat 2 nhan khac nhau. "
                f"Hien tai chi tim thay: {unique_labels}"
            )

        self.label2id = {label: idx for idx, label in enumerate(unique_labels)}
        self.id2label = {idx: label for idx, label in enumerate(unique_labels)}
        self.num_labels = len(self.label2id)

        logger.info(
            f"Da xay dung ban do cho {self.num_labels} nhan: {list(self.label2id.keys())}"
        )

    def _clean_and_validate(self, raw_data: list):
        """Lọc bỏ các bản ghi lỗi hoặc thiếu trường thông tin."""
        clean_data = []
        skipped = 0

        for item in raw_data:
            if not isinstance(item, dict):
                skipped += 1
                continue
            if "text" not in item or "label" not in item:
                skipped += 1
                continue

            text = str(item["text"]).strip()
            label = str(item["label"]).strip()

            if not text or not label:
                skipped += 1
                continue

            clean_data.append({"text": text, "label": label})

        logger.info(
            f"Thong ke du lieu: {len(clean_data)} hop le, {skipped} bi loai bo."
        )
        return clean_data

    def _compute_data_hash(self, clean_data: list) -> str:
        """Tạo 'dấu vân tay' (hash) cho dữ liệu để kiểm tra cache."""
        hash_payload = {"data": clean_data, "label2id": self.label2id}
        data_str = json.dumps(hash_payload, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(data_str.encode()).hexdigest()[:12]

    def process(self, raw_data: list, tokenizer, **kwargs):
        """
        Luồng xử lý chính (Template Method).
        Bước 1-2-4-5 giống nhau cho mọi model.
        Bước 3 (preprocess) gọi abstract method _preprocess_text().
        """
        # 1. Làm sạch dữ liệu
        clean_data = self._clean_and_validate(raw_data)
        if len(clean_data) == 0:
            raise ValueError("Khong con ban ghi nao hop le sau khi loc!")

        # 2. Quét nhãn và xây dựng label maps
        self._build_label_maps(clean_data)

        # 3. Quản lý Cache
        data_hash = self._compute_data_hash(clean_data)
        cache_path = os.path.join(
            self.config.cache_dir, f"{self._cache_prefix}_{data_hash}.json"
        )

        if os.path.exists(cache_path):
            logger.info(f"Tim thay cache ({cache_path}). Doc tu o cung...")
            with open(cache_path, "r", encoding="utf-8") as f:
                cached = json.load(f)
            processed_texts = cached["texts"]
            labels = cached["labels"]
        else:
            logger.info("Khong tim thay cache. Bat dau tien xu ly du lieu...")
            processed_texts = []
            labels = []
            errors = 0

            for item in tqdm(clean_data, desc=f"Xu ly du lieu ({self._cache_prefix})", unit="cau"):
                try:
                    processed_text = self._preprocess_text(item["text"], **kwargs)
                    processed_texts.append(processed_text)
                    labels.append(self.label2id[item["label"]])
                except Exception:
                    errors += 1
                    continue

            if errors > 0:
                logger.warning(f"Co {errors} cau bi loi khi xu ly (da bo qua).")

            # Lưu cache
            os.makedirs(self.config.cache_dir, exist_ok=True)
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(
                    {"texts": processed_texts, "labels": labels}, f, ensure_ascii=False
                )
            logger.info(f"Da luu cache tai: {cache_path}")

        # 4. Tạo HuggingFace Dataset và chia Train/Test
        dataset = Dataset.from_dict({"text": processed_texts, "label": labels})
        dataset = dataset.train_test_split(test_size=0.2, seed=self.config.seed)
        logger.info(
            f"Chia du lieu: Train={len(dataset['train'])} | Test={len(dataset['test'])}"
        )

        # 5. Tokenize dữ liệu bằng bộ tokenizer của model
        def tokenize_function(examples):
            return tokenizer(
                examples["text"],
                padding="max_length",
                truncation=True,
                max_length=self.config.max_length,
            )

        logger.info("Dang Ma hoa van ban (Tokenization)...")
        tokenized_datasets = dataset.map(tokenize_function, batched=True)
        logger.info("Tien xu ly du lieu hoan tat!")

        return tokenized_datasets
