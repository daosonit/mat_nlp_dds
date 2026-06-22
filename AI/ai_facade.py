import sys
import os
import logging
import torch

# Thêm thư mục NLP vào sys.path để load được các module chung
nlp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "NLP"))
if nlp_dir not in sys.path:
    sys.path.append(nlp_dir)

from libs.detection import TeencodeDetector
from training.phobert_strategy import PhoBertStrategy
from training.visobert_strategy import ViSoBertStrategy
from training.router import ModelRouter

logger = logging.getLogger(__name__)


class AIFacade:
    """
    Facade pattern component: Encapsulates the complex initialization logic
    for AI models, strategies, and resources required by the FastAPI server.
    """

    @staticmethod
    def initialize_api_resources(app):
        """Khởi tạo các tài nguyên nhẹ dành riêng cho API Server."""
        logger.info("=" * 50)
        logger.info("  KHỞI TẠO API GATEWAY")
        logger.info("=" * 50)

        logger.info("API Gateway đã sẵn sàng!")
        logger.info("=" * 50)

    @staticmethod
    def initialize_worker_resources() -> ModelRouter:
        """Khởi tạo các tài nguyên nặng (AI Models) dành riêng cho Worker."""
        logger.info("=" * 50)
        logger.info("  KHỞI TẠO AI WORKER MODELS")
        logger.info("=" * 50)

        device = 0 if torch.cuda.is_available() else -1
        logger.info(f"Thiết bị: {'GPU' if device == 0 else 'CPU'}")

        # Lấy đường dẫn tuyệt đối của thư mục chứa ai_facade.py
        base_dir = os.path.dirname(os.path.abspath(__file__))

        # 1. Teencode Detector
        detector = TeencodeDetector(
            dictionary_path=os.path.join(base_dir, "libs", "teencode_dictionary.json"),
            min_matches=1,
        )

        # 2. PhoBERT Strategy
        phobert = PhoBertStrategy(
            model_path=os.path.join(base_dir, "ai_models", "phobert_sentiment_model_final"),
            vncorenlp_dir=os.path.join(base_dir, "ai_models", "vncorenlp"),
            device=device,
        )
        phobert.initialize()

        # 3. ViSoBERT Strategy
        visobert = ViSoBertStrategy(
            model_path=os.path.join(base_dir, "ai_models", "visobert_sentiment_model_final"),
            device=device,
        )
        visobert.initialize()

        # 4. Model Router (đăng ký strategies)
        router = ModelRouter(detector=detector)
        router.register("phobert", phobert)
        router.register("visobert", visobert)
        router.set_default("phobert")

        logger.info("AI Worker Models đã sẵn sàng!")
        logger.info("=" * 50)

        return router
