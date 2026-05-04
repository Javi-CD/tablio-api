import uuid

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from jose import JWTError

from app.core.security import decode_access_token
from app.core.websocket_manager import ws_manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/restaurants/{restaurant_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    restaurant_id: uuid.UUID,
    token: str = Query(...),
) -> None:
    try:
        decode_access_token(token)
    except JWTError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await ws_manager.connect(restaurant_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(restaurant_id, websocket)
