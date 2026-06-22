import asyncio
from services.rabbitmq_service import rabbitmq, ROUTING_KEY_PREDICT_RESULTS
from services.websocket_manager_service import ws_manager


async def handle_predict_result(payload: dict):
    """
    Xử lý kết quả trả về từ AI Worker.
    Hiện tại log ra console. Sau này có thể lưu DB hoặc gửi qua WebSocket.
    """
    # Gửi kết quả qua WebSocket cho tab/client cụ thể
    client_id = payload.get("client_id")
    logger.info("Có tin nhắn")
    if client_id:
        if client_id in ws_manager.active_connections:
            await ws_manager.send_personal_message(
                payload, client_id, cmd="predict_result"
            )
    else:
        await ws_manager.broadcast(payload, cmd="predict_result")


def start_predict_result_consumer():
    """
    Kích hoạt Background Task lắng nghe kết quả từ Queue
    """
    asyncio.create_task(
        rabbitmq.consume_messages(
            queue_name=ROUTING_KEY_PREDICT_RESULTS,
            callback_function=handle_predict_result,
        )
    )
