#!/bin/bash
set -e

echo "=========================================================="
echo "BẮT ĐẦU TẢI CÁC TÀI NGUYÊN VÀ MÔ HÌNH"
echo "=========================================================="

python -c "
import os, urllib.request
file_path = './libs/detection/models/lid.176.ftz'
if not os.path.exists(file_path):
    print('Đang tải FastText Language Detection Model vào ./libs/detection/models...')
    os.makedirs('./libs/detection/models', exist_ok=True)
    urllib.request.urlretrieve('https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz', file_path)
else:
    print('FastText Model đã tồn tại trong cache, bỏ qua tải.')
"

echo "=========================================================="
echo "HOÀN TẤT TẢI TOÀN BỘ TÀI NGUYÊN MODEL!"
echo "=========================================================="

# Thực thi lệnh chính (CMD)
exec "$@"
