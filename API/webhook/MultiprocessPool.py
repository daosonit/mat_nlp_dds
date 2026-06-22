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

load_dotenv()

N8N_WEBHOOK_URL = os.getenv(
    "N8N_WEBHOOK_URL", "http://192.168.1.99:56781/webhook/test1"
)
N8N_API_KEY = os.getenv("N8N_API_KEY", "matgroup_n8n_secret_2026")


def load_comments():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, "million_car_comments.json")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return ["Lỗi dữ liệu"]


async def worker(client, queue, headers, comments, stats):
    """Worker bất đồng bộ chạy bên trong từng Process"""
    while True:
        try:
            queue.get_nowait()
        except asyncio.QueueEmpty:
            break

        random_text = random.choice(comments)
        payload = {
            "text": random_text,
            "timer": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        try:
            response = await client.post(
                N8N_WEBHOOK_URL, json=payload, headers=headers, timeout=15.0
            )
            response.raise_for_status()
            stats["success"] += 1
        except Exception:
            stats["fail"] += 1

        queue.task_done()


async def async_process_runner(num_requests, process_id):
    """Hàm quản lý Event Loop cho từng Process riêng biệt"""
    comments = load_comments()
    queue = asyncio.Queue()

    for i in range(num_requests):
        queue.put_nowait(i)

    headers = {"Authorization": f"Bearer {N8N_API_KEY}"}
    stats = {"success": 0, "fail": 0}

    # Mỗi process chạy 50 công nhân (worker)
    num_async_workers = 50

    async with httpx.AsyncClient() as client:
        workers = []
        for _ in range(num_async_workers):
            task = asyncio.create_task(worker(client, queue, headers, comments, stats))
            workers.append(task)

        await asyncio.gather(*workers)

    return stats


def process_entry_point(num_requests, process_id):
    """Điểm mồi để chạy Asyncio bên trong Multiprocessing"""
    print(f"[Process #{process_id}] Đang gánh {num_requests} requests...")
    # Mỗi process tự khởi tạo một Event Loop riêng của nó, né hoàn toàn GIL
    return asyncio.run(async_process_runner(num_requests, process_id))


def run_ultimate_load_test():
    total_requests = 1000000
    num_cores = multiprocessing.cpu_count()

    print("=" * 60)
    print(f" KÍCH HOẠT MÔ HÌNH TỐI THƯỢNG: MULTIPROCESSING + ASYNCIO ")
    print(f"Tổng số requests: {total_requests}")
    print(f"Sử dụng toàn bộ sức mạnh CPU: {num_cores} Lõi (Cores)")
    print("=" * 60)

    # Chia đều công việc cho các lõi CPU
    requests_per_core = total_requests // num_cores
    chunks = [requests_per_core] * num_cores

    # Cộng dồn số lẻ vào lõi cuối cùng
    chunks[-1] += total_requests % num_cores

    start_time = datetime.now()

    # Kích hoạt toàn bộ các lõi CPU cùng chạy
    total_success = 0
    total_fail = 0

    with ProcessPoolExecutor(max_workers=num_cores) as executor:
        # Giao việc cho các lõi
        futures = []
        for i, chunk in enumerate(chunks):
            futures.append(executor.submit(process_entry_point, chunk, i))

        # Thu thập kết quả từ các lõi
        for future in futures:
            result = future.result()
            total_success += result["success"]
            total_fail += result["fail"]

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    rps = total_requests / duration if duration > 0 else 0

    print("\n" + "=" * 50)
    print(" ĐÃ HOÀN TẤT CHIẾN DỊCH TẤN CÔNG 1 TRIỆU REQUESTS!")
    print(f" Thời gian tổng: {duration:.2f} giây")
    print(f" Tốc độ (RPS): {rps:.2f} requests / giây")
    print(f" Thành công: {total_success} |  Thất bại: {total_fail}")
    print("=" * 50)


if __name__ == "__main__":
    run_ultimate_load_test()

"""
=============================================================================
TÀI LIỆU (DOCUMENTATION): MÔ HÌNH MULTIPROCESSING + ASYNCIO
=============================================================================
Vấn đề lớn nhất của Python (Cơ chế GIL):
Dù bạn dùng bao nhiêu luồng `asyncio` hay Worker Pool đi nữa, Python mặc định 
chỉ cho phép chương trình chạy trên ĐÚNG 1 LÕI (CORE) CPU duy nhất do vướng 
phải một bức tường gọi là GIL (Global Interpreter Lock). 
Ví dụ: Nếu máy Mac có 8 Lõi CPU, thì 7 Lõi còn lại sẽ ngồi chơi xơi nước 
trong khi 1 Lõi đang gánh còng lưng toàn bộ 1 triệu requests!

Cách mô hình MultiprocessPool.py (Tối thượng) giải quyết:
1. Đếm xem máy của bạn có bao nhiêu lõi CPU (ví dụ: 8 Lõi).
2. Chặt 1 triệu requests ra làm các phần bằng nhau (Mỗi phần 125,000 requests).
3. "Phân thân" ra làm 8 chương trình Python (Process) chạy hoàn toàn độc lập. 
   Mỗi chương trình độc chiếm 1 lõi CPU, và tự khởi tạo một đội Worker Pool 
   (Asyncio) siêu tốc riêng của nó.
4. Cuối cùng, thu thập và cộng dồn báo cáo tổng từ cả 8 lõi CPU trả về.

=> Kết quả: Phá vỡ hoàn toàn giới hạn GIL, huy động 100% toàn bộ sức mạnh phần 
cứng của chiếc máy Mac. Đây chính là giới hạn vật lý tối đa của ngôn ngữ 
Python trong việc thiết kế công cụ bắn Load Testing.
=============================================================================
"""
