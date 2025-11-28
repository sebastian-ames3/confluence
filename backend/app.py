"""
Macro Confluence Hub - Backend API

FastAPI application providing REST endpoints for:
- Data collection from research sources
- AI-powered content analysis
- Confluence scoring and tracking
- Dashboard data queries
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from project root
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

# Initialize FastAPI app
app = FastAPI(
    title="Macro Confluence Hub API",
    description="Investment research aggregation and confluence analysis system",
    version="0.1.0",
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "message": "Macro Confluence Hub API",
        "version": "0.1.0",
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for Railway."""
    return {
        "status": "healthy",
        "database": "connected",  # TODO: Add actual DB check in Phase 1
    }


# Import and include route modules
from backend.routes import dashboard, websocket, heartbeat, confluence, synthesis

app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(confluence.router, prefix="/api/confluence", tags=["confluence"])
app.include_router(synthesis.router, prefix="/api/synthesis", tags=["synthesis"])
app.include_router(websocket.router, tags=["websocket"])
app.include_router(heartbeat.router, prefix="/api", tags=["heartbeat"])

# Mount static files for frontend
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
