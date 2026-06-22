import os
import logging

# pyrefly: ignore [missing-import]
import py_vncorenlp

from core.base.base_model_builder import BaseModelBuilder

logger = logging.getLogger(__name__)

import urllib.request

def _download_vncorenlp(save_dir: str):
    """Tải VnCoreNLP thuần Python (không phụ thuộc lệnh wget của OS)."""
    base_url = "https://raw.githubusercontent.com/vncorenlp/VnCoreNLP/master"
    files = [
        "VnCoreNLP-1.2.jar",
        "models/wordsegmenter/vi-vocab",
        "models/wordsegmenter/wordsegmenter.rdr",
        "models/postagger/vi-tagger",
        "models/ner/vi-500brownclusters.xz",
        "models/ner/vi-ner.xz",
        "models/ner/vi-pretrainedembeddings.xz",
        "models/dep/vi-dep.xz"
    ]
    
    for f in files:
        url = f"{base_url}/{f}"
        local_path = os.path.join(save_dir, f)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        if not os.path.exists(local_path):
            logger.info(f"Downloading {f}...")
            urllib.request.urlretrieve(url, local_path)


class PhoBertModelBuilder(BaseModelBuilder):
    """
    Model Builder cho PhoBERT.

    Kế thừa build_model() từ BaseModelBuilder.
    Thêm method riêng: build_vncorenlp() để khởi tạo tách từ tiếng Việt.
    """

    def __init__(self, config):
        super().__init__(config)
        self.segmenter = None

    def build_vncorenlp(self, save_dir="./vncorenlp"):
        """Tải và khởi động VnCoreNLP segmenter (chỉ PhoBERT cần)."""
        vncorenlp_dir = os.path.abspath(save_dir)

        if not os.path.exists(os.path.join(vncorenlp_dir, "VnCoreNLP-1.2.jar")):
            logger.info("Dang tai model VnCoreNLP lan dau...")
            os.makedirs(vncorenlp_dir, exist_ok=True)
            try:
                _download_vncorenlp(vncorenlp_dir)
            except Exception as e:
                raise RuntimeError(
                    f"Khong the tai VnCoreNLP. Kiem tra ket noi mang.\nChi tiet loi: {e}"
                )

        try:
            current_dir = os.getcwd()
            self.segmenter = py_vncorenlp.VnCoreNLP(
                annotators=["wseg"], save_dir=vncorenlp_dir
            )
            os.chdir(current_dir)
        except Exception as e:
            raise RuntimeError(
                f"Khong the khoi dong VnCoreNLP. Hay chac chan da cai Java:\n"
                f"   Ubuntu: sudo apt install -y openjdk-17-jdk\n"
                f"   macOS: brew install openjdk@17\n"
                f"Chi tiet loi: {e}"
            )

        logger.info("Da khoi tao RDRSegmenter (VnCoreNLP) thanh cong.")
        return self.segmenter
