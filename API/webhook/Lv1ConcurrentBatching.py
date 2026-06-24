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





async def trigger_single_request(client, run_idx):
    random_text = generate_random_comment()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload = {"text": random_text, "timer": current_time}
    headers = {"Authorization": f"Bearer {API_TOKEN}"}

    try:
        response = await client.post(
            PREDICT_URL, json=payload, headers=headers, timeout=15.0
        )
        response.raise_for_status()
        print(f"[#{run_idx:04d}] Thành công: {response.text}")
    except Exception as e:
        print(f"[#{run_idx:04d}] Thất bại: {e}")


async def run_load_test():
    total_requests = 1000
    batch_size = 50  # Bắn 50 luồng cùng 1 lúc để ép tải Nginx và GPU

    print(
        f"Bắt đầu Load Test: {total_requests} requests (Bắn {batch_size} luồng song song)"
    )

    # Dùng 1 Client duy nhất để tận dụng Connection Pooling (nhanh hơn rất nhiều)
    async with httpx.AsyncClient() as client:
        tasks = []
        for i in range(1, total_requests + 1):
            tasks.append(trigger_single_request(client, i))

            # Đủ 50 requests thì xả đi một lượt
            if len(tasks) >= batch_size:
                await asyncio.gather(*tasks)
                tasks = []

        # Xả nốt những requests còn dư
        if tasks:
            await asyncio.gather(*tasks)

    print("Đã hoàn tất chiến dịch Load Test 1000 requests!")


def main():
    asyncio.run(run_load_test())


if __name__ == "__main__":
    main()

"""
=============================================================================
TÀI LIỆU (DOCUMENTATION): MÔ HÌNH CONCURRENT BATCHING (GOM LÔ)
=============================================================================
Cơ chế hoạt động của Concurrent Batching:
1. Nhặt ra 50 request (kích thước batch) và nhét vào một cái "giỏ" (mảng tasks).
2. Sử dụng `asyncio.gather(*tasks)` để ném cả 50 request này lên mạng CÙNG 1 LÚC.
3. Sau đó, nó ĐỨNG CHỜ. Nó bắt buộc phải đợi đến khi cả 50 request này chạy xong 
   100% (request nào xong trước thì phải rảnh rỗi ngồi chơi).
4. Khi request cuối cùng (chậm nhất) trong lô hoàn thành, nó mới tiếp tục gom 
   50 request của lô tiếp theo và bắn đi.

Ưu điểm:
- Rất dễ hiểu, logic rõ ràng, dễ bảo trì (chỉ cần chia mảng và gather).
- Cải thiện tốc độ cực lớn so với vòng lặp `for` tuần tự truyền thống.
- Tránh được lỗi quá tải bộ nhớ RAM khi phải xử lý hàng triệu request.

Nhược điểm (Hiệu ứng Răng cưa - Sawtooth):
- Ví dụ trong 50 request có 49 cái chạy cực nhanh mất 0.1s, nhưng xui xẻo 
  có 1 cái bị kẹt mạng mất 5s.
- Lúc này, 49 cái kia sẽ phải nằm chờ đủ 5 giây để chốt sổ lô cũ thì mới được 
  khởi động lô mới. Gây ra các khoảng thời gian trễ (Bottleneck) làm lãng 
  phí tài nguyên băng thông và CPU của hệ thống đích.
- (Để khắc phục hoàn toàn nhược điểm này, trong MLOps người ta thường sử dụng 
  các kiến trúc cao cấp hơn như Semaphore hoặc Queue Worker Pool).
=============================================================================
"""
