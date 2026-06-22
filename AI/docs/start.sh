#!/bin/bash

# Đảm bảo script luôn chạy ở thư mục gốc của dự án (thư mục NLP)
cd "$(dirname "$0")/.." || exit
pip install -r requirements.txt
echo "=========================================================="
echo "BẮT ĐẦU TẢI CÁC TÀI NGUYÊN VÀ MÔ HÌNH VÀO THƯ MỤC libs/"
echo "=========================================================="

echo "[1/4] Đang tải AI tách từ tiếng Việt (VnCoreNLP)..."
python -c 'import py_vncorenlp, os; os.makedirs("./libs/vncorenlp", exist_ok=True); py_vncorenlp.download_model(save_dir="./libs/vncorenlp")'

echo ""
echo "[2/4] Đang tải AI phân tích văn bản chuẩn (PhoBERT)..."
python -c 'from huggingface_hub import snapshot_download; snapshot_download(repo_id="vinai/phobert-base-v2", local_dir="./libs/phobert_sentiment_model_final")'

echo ""
echo "[3/4] Đang tải AI phân tích Teencode mạng xã hội (ViSoBERT)..."
python -c 'from huggingface_hub import snapshot_download; snapshot_download(repo_id="uitnlp/visobert", local_dir="./libs/visobert_sentiment_model_final")'

echo ""
echo "[4/4] Đang tải AI nhận diện Tiếng Việt / Ngôn ngữ (FastText)..."
python -c 'import os, urllib.request; os.makedirs("./libs/detection/models", exist_ok=True); urllib.request.urlretrieve("https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz", "./libs/detection/models/lid.176.ftz")'

echo "=========================================================="
echo "HOÀN TẤT TẢI TOÀN BỘ TÀI NGUYÊN MODEL!"
echo "=========================================================="
