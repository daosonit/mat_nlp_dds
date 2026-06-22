# Hướng Dẫn Triển Khai Product (MAT Project)

Tài liệu này dành cho đội ngũ DevOps hoặc System Admin phụ trách việc đưa dự án MAT lên môi trường Production. Cấu trúc dự án đã được Dockerized hoàn chỉnh bằng `docker-compose`.

## Yêu cầu Hệ thống (Prerequisites)

- Hệ điều hành: Ubuntu 22.04 / 24.04 / 26.04 (hoặc tương đương)
- Đã cài đặt **Docker** và **Docker Compose**.
- RAM: Khuyến nghị >= 8GB (Do có AI Model và Next.js build).
- Dung lượng đĩa: Đủ lớn để lưu AI Models (~3-5GB) vào volume.

## Cấu trúc thư mục chuẩn bị

Codebase trên server cần có đầy đủ:

```
/MAT
├── AI/                 # Code AI Worker
├── API/                # Code FastAPI Backend
├── Web/                # Code Next.js Frontend
├── docker-compose.yml  # File orchestration chính
├── init-db.sql         # Script tạo extension cho Postgres
└── DEPLOYMENT_GUIDE.md # (File hướng dẫn này)
```

> **Lưu ý:** Bạn không cần phải kéo các models nặng (PhoBERT, ViSoBERT, VnCoreNLP) về bằng tay. Hệ thống sẽ **tự động tải xuống** trong lần chạy đầu tiên.

## Bước 1: Khởi tạo biến môi trường (.env)

Dự án được thiết kế theo kiến trúc Microservices độc lập. Do đó, mỗi khối (DB/RMQ, API, AI, Web) đều có riêng một file cấu hình mẫu `.env.product`.

Bạn cần copy các file mẫu này thành file `.env` tương ứng, sau đó có thể mở ra để chỉnh sửa password/IP tùy theo server thực tế:

```bash
# 1. Biến môi trường Root (dành cho cấp phát DB và RabbitMQ lúc khởi động)
cp .env.product .env

# 2. Biến môi trường cho API Backend
cp API/.env.product API/.env

# 3. Biến môi trường cho AI Worker
cp AI/.env.product AI/.env

# 4. Biến môi trường cho Web Frontend
cp Web/.env.product Web/.env
```

> **LƯU Ý QUAN TRỌNG DÀNH CHO DEVOPS:**
>
> - **Đối với Backend/AI:** Nếu bạn đổi `POSTGRES_PASSWORD` ở file `.env` root, hãy nhớ cập nhật lại chuỗi kết nối `DATABASE_URL` trong file `API/.env` và `AI/.env` cho khớp.
> - **Đối với Web Frontend (`Web/.env`):** File này chứa `NEXT_PUBLIC_API_URL`. Vì đây là URL public trả về cho trình duyệt của User gọi API, bạn **BẮT BUỘC** phải mở file `Web/.env` ra và sửa `https://api.yourdomain.com` thành Tên miền (Domain) hoặc IP Public thực tế của con Server đang chạy API Backend này. Trình duyệt client sẽ không thể truy cập nếu để sai URL.

## Bước 2: Triển khai Hệ thống

Chạy lệnh để khởi động toàn bộ Stack:

```bash
docker compose up -d --build
```

_Ghi chú: Lệnh này sẽ tự động build image cho API, Web và AI. Code của bạn được COPY trực tiếp vào Image nên sẽ độc lập hoàn toàn. Quá trình build Frontend (Next.js) có thể mất vài phút._

## Bước 3: Theo dõi quá trình tải Models (Quan trọng)

Ngay sau khi `ai_worker` khởi động, nó sẽ bắt đầu tải các thư viện NLP nặng từ HuggingFace và Facebook (FastText). Quá trình này diễn ra **trước khi** AI worker thực sự bắt đầu lắng nghe RabbitMQ.

Để theo dõi xem nó tải xong chưa, hãy xem log của `ai_worker`:

```bash
docker compose logs -f ai_worker
```

Bạn sẽ thấy output tương tự như sau:

```
=====================================
   KIỂM TRA & TẢI MÔ HÌNH AI NẶNG
=====================================
1. Đang tải VnCoreNLP...
2. Đang tải PhoBERT Sentiment Model...
Fetching 12 files: 100%|██████████| 12/12 [00:15<00:00,  1.23it/s]
3. Đang tải ViSoBERT Sentiment Model...
4. Đang tải FastText Language Detection Model...
=====================================
   TẢI MÔ HÌNH HOÀN TẤT. START WORKER
=====================================
```

Khi bạn thấy dòng `START WORKER`, hệ thống AI đã thực sự sẵn sàng!
_(Lưu ý: Các models này được lưu vào Docker Volume `ai_models_cache`. Ở các lần restart hoặc `up -d` sau, nó sẽ skip bước tải này vì file đã tồn tại)._

## Bước 4: Kiểm tra trạng thái

Kiểm tra xem tất cả containers đã "Up" chưa:

```bash
docker compose ps
```

Mở trình duyệt:

- Web Frontend: `http://<IP-SERVER>:3000`
- API Backend (Swagger UI): `http://<IP-SERVER>:8000/docs`
- RabbitMQ Management: `http://<IP-SERVER>:15672`

## Bước 5: Cập nhật (Update Code)

Khi có code mới đẩy lên Git, bạn thực hiện pull code về server và chạy lại lệnh:

```bash
docker compose up -d --build
```

Dữ liệu Postgres, RabbitMQ và kho Models AI vẫn được giữ nguyên không bị mất.

## Bước 6: Chạy AI Train (Khi cần thiết)

Do việc train model không phải là tác vụ chạy liên tục 24/7 như các Web Service thông thường, nên container `ai_train` được cấu hình ẩn dưới `profile: training`.

Khi bạn muốn chủ động chạy tiến trình Training:

```bash
docker compose --profile training up ai_train
```

Sau khi train xong, container này sẽ tự động Exit. Dữ liệu và models mới có thể được mount/sync tuỳ cấu hình.

## Bước 7: Cấu hình Server có GPU (Nvidia)

Do đặc thù dự án xử lý NLP nặng (PhoBERT, ViSoBERT), chạy trên CPU sẽ khá chậm. Nếu server của bạn có GPU Nvidia, hãy làm theo các bước sau để tăng tốc AI Worker:

1. **Cài đặt Nvidia Drivers & Docker Toolkit trên Host Server:**
   Đảm bảo server đã cài `nvidia-driver` và `nvidia-container-toolkit`.
   ```bash
   sudo apt install nvidia-driver-535 nvidia-container-toolkit
   sudo systemctl restart docker
   ```
2. **Kích hoạt GPU trong `docker-compose.yml`:**
   Mở file `docker-compose.yml`, tìm đến mục `ai_worker` và `ai_train`, **bỏ comment (uncomment)** phần cấu hình `deploy`:
   ```yaml
   deploy:
     resources:
       reservations:
         devices:
           - driver: nvidia
             count: 1
             capabilities: [gpu]
   ```
3. Khởi động lại container: `docker compose up -d --build`

---

**Troubleshooting:**

- Nếu AI Worker báo lỗi OutOfMemory (OOM) khi đang tải model hoặc load model vào RAM, hãy cân nhắc tăng RAM hoặc cấu hình Swap cho Server.
- Nếu Postgres báo lỗi thiếu quyền tạo extension `pg_trgm`, hãy đảm bảo `init-db.sql` đã chạy thành công hoặc vào trực tiếp DB để gõ `CREATE EXTENSION pg_trgm;`.
