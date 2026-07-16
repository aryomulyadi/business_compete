import asyncio
import threading
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status

from deep_research_team.settings import setup_logging

from fastapi_backend.workers.crew_runner import run_crew_task
from fastapi_backend.workers.progress_store import create_task, get_task

logger = setup_logging(__name__)

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, list[WebSocket]] = {}
        self._lock = threading.Lock()

    async def connect(self, task_id: str, ws: WebSocket) -> None:
        await ws.accept()
        with self._lock:
            self._connections.setdefault(task_id, []).append(ws)

    async def broadcast(self, task_id: str, data: dict[str, Any]) -> None:
        with self._lock:
            targets = list(self._connections.get(task_id, []))
        for ws in targets:
            try:
                await ws.send_json(data)
            except Exception:
                with self._lock:
                    if task_id in self._connections:
                        self._connections[task_id] = [c for c in self._connections[task_id] if c != ws]

    def disconnect(self, task_id: str, ws: WebSocket) -> None:
        with self._lock:
            if task_id in self._connections:
                self._connections[task_id] = [c for c in self._connections[task_id] if c != ws]


manager = ConnectionManager()


@router.post("/start")
async def start_analysis(payload: dict[str, str]) -> dict[str, Any]:
    business_field = (payload.get("business_field") or "").strip()
    if not business_field:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="business_field is required")
    if len(business_field) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="business_field too short (min 10 characters)",
        )

    task_id = str(uuid.uuid4())
    create_task(task_id, business_field)

    threading.Thread(target=run_crew_task, args=(task_id, business_field), daemon=True).start()

    return {"task_id": task_id, "field": business_field}


@router.get("/status/{task_id}")
async def get_status(task_id: str) -> dict[str, Any]:
    tp = get_task(task_id)
    if tp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return tp.to_dict()


@router.websocket("/ws/progress/{task_id}")
async def ws_progress(websocket: WebSocket, task_id: str) -> None:
    await manager.connect(task_id, websocket)
    try:
        while True:
            tp = get_task(task_id)
            if tp is None:
                await websocket.send_json({"error": "Task not found"})
                break
            await websocket.send_json(tp.to_dict())
            if tp.status in ("completed", "failed"):
                break
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(task_id, websocket)
