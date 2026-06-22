from core.base.base_model_builder import BaseModelBuilder


class ViSoBertModelBuilder(BaseModelBuilder):
    """
    Model Builder cho ViSoBERT.

    Kế thừa 100% từ BaseModelBuilder.
    ViSoBERT KHÔNG cần VnCoreNLP, nên không có method thêm.
    File này tồn tại để giữ tính nhất quán với PhoBERT module.
    """

    pass
