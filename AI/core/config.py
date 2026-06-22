import os

# Base Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIBS_DIR = os.path.join(BASE_DIR, "libs")

# PhoBERT Paths
PHOBERT_MODEL_DIR = os.path.join(LIBS_DIR, "phobert_sentiment_model_final")
PHOBERT_CHECKPOINT_DIR = os.path.join(LIBS_DIR, "phobert_sentiment_model_checkpoints")
PHOBERT_CACHE_DIR = os.path.join(LIBS_DIR, "cache_tokenized_data")
VNCORENLP_DIR = os.path.join(LIBS_DIR, "vncorenlp")

# ViSoBERT Paths
VISOBERT_MODEL_DIR = os.path.join(LIBS_DIR, "visobert_sentiment_model_final")
VISOBERT_CHECKPOINT_DIR = os.path.join(LIBS_DIR, "visobert_sentiment_model_checkpoints")
VISOBERT_CACHE_DIR = os.path.join(LIBS_DIR, "cache_visobert_tokenized_data")
