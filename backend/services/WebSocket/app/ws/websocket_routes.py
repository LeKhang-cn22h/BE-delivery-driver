from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ws.connection_manager import manager

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/track/{driver_id}")
async def track_driver_ws(websocket: WebSocket, driver_id: str):
    """WebSocket để theo dõi 1 driver cụ thể"""
    await manager.connect_viewer(driver_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect_viewer(driver_id, websocket)


@router.websocket("/ws/track-all")
async def track_all_drivers_ws(websocket: WebSocket):
    """WebSocket để theo dõi TẤT CẢ drivers (cho admin)"""
    await manager.connect_admin(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect_admin(websocket)