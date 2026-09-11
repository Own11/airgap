import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.db.sqlite import SQLiteDatabase
from app.api.routes_upload import router as upload_router
from app.api.routes_process import router as process_router

settings = get_settings()
logging.basicConfig(level=settings.log_level, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

app = FastAPI(title=settings.app_name, version="0.1.0")
app.include_router(upload_router)
app.include_router(process_router)
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


@app.on_event("startup")
async def initialize_database() -> None:
    SQLiteDatabase(settings).initialize()


@app.get("/")
async def root() -> FileResponse:
    return FileResponse(frontend_dir / "index.html")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}
