import sys
import os
import asyncio
import logging

# Thêm thư mục NLP vào cuối sys.path để load được các module chung (training, database)
nlp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "NLP"))
if nlp_dir not in sys.path:
    sys.path.append(nlp_dir)

from ai_facade import AIFacade
from services.rabbitmq_service import rabbitmq
from worker.background_worker import start_rabbitmq_worker

# Cấu hình logging cơ bản
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """
    Điểm nạp (Entrypoint) dành riêng cho AI Worker.
    Nhiệm vụ: Nạp Model AI (nặng) và chạy vòng lặp RabbitMQ.
    """
    logger.info(
        "Đang khởi tạo AI Models cho Worker (Quá trình này có thể mất chút thời gian)..."
    )

    model_router = AIFacade.initialize_worker_resources()

    logger.info("Kết nối tới RabbitMQ...")
    await rabbitmq.connect()

    # Chạy vòng lặp worker vô tận (sẽ bị block ở đây)
    logger.info("Bật Background Worker lắng nghe...")
    await start_rabbitmq_worker(model_router)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Đã nhận lệnh tắt. Tắt AI Worker an toàn.")
