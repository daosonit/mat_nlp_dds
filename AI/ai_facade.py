import sys
import os
import torch

# Thêm thư mục NLP vào sys.path để load được các module chung
nlp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "NLP"))
if nlp_dir not in sys.path:
    sys.path.append(nlp_dir)

from libs.detection import TeencodeDetector
from training.phobert_strategy import PhoBertStrategy
from training.visobert_strategy import ViSoBertStrategy
from training.router import ModelRouter


class AIFacade:
    """
    Facade pattern component: Encapsulates the complex initialization logic
    for AI models, strategies, and resources required by the FastAPI server.
    """

    @staticmethod
    def initialize_api_resources(app):
        """Khởi tạo các tài nguyên nhẹ dành riêng cho API Server."""
        pass

    @staticmethod
    def initialize_worker_resources() -> ModelRouter:
        """
        Khởi tạo các tài nguyên nặng (AI Models) dành riêng cho Worker.
        Code chạy trên Ubuntu: Dùng GPU (CUDA)
        Code chạy trên Macbook của bạn: Dùng GPU (MPS)
        Code chạy trên máy đời cũ/không có card: Dùng CPU
        """
        if torch.cuda.is_available():
            device = "cuda:0"  # Dành cho server Ubuntu có card NVIDIA
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device = "mps"  # Dành cho Macbook chip M1/M2/M3...
        else:
            device = "cpu"  # Chạy bằng chip CPU bình thường

        # Lấy đường dẫn tuyệt đối của thư mục chứa ai_facade.py
        base_dir = os.path.dirname(os.path.abspath(__file__))

        # 1. Teencode Detector
        detector = TeencodeDetector(
            dictionary_path=os.path.join(base_dir, "libs", "teencode_dictionary.json"),
            min_matches=1,
        )

        # 2. Nạp mô hình PhoBERT
        phobert = PhoBertStrategy(device=device)
        phobert.initialize()

        # 3. Nạp mô hình ViSoBERT
        visobert = ViSoBertStrategy(device=device)
        visobert.initialize()

        # 4. Đăng ký Model Router
        router = ModelRouter(detector=detector)
        router.register("phobert", phobert)
        router.register("visobert", visobert)
        router.set_default("phobert")

        return router
