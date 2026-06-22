#!/bin/bash
set -e

echo "====================================="
echo "   KIỂM TRA & TẢI MÔ HÌNH AI NẶNG"
echo "====================================="

# Cài thư viện huggingface_hub nếu chưa có
pip install --no-cache-dir huggingface_hub py_vncorenlp

echo "1. Đang tải VnCoreNLP..."
python -c 'import py_vncorenlp, os; os.makedirs("./ai_models/vncorenlp", exist_ok=True); py_vncorenlp.download_model(save_dir="./ai_models/vncorenlp")'

echo "2. Đang tải PhoBERT Sentiment Model..."
python -c 'from huggingface_hub import snapshot_download; snapshot_download(repo_id="vinai/phobert-base-v2", local_dir="./ai_models/phobert_sentiment_model_final")'

echo "3. Đang tải ViSoBERT Sentiment Model..."
python -c 'from huggingface_hub import snapshot_download; snapshot_download(repo_id="uitnlp/visobert", local_dir="./ai_models/visobert_sentiment_model_final")'

echo "4. Đang tải FastText Language Detection Model..."
python -c 'import os, urllib.request; os.makedirs("./ai_models/detection_models", exist_ok=True); file_path="./ai_models/detection_models/lid.176.ftz"; urllib.request.urlretrieve("https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz", file_path) if not os.path.exists(file_path) else None'

echo "====================================="
echo "   TẢI MÔ HÌNH HOÀN TẤT. START WORKER"
echo "====================================="

# Thực thi lệnh chính của container (CMD)
exec "$@"
