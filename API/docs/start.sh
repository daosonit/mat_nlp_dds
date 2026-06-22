#!/bin/bash

# Đảm bảo script luôn chạy ở thư mục gốc của dự án (thư mục NLP)
cd "$(dirname "$0")/.." || exit
pip install -r requirements.txt
echo "=========================================================="
echo "BẮT ĐẦU TẢI CÁC TÀI NGUYÊN VÀ MÔ HÌNH VÀO THƯ MỤC libs/"
echo "=========================================================="
echo " Đang tải AI nhận diện Tiếng Việt / Ngôn ngữ (FastText)..."
python -c 'import os, urllib.request; os.makedirs("./libs/detection/models", exist_ok=True); urllib.request.urlretrieve("https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz", "./libs/detection/models/lid.176.ftz")'

echo "=========================================================="
echo "HOÀN TẤT TẢI TOÀN BỘ TÀI NGUYÊN MODEL!"
echo "=========================================================="
