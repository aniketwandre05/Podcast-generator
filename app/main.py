import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from app.api.episodes import router as episodes_router
from app.api.events import router as events_router
from app.api.export import router as export_router
from app.api.voices import router as voices_router
from app.core.config import settings
from app.core.database import init_db

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("podcastai")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing PodcastAI Backend...")
    # Validate API key (logs warning if missing, allows graceful boot)
    settings.validate_api_key(raise_error=False)
    # Initialize SQLite database and auto-migrate schema
    init_db()
    logger.info("Database initialized. Ready to generate podcasts.")
    yield
    logger.info("Shutting down PodcastAI Backend.")

app = FastAPI(
    title="PodcastAI - AI Podcast Generator",
    description="Automated multi-speaker podcast generation using Sarvam AI (Sarvam LLM, Bulbul TTS, Sarvam Translate).",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if settings.CORS_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )

# Include API Routers
app.include_router(episodes_router)
app.include_router(events_router)
app.include_router(voices_router)
app.include_router(export_router)

@app.get("/api/health")
def health_check():
    has_key = bool(settings.SARVAM_API_KEY and not settings.SARVAM_API_KEY.startswith("your_"))
    return {
        "status": "healthy" if has_key else "needs_configuration",
        "service": "PodcastAI Backend",
        "sarvam_connected": has_key,
        "message": "System ready" if has_key else "SARVAM_API_KEY is required to generate audio. Configure it in Render environment settings.",
    }

# Mount static storage for assets
app.mount("/assets/music", StaticFiles(directory=str(settings.MUSIC_DIR)), name="music")

# Mount frontend production build as catch-all SPA at the very end
frontend_dist = settings.BASE_DIR / "frontend" / "dist"
if frontend_dist.exists():
    # Mount hashed Vite static assets (/assets/index-*.js, /assets/index-*.css)
    if (frontend_dist / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="frontend-assets")

    # Catch-all route to serve SPA index.html for client-side routing
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = frontend_dist / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)

