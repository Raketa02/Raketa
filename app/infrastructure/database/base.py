"""SQLAlchemy declarative base shared by every persistence adapter.

ORM models in `modules/*/infrastructure/` inherit from this so Alembic can
discover them through `Base.metadata`.
"""
from sqlalchemy.orm import declarative_base

Base = declarative_base()
