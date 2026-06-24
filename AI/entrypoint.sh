#!/bin/bash
set -e

echo "====================================="
echo "   KIỂM TRA TÀI NGUYÊN AI MÔ HÌNH"
echo "====================================="

echo "Cập nhật các thư viện từ requirements.txt..."
pip install --no-cache-dir -r requirements.txt
# Cài thư viện ngầm nếu chưa có
pip install --no-cache-dir huggingface_hub py_vncorenlp protobuf >/dev/null 2>&1

python -c "
import urllib.request, os

save_dir = './libs/vncorenlp'
target = os.path.join(save_dir, 'models', 'wordsegmenter', 'wordsegmenter.rdr')

if not os.path.exists(target):
    print('1. Đang tải VnCoreNLP (thuần Python) vào ./libs...')
    base_url = 'https://raw.githubusercontent.com/vncorenlp/VnCoreNLP/master'
    files = [
        'VnCoreNLP-1.2.jar',
        'models/wordsegmenter/vi-vocab',
        'models/wordsegmenter/wordsegmenter.rdr',
        'models/postagger/vi-tagger',
        'models/ner/vi-500brownclusters.xz',
        'models/ner/vi-ner.xz',
        'models/ner/vi-pretrainedembeddings.xz',
        'models/dep/vi-dep.xz',
    ]
    try:
        for f in files:
            url = f'{base_url}/{f}'
            local_path = os.path.join(save_dir, f)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            if not os.path.exists(local_path):
                print(f'Downloading {f}...')
                urllib.request.urlretrieve(url, local_path)
        print('Tải xong VnCoreNLP.')
    except Exception as e:
        print(f'Lỗi tải VnCoreNLP: {e}')
else:
    print('1. VnCoreNLP đã tồn tại trong cache, bỏ qua tải.')
"

python -c "
import os
from huggingface_hub import snapshot_download
target = './libs/phobert_sentiment_model_final'
if not os.path.exists(target):
    print('2. Đang tải PhoBERT Sentiment Model vào ./libs...')
    try:
        snapshot_download(repo_id='vinai/phobert-base-v2', local_dir=target)
        print('Tải xong PhoBERT.')
    except Exception as e:
        print(f'Lỗi tải PhoBERT: {e}')
else:
    print('2. PhoBERT Sentiment Model đã tồn tại trong cache, bỏ qua tải.')
"

python -c "
import os
from huggingface_hub import snapshot_download
target = './libs/visobert_sentiment_model_final'
if not os.path.exists(target):
    print('3. Đang tải ViSoBERT Sentiment Model vào ./libs...')
    try:
        snapshot_download(repo_id='uitnlp/visobert', local_dir=target)
        print('Tải xong ViSoBERT.')
    except Exception as e:
        print(f'Lỗi tải ViSoBERT: {e}')
else:
    print('3. ViSoBERT Sentiment Model đã tồn tại trong cache, bỏ qua tải.')
"

python -c "
import os, urllib.request
file_path = './libs/detection/models/lid.176.ftz'
temp_path = file_path + '.tmp'
if not os.path.exists(file_path):
    print('4. Đang tải FastText Language Detection Model vào ./libs...')
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    try:
        urllib.request.urlretrieve('https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz', temp_path)
        os.rename(temp_path, file_path)
        print('Tải xong FastText.')
    except Exception as e:
        print(f'Lỗi tải FastText: {e}')
        if os.path.exists(temp_path):
            os.remove(temp_path)
else:
    print('4. FastText Model đã tồn tại trong cache, bỏ qua tải.')
"

echo "====================================="
echo "   SẴN SÀNG KHỞI ĐỘNG HỆ THỐNG!"
echo "====================================="

# Thực thi lệnh chính của container (CMD)
exec "$@"
