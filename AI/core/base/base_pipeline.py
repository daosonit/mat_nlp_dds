import os
import json
import logging
from abc import ABC, abstractmethod

import numpy as np

# pyrefly: ignore [missing-import]
import torch

from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.utils.class_weight import compute_class_weight
from transformers import Trainer, TrainingArguments, EarlyStoppingCallback
from torch import nn
from core.base.base_config import BaseTrainConfig

logger = logging.getLogger(__name__)


class BaseTrainingPipeline(ABC):
    """
    Nhạc trưởng điều phối cơ sở (Facade + Template Method Pattern).

    Chứa toàn bộ logic dùng chung:
    - build_model(): Tải model dựa trên labels
    - _compute_metrics(): Tính accuracy, F1, precision, recall
    - train_and_save(): Cấu hình Trainer, train, lưu model + label_mapping.json

    Lớp con chỉ cần override 1 method:
    - prepare_data(): PhoBERT cần VnCoreNLP, ViSoBERT thì không.
    """

    def __init__(self, config: BaseTrainConfig):
        self.config = config
        self.data_processor = None  # Lớp con tự khởi tạo
        self.model_builder = None   # Lớp con tự khởi tạo
        self.tokenized_datasets = None
        self.trainer = None

    @abstractmethod
    def prepare_data(self, raw_data: list):
        """
        Điểm khác biệt DUY NHẤT giữa các pipeline.
        - PhoBERT: Khởi tạo VnCoreNLP → tách từ → tokenize
        - ViSoBERT: Tokenize thẳng (không cần tách từ)
        """
        ...

    def build_model(self):
        """Khởi tạo Model dựa trên số lượng nhãn (DÙNG CHUNG)."""
        logger.info("--- BƯỚC 2: KHỞI TẠO MÔ HÌNH ---")
        if self.data_processor.num_labels == 0:
            raise RuntimeError(
                "Chưa quét dữ liệu để lấy nhãn. Hãy chạy prepare_data() trước!"
            )

        self.model_builder.build_model(
            num_labels=self.data_processor.num_labels,
            label2id=self.data_processor.label2id,
            id2label=self.data_processor.id2label,
        )
        logger.info("Hoàn tất khởi tạo mô hình!")

    def _compute_metrics(self, eval_pred):
        """Hàm tính toán đa chỉ số nội bộ cho Trainer (DÙNG CHUNG)."""
        logits, labels = eval_pred
        predictions = np.argmax(logits, axis=-1)

        average = "weighted"
        return {
            "accuracy": (predictions == labels).mean(),
            "f1": f1_score(labels, predictions, average=average, zero_division=0),
            "precision": precision_score(
                labels, predictions, average=average, zero_division=0
            ),
            "recall": recall_score(
                labels, predictions, average=average, zero_division=0
            ),
        }

    def train_and_save(self):
        """Khởi động quá trình Huấn luyện và Lưu trữ mô hình (DÙNG CHUNG)."""
        logger.info("--- BƯỚC 3: HUẤN LUYỆN & LƯU MÔ HÌNH ---")

        report_to = ["wandb"] if self.config.use_wandb else ["none"]
        use_fp16 = self.config.use_fp16 and torch.cuda.is_available()

        if self.config.use_fp16 and not torch.cuda.is_available():
            logger.warning("FP16 bị tắt vì không tìm thấy GPU. Đang chạy bằng CPU.")
            
        use_cpu_flag = False
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            logger.warning("Phát hiện lỗi MPS trên Mac. Đang ép buộc dùng CPU để đảm bảo ổn định.")
            use_cpu_flag = True

        training_args = TrainingArguments(
            output_dir=self.config.checkpoint_dir,
            eval_strategy="epoch",
            save_strategy="epoch",
            learning_rate=self.config.learning_rate,
            per_device_train_batch_size=self.config.batch_size,
            per_device_eval_batch_size=self.config.batch_size,
            num_train_epochs=self.config.epochs,
            weight_decay=self.config.weight_decay,
            load_best_model_at_end=True,
            metric_for_best_model="f1",
            greater_is_better=True,
            report_to=report_to,
            run_name=self.config.wandb_project if self.config.use_wandb else None,
            fp16=use_fp16,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            lr_scheduler_type="cosine",
            warmup_ratio=0.1,
            use_cpu=use_cpu_flag,
        )

        callbacks = [EarlyStoppingCallback(early_stopping_patience=2)]

        # --- TINH TOAN CLASS WEIGHTS CHO DU LIEU MAT CAN BANG ---
        train_labels = self.tokenized_datasets["train"]["label"]
        classes = np.unique(train_labels)
        weights = compute_class_weight(class_weight="balanced", classes=classes, y=train_labels)
        class_weights_tensor = torch.tensor(weights, dtype=torch.float).to(self.model_builder.model.device)
        logger.info(f"Class weights (can bang du lieu): {weights}")

        class CustomTrainer(Trainer):
            def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):
                labels = inputs.pop("labels")
                outputs = model(**inputs)
                logits = outputs.get("logits")
                # Đảm bảo trọng số luôn cùng thiết bị với logits (ví dụ: cuda:0)
                loss_fct = nn.CrossEntropyLoss(weight=class_weights_tensor.to(logits.device))
                loss = loss_fct(
                    logits.view(-1, self.model.config.num_labels), labels.view(-1)
                )
                return (loss, outputs) if return_outputs else loss

        self.trainer = CustomTrainer(
            model=self.model_builder.model,
            args=training_args,
            train_dataset=self.tokenized_datasets["train"],
            eval_dataset=self.tokenized_datasets["test"],
            compute_metrics=self._compute_metrics,
            callbacks=callbacks,
            processing_class=self.model_builder.tokenizer,
        )

        logger.info(
            f"Trainer cấu hình: "
            f"Model={self.config.model_name} | "
            f"FP16={'Bật' if use_fp16 else 'Tắt'} | "
            f"Batch giả lập={self.config.batch_size * self.config.gradient_accumulation_steps} | "
            f"LR Scheduler=Cosine"
        )

        # 1. Bắt đầu train
        logger.info("ĐANG HUẤN LUYỆN (Training)...")
        self.trainer.train()

        # 2. Lưu mô hình
        logger.info(f"Lưu mô hình hoàn chỉnh vào: {self.config.output_dir}")
        self.trainer.save_model(self.config.output_dir)
        self.model_builder.tokenizer.save_pretrained(self.config.output_dir)

        # 3. Lưu bản đồ nhãn cho quá trình Suy luận (Inference)
        label_map_path = os.path.join(self.config.output_dir, "label_mapping.json")
        with open(label_map_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "label2id": self.data_processor.label2id,
                    "id2label": self.data_processor.id2label,
                },
                f,
                ensure_ascii=False,
            )

        logger.info("=== QUÁ TRÌNH HUẤN LUYỆN ĐÃ HOÀN TẤT THÀNH CÔNG! ===")
