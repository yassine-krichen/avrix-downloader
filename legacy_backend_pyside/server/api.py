from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import json
import asyncio
from pathlib import Path

from core.queue_service import QueueService
from core.download_queue import DownloadQueue
from core.queue_storage import JsonQueueStorage
from core.queue_item import QueueItem
from core.utils import ConfigManager
from core.settings_service import SettingsService, JsonSettingsRepository, AppSettings

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Services
config_manager = ConfigManager()
settings_repo = JsonSettingsRepository(config_manager)

# Create default settings
default_settings = AppSettings(
    download_path=str(Path.home() / 'Downloads' / 'Avrix'),
    format_type='mp4',
    quality='1080p',
    last_url='',
    download_subtitles=False,
    subtitle_languages='en',
    embed_thumbnail=False,
    notifications_enabled=True,
    max_concurrent_downloads=3
)
settings_service = SettingsService(settings_repo, default_settings)

queue_storage = JsonQueueStorage()
download_queue = DownloadQueue(queue_storage)
queue_service = QueueService(download_queue, max_concurrent=settings_service.get('max_concurrent_downloads', 3))

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# Event Listeners
loop = None

def on_item_updated(item):
    if loop:
        asyncio.run_coroutine_threadsafe(
            manager.broadcast({"type": "progress", "data": item.__dict__}),
            loop
        )

def on_item_completed(item):
    if loop:
        asyncio.run_coroutine_threadsafe(
            manager.broadcast({"type": "completed", "data": item.__dict__}),
            loop
        )

def on_item_failed(item, error):
    if loop:
        asyncio.run_coroutine_threadsafe(
            manager.broadcast({"type": "error", "data": {"id": item.id, "error": error}}),
            loop
        )

@app.on_event("startup")
async def startup_event():
    global loop
    loop = asyncio.get_event_loop()
    
    # Connect callbacks
    queue_service.item_updated.connect(on_item_updated)
    queue_service.item_completed.connect(on_item_completed)
    queue_service.item_failed.connect(on_item_failed)

# Models
class DownloadRequest(BaseModel):
    url: str
    format_type: str = "mp4"
    quality: str = "1080p"
    download_subtitles: bool = False

class SettingsUpdate(BaseModel):
    download_path: Optional[str] = None
    format_type: Optional[str] = None
    quality: Optional[str] = None
    download_subtitles: Optional[bool] = None
    subtitle_languages: Optional[str] = None
    embed_thumbnail: Optional[bool] = None
    notifications_enabled: Optional[bool] = None
    max_concurrent_downloads: Optional[int] = None

# Endpoints
@app.get("/")
def read_root():
    return {"status": "Avrix Downloader API Running"}

@app.post("/download")
def add_download(request: DownloadRequest):
    # Use configured download path if not specified (though request doesn't have it yet)
    download_path = settings_service.get('download_path')
    
    item = queue_service.add_to_queue(
        url=request.url,
        download_path=download_path,
        format_type=request.format_type,
        quality=request.quality,
        download_subtitles=request.download_subtitles
    )
    return {"status": "added", "id": item.id}

@app.get("/queue")
def get_queue():
    return [item.__dict__ for item in download_queue.get_all_items()]

@app.get("/settings")
def get_settings():
    return settings_service.get_all().__dict__

@app.post("/settings")
def update_settings(settings: SettingsUpdate):
    update_data = {k: v for k, v in settings.dict().items() if v is not None}
    settings_service.update(**update_data)
    
    # Update services that depend on settings
    if 'max_concurrent_downloads' in update_data:
        queue_service.max_concurrent = update_data['max_concurrent_downloads']
        
    return settings_service.get_all().__dict__

@app.get("/system/info")
def get_system_info():
    return {
        "version": "2.0.0",
        "platform": "win32", 
        "default_download_path": str(Path.home() / 'Downloads' / 'Avrix')
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
