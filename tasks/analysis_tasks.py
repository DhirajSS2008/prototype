"""Celery background tasks for transaction analysis."""

import logging
from database import SessionLocal
from services.profiler_service import run_full_profile
from redis_client import cache_set

logger = logging.getLogger(__name__)


def run_profiler_analysis(user_id: int):
    """Background task: analyze transaction history and compute expense profile.
    
    Note: Without Redis/Celery, this runs synchronously.
    """
    db = SessionLocal()
    try:
        logger.info(f"Starting profiler analysis for user {user_id}...")
        profile = run_full_profile(db, user_id)
        
        # Cache the result per user
        cache_set(f"expense_profile:{user_id}", profile, ttl=3600)
        
        logger.info(f"Profiler analysis complete: {profile.get('total_transactions', 0)} transactions analyzed")
        return profile
        
    except Exception as e:
        logger.error(f"Profiler analysis failed: {e}")
        raise
    finally:
        db.close()


# Try to register as Celery task if available
try:
    from celery_app import celery_app

    @celery_app.task(name="run_profiler_analysis")
    def celery_run_profiler_analysis(user_id: int):
        return run_profiler_analysis(user_id)
except Exception:
    # Celery not available — tasks will run synchronously
    pass
