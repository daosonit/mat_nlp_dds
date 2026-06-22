#!/bin/bash
set -e

echo "=========================================================="
echo "BẮT ĐẦU TẢI CÁC TÀI NGUYÊN VÀ MÔ HÌNH"
echo "=========================================================="

MODEL_DIR="./libs/detection/models"
MODEL_FILE="${MODEL_DIR}/lid.176.ftz"

echo "Đang tải AI nhận diện Tiếng Việt / Ngôn ngữ (FastText)..."
python -c "import os, urllib.request; \
os.makedirs('${MODEL_DIR}', exist_ok=True); \
urllib.request.urlretrieve('https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz', '${MODEL_FILE}') if not os.path.exists('${MODEL_FILE}') else print('Model đã tồn tại, bỏ qua tải xuống.')"

echo "=========================================================="
echo "HOÀN TẤT TẢI TOÀN BỘ TÀI NGUYÊN MODEL!"
echo "=========================================================="

# Thực thi lệnh chính (CMD)
exec "$@"
