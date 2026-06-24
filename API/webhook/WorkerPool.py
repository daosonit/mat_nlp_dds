#!/usr/bin/env python3
import os
import sys
import json
import random
import httpx
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from ultils import generate_random_comment

load_dotenv()

PREDICT_URL = os.getenv("PREDICT_URL", "http://192.168.1.99:8000/predict")
API_TOKEN = os.getenv(
    "API_TOKEN",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc4Mjg5MTYyN30.2jESTdblm481_w9TACwdE8xMgFFRw9nw-24Vj6zMnVY",
)


async def worker(client, queue, headers, worker_id, stats):
    """Mỗi worker là 1 công nhân chuyên lấy việc từ Queue ra làm liên tục"""
    while True:
        try:
            run_idx = queue.get_nowait()
        except asyncio.QueueEmpty:
            break  # Hết việc thì công nhân nghỉ

        random_text = generate_random_comment()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload = {"text": random_text, "timer": current_time}

        try:
            response = await client.post(
                PREDICT_URL, json=payload, headers=headers, timeout=15.0
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
    total_requests = 1000000
    num_workers = 150  # 150 công nhân chạy song song (Tối ưu nhất cho Python)

    print(
        f"Bắt đầu Load Test siêu tốc: {total_requests} requests bằng WORKER POOL ({num_workers} công nhân)"
    )

    queue = asyncio.Queue()
    # Thả 1 triệu mã ID công việc vào Queue
    for i in range(1, total_requests + 1):
        queue.put_nowait(i)

    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    stats = {"success": 0, "fail": 0, "total": total_requests}

    # Bắt đầu tính giờ
    start_time = datetime.now()

    async with httpx.AsyncClient() as client:
        # Khởi tạo 150 công nhân
        workers = []
        for i in range(num_workers):
            task = asyncio.create_task(worker(client, queue, headers, i, stats))
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
