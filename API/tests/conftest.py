import os
import sys

# Thêm thư mục gốc (NLP) vào PYTHONPATH để pytest có thể import các module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
