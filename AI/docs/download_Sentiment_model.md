1. Lệnh tải AI tách từ tiếng Việt (vncorenlp):
   python -c 'import py_vncorenlp, os; os.makedirs("./libs/vncorenlp", exist_ok=True); py_vncorenlp.download_model(save_dir="./libs/vncorenlp")'

2. Lệnh tải AI phân tích văn bản chuẩn (phobert_sentiment_model_final):
   python -c 'from huggingface_hub import snapshot_download; snapshot_download(repo_id="vinai/phobert-base-v2", local_dir="./libs/phobert_sentiment_model_final")'

3. Lệnh tải AI phân tích Teencode mạng xã hội (visobert_sentiment_model_final):
   python -c 'from huggingface_hub import snapshot_download; snapshot_download(repo_id="uitnlp/visobert", local_dir="./libs/visobert_sentiment_model_final")'

4. Lệnh tải AI nhận diện Tiếng Việt / Ngôn ngữ (FastText):
   python -c 'import os, urllib.request; os.makedirs("./libs/detection/models", exist_ok=True); urllib.request.urlretrieve("https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz", "./libs/detection/models/lid.176.ftz")'
