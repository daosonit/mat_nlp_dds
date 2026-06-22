#!/bin/bash
set -e

# Khai báo biến môi trường thư mục chứa model, mặc định là ./ai_models
# Bạn có thể đổi thư mục bằng cách truyền ENV: AI_MODELS_DIR=/thu/muc/khac
AI_MODELS_DIR="${AI_MODELS_DIR:-./ai_models}"

echo "====================================="
echo "   KIỂM TRA & TẢI MÔ HÌNH AI NẶNG"
echo "====================================="

# Cài thư viện huggingface_hub nếu chưa có
pip install --no-cache-dir huggingface_hub py_vncorenlp

echo "Cài đặt protobuf (nếu thiếu)..."
pip install protobuf

echo "1. Đang tải VnCoreNLP vào ${AI_MODELS_DIR}..."
python -c "
import py_vncorenlp, os
save_dir = '${AI_MODELS_DIR}/vncorenlp'
target = os.path.join(save_dir, 'models', 'wordsegmenter', 'wordsegmenter.rdr')
if not os.path.exists(target):
    os.makedirs(save_dir, exist_ok=True)
    try:
        py_vncorenlp.download_model(save_dir=save_dir)
    except FileExistsError:
        pass
"

echo "2. Đang tải PhoBERT Sentiment Model vào ${AI_MODELS_DIR}..."
python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='vinai/phobert-base-v2', local_dir='${AI_MODELS_DIR}/phobert_sentiment_model_final')"

echo "3. Đang tải ViSoBERT Sentiment Model vào ${AI_MODELS_DIR}..."
python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='uitnlp/visobert', local_dir='${AI_MODELS_DIR}/visobert_sentiment_model_final')"

echo "4. Đang tải FastText Language Detection Model vào ${AI_MODELS_DIR}..."
python -c "import os, urllib.request; os.makedirs('${AI_MODELS_DIR}/detection_models', exist_ok=True); file_path='${AI_MODELS_DIR}/detection_models/lid.176.ftz'; urllib.request.urlretrieve('https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz', file_path) if not os.path.exists(file_path) else None"

echo "====================================="
echo "   TẢI MÔ HÌNH HOÀN TẤT. START WORKER"
echo "====================================="

# Thực thi lệnh chính của container (CMD)
exec "$@"
