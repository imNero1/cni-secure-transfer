import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# ---------------------------------------------------------
# 1. DATABASE CONFIGURATION & ENGINE SETUP
# ---------------------------------------------------------
DEFAULT_PG_URL = "postgresql://postgres:postgres@localhost:5432/cni_transfer_db"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_PG_URL)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ---------------------------------------------------------
# 2. DATABASE MODEL (transfer_logs table)
# ---------------------------------------------------------
class TransferLog(Base):
    """Stores audit logs for all file uploads and downloads."""
    __tablename__ = "transfer_logs"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False, index=True)
    actor_role = Column(String, nullable=False)   # MINISTRY_OF_INTERIOR or CNI
    action_type = Column(String, nullable=False)  # UPLOAD_ENCRYPT or DECRYPT_DOWNLOAD
    has_sensitive_data = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


# ---------------------------------------------------------
# 3. LIFECYCLE & DEPENDENCY FUNCTIONS
# ---------------------------------------------------------
def init_db():
    """Initializes the database schema (creates tables if they don't exist)."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency for managing database sessions per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------
# 4. AUDIT LOGGING OPERATIONS
# ---------------------------------------------------------
def log_transfer_event(
    db: Session,
    filename: str,
    actor_role: str,
    action_type: str,
    has_sensitive_data: bool
):
    """Inserts a new transfer audit log into PostgreSQL."""
    log_entry = TransferLog(
        filename=filename,
        actor_role=actor_role,
        action_type=action_type,
        has_sensitive_data=has_sensitive_data
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry


def fetch_all_logs(db: Session):
    """Queries all audit log records from the database, newest first."""
    return db.query(TransferLog).order_by(TransferLog.timestamp.desc()).all()


# ---------------------------------------------------------
# 5. STANDALONE SCRIPT TEST
# ---------------------------------------------------------
if __name__ == "__main__":
    init_db()
    session = SessionLocal()
    test_entry = log_transfer_event(
        db=session,
        filename="test_citizens.xlsx",
        actor_role="MINISTRY_OF_INTERIOR",
        action_type="UPLOAD_ENCRYPT",
        has_sensitive_data=True
    )
    print(f"[+] Database initialized and log created with ID: {test_entry.id}")
    session.close()