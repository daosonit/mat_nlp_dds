#!/usr/bin/env python3
import os
import sys
import json
import random
import httpx
import asyncio
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

N8N_WEBHOOK_URL = os.getenv(
    "N8N_WEBHOOK_URL", "http://192.168.1.99:56781/webhook/test1"
)
N8N_API_KEY = os.getenv("N8N_API_KEY", "matgroup_n8n_secret_2026")


def load_comments():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, "million_car_comments.json")
    try:
        print("Đang nạp file 52MB vào RAM, vui lòng đợi 1 chút...")
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Lỗi đọc file dữ liệu: {e}")
        return ["Lỗi không đọc được dữ liệu mock"]


async def worker(client, queue, headers, comments, worker_id, stats):
    """Mỗi worker là 1 công nhân chuyên lấy việc từ Queue ra làm liên tục"""
    while True:
        try:
            run_idx = queue.get_nowait()
        except asyncio.QueueEmpty:
            break  # Hết việc thì công nhân nghỉ

        random_text = random.choice(comments)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload = {"text": random_text, "timer": current_time}

        try:
            response = await client.post(
                N8N_WEBHOOK_URL, json=payload, headers=headers, timeout=15.0
            )
            response.raise_for_status()
            stats["success"] += 1
        except Exception:
            stats["fail"] += 1

        queue.task_done()

        # In log định kỳ để Terminal không bị lag rụng rời
        total_done = stats["success"] + stats["fail"]
        if total_done % 5000 == 0:
            print(
                f"Tiến độ: {total_done} / {stats['total']} (Thành công: {stats['success']}, Lỗi: {stats['fail']})"
            )


async def run_load_test():
    comments = load_comments()
    total_requests = 1000000
    num_workers = 150  # 150 công nhân chạy song song (Tối ưu nhất cho Python)

    print(
        f"Bắt đầu Load Test siêu tốc: {total_requests} requests bằng WORKER POOL ({num_workers} công nhân)"
    )

    queue = asyncio.Queue()
    # Thả 1 triệu mã ID công việc vào Queue
    for i in range(1, total_requests + 1):
        queue.put_nowait(i)

    headers = {"Authorization": f"Bearer {N8N_API_KEY}"}
    stats = {"success": 0, "fail": 0, "total": total_requests}

    # Bắt đầu tính giờ
    start_time = datetime.now()

    async with httpx.AsyncClient() as client:
        # Khởi tạo 150 công nhân
        workers = []
        for i in range(num_workers):
            task = asyncio.create_task(
                worker(client, queue, headers, comments, i, stats)
            )
            workers.append(task)

        # Chờ cả 150 công nhân làm xong hết Queue
        await asyncio.gather(*workers)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    rps = total_requests / duration if duration > 0 else 0

    print("=" * 50)
    print("ĐÃ HOÀN TẤT CHIẾN DỊCH 1 TRIỆU REQUESTS!")
    print(f"Thời gian tổng: {duration:.2f} giây")
    print(f"Tốc độ (RPS): {rps:.2f} requests / giây")
    print(f"Thành công: {stats['success']} | Thất bại: {stats['fail']}")
    print("=" * 50)


def main():
    asyncio.run(run_load_test())


if __name__ == "__main__":
    main()

"""
=============================================================================
TÀI LIỆU (DOCUMENTATION): MÔ HÌNH WORKER POOL (PRODUCER - CONSUMER)
=============================================================================
Vấn đề của việc tạo quá nhiều Coroutine cùng lúc:
Nếu dùng `asyncio.gather()` cho 1 triệu request, Python sẽ phải cấp phát và 
khởi tạo sẵn 1 triệu Coroutine (Tác vụ) ngay lập tức trên bộ nhớ RAM. 
Việc này gây ra tình trạng "tràn RAM" hoặc "hết bộ nhớ" và làm Event Loop 
bị quá tải (Overhead) trước cả khi gửi request mạng.

Cách mô hình WorkerPool.py giải quyết:
1. Tạo một cái "Rổ chứa việc" (asyncio.Queue). Rổ này cực kỳ nhẹ, chứa 1 triệu 
   mã ID công việc (số nguyên) hầu như không tốn RAM.
2. Thay vì tạo 1 triệu Coroutine, hệ thống chỉ tuyển đúng 150 "công nhân" 
   (Worker Coroutines) chạy song song.
3. 150 công nhân này sẽ chạy trong một vòng lặp vô tận (while True), liên tục 
   thò tay vào Queue bốc việc ra làm. Làm xong lại bốc việc mới cho đến khi 
   nào rổ trống rỗng thì thôi.

=> Kết quả: Tối ưu hoá tuyệt đối mức tiêu thụ RAM và CPU của Python ở môi trường 
đơn lõi (Single-core Asyncio). Tránh hoàn toàn lỗi OOM (Out Of Memory).
Đây là kiến trúc tiêu chuẩn (Best Practice) cho các hệ thống MLOps/Backend 
cần cày cuốc hàng triệu bản ghi I/O.
=============================================================================
"""
