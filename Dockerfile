# =========================================================
# BASE IMAGE
# =========================================================

FROM python:3.12-slim-bookworm


# =========================================================
# PYTHON / PIP SETTINGS
# =========================================================

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1


# =========================================================
# WORKING DIRECTORY
# =========================================================

WORKDIR /app


# =========================================================
# SYSTEM DEPENDENCIES
# =========================================================

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*


# =========================================================
# PYTHON DEPENDENCIES
# =========================================================

COPY requirements.txt /app/requirements.txt


RUN python -m pip install --upgrade pip \
    && python -m pip install -r /app/requirements.txt


# =========================================================
# APPLICATION SOURCE
# =========================================================

COPY app /app/app

COPY streamlit_app.py /app/streamlit_app.py


# =========================================================
# RUNTIME DIRECTORIES
# =========================================================

RUN mkdir -p /app/uploads \
    /root/.cache/huggingface


# =========================================================
# DOCUMENTATION PORTS
# =========================================================

EXPOSE 8000
EXPOSE 8501


# =========================================================
# DEFAULT COMMAND
#
# Docker Compose overrides this for the frontend service.
# =========================================================

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]