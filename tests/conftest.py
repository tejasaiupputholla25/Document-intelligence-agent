import os
import sys

from pathlib import Path

import pytest

from dotenv import load_dotenv


# =========================================================
# PROJECT ROOT
# =========================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)


if str(PROJECT_ROOT) not in sys.path:

    sys.path.insert(
        0,
        str(PROJECT_ROOT)
    )


# =========================================================
# LOAD .ENV
# =========================================================

load_dotenv(
    PROJECT_ROOT
    / ".env"
)


# =========================================================
# TEST DATABASE VARIABLES
# =========================================================

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL"
)

TEST_PG_CONN_STR = os.getenv(
    "TEST_PG_CONN_STR"
)


if not TEST_DATABASE_URL:

    raise RuntimeError(
        "TEST_DATABASE_URL is missing."
    )


if not TEST_PG_CONN_STR:

    raise RuntimeError(
        "TEST_PG_CONN_STR is missing."
    )


# =========================================================
# SAFETY CHECK
# =========================================================

if "docintel_test" not in TEST_DATABASE_URL:

    raise RuntimeError(
        "Refusing to run tests because "
        "TEST_DATABASE_URL does not point "
        "to docintel_test."
    )


if "docintel_test" not in TEST_PG_CONN_STR:

    raise RuntimeError(
        "Refusing to run pgvector tests because "
        "TEST_PG_CONN_STR does not point "
        "to docintel_test."
    )


# =========================================================
# OVERRIDE APPLICATION DATABASES
# =========================================================

os.environ[
    "DATABASE_URL"
] = TEST_DATABASE_URL


os.environ[
    "PG_CONN_STR"
] = TEST_PG_CONN_STR


os.environ[
    "HF_TOKEN"
] = "test-token-not-for-real-api-use"


# =========================================================
# DATABASE RESET FIXTURE
# =========================================================

@pytest.fixture
def reset_metadata_db():

    from app.db.database import (
        Base,
        engine,
    )

    from app.db import models


    Base.metadata.drop_all(
        bind=engine
    )

    Base.metadata.create_all(
        bind=engine
    )


    yield


    Base.metadata.drop_all(
        bind=engine
    )

    Base.metadata.create_all(
        bind=engine
    )


# =========================================================
# PGVECTOR CLEANUP FIXTURE
# =========================================================

@pytest.fixture
def clean_vector_store():

    from app.semantic_search import (
        document_store,
    )


    document_store.delete_all_documents()


    yield document_store


    document_store.delete_all_documents()


# =========================================================
# FASTAPI CLIENT FIXTURE
# =========================================================

@pytest.fixture
def client(
    monkeypatch,
    reset_metadata_db,
):

    from fastapi.testclient import (
        TestClient,
    )

    import app.api.main as api_main


    def fake_agent(
        question: str,
        session_id: str,
    ) -> str:

        return (
            f"Test answer for: {question}"
        )


    monkeypatch.setattr(
        api_main,
        "run_document_agent",
        fake_agent,
    )


    with TestClient(
        api_main.app
    ) as test_client:

        yield test_client