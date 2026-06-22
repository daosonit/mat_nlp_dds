"""
NLP AI Server — Kiến trúc Strategy + Dependency Injection.

File này chỉ làm 2 việc:
1. Lifespan: Khởi tạo/giải phóng resources (models, detector)
2. Routes: Định nghĩa API endpoints

Toàn bộ business logic nằm trong:
- models/       → Strategy Pattern
- detection/    → TeencodeDetector
- auth/         → JWT authentication
"""

import os
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Ép HuggingFace tải hoàn toàn từ local, không gửi HTTP requests
os.environ["HF_HUB_OFFLINE"] = "1"

load_dotenv()

# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware

from services.language_detector_service import VietnameseDetector
from services.rabbitmq_service import rabbitmq
from consumers.predict_result_consumer import start_predict_result_consumer

# ==========================================
# LOGGING (thay thế print)
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ==========================================
# LIFESPAN — Dependency Injection
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Hàm này chạy một lần duy nhất khi khởi động ứng dụng.
    Dùng để khởi tạo database, kết nối, tải model AI...
    """
    logger.info("=" * 50)
    logger.info("  KHỞI TẠO API GATEWAY")
    logger.info("=" * 50)

    logger.info("API Gateway đã sẵn sàng!")
    logger.info("=" * 50)

    # Khởi động RabbitMQ
    await rabbitmq.connect()

    # Khởi tạo mô hình nhận diện ngôn ngữ
    app.state.language_detector = VietnameseDetector()

    # Kích hoạt Background Task lắng nghe kết quả từ Queue
    start_predict_result_consumer()

    yield  # Server chạy

    # Shutdown cleanup
    logger.info("Server đang tắt...")
    await rabbitmq.close()


# ==========================================
# FASTAPI APP
# ==========================================
app = FastAPI(
    title="NLP AI Server",
    description="Máy chủ AI Backend hỗ trợ phân tích cảm xúc",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


from api import auth_router, predict_router, words_training_router

app.include_router(auth_router.router)
app.include_router(predict_router.router)
app.include_router(words_training_router.router)
