import json
from fastapi import WebSocket
from typing import List


class WebSocketManager:
    def __init__(self):
        # Map client_id -> WebSocket (1 kết nối duy nhất mỗi tab/client)
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_personal_message(
        self, message: dict, client_id: str, cmd: str = "predict_result"
    ):
        if client_id in self.active_connections:
            connection = self.active_connections[client_id]
            # Gắn thêm cmd vào message
            message["cmd"] = cmd
            try:
                await connection.send_json(message)
            except Exception:
                pass

    async def broadcast(self, message: dict, cmd: str = "predict_result"):
        # Gắn thêm cmd vào message
        message["cmd"] = cmd
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except Exception:
                pass


ws_manager = WebSocketManager()
