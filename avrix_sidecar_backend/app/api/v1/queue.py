from fastapi import APIRouter

from app.contracts.queue import QueueCreateRequest, QueueItem, QueueMoveRequest
from app.services.queue_service import queue_service

router = APIRouter(prefix="/queue", tags=["queue"])


@router.get("", response_model=list[QueueItem])
def get_queue_items() -> list[QueueItem]:
    return queue_service.list_items()


@router.post("", response_model=QueueItem, status_code=201)
def add_queue_item(payload: QueueCreateRequest) -> QueueItem:
    return queue_service.add_item(payload)


@router.delete("/{item_id}", status_code=204)
def remove_queue_item(item_id: str):
    queue_service.remove_item(item_id)


@router.post("/{item_id}/move", response_model=list[QueueItem])
def move_queue_item(item_id: str, payload: QueueMoveRequest) -> list[QueueItem]:
    return queue_service.move_item(item_id, payload.direction)


@router.delete("/finished", response_model=list[QueueItem])
def clear_finished_queue() -> list[QueueItem]:
    return queue_service.clear_finished()


@router.delete("", status_code=204)
def clear_all_queue():
    queue_service.clear_all()
