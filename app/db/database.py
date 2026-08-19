import os

from sqlalchemy import create_engine

from sqlalchemy.orm import (
    DeclarativeBase,
    sessionmaker,
)

from app import config


# =========================================================
# DATABASE CONFIGURATION
# =========================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL"
)


if not DATABASE_URL:

    raise ValueError(
        "DATABASE_URL is missing. "
        "Add it to the project .env file."
    )


# =========================================================
# SQLALCHEMY BASE
# =========================================================

class Base(
    DeclarativeBase
):
    """
    Base class for all SQLAlchemy ORM models.
    """

    pass


# =========================================================
# DATABASE ENGINE
# =========================================================

engine = create_engine(

    DATABASE_URL,

    # Check that pooled connections
    # are still alive before using them.
    pool_pre_ping=True,
)


# =========================================================
# SESSION FACTORY
# =========================================================

SessionLocal = sessionmaker(

    bind=engine,

    autoflush=False,

    expire_on_commit=False,
)


# =========================================================
# CREATE TABLES
# =========================================================

def create_database_tables() -> None:
    """
    Create application metadata tables
    that do not already exist.
    """

    # Import the models before create_all()
    # so Base.metadata knows about them.
    from app.db import models

    Base.metadata.create_all(
        bind=engine
    )