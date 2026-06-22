from fastapi import (
    APIRouter,
    Depends,
    Request,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    Query,
    status,
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import re
import uuid
from typing import List

from services.rabbitmq_service import rabbitmq, ROUTING_KEY_PREDICT_REQUESTS
from api.dependencies import verify_jwt_token, verify_ws_jwt_token
from services.websocket_manager_service import ws_manager

router = APIRouter(tags=["Prediction"])


class PredictRequest(BaseModel):
    text: str
    client_id: str | None = None


class PredictBatchRequest(BaseModel):
    texts: List[str]
    client_id: str | None = None


class PredictResponse(BaseModel):
    text: str
    segmented_text: str
    label: str
    score: float
    model_used: str
    is_teencode: bool


def process_text_for_prediction(text: str, language_detector):
    """
    Hàm dùng chung để làm sạch, kiểm tra tính hợp lệ và ngôn ngữ của văn bản.
    Trả về: (is_valid, reason, lang_info, text_clean)
    """
    text_clean = text.strip()

    has_meaningful_chars = re.search(
        r"[a-zA-Z0-9_áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ]",
        text_clean,
    )

    if not text_clean or not has_meaningful_chars:
        return False, "Văn bản trống hoặc không chứa từ vựng có nghĩa", None, text_clean

    lang_info = language_detector.is_vietnamese(text_clean)
    if not lang_info["is_vietnamese"]:
        return False, "Không phải tiếng Việt", lang_info, text_clean

    return True, None, lang_info, text_clean


@router.post(
    "/predict",
)
async def predict(
    request: PredictRequest, req: Request, username: str = Depends(verify_jwt_token)
):
    """
    Phân tích cảm xúc text tiếng Việt.
    """
    language_detector = req.app.state.language_detector
    is_valid, reason, lang_info, text_clean = process_text_for_prediction(
        request.text, language_detector
    )

    if not is_valid:
        if lang_info:
            return JSONResponse(status_code=400, content=lang_info)
        raise HTTPException(
            status_code=400,
            detail=reason,
        )

    # Nếu hợp lệ thì đẩy vào RabbitMQ
    task_id = str(uuid.uuid4())
    message_payload = {
        "task_id": task_id,
        "text": text_clean,
        "lang_info": lang_info,
        "client_id": request.client_id,
    }
    await rabbitmq.publish_message(
        message_payload, routing_key=ROUTING_KEY_PREDICT_REQUESTS
    )

    return JSONResponse(
        status_code=200,
        content={
            "status": 200,
            "task_id": task_id,
            "message": "Văn bản hợp lệ (Tiếng Việt). Đã đẩy vào hàng đợi RabbitMQ để xử lý.",
            "data": message_payload,
        },
    )


@router.post("/predict/batch")
async def predict_batch(
    request: PredictBatchRequest,
    req: Request,
    username: str = Depends(verify_jwt_token),
):
    """
    Phân tích cảm xúc một mảng text tiếng Việt.
    """
    language_detector = req.app.state.language_detector

    queued_tasks = []
    invalid_texts = []

    for idx, text in enumerate(request.texts):
        is_valid, reason, lang_info, text_clean = process_text_for_prediction(
            text, language_detector
        )

        if not is_valid:
            invalid_texts.append(
                {
                    "index": idx,
                    "text": text_clean,
                    "reason": reason,
                    "lang_info": lang_info,
                }
            )
            continue

        task_id = str(uuid.uuid4())
        message_payload = {
            "task_id": task_id,
            "text": text_clean,
            "lang_info": lang_info,
            "client_id": request.client_id,
        }
        await rabbitmq.publish_message(
            message_payload, routing_key=ROUTING_KEY_PREDICT_REQUESTS
        )

        queued_tasks.append({"index": idx, "task_id": task_id, "text": text_clean})

    return JSONResponse(
        status_code=200,
        content={
            "status": "queued_batch",
            "message": f"Đã đẩy {len(queued_tasks)} văn bản vào hàng đợi. {len(invalid_texts)} văn bản bị loại.",
            "queued_tasks": queued_tasks,
            "invalid_texts": invalid_texts,
        },
    )


@router.websocket("/ws")
async def websocket_predict_results(
    websocket: WebSocket,
    client_id: str = Query(...),
    username: str = Depends(verify_ws_jwt_token),
):
    """
    WebSocket Endpoint để Frontend lắng nghe kết quả trả về từ AI Worker.
    Frontend kết nối tới: ws://<domain>/predict/ws?token=<jwt_token>&client_id=<uuid>
    """
    await ws_manager.connect(websocket, client_id)
    try:
        while True:
            # Chờ nhận dữ liệu từ client
            data = await websocket.receive_text()
            print(f"Nhận dữ liệu từ client {client_id}: {data}")

            # TODO: Có thể if/else kiểm tra data để gọi lệnh điều khiển AI Worker

    except WebSocketDisconnect:
        ws_manager.disconnect(client_id)
