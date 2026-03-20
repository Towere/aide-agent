import uvicorn
from backend.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.debug
    )
