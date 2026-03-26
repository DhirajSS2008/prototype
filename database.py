"""SQLAlchemy database setup."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config import get_settings

settings = get_settings()

# Build engine — MySQL by default, SQLite as fallback
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables."""
    from models.user import User
    from models.transaction import Transaction
    from models.cash_balance import CashBalanceSnapshot
    from models.priority_mapping import PriorityMapping
    from models.affordability_check import AffordabilityCheck
<<<<<<< HEAD
    from models.ai_action_log import AIActionLog
    from models.vendor_contact import VendorContact
    from models.email_draft import EmailDraft
=======
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
    Base.metadata.create_all(bind=engine)
