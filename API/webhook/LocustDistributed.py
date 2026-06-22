import os
import json
import random
from datetime import datetime
from locust import FastHttpUser, task, between
from dotenv import load_dotenv

load_dotenv()

N8N_WEBHOOK_URL = os.getenv(
    "N8N_WEBHOOK_URL", "http://192.168.1.99:56781/webhook/test1"
)
N8N_API_KEY = os.getenv("N8N_API_KEY", "matgroup_n8n_secret_2026")


# Nạp dữ liệu 1 lần duy nhất ở cấp độ Module (Biến Toàn Cục)
# Việc này đảm bảo kể cả khi có 10,000 user sinh ra, file 52MB vẫn chỉ đọc 1 lần!
def load_comments():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, "million_car_comments.json")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return ["Lỗi dữ liệu mock"]


print("Đang nạp dữ liệu Mock 52MB vào RAM cho Cảnh giới 2...")
COMMENTS_DATA = load_comments()


class N8NLoadTester(FastHttpUser):
    # FastHttpUser sử dụng động cơ geventhttpclient (viết bằng C) nhanh gấp 5 lần HttpUser bình thường

    # Thời gian nghỉ giữa các lần nã đạn của 1 user
    # (Để 0 giây nghĩa là 1 user bắn xong phát này sẽ bóp cò phát tiếp theo ngay lập tức)
    wait_time = between(0.0, 0.0)

    @task
    def shoot_webhook(self):
        random_text = random.choice(COMMENTS_DATA)
        payload = {
            "text": random_text,
            "timer": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        headers = {"Authorization": f"Bearer {N8N_API_KEY}"}

        # FastHttpUser tự động gom connection pool và xử lý cực nhanh
        with self.client.post(
            N8N_WEBHOOK_URL,
            json=payload,
            headers=headers,
            timeout=15.0,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Lỗi {response.status_code}")


"""
=============================================================================
TÀI LIỆU (DOCUMENTATION): CẢNH GIỚI 2 - TẤN CÔNG PHÂN TÁN (LOCUST)
=============================================================================
Nguyên lý: 
Vượt qua sự bó hẹp của lập trình tuyến tính. Locust cho phép bạn tạo ra một 
quân đoàn User ảo (Virtual Users). Bạn có thể dễ dàng ra lệnh đẻ ra 10,000 
user cùng một lúc để "cắn xé" server. Locust sử dụng công nghệ Greenlets 
(Siêu luồng) để có thể chịu được lượng user ảo khổng lồ này mà không tràn RAM.

CÁCH KHỞI ĐỘNG CẢNH GIỚI 2:
Mô hình này KHÔNG chạy bằng lệnh `python3` thông thường!

CÁCH 1 (Chạy có giao diện Dashboard siêu đẹp):
Mở Terminal và gõ lệnh sau để mở Trạm Chỉ Huy:
    locust -f Api/webhook/LocustDistributed.py

Sau đó, mở trình duyệt web và truy cập vào: http://localhost:8089
Tại giao diện Web, bạn có thể nhập số lượng Người dùng (Users) và Tốc độ đẻ 
user (Spawn rate). Locust sẽ vẽ biểu đồ trực tiếp (Real-time) rất chuyên nghiệp 
để bạn theo dõi Server n8n đang giãy giụa như thế nào.

CÁCH 2 (Chạy ngầm dòng lệnh - Chuyên dùng cho máy chủ rảnh rỗi):
Để nã 1 triệu requests không cần giao diện, gõ lệnh:
    locust -f Api/webhook/LocustDistributed.py --headless -u 1000 -r 100 -n 1000000

(-u 1000: 1000 users ảo | -r 100: sinh ra 100 user/giây | -n: tổng số request)

CÁCH 3 (Phân tán nhiều máy - Distributed Mode):
Dùng máy Mac làm Tướng: `locust -f Api/webhook/LocustDistributed.py --master`
Dùng các Laptop khác trong công ty làm Lính: `locust -f Api/webhook/LocustDistributed.py --worker --master-host=<IP_Máy_Mac>`
Lúc này 10 chiếc Laptop sẽ cùng hợp lực xả đạn vào Server. Giới hạn duy nhất 
lúc này là ... gói cước cáp quang nhà bạn!
=============================================================================
"""
