import os

from pathlib import Path

from dotenv import (
    load_dotenv,
)


# =========================================================
# PROJECT PATHS
# =========================================================
#
# __file__
#     app/config.py
#
# parent
#     app/
#
# parent.parent
#     document-intelligence-agent/
# =========================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)


# =========================================================
# ENVIRONMENT FILE
# =========================================================

ENV_FILE = (
    BASE_DIR
    / ".env"
)


load_dotenv(
    dotenv_path=
        ENV_FILE
)


# =========================================================
# HUGGING FACE
# =========================================================

HF_TOKEN = os.getenv(
    "HF_TOKEN"
)


if not HF_TOKEN:

    raise ValueError(
        "HF_TOKEN is missing. "
        f"Expected .env file at: "
        f"{ENV_FILE}"
    )


# =========================================================
# DATABASE
# =========================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL"
)


PG_CONN_STR = os.getenv(
    "PG_CONN_STR"
)


# =========================================================
# FASTAPI
# =========================================================

API_BASE_URL = os.getenv(

    "API_BASE_URL",

    "http://127.0.0.1:8000",
)