import os
import logging

# pyrefly: ignore [missing-import]
import py_vncorenlp

from core.base.base_model_builder import BaseModelBuilder

logger = logging.getLogger(__name__)


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
                py_vncorenlp.download_model(save_dir=vncorenlp_dir)
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
                f"Khong the khoi dong VnCoreNLP. Hay chac chan da cai Java 17:\n"
                f"   sudo apt install -y openjdk-17-jdk\n"
                f"Chi tiet loi: {e}"
            )

        logger.info("Da khoi tao RDRSegmenter (VnCoreNLP) thanh cong.")
        return self.segmenter
