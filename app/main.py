from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.logging import logger
from app.api.v1.router import api_router
from app.websocket.chat_handler import ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown event lifespan."""
    logger.info("Starting up %s (version: %s)...", settings.PROJECT_NAME, settings.VERSION)
    
    # Ensure required data directories exist
    settings.get_absolute_path(settings.VECTOR_STORE_PATH)
    settings.get_absolute_path(settings.KNOWLEDGE_BASE_PATH)
    settings.get_absolute_path(settings.STORAGE_PATH)
    logger.info("Verified data directories are ready.")
    
    yield
    
    logger.info("Shutting down %s...", settings.PROJECT_NAME)


# Initialize FastAPI App
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API for AI-Powered Civic Service, Application and Grievance Assistant.",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure Cross-Origin Resource Sharing (CORS)
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Mount API v1 routes and WebSockets
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(ws_router)

# Mount static directory for browser UI
static_dir = Path(__file__).resolve().parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


from fastapi.responses import FileResponse, RedirectResponse

@app.get("/", tags=["Root"], include_in_schema=False)
async def root():
    """Serve civic portal frontend homepage."""
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return RedirectResponse(url="/docs")


@app.get("/chat", tags=["Root"], include_in_schema=False)
async def chat_page():
    """Serve grounded civic chatbot page."""
    chat_file = static_dir / "chat.html"
    if chat_file.exists():
        return FileResponse(str(chat_file))
    return RedirectResponse(url="/static/chat.html")

