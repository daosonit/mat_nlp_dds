# Hướng Dẫn Triển Khai (Deployment Guide)

Dưới đây là các bước chi tiết để triển khai hệ thống MAT NLP DDS lên server.

## Bước 1: Clone mã nguồn từ GitHub

Tải mã nguồn dự án về máy server bằng lệnh `git clone` nhánh main:

```bash
git clone https://github.com/daosonit/mat_nlp_dds
```

Di chuyển vào thư mục dự án vừa tải về:

```bash
cd mat_nlp_dds
```

## Bước 2: Cấu hình tên miền (Domain)

Bạn cần mở và chỉnh sửa lại tên miền (domain) của bạn trong các file cấu hình môi trường của phần Web:

- `Web/.env.product`
- `Web/.env`

_Lưu ý: Hãy thay thế các giá trị host/domain mặc định trong file bằng domain thực tế mà server bạn đang sử dụng._

## Bước 3: Khởi chạy hệ thống bằng Docker Compose

Sau khi đã cấu hình xong tên miền, bạn tiến hành build và khởi động toàn bộ hệ thống (Web, API, DB, RabbitMQ...) bằng lệnh sau:

```bash
docker compose up -d --build
```

_Vui lòng chờ một vài phút để Docker tiến hành tải các images, cài đặt thư viện và khởi động các container._

## Bước 4: Chạy quá trình huấn luyện AI (Training)

Quá trình huấn luyện mô hình được cấu hình chạy riêng lẻ khi cần thiết. Khi toàn bộ hệ thống đã khởi động xong, bạn có thể chạy tiến trình train bằng lệnh:

```bash
docker compose --profile training up ai_train
```

_Tiến trình này sẽ chạy các script huấn luyện bên trong container `ai_train`. Khi quá trình huấn luyện hoàn tất, container này sẽ tự động dừng._

## Bước 5: Kiểm tra kết quả

Sau khi quá trình huấn luyện hoàn tất, để kiểm tra các kết quả train hoặc log của hệ thống, bạn cần truy cập trực tiếp vào Database hoặc RabbitMQ.

Bạn có thể xem các thông tin đăng nhập, cổng (port) kết nối của Database và RabbitMQ tại file cấu hình ở thư mục gốc:

- `.env.product`
