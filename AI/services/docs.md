# Kế hoạch nâng cấp RabbitMQ Service (Enterprise-Grade)

Dưới đây là biên bản "Hội chẩn" từ 3 vị chuyên gia để nâng cấp `rabbitmq_service.py` lên mức độ Enterprise. Xin sếp xem xét và phê duyệt trước khi tôi tiến hành phẫu thuật mã nguồn!

## 1. Chuyên gia Python Bất đồng bộ (AsyncIO / Concurrency)

**Vấn đề:**

- Hàm đếm ngược thời gian đang dùng `asyncio.get_event_loop().time()`, có thể bị ảnh hưởng bởi event loop lag. Tốt nhất nên dùng `time.monotonic()` cho việc đếm ngược timeout.
- Vòng lặp reconnect cố định `sleep(5)` không tối ưu. Nên dùng **Exponential Backoff** (tăng dần thời gian chờ: 2s -> 4s -> 8s -> tối đa 60s) để tránh việc dồn dập "bão kết nối" (connection storm) vào server RabbitMQ khi server chưa kịp khởi động xong.

**Đề xuất thay đổi:**

- Tích hợp `time.monotonic()`.
- Thêm biến đếm `retry_count` ở vòng lặp ngoài cùng để tính `sleep_time = min(60, 2 ** retry_count)`.

## 2. Kỹ sư Kiến trúc RabbitMQ (AMQP / Message Broker)

**Vấn đề:**

- Hiện tại khi có lỗi xảy ra (AI lỗi, data sai định dạng), code gọi `m.reject(requeue=True)`. Tin nhắn hỏng (Poison Message) sẽ bị trả về hàng đợi và lại được hút ra xử lý -> lỗi tiếp -> trả về hàng đợi -> tạo thành vòng lặp vô tận (Infinite Loop) gây chết CPU và nghẽn toàn bộ luồng.
- `prefetch_count` đang bằng đúng `batch_size`. Điều này làm luồng I/O mạng bị ngắt quãng (phải xử lý xong batch mới tải batch mới). Nên đặt `prefetch_count = batch_size * 2` để RabbitMQ tự động tải sẵn batch tiếp theo xuống RAM trong lúc AI đang xử lý batch hiện tại.

**Đề xuất thay đổi:**

- Cấu hình **Dead Letter Exchange (DLX)**. Bất cứ khi nào tạo `queue_name`, ta tự động tạo thêm một queue `${queue_name}_dead_letters`.
- Thay đổi logic bắt lỗi: Nếu lỗi định dạng JSON hoặc AI sập, dùng `m.reject(requeue=False)` để tin nhắn độc hại bị "nhốt" vào khu cách ly (DLQ), không gây hại cho hệ thống chính.
- Set `prefetch_count = batch_size * 2`.

## 3. Kỹ sư Hệ thống Phân tán (Distributed Systems)

**Vấn đề:**

- **Rò rỉ tin nhắn lúc Shutdown (Graceful Shutdown):** Nếu quá trình gom batch (ví dụ đã hút được 15/32 tin nhắn) đang diễn ra mà có lệnh tắt ứng dụng (Gây ra `asyncio.CancelledError`), 15 tin nhắn này đang nằm trên RAM (Unacked). Mặc dù khi tắt hẳn, RabbitMQ sẽ trả chúng lại hàng đợi, nhưng việc để connection tự drop là không "sạch sẽ".
- Cần trả lại `requeue=True` cho các tin nhắn đang cầm trên tay một cách chủ động trước khi thoát hẳn.

**Đề xuất thay đổi:**

- Xử lý block `except asyncio.CancelledError:` bên trong lúc gom batch: chủ động lặp qua `batch_msgs` và gọi `await m.reject(requeue=True)` để trả lại an toàn trước khi `raise`.

---

> [!WARNING]
> **User Review Required**
> Thay đổi DLX sẽ tự động tạo thêm các hàng đợi có đuôi `_dead_letters` trên RabbitMQ server của bạn. Điều này là tiêu chuẩn trong thiết kế phân tán nhưng sẽ tốn thêm 1 chút xíu không gian lưu trữ cho các tin nhắn bị lỗi.
> Bạn có đồng ý với toàn bộ phương án hội chẩn trên để tôi bắt đầu viết code không?
