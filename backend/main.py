"""LiquiSense — FastAPI Application Entry Point."""

import os
import sys
import logging

# Force UTF-8 output on Windows to prevent UnicodeEncodeError for ₹ etc.
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from database import init_db, SessionLocal
from models.priority_mapping import PriorityMapping, DEFAULT_PRIORITY_MAPPINGS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_priority_mappings():
    """Seed default priority mappings if table is empty."""
    db = SessionLocal()
    try:
        count = db.query(PriorityMapping).count()
        if count == 0:
            for mapping in DEFAULT_PRIORITY_MAPPINGS:
                db.add(PriorityMapping(**mapping))
            db.commit()
            logger.info(f"Seeded {len(DEFAULT_PRIORITY_MAPPINGS)} priority mappings")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle handler."""
    settings = get_settings()
    
    # Create upload directory
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Init DB
    init_db()
    seed_priority_mappings()
    
    logger.info("LiquiSense API started 🚀")
    yield
    logger.info("LiquiSense API shutting down")


# Create app
settings = get_settings()

app = FastAPI(
    title="LiquiSense API",
    description="LiquiSense — Financial affordability engine for small business owners",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from routers.auth import router as auth_router
from routers.upload import router as upload_router
from routers.transactions import router as transactions_router
from routers.affordability import router as affordability_router
from routers.dashboard import router as dashboard_router

app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(transactions_router)
app.include_router(affordability_router)
app.include_router(dashboard_router)


@app.get("/")
def root():
    return {
        "app": "LiquiSense API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/api/health")
def health_check():
    return {"status": "healthy"}
