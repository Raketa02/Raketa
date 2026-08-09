"""SQLAlchemy declarative base shared by every persistence adapter.

ORM models in `modules/*/infrastructure/` inherit from this so Alembic can
discover them through `Base.metadata`.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
