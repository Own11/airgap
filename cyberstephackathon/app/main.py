import logging
from importlib.util import find_spec
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.db.sqlite import SQLiteDatabase
from app.api.routes_upload import router as upload_router
from app.api.routes_process import router as process_router
from app.api.routes_auth import router as auth_router
from app.api.routes_results import router as results_router
from app.api.routes_transcript import router as transcript_router
from app.api.routes_chat import router as chat_router

settings = get_settings()
logging.basicConfig(level=settings.log_level, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

app = FastAPI(title=settings.app_name, version="0.1.0")
app.include_router(upload_router)
app.include_router(process_router)
app.include_router(auth_router)
app.include_router(results_router)
app.include_router(transcript_router)
app.include_router(chat_router)
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


@app.on_event("startup")
async def initialize_database() -> None:
    SQLiteDatabase(settings).initialize()


@app.get("/")
async def root() -> FileResponse:
    return FileResponse(frontend_dir / "index.html")


@app.get("/dashboard")
async def dashboard() -> FileResponse:
    return FileResponse(frontend_dir / "dashboard.html")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@app.get("/health/models")
async def model_health() -> dict[str, object]:
    return {
        "transcription": bool(find_spec("faster_whisper")),
        "ollama_client": bool(find_spec("ollama")),
        "reportlab": bool(find_spec("reportlab")),
        "ollama_url": settings.ollama_base_url,
        "ollama_model": settings.ollama_model,
    }
