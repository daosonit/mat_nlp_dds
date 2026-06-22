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


async def trigger_single_request(client, semaphore, headers, comments, run_idx):
    # Xin phép Semaphore trước khi chạy. Nếu đã đủ 50 luồng thì phải xếp hàng chờ.
    async with semaphore:
        random_text = random.choice(comments)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload = {"text": random_text, "timer": current_time}

        try:
            response = await client.post(
                N8N_WEBHOOK_URL, json=payload, headers=headers, timeout=15.0
            )
            response.raise_for_status()
            print(f"[#{run_idx:04d}] Thành công: {response.text}")
        except Exception as e:
            print(f"[#{run_idx:04d}] Thất bại: {e}")


async def run_load_test():
    comments = load_comments()
    total_requests = 1000000
    concurrency_limit = 100  # Luôn giữ đúng 100 kết nối chạy song song

    print(
        f"Bắt đầu Load Test: {total_requests} requests (Duy trì mượt mà {concurrency_limit} luồng song song)"
    )

    # Khởi tạo Semaphore và Headers 1 lần duy nhất để tối ưu RAM
    semaphore = asyncio.Semaphore(concurrency_limit)
    headers = {"Authorization": f"Bearer {N8N_API_KEY}"}

    # Dùng 1 Client duy nhất để tận dụng Connection Pooling
    async with httpx.AsyncClient() as client:
        tasks = []
        for i in range(1, total_requests + 1):
            tasks.append(
                trigger_single_request(client, semaphore, headers, comments, i)
            )

        # Kích hoạt toàn bộ mảng. Semaphore sẽ làm nhiệm vụ điều phối luồng xe!
        await asyncio.gather(*tasks)

    print("Đã hoàn tất chiến dịch Load Test 1000 requests!")


def main():
    asyncio.run(run_load_test())


if __name__ == "__main__":
    main()

"""
=============================================================================
TÀI LIỆU (DOCUMENTATION): MÔ HÌNH SEMAPHORE (SLIDING WINDOW CONCURRENCY)
=============================================================================
Vấn đề của mô hình Concurrent Batching (Gom lô chờ đợi):
Nếu dùng Batching (ví dụ cắt khúc 100 request một lô), hệ thống sẽ gặp hiện 
tượng hiệu năng hình "Răng cưa" (Sawtooth). Nghĩa là nó phải đợi toàn bộ 100 
request chạy xong 100% thì mới được nạp lô tiếp theo. Kể cả khi 99 cái đã xong 
nhưng bị kẹt 1 cái mạng lag, thì toàn bộ hệ thống vẫn phải đứng chờ, gây lãng 
phí tài nguyên băng thông và CPU.

Cách mô hình SemaphoreConcurrency.py giải quyết:
1. Tạo một cái "Van điều áp" (asyncio.Semaphore) với giới hạn kích thước là 
   100 luồng chạy song song.
2. Nó tung toàn bộ các request vào mạng cùng một lúc (bằng gather), nhưng 
   Semaphore sẽ làm nhiệm vụ bảo vệ cổng (Gatekeeper).
3. Tại bất kỳ thời điểm nào, Semaphore chỉ cho phép đúng 100 luồng đi qua. 
   Ngay khi có 1 luồng xử lý xong và quay về, Semaphore lập tức mở rào cho 
   luồng thứ 101 đi vào lấp đầy chỗ trống.

=> Kết quả: Biểu đồ chịu tải (Load Profile) đi ngang một đường thẳng tắp và 
mượt mà (Sliding Window). Lúc nào hệ thống đích cũng phải gồng 
gánh với 100% công suất liên tục mà không có bất kỳ khoảng thời gian "chết" 
nào như mô hình Batching.
=============================================================================
"""
