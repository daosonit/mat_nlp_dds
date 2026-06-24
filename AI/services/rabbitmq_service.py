import os
import json
import asyncio
import time
import aio_pika
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# CẤU HÌNH KẾT NỐI (Lấy từ .env hoặc mặc định theo file docker-compose)
# ========================================
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = os.getenv("RABBITMQ_PORT", "5672")

RABBITMQ_URL = os.getenv(
    "RABBITMQ_URL",
    f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/",
)

# =============================================================================
# CONSTANTS
# ========================================
ROUTING_KEY_PREDICT_REQUESTS = "ai_predict_requests"
ROUTING_KEY_PREDICT_RESULTS = "ai_predict_results"


class RabbitMQService:
    """
    Service quản lý toàn bộ giao tiếp với RabbitMQ sử dụng thư viện aio_pika
    Hỗ trợ Bất đồng bộ (Asyncio) để tối đa hóa tốc độ I/O.
    """

    def __init__(self):
        self.connection = None
        self.publisher_channel = None
        self.consumer_channel = None

    async def connect(self):
        """Khởi tạo kết nối siêu tốc đến đập thủy điện RabbitMQ"""
        if not self.connection or self.connection.is_closed:
            try:
                # connect_robust giúp tự động kết nối lại nếu bị đứt mạng tạm thời
                self.connection = await aio_pika.connect_robust(RABBITMQ_URL)
            except Exception as e:
                raise e

    async def get_publisher_channel(self) -> aio_pika.Channel:
        """Tạo/Lấy channel dùng riêng cho việc gửi (Publish)"""
        await self.connect()
        if not self.publisher_channel or self.publisher_channel.is_closed:
            self.publisher_channel = await self.connection.channel()
        return self.publisher_channel

    async def get_consumer_channel(self) -> aio_pika.Channel:
        """Tạo/Lấy channel dùng riêng cho việc nghe (Consume)"""
        await self.connect()
        if not self.consumer_channel or self.consumer_channel.is_closed:
            self.consumer_channel = await self.connection.channel()
        return self.consumer_channel

    async def close(self):
        """Đóng kết nối an toàn khi tắt app"""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()

    async def _setup_queue(self, channel: aio_pika.Channel, queue_name: str):
        """Khởi tạo Queue với DLX. Tự động xóa và tạo lại nếu cấu hình cũ không khớp."""
        dlx_name = f"{queue_name}_dlx"
        dlq_name = f"{queue_name}_dead_letters"

        try:
            dlx = await channel.declare_exchange(
                dlx_name, aio_pika.ExchangeType.DIRECT, durable=True
            )
            dlq = await channel.declare_queue(dlq_name, durable=True)
            await dlq.bind(dlx, routing_key=queue_name)

            queue = await channel.declare_queue(
                queue_name,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": dlx_name,
                    "x-dead-letter-routing-key": queue_name,
                },
            )
            return queue
        except Exception as e:
            # Gặp lỗi cấu hình hoặc PRECONDITION_FAILED, ném lỗi để luồng bên ngoài
            # (như hàm try/except ở consume_messages_batch) tự động cấp phát lại Channel mới.
            raise e

    async def publish_message(self, message: dict, routing_key: str):
        """
        [SỬ DỤNG BỞI API GATEWAY / WORKER]
        Nhận request và ném ngay lập tức vào Queue đích danh.
        Tốc độ ném cực nhanh, không block luồng hiện tại.
        """
        channel = await self.get_publisher_channel()

        # Khai báo queue trước khi publish để chắc chắn nó tồn tại cùng với cấu hình DLX
        await self._setup_queue(channel, routing_key)

        message_body = json.dumps(message).encode()
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=message_body,
                # PERSISTENT: Lưu thẳng tin nhắn xuống ổ cứng (HDD/SSD) để đảm bảo không rớt data
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=routing_key,
        )

    async def _ensure_connection(self):
        """
        Đảm bảo kết nối và channel luôn sẵn sàng.
        Nếu đứt kết nối, nó sẽ tự động gọi lại hàm connect().
        """
        if not self.connection or self.connection.is_closed:
            self.connection = None
            self.publisher_channel = None
            self.consumer_channel = None
            await self.connect()

    async def _reject_messages(self, messages: list, requeue: bool):
        """
        Hàm tiện ích để từ chối (NACK) một danh sách tin nhắn.
        requeue=True: Trả lại Queue để thử lại.
        requeue=False: Đẩy vào Dead Letter Exchange (DLX) để cách ly.
        """
        for m in messages:
            try:
                await m.reject(requeue=requeue)
            except Exception:
                pass  # Bỏ qua nếu tin nhắn đã bị hủy (do rớt mạng)

    async def _gather_batch(self, queue_iter, batch_size: int, timeout: float) -> list:
        """
        Lắng nghe và gom đủ tin nhắn theo batch_size hoặc chờ hết timeout.
        Trả về: Danh sách các tin nhắn đã gom được.
        """
        batch_msgs = []
        try:
            # Chờ tin nhắn đầu tiên (không giới hạn thời gian)
            msg = await anext(queue_iter)
            batch_msgs.append(msg)

            # Đã có 1 tin nhắn, bắt đầu đếm ngược thời gian cho các tin nhắn tiếp theo
            start_time = time.monotonic()
            while len(batch_msgs) < batch_size:
                remaining = timeout - (time.monotonic() - start_time)
                if remaining <= 0:
                    break  # Hết thời gian chờ

                try:
                    # Cố gắng lấy thêm tin nhắn trong thời gian còn lại
                    msg = await asyncio.wait_for(anext(queue_iter), timeout=remaining)
                    batch_msgs.append(msg)
                except asyncio.TimeoutError:
                    break  # Hết thời gian chờ, tiến hành xử lý batch hiện tại

            return batch_msgs

        except asyncio.CancelledError:
            # Graceful Shutdown: Trả lại các tin nhắn đang gom dở về Queue trước khi tắt
            await self._reject_messages(batch_msgs, requeue=True)
            raise  # Ném lỗi lên để thoát an toàn
        except StopAsyncIteration:
            # Nếu đang gom mà mất mạng:
            if not batch_msgs:
                raise  # Báo lên trên để kích hoạt vòng lặp reconnect
            # Nếu đã gom được vài tin, cứ trả về để xử lý nốt
            return batch_msgs

    async def _process_batch(self, batch_msgs: list, callback_function):
        """
        Trích xuất dữ liệu, truyền cho AI (callback), và phản hồi ACK/NACK.
        """
        try:
            # 1. Chuyển đổi dữ liệu JSON
            payloads = [json.loads(m.body.decode()) for m in batch_msgs]

            # 2. Gọi hàm AI xử lý (callback)
            await callback_function(payloads)

            # 3. Nếu chạy thành công, tiến hành ACK (Xác nhận đã xong)
            for m in batch_msgs:
                await m.ack()

        except asyncio.CancelledError:
            # Nếu bị ngắt giữa chừng lúc đang chạy AI, trả lại queue
            await self._reject_messages(batch_msgs, requeue=True)
            raise
        except Exception as e:
            # Đẩy toàn bộ tin nhắn bị lỗi vào DLX (Khu cách ly) để không lặp vô tận
            await self._reject_messages(batch_msgs, requeue=False)

    async def consume_messages_batch(
        self, queue_name: str, batch_size: int, timeout: float, callback_function
    ):
        """
        [SỬ DỤNG BỞI AI WORKER CAO CẤP]
        Hàm ĐIỀU PHỐI (Orchestrator): Gom tin nhắn và xử lý theo batch.
        Có cơ chế tự động phục hồi kết nối (Self-Healing).
        """
        retry_count = 0
        while True:
            try:
                # 1. Chuẩn bị kết nối và Queue (DLX)
                await self._ensure_connection()
                channel = await self.get_consumer_channel()
                queue = await self._setup_queue(channel, queue_name)

                # 2. Tối ưu Pipeline mạng (luôn tải sẵn gấp đôi lượng cần thiết)
                await channel.set_qos(prefetch_count=batch_size * 2)

                retry_count = 0  # Reset bộ đếm lỗi khi đã chạy ngon lành

                # 3. Vòng lặp chính để liên tục gom và xử lý
                async with queue.iterator() as queue_iter:
                    while True:
                        # Gom tin nhắn
                        batch_msgs = await self._gather_batch(
                            queue_iter, batch_size, timeout
                        )

                        # Có tin nhắn thì mang đi xử lý
                        if batch_msgs:
                            await self._process_batch(batch_msgs, callback_function)

            except StopAsyncIteration:
                pass
            except asyncio.CancelledError:
                raise  # Lệnh tắt Worker, thoát ngay!
            except Exception as e:
                pass

            # 4. Exponential Backoff (Cơ chế chống bão mạng)
            sleep_time = min(60, 2**retry_count)
            await asyncio.sleep(sleep_time)
            retry_count += 1


# -----------------------------------------------------------------------------
# KHỞI TẠO SINGLETON
# Khởi tạo một đối tượng toàn cục duy nhất để dùng chung cho toàn bộ Project
# Bạn chỉ cần `from Api.rabbitmq.service import rabbitmq` ở các file khác.
# -----------------------------------------------------------------------------
rabbitmq = RabbitMQService()
