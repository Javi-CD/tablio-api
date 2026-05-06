import json
import uuid
from collections import defaultdict

from fastapi import WebSocket


class WebSocketManager:
    def __init__(self) -> None:
        self._connections: dict[uuid.UUID, set[WebSocket]] = defaultdict(set)

    async def connect(self, restaurant_id: uuid.UUID, ws: WebSocket) -> None:
        await ws.accept()
        self._connections[restaurant_id].add(ws)

    def disconnect(self, restaurant_id: uuid.UUID, ws: WebSocket) -> None:
        self._connections[restaurant_id].discard(ws)
        if not self._connections[restaurant_id]:
            del self._connections[restaurant_id]

    async def broadcast(
        self, restaurant_id: uuid.UUID, payload: dict[str, object]
    ) -> None:
        dead: list[WebSocket] = []
        for ws in list(self._connections.get(restaurant_id, set())):
            try:
                await ws.send_text(json.dumps(payload))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(restaurant_id, ws)


ws_manager = WebSocketManager()
