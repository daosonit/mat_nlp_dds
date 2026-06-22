from dataclasses import dataclass


@dataclass
class BaseTrainConfig:
    """
    Cau hinh chung (Base Config) cho moi mo hinh NLP.

    Chua toan bo cac tham so dung chung giua PhoBERT, ViSoBERT, va bat ky
    mo hinh nao trong tuong lai (BARTPho, mBERT...).

    Khi tao mo hinh moi, chi can ke thua va override cac gia tri mac dinh:
    - model_name, output_dir, checkpoint_dir, cache_dir, wandb_project
    - max_length_limit (gioi han kien truc cua model)
    """

    # --- MO HINH (Bat buoc override) ---
    model_name: str = ""
    output_dir: str = ""
    checkpoint_dir: str = ""
    cache_dir: str = ""

    # --- SIEU THAM SO (Hyperparameters) ---

    # So vong hoc (Epoch): AI se doc qua toan bo du lieu bao nhieu lan.
    epochs: int = 5

    # Toc do hoc (Learning Rate): 2e-5 la gia tri "vang" cho BERT-family.
    learning_rate: float = 2e-5

    # So luong cau binh luan AI doc cung mot luc (Batch Size).
    batch_size: int = 16

    # He so phan ra trong luong (Weight Decay): Chong hoc vet.
    weight_decay: float = 0.01

    # Do dai toi da cua 1 cau (tinh bang so token).
    max_length: int = 128

    # Gioi han max_length cua kien truc model (override theo tung model).
    max_length_limit: int = 512

    # --- TOI UU TOC DO ---

    # Mixed Precision (FP16): Tang toc gap doi tren GPU co Tensor Cores.
    use_fp16: bool = True

    # Gradient Accumulation: "Gia lap" batch_size lon hon.
    gradient_accumulation_steps: int = 4

    # --- GIAM SAT ---
    use_wandb: bool = False
    wandb_project: str = ""

    # --- SEED ---
    seed: int = 42

    def validate(self):
        """Kiem tra cac gia tri cau hinh co hop le khong truoc khi bat dau train."""
        errors = []

        if not self.model_name:
            errors.append("model_name khong duoc de trong.")
        if not self.output_dir:
            errors.append("output_dir khong duoc de trong.")
        if self.epochs < 1:
            errors.append(f"epochs phai >= 1, hien tai: {self.epochs}")
        if self.batch_size < 1:
            errors.append(f"batch_size phai >= 1, hien tai: {self.batch_size}")
        if self.learning_rate <= 0:
            errors.append(f"learning_rate phai > 0, hien tai: {self.learning_rate}")
        if self.max_length < 16:
            errors.append(f"max_length phai >= 16, hien tai: {self.max_length}")
        if self.gradient_accumulation_steps < 1:
            errors.append(
                f"gradient_accumulation_steps phai >= 1, hien tai: {self.gradient_accumulation_steps}"
            )
        if self.max_length > self.max_length_limit:
            errors.append(
                f"max_length phai <= {self.max_length_limit} do gioi han kien truc model, "
                f"hien tai: {self.max_length}"
            )

        if errors:
            raise ValueError(
                "Cau hinh khong hop le:\n" + "\n".join(f"  - {e}" for e in errors)
            )

        return True
