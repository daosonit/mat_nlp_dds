HƯỚNG DẪN TRIỂN KHAI (DEPLOYMENT GUIDE)

Dưới đây là các bước chi tiết để triển khai hệ thống MAT NLP DDS lên server.

BƯỚC 1: CLONE MÃ NGUỒN

- Tải mã nguồn từ GitHub (nhánh main):
  git clone https://github.com/daosonit/mat_nlp_dds
- Di chuyển vào thư mục dự án:
  cd mat_nlp_dds

BƯỚC 2: CẤU HÌNH TÊN MIỀN (DOMAIN)

- Bạn cần mở và chỉnh sửa lại tên miền của mình trong các file cấu hình môi trường của phần Web:
  - Web/.env.product
  - Web/.env
- Lưu ý: Thay thế các giá trị host/domain mặc định bằng domain thực tế đang dùng trên server.

BƯỚC 3: KHỞI CHẠY HỆ THỐNG

- Khi đã cấu hình xong, tiến hành khởi động toàn bộ hệ thống bằng lệnh:
  docker compose up -d --build
- LƯU Ý QUAN TRỌNG: Quá trình cài đặt lần đầu sẽ tốn khá nhiều thời gian. Hệ thống cần tải các thư viện và mô hình AI (PhoBERT, ViSoBERT, FastText, VnCoreNLP) nặng khoảng 2GB vào các thư mục:
  - /libs/detection/models
  - /libs/phobert_sentiment_model_final
  - /libs/visobert_sentiment_model_final
  - /libs/vncorenlp
- Bạn phải đợi cho đến khi toàn bộ các thư mục này được tải xong (container api và ai_worker chạy ổn định) thì mới có thể thực hiện bước tiếp theo.

BƯỚC 4: HUẤN LUYỆN AI (TRAINING)

- Quá trình huấn luyện được cấu hình chạy riêng lẻ. Chỉ khi nào Bước 3 đã hoàn tất 100% (tải xong các model), bạn mới chạy lệnh sau để bắt đầu train:
  docker compose --profile training up ai_train
- Tiến trình này sẽ chạy các script huấn luyện bên trong container ai_train, và sẽ tự động dừng lại khi hoàn tất.

BƯỚC 5: KIỂM TRA KẾT QUẢ

- Sau khi huấn luyện hoàn tất, bạn có thể kiểm tra kết quả hoặc log hệ thống bằng cách truy cập trực tiếp vào Database hoặc RabbitMQ.
- Thông tin đăng nhập và cổng kết nối của DB/RabbitMQ nằm tại file cấu hình gốc:
  - .env.product
