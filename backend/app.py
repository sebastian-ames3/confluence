"""
Macro Confluence Hub - Backend API

FastAPI application providing REST endpoints for:
- Data collection from research sources
- AI-powered content analysis
- Confluence scoring and tracking
- Dashboard data queries

Security features (PRD-015):
- HTTP Basic Auth on all API routes (except /health)
- Rate limiting to prevent API abuse

Observability (PRD-034):
- Sentry error monitoring (when SENTRY_DSN is configured)
- Environment variable validation at startup

Version: 1.0.2 - PRD-034 Observability Foundation
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
import os
from pathlib import Path
from dotenv import load_dotenv
import logging

# Load environment variables from project root
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

# Set up logging
logger = logging.getLogger(__name__)

# ============================================================================
# PRD-034: Sentry Error Monitoring
# ============================================================================
# Initialize Sentry only if SENTRY_DSN is configured
if os.getenv("SENTRY_DSN"):
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration

        sentry_sdk.init(
            dsn=os.getenv("SENTRY_DSN"),
            integrations=[FastApiIntegration()],
            traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
            environment=os.getenv("RAILWAY_ENV", "development"),
            send_default_pii=False,  # Don't send personally identifiable information
        )
        logger.info("Sentry error monitoring initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize Sentry: {e}")
else:
    logger.info("Sentry not configured (SENTRY_DSN not set)")

# ============================================================================
# PRD-034: Environment Variable Validation
# ============================================================================
REQUIRED_ENV_VARS = ["CLAUDE_API_KEY", "AUTH_USERNAME", "AUTH_PASSWORD"]

def validate_environment():
    """Validate required environment variables are set in production."""
    if os.getenv("RAILWAY_ENV") == "production":
        missing = [v for v in REQUIRED_ENV_VARS if not os.getenv(v)]
        if missing:
            raise RuntimeError(f"Missing required environment variables: {missing}")
    else:
        # In development, just warn about missing vars
        missing = [v for v in REQUIRED_ENV_VARS if not os.getenv(v)]
        if missing:
            logger.warning(f"Missing environment variables (not enforced in dev): {missing}")

validate_environment()

# Import rate limiter
from backend.utils.rate_limiter import limiter, rate_limit_exceeded_handler

# Initialize FastAPI app
app = FastAPI(
    title="Macro Confluence Hub API",
    description="Investment research aggregation and confluence analysis system",
    version="1.0.0",
)

# Add rate limiter to app state
app.state.limiter = limiter

# Register rate limit exceeded handler
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


# Global exception handler to catch all unhandled errors and return JSON
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    from fastapi.responses import JSONResponse

    error_detail = f"{type(exc).__name__}: {str(exc)}\n{traceback.format_exc()}"
    print(f"GLOBAL ERROR HANDLER: {error_detail}")  # Log to stdout for Railway logs

    return JSONResponse(
        status_code=500,
        content={
            "detail": error_detail,
            "error_type": type(exc).__name__,
            "error_message": str(exc)
        }
    )


# Configure CORS for frontend
def get_allowed_origins():
    """Get allowed CORS origins based on environment."""
    railway_url = os.getenv("RAILWAY_API_URL")
    railway_env = os.getenv("RAILWAY_ENV")

    if railway_env == "production" and railway_url:
        # Production: only allow the Railway URL
        return [railway_url, railway_url.replace("https://", "http://")]
    else:
        # Development: allow localhost variants
        return [
            "http://localhost:8000",
            "http://localhost:3000",
            "http://127.0.0.1:8000",
            "http://127.0.0.1:3000",
        ]


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
@app.get("/index.html")
async def root():
    """Serve the dashboard HTML."""
    from fastapi.responses import FileResponse
    frontend_path = Path(__file__).parent.parent / "frontend" / "index.html"
    if frontend_path.exists():
        return FileResponse(frontend_path, media_type="text/html")
    return {
        "message": "Macro Confluence Hub API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for Railway."""
    from backend.models import SessionLocal
    from sqlalchemy import text

    db_status = "connected"
    try:
        # Actually verify database connectivity (SQLAlchemy 2.0 compatible)
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
    }


# Import and include route modules
from backend.routes import dashboard, websocket, heartbeat, confluence, synthesis, trigger, search, collect, analyze, themes, auth, engagement, symbols

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])  # PRD-036: JWT Auth
app.include_router(engagement.router, prefix="/api", tags=["engagement"])  # PRD-038: User Engagement
app.include_router(symbols.router)  # PRD-039: Symbol-Level Confluence
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(confluence.router, prefix="/api/confluence", tags=["confluence"])
app.include_router(synthesis.router, prefix="/api/synthesis", tags=["synthesis"])
app.include_router(trigger.router, prefix="/api/trigger", tags=["trigger"])
app.include_router(search.router, prefix="/api/search", tags=["search"])  # PRD-016
app.include_router(collect.router, prefix="/api", tags=["collect"])  # Discord local upload endpoint
app.include_router(analyze.router, prefix="/api", tags=["analyze"])  # Content analysis endpoint
app.include_router(themes.router, prefix="/api", tags=["themes"])  # PRD-024 theme tracking
app.include_router(websocket.router, tags=["websocket"])
app.include_router(heartbeat.router, prefix="/api", tags=["heartbeat"])

# Mount static files for frontend assets
frontend_path = Path(__file__).parent.parent / "frontend"
css_path = frontend_path / "css"
js_path = frontend_path / "js"
images_path = frontend_path / "images"

# Debug: log paths at startup
print(f"STATIC FILES DEBUG: frontend_path={frontend_path}, exists={frontend_path.exists()}")
print(f"STATIC FILES DEBUG: css_path={css_path}, exists={css_path.exists()}")
print(f"STATIC FILES DEBUG: js_path={js_path}, exists={js_path.exists()}")
print(f"STATIC FILES DEBUG: images_path={images_path}, exists={images_path.exists()}")

# Mount static asset directories
if css_path.exists():
    app.mount("/css", StaticFiles(directory=str(css_path)), name="css")
    print("STATIC FILES: Mounted /css")
if js_path.exists():
    app.mount("/js", StaticFiles(directory=str(js_path)), name="js")
    print("STATIC FILES: Mounted /js")
if images_path.exists():
    app.mount("/images", StaticFiles(directory=str(images_path)), name="images")
    print("STATIC FILES: Mounted /images")
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
    print("STATIC FILES: Mounted /static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
