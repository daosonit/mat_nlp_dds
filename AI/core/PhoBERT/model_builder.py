import os

# pyrefly: ignore [missing-import]
import py_vncorenlp

from core.base.base_model_builder import BaseModelBuilder


from core.config import VNCORENLP_DIR

class PhoBertModelBuilder(BaseModelBuilder):
    """
    Model Builder cho PhoBERT.

    Kế thừa build_model() từ BaseModelBuilder.
    Thêm method riêng: build_vncorenlp() để khởi tạo tách từ tiếng Việt.
    """

    def __init__(self, config):
        super().__init__(config)
        self.segmenter = None

    def build_vncorenlp(self, save_dir=VNCORENLP_DIR):
        """Khởi động VnCoreNLP segmenter (chỉ PhoBERT cần)."""
        vncorenlp_dir = os.path.abspath(save_dir)

        if not os.path.exists(os.path.join(vncorenlp_dir, "VnCoreNLP-1.2.jar")):
            raise RuntimeError(
                f"Không tìm thấy file VnCoreNLP-1.2.jar tại {vncorenlp_dir}. Vui lòng chạy lệnh cài đặt qua entrypoint.sh trước khi khởi động Worker."
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

        return self.segmenter
