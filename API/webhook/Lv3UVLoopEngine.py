#!/usr/bin/env python3
import os
import sys
import json
import random
import httpx
import asyncio
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from dotenv import load_dotenv
from ultils import generate_random_comment

#  THÊM ĐỘNG CƠ C++
import uvloop

load_dotenv()

PREDICT_URL = os.getenv("PREDICT_URL", "http://192.168.1.99:8000/predict")
API_TOKEN = os.getenv(
    "API_TOKEN",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc4Mjg5MTYyN30.2jESTdblm481_w9TACwdE8xMgFFRw9nw-24Vj6zMnVY",
)


async def worker(client, queue, headers, stats):
    """Mỗi worker lấy việc từ Queue ra làm liên tục"""
    while True:
        try:
            queue.get_nowait()
        except asyncio.QueueEmpty:
            break

        random_text = generate_random_comment()
        payload = {
            "text": random_text,
            "timer": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        try:
            response = await client.post(
                PREDICT_URL, json=payload, headers=headers, timeout=15.0
            )
            response.raise_for_status()
            stats["success"] += 1
        except Exception:
            stats["fail"] += 1

        queue.task_done()


async def async_process_runner(num_requests, process_id):
    """Hàm quản lý Event Loop cho từng Process riêng biệt"""
    queue = asyncio.Queue()

    for i in range(num_requests):
        queue.put_nowait(i)

    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    stats = {"success": 0, "fail": 0}

    # Giữ 50 luồng mạng cho mỗi Lõi CPU
    num_async_workers = 50

    async with httpx.AsyncClient() as client:
        workers = []
        for _ in range(num_async_workers):
            task = asyncio.create_task(worker(client, queue, headers, stats))
            workers.append(task)

        await asyncio.gather(*workers)

    return stats


def process_entry_point(num_requests, process_id):
    """Điểm mồi để chạy Asyncio bên trong Multiprocessing"""

    #  KÍCH HOẠT CẢNH GIỚI 1: THAY THẾ LÕI PYTHON BẰNG LÕI C++ UVLOOP
    # Phải gọi lệnh này TRƯỚC KHI tạo event loop trong process này!
    uvloop.install()

    print(
        f"[Core #{process_id}] Khởi động động cơ UVLoop (C++). Đang xử lý {num_requests} requests..."
    )
    return asyncio.run(async_process_runner(num_requests, process_id))


def run_ultimate_uvloop_test():
    total_requests = 100000
    num_cores = multiprocessing.cpu_count()

    print("=" * 60)
    print(f" KÍCH HOẠT CẢNH GIỚI 1: MULTIPROCESSING + ĐỘNG CƠ C++ (UVLOOP) ")
    print(f"Tổng số requests: {total_requests}")
    print(f"Lõi xử lý: {num_cores} Cores (Full sức mạnh máy Mac)")
    print("=" * 60)

    requests_per_core = total_requests // num_cores
    chunks = [requests_per_core] * num_cores
    chunks[-1] += total_requests % num_cores

    start_time = datetime.now()
    total_success = 0
    total_fail = 0

    with ProcessPoolExecutor(max_workers=num_cores) as executor:
        futures = []
        for i, chunk in enumerate(chunks):
            futures.append(executor.submit(process_entry_point, chunk, i))

        for future in futures:
            result = future.result()
            total_success += result["success"]
            total_fail += result["fail"]

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    rps = total_requests / duration if duration > 0 else 0

    print("\n" + "=" * 50)
    print(" ĐÃ HOÀN TẤT CHIẾN DỊCH TẤN CÔNG 1 TRIỆU REQUESTS BẰNG UVLOOP!")
    print(f" Thời gian tổng: {duration:.2f} giây")
    print(f" Tốc độ (RPS): {rps:.2f} requests / giây")
    print(f" Thành công: {total_success} |  Thất bại: {total_fail}")
    print("=" * 50)


if __name__ == "__main__":
    run_ultimate_uvloop_test()

"""
=============================================================================
TÀI LIỆU (DOCUMENTATION): CẢNH GIỚI 1 - ĐỘNG CƠ C++ (UVLOOP)
=============================================================================
Nguyên lý nâng cấp tốc độ:
Mặc định, thư viện `asyncio` của Python được viết bằng chính ngôn ngữ Python (thuần).
Nó giống như việc bạn lái một chiếc ô tô với động cơ phân khối nhỏ.

Bằng cách cài đặt thư viện `uvloop` và gán lệnh `uvloop.install()` vào ngay đầu 
mỗi tiến trình (process), ta đã tháo cái động cơ cũ của Python ra và lắp vào 
đó một "động cơ phản lực" được viết 100% bằng ngôn ngữ C/C++ (cùng công nghệ 
lõi với NodeJS).

Kết hợp với Multiprocessing (chia đều việc cho toàn bộ các lõi CPU của Mac),
kiến trúc này mang lại tốc độ I/O mạng (Network I/O) nhanh gấp 2 đến 4 lần 
so với Python mặc định. Đây chính là công thức "Tuyệt kỹ" tối đa nhất mà 
bạn có thể ép xung được bằng ngôn ngữ Python!
=============================================================================
"""
