import os
import json
import asyncio
import time
import aio_pika
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# CẤU HÌNH KẾT NỐI
# ========================================
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "matgroup_rmq")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "matgroup_rmq123")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "192.168.1.99")
RABBITMQ_PORT = os.getenv("RABBITMQ_PORT", "5672")

RABBITMQ_URL = os.getenv(
    "RABBITMQ_URL",
    f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/"
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
        self.channel = None

    async def connect(self):
        """Khởi tạo kết nối siêu tốc đến RabbitMQ"""
        if not self.connection:
            try:
                # connect_robust giúp tự động kết nối lại nếu bị đứt mạng tạm thời
                self.connection = await aio_pika.connect_robust(RABBITMQ_URL)
                self.channel = await self.connection.channel()

                print(" Đã kết nối thành công tới RabbitMQ!")
            except Exception as e:
                print(f" Lỗi kết nối RabbitMQ: {e}")
                raise e

    async def close(self):
        """Đóng kết nối an toàn khi tắt app"""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            print(" Đã đóng kết nối RabbitMQ an toàn.")

    async def _setup_queue(self, queue_name: str):
        """Khởi tạo Queue với DLX. Tự động xóa và tạo lại nếu cấu hình cũ không khớp."""
        dlx_name = f"{queue_name}_dlx"
        dlq_name = f"{queue_name}_dead_letters"

        try:
            dlx = await self.channel.declare_exchange(
                dlx_name, aio_pika.ExchangeType.DIRECT, durable=True
            )
            dlq = await self.channel.declare_queue(dlq_name, durable=True)
            await dlq.bind(dlx, routing_key=queue_name)

            queue = await self.channel.declare_queue(
                queue_name,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": dlx_name,
                    "x-dead-letter-routing-key": queue_name,
                },
            )
            return queue
        except Exception as e:
            if "PRECONDITION_FAILED" in str(e):
                print(
                    f" Cảnh báo: Queue '{queue_name}' sai cấu hình DLX. Đang xóa và tạo lại..."
                )
                # Khi Channel gặp PRECONDITION_FAILED, RabbitMQ tự động đóng Channel đó. Ta phải mở lại.
                self.channel = await self.connection.channel()
                await self.channel.queue_delete(queue_name)
                # Gọi lại chính nó sau khi xóa xong
                return await self._setup_queue(queue_name)
            else:
                raise e

    async def publish_message(self, message: dict, routing_key: str):
        """
        [SỬ DỤNG BỞI API GATEWAY / WORKER]
        Nhận request và ném ngay lập tức vào Queue đích danh.
        Tốc độ ném cực nhanh, không block luồng hiện tại.
        """
        if not self.channel:
            await self.connect()

        # Khai báo queue trước khi publish để chắc chắn nó tồn tại cùng với cấu hình DLX
        await self._setup_queue(routing_key)

        message_body = json.dumps(message).encode()
        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=message_body,
                # PERSISTENT: Lưu thẳng tin nhắn xuống ổ cứng (HDD/SSD) để đảm bảo không rớt data
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=routing_key,
        )

    async def consume_messages(self, queue_name: str, callback_function):
        """
        [SỬ DỤNG BỞI N8N WORKER / AI WORKER]
        Đứng canh ở đập thủy điện, hút tin nhắn ra xử lý từ từ (Rate Limiting).
        """
        if not self.channel:
            await self.connect()

        # Khai báo queue trước khi get
        queue = await self._setup_queue(queue_name)

        # QOS (Quality of Service): Prefetch count = 50
        # Mỗi lần chỉ lấy tối đa 50 tin nhắn ra RAM để làm. Tránh việc hút cả 1 triệu
        # tin nhắn vào RAM làm sập n8n. Làm xong 1 cái, nó mới nhả 1 cái khác ra.
        await self.channel.set_qos(prefetch_count=50)

        print(f" Đang lắng nghe trên hàng đợi '{queue_name}'...")

        # Vòng lặp vô tận (Luôn luôn lắng nghe)
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                # message.process() tự động gửi tín hiệu ACK (Acknowledge) về cho
                # RabbitMQ báo rằng: "Tôi đã làm xong nhiệm vụ này, hãy xóa nó khỏi hàng đợi".
                # Nếu code bị lỗi giữa chừng, tin nhắn sẽ bị văng ngược lại Queue để người khác làm.
                async with message.process():
                    payload = json.loads(message.body.decode())
                    # Gọi hàm xử lý thực tế của bạn (Chạy AI model...)
                    await callback_function(payload)

    async def _ensure_connection(self):
        """
        Đảm bảo kết nối và channel luôn sẵn sàng.
        Nếu đứt kết nối, nó sẽ tự động gọi lại hàm connect().
        """
        if not self.connection or self.connection.is_closed:
            self.connection = None
            self.channel = None
            await self.connect()
        elif self.channel.is_closed:
            self.channel = await self.connection.channel()

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
            print(f" Lỗi trong quá trình xử lý Batch: {e}")
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
                queue = await self._setup_queue(queue_name)

                # 2. Tối ưu Pipeline mạng (luôn tải sẵn gấp đôi lượng cần thiết)
                await self.channel.set_qos(prefetch_count=batch_size * 2)

                print(
                    f" Đang lắng nghe BATCH trên hàng đợi '{queue_name}' (size={batch_size}, timeout={timeout}s)..."
                )

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
                print(f" Lỗi trong consume_messages_batch: {e}")
                pass

            # 4. Exponential Backoff (Cơ chế chống bão mạng)
            sleep_time = min(60, 2**retry_count)
            print(f" Đang kết nối lại sau {sleep_time}s...")
            await asyncio.sleep(sleep_time)
            retry_count += 1


# -----------------------------------------------------------------------------
# KHỞI TẠO SINGLETON
# Khởi tạo một đối tượng toàn cục duy nhất để dùng chung cho toàn bộ Project
# Bạn chỉ cần `from Api.rabbitmq.service import rabbitmq` ở các file khác.
# -----------------------------------------------------------------------------
rabbitmq = RabbitMQService()
