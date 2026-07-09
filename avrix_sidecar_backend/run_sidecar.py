import uvicorn

from app.core.config import settings
from app.main import app

if __name__ == "__main__":
    uvicorn.run(app, host=settings.app_host, port=settings.app_port, reload=False)
