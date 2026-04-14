from collections.abc import Generator
import logging

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.models.db import Base

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
logger = logging.getLogger(__name__)


def init_db() -> bool:
	try:
		Base.metadata.create_all(bind=engine)
		return True
	except SQLAlchemyError as exc:
		logger.warning("Database initialization skipped: %s", exc.__class__.__name__)
		return False


def get_db() -> Generator[Session, None, None]:
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()

