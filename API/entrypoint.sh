#!/bin/bash
set -e

echo "=========================================================="
echo "BẮT ĐẦU TẢI CÁC TÀI NGUYÊN VÀ MÔ HÌNH (API)"
echo "=========================================================="

echo "Cập nhật các thư viện từ requirements.txt..."
pip install --no-cache-dir -r requirements.txt

python -c "
import os, urllib.request
file_path = './libs/detection/models/lid.176.ftz'
temp_path = file_path + '.tmp'
if not os.path.exists(file_path):
    print('Đang tải FastText Language Detection Model vào ./libs/detection/models...')
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
    print('FastText Model đã tồn tại trong cache, bỏ qua tải.')
"

echo "=========================================================="
echo "HOÀN TẤT TẢI TOÀN BỘ TÀI NGUYÊN MODEL!"
echo "=========================================================="

# Thực thi lệnh chính (CMD)
exec "$@"
