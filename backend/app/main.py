"""Main FastAPI application entry point for APEX OSINT."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db
from app.api.v1.workspaces import router as workspaces_router
from app.api.v1.investigations import router as investigations_router
from app.api.v1.targets import router as targets_router
from app.api.v1.graph import router as graph_router
from app.api.v1.ai import router as ai_router
from app.api.v1.modules import router as modules_router
from app.api.v1.reports import router as reports_router
from app.api.v1.demo import router as demo_router
from app.api.v1.settings import router as settings_router
from app.api.v1.parse import router as parse_router
from app.modules.registry import module_registry

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("apex.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: database initialization and teardown."""
    logger.info("Initializing APEX OSINT database schema...")
    await init_db()
    logger.info("APEX OSINT backend started successfully.")
    yield
    logger.info("APEX OSINT backend shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Local-first, modular, AI-assisted OSINT investigation platform. Intelligence, connected.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global safe error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception processing %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An error occurred while processing the intelligence request.",
            "path": request.url.path
        }
    )


# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health and runtime diagnostics endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "tagline": settings.TAGLINE,
        "modules_count": len(module_registry.list_modules()),
        "gemini_active": bool(settings.GEMINI_API_KEY),
    }


# Include API routers
app.include_router(workspaces_router, prefix="/api")
app.include_router(investigations_router, prefix="/api")
app.include_router(targets_router, prefix="/api")
app.include_router(graph_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(modules_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(demo_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(parse_router, prefix="/api")

# Serve production frontend if built
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))

