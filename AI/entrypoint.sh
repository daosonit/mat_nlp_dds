#!/bin/bash
set -e

# Khai báo biến môi trường thư mục chứa model, mặc định là ./ai_models
# Bạn có thể đổi thư mục bằng cách truyền ENV: AI_MODELS_DIR=/thu/muc/khac
AI_MODELS_DIR="${AI_MODELS_DIR:-./ai_models}"

echo "====================================="
echo "   KIỂM TRA TÀI NGUYÊN AI MÔ HÌNH"
echo "====================================="

# Cài thư viện ngầm nếu chưa có
pip install --no-cache-dir huggingface_hub py_vncorenlp protobuf >/dev/null 2>&1

python -c "
import py_vncorenlp, os
save_dir = '${AI_MODELS_DIR}/vncorenlp'
target = os.path.join(save_dir, 'models', 'wordsegmenter', 'wordsegmenter.rdr')
if not os.path.exists(target):
    print('1. Đang tải VnCoreNLP vào ${AI_MODELS_DIR}...')
    os.makedirs(save_dir, exist_ok=True)
    try:
        py_vncorenlp.download_model(save_dir=save_dir)
    except FileExistsError:
        pass
else:
    print('1. VnCoreNLP đã tồn tại trong cache, bỏ qua tải.')
"

python -c "
import os
from huggingface_hub import snapshot_download
target = '${AI_MODELS_DIR}/phobert_sentiment_model_final'
if not os.path.exists(target):
    print('2. Đang tải PhoBERT Sentiment Model vào ${AI_MODELS_DIR}...')
    snapshot_download(repo_id='vinai/phobert-base-v2', local_dir=target)
else:
    print('2. PhoBERT Sentiment Model đã tồn tại trong cache, bỏ qua tải.')
"

python -c "
import os
from huggingface_hub import snapshot_download
target = '${AI_MODELS_DIR}/visobert_sentiment_model_final'
if not os.path.exists(target):
    print('3. Đang tải ViSoBERT Sentiment Model vào ${AI_MODELS_DIR}...')
    snapshot_download(repo_id='uitnlp/visobert', local_dir=target)
else:
    print('3. ViSoBERT Sentiment Model đã tồn tại trong cache, bỏ qua tải.')
"

python -c "
import os, urllib.request
file_path = '${AI_MODELS_DIR}/detection_models/lid.176.ftz'
if not os.path.exists(file_path):
    print('4. Đang tải FastText Language Detection Model vào ${AI_MODELS_DIR}...')
    os.makedirs('${AI_MODELS_DIR}/detection_models', exist_ok=True)
    urllib.request.urlretrieve('https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz', file_path)
else:
    print('4. FastText Model đã tồn tại trong cache, bỏ qua tải.')
"

echo "====================================="
echo "   SẴN SÀNG KHỞI ĐỘNG HỆ THỐNG!"
echo "====================================="

# Thực thi lệnh chính của container (CMD)
exec "$@"
